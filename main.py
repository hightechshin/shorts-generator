import os
import re
import textwrap
import uuid
import requests
import subprocess
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
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_ROLE']
SUPABASE_REST = "https://bxrpebzmcgftbnlfdrre.supabase.co/rest/v1"

FONT_PATH = "NotoSansKR-VF.ttf"

def fix_url(url):
    return url if url and url.startswith("http") else f"https:{url}" if url else None

def sanitize_drawtext(text):
    return text.strip().replace("'", "\\'").replace(":", "\\:")

def generate_drawtext_filters(text, duration, font_path=FONT_PATH):
    # 1️⃣ 자막 처리 (14자 단위 줄바꿈)
    lines = textwrap.wrap(text.strip(), width=14)
    per_line_sec = duration / len(lines)
    filters = []
    
    for i, line in enumerate(lines):
        start = round(i * per_line_sec, 2)  # 자막 시작 시간
        end = round(start + per_line_sec, 2)  # 자막 끝 시간
        safe_text = sanitize_drawtext(line)

        # 2️⃣ 간단한 alpha_expr 수정
        alpha_expr = f"if(lt(t,{start}),0,if(lt(t,{end}),1,0))"

        drawtext = (
            f"drawtext=fontfile='{font_path}':"
            f"text='{safe_text}':"
            f"fontcolor=white:fontsize=60:borderw=4:bordercolor=black:"
            f"box=1:boxcolor=black@0.5:boxborderw=20:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"alpha='{alpha_expr}':"
            f"enable='between(t,{start},{end})'"
        )
        filters.append(drawtext)

    # 전체 필터 반환
    return "scale=1080:1920," + ",".join(filters)

def upload_to_supabase(file_content, file_name, file_type):
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file_type
    }
    upload_url = f"{SUPABASE_UPLOAD}/{file_name}"
    res = requests.post(upload_url, headers=headers, data=file_content)
    return file_name if res.status_code in [200, 201] else None

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

def get_audio_duration(filepath):
    audio = AudioSegment.from_file(filepath)
    return round(audio.duration_seconds, 2)

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

        duration = get_audio_duration(audio_path)
        filter_str = generate_drawtext_filters(text, duration)

        command = [
            "ffmpeg", "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-shortest", "-t", str(min(duration, 59)),
            "-vf", filter_str,
            "-preset", "ultrafast",
            "-y", output_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("\n🔧 FFMPEG STDERR:\n", result.stderr.decode())

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            return {"error": "Video too small. drawtext may have failed."}, 500

        with open(output_path, "rb") as f:
            uploaded_path = upload_to_supabase(f.read(), video_name, "video/mp4")
        if not uploaded_path:
            return {"error": "Video upload failed"}, 500

        signed_url = generate_signed_url(uploaded_path)
        if not signed_url:
            return {"error": "Signed URL 생성 실패"}, 500

        db_data = {
            "image_url": f"{SUPABASE_PUBLIC}/{image_name}",
            "audio_url": f"{SUPABASE_PUBLIC}/{audio_name}",
            "video_url": signed_url,
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
            "video_url": signed_url,
            "log_id": res.json()[0]["id"]
        }

    except Exception as e:
        print("❌ 예외 발생:", str(e))
        return {"error": str(e)}, 500

@app.route("/")
def home():
    return "✅ Shorts Generator Flask 서버 실행 중"



















