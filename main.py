import os
import requests
import subprocess
import psutil
import uuid
import textwrap
import time
from flask import Flask, request
from datetime import datetime
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SUPABASE_BUCKET = "uploads"
SUPABASE_BASE = "https://bxrpebzmcgftbnlfdrre.supabase.co/storage/v1/object"
SUPABASE_PUBLIC = f"{SUPABASE_BASE}/public/{SUPABASE_BUCKET}"
SUPABASE_UPLOAD = f"{SUPABASE_BASE}/{SUPABASE_BUCKET}"
SUPABASE_SIGN = f"{SUPABASE_BASE}/sign/{SUPABASE_BUCKET}"
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_ROLE']
SUPABASE_REST = "https://bxrpebzmcgftbnlfdrre.supabase.co/rest/v1"

def fix_url(url):
    return url if url and url.startswith("http") else f"https:{url}" if url else None

def upload_to_supabase(file_content, file_name, file_type):
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file_type
    }
    upload_url = f"{SUPABASE_UPLOAD}/{file_name}"
    res = requests.post(upload_url, headers=headers, data=file_content)
    return res.status_code in [200, 201]

def generate_signed_url(file_path, expires_in=3600):
    url = f"{SUPABASE_BASE}/sign/{SUPABASE_BUCKET}/{file_path}"
    res = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        },
        json={"expiresIn": expires_in}
    )
    return res.json().get("signedURL") if res.status_code == 200 else None



@app.route("/upload_and_generate", methods=["POST"])
def upload_and_generate():
    image_url = fix_url(request.form.get("image_url"))
    audio_url = fix_url(request.form.get("mp3_url"))
    text = request.form.get("text")

    if not image_url or not audio_url or not text:
        return {"error": "image_url, mp3_url, text are required"}, 400

    try:
        r_img = requests.get(image_url)
        r_audio = requests.get(audio_url)
        if r_img.status_code != 200 or r_audio.status_code != 200:
            return {"error": "Failed to download image or audio"}, 400

        uid = str(uuid.uuid4())
        image_name = f"{uid}_bg.jpg"
        audio_name = f"{uid}_audio.mp3"
        video_name = f"{uid}_video.mp4"

        image_path = os.path.join(UPLOAD_FOLDER, image_name)
        audio_path = os.path.join(UPLOAD_FOLDER, audio_name)
        output_path = os.path.join(OUTPUT_FOLDER, video_name)

        with open(image_path, "wb") as f:
            f.write(r_img.content)
        with open(audio_path, "wb") as f:
            f.write(r_audio.content)

        # 자막 분할 및 타이밍 계산
        audio = AudioSegment.from_file(audio_path)
        audio_duration = audio.duration_seconds
        lines = textwrap.wrap(text.strip(), width=14)
        seconds_per_line = audio_duration / len(lines)
        subtitles = []
        for i, line in enumerate(lines):
            start = round(i * seconds_per_line, 2)
            end = round(start + seconds_per_line, 2)
            subtitles.append({"start": start, "end": end, "text": line})

        # drawtext 필터 생성
        font_path = "NotoSansKR-VF.ttf"
        drawtext_filters = []
        for sub in subtitles:
            alpha_expr = (
                f"if(lt(t,{sub['start']}),0,"
                f"if(lt(t,{sub['start']}+0.5),(t-{sub['start']})/0.5,"
                f"if(lt(t,{sub['end']}-0.5),1,"
                f"(1-(t-{sub['end']}+0.5)/0.5))))"
            )
            safe_text = sub['text'].replace("'", r"\'").replace(",", r"\,")
            drawtext = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{safe_text}':"
                f"fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2:"
                f"alpha='{alpha_expr}':"
                f"borderw=4:bordercolor=black:box=1:boxcolor=black@0.5:boxborderw=20:"
                f"enable='between(t,{sub['start']},{sub['end']})'"
            )
            drawtext_filters.append(drawtext)

        filterchain = "scale=1080:1920," + ",".join(drawtext_filters)

        command = [
            "ffmpeg", "-y", "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", filterchain,
            "-shortest",
            "-preset", "ultrafast",
            output_path
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=180)

        if process.returncode != 0:
            return {"error": "FFmpeg failed", "ffmpeg_output": stderr.decode()}, 500

        if not os.path.exists(output_path):
            return {"error": "Output file not found after FFmpeg"}, 500

        # 업로드
        with open(output_path, "rb") as f:
            video_uploaded = upload_to_supabase(f.read(), video_name, "video/mp4")
        with open(audio_path, "rb") as f:
            audio_uploaded = upload_to_supabase(f.read(), audio_name, "audio/mpeg")
        with open(image_path, "rb") as f:
            image_uploaded = upload_to_supabase(f.read(), image_name, "image/jpeg")

        if not (video_uploaded and image_uploaded and audio_uploaded):
            return {"error": "Upload to Supabase failed"}, 500

        time.sleep(2)  # Supabase 처리 지연 방지

        video_signed_url = get_signed_url(video_name)
        audio_signed_url = get_signed_url(audio_name)
        image_signed_url = get_signed_url(image_name)

        if not all([video_signed_url, audio_signed_url, image_signed_url]):
            return {"error": "Failed to generate one or more signed URLs"}, 500

        db_data = {
            "image_url": image_signed_url,
            "audio_url": audio_signed_url,
            "video_url": video_signed_url,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        }

        res = requests.post(
            f"{SUPABASE_REST}/videos",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json=db_data
        )

        if res.status_code not in [200, 201]:
            return {"error": "DB insert failed", "detail": res.text}, 500

        return {
            "video_url": video_signed_url,
            "image_url": image_signed_url,
            "audio_url": audio_signed_url,
            "log_id": res.json()[0]["id"]
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/")
def home():
    return "✅ Shorts Generator Flask 서버 실행 중"






































