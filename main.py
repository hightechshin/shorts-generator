import os
import requests
import subprocess
from flask import Flask, request
from datetime import datetime
import uuid
import textwrap
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

def fix_url(url):
    if not url:
        return None
    return url if url.startswith("http") else f"https:{url}"

def upload_to_supabase(file_content, file_name, file_type):
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file_type
    }
    upload_url = f"{SUPABASE_UPLOAD}/{file_name}"
    res = requests.post(upload_url, headers=headers, data=file_content)
    if res.status_code in [200, 201]:
        return f"{SUPABASE_PUBLIC}/{file_name}"
    return None

def get_audio_duration(filepath):
    audio = AudioSegment.from_file(filepath)
    return audio.duration_seconds

def format_srt_time(seconds):
    from datetime import timedelta
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    ms = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, sec = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{sec:02},{ms:03}"

def generate_srt_timed(text, total_duration, srt_path):
    lines = textwrap.wrap(text.strip(), width=14)
    num_lines = len(lines)
    sec_per_line = total_duration / num_lines
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,NotoSansKR,48,&H00FFFF00,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,20,1\n\n")
        f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for i, line in enumerate(lines):
            start = format_srt_time(i * sec_per_line).replace(",", ".")
            end = format_srt_time((i + 1) * sec_per_line).replace(",", ".")
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{line}\\N\n")

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
        ass_name = f"{uid}.ass"

        image_path = os.path.join(UPLOAD_FOLDER, image_name)
        audio_path = os.path.join(UPLOAD_FOLDER, audio_name)
        output_path = os.path.join(OUTPUT_FOLDER, video_name)
        ass_path = os.path.join(UPLOAD_FOLDER, ass_name)

        with open(image_path, "wb") as f:
            f.write(r_img.content)
        with open(audio_path, "wb") as f:
            f.write(r_audio.content)

        duration = get_audio_duration(audio_path)
        generate_srt_timed(text, duration, ass_path)

        command = [
            "ffmpeg",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", f"ass={ass_path}",
            "-shortest", "-y", output_path
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("\n🔧 FFMPEG STDERR:\n", result.stderr.decode())

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return {"error": "Video generation failed"}, 500

        with open(output_path, "rb") as f:
            video_public_url = upload_to_supabase(f.read(), video_name, "video/mp4")

        if not video_public_url:
            return {"error": "Video upload failed"}, 500

        db_data = {
            "image_url": f"{SUPABASE_PUBLIC}/{image_name}",
            "audio_url": f"{SUPABASE_PUBLIC}/{audio_name}",
            "video_url": video_public_url,
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
            "video_url": video_public_url,
            "log_id": res.json()[0]["id"]
        }

    except Exception as e:
        print("❌ 예외 발생:", str(e))
        return {"error": str(e)}, 500

@app.route("/")
def home():
    return "✅ Shorts Generator Flask 서버 실행 중"










