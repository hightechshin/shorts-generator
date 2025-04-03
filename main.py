import os
import requests
import subprocess
from flask import Flask, request
from datetime import datetime
import uuid

app = Flask(__name__)

# 📁 폴더 설정
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔐 Supabase 설정
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

        # 자막 없이 영상 생성 (단순 이미지 + 오디오)
        filterchain = "scale=1080:1920"  # 단순 이미지 크기 설정

        # ffmpeg 명령어 실행
        command = [
            "ffmpeg",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-t", "35",  # mp3 길이에 맞춰 35초
            "-shortest",
            "-vf", filterchain,
            "-preset", "ultrafast",
            "-y", output_path
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



























