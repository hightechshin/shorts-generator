import os
import requests
import subprocess
from flask import Flask, request
from datetime import datetime, timedelta
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
        return file_name
    return None


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
    if res.status_code == 200:
        return res.json().get("signedURL")
    else:
        print("❌ Signed URL 생성 실패:", res.text)
        return None


def get_audio_duration(filepath):
    audio = AudioSegment.from_file(filepath)
    return audio.duration_seconds


def srt_time(seconds):
    td = timedelta(seconds=seconds)
    return str(td)[:-3].replace('.', ',').zfill(12)


def generate_srt(text, total_duration, srt_path):
    try:
        if total_duration <= 0:
            print("❌ 유효하지 않은 오디오 길이:", total_duration)
            return

        lines = textwrap.wrap(text.strip(), width=14)
        num_lines = len(lines)
        sec_per_line = total_duration / num_lines if num_lines > 0 else 1

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines):
                start = srt_time(i * sec_per_line)
                end = srt_time((i + 1) * sec_per_line)
                f.write(f"{i+1}\n{start} --> {end}\n{line}\n\n")

        print("✅ 자막 생성 완료:", srt_path)
        print("✅ 존재 여부:", os.path.exists(srt_path))

    except Exception as e:
        print("❌ SRT 생성 중 오류:", e)


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
        srt_name = f"{uid}.srt"

        image_path = os.path.join(UPLOAD_FOLDER, image_name)
        audio_path = os.path.join(UPLOAD_FOLDER, audio_name)
        output_path = os.path.join(OUTPUT_FOLDER, video_name)
        srt_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, srt_name))
        print("📁 SRT 저장 경로:", srt_path)

        with open(image_path, "wb") as f:
            f.write(r_img.content)
        with open(audio_path, "wb") as f:
            f.write(r_audio.content)

        duration = get_audio_duration(audio_path)
        print("🔍 오디오 길이 (초):", duration)

        if duration <= 0:
            return {"error": "Invalid audio duration"}, 400

        generate_srt(text, duration, srt_path)

        command = [
            "ffmpeg",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", f"subtitles={srt_path}",
            "-shortest", "-y", output_path
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("\n🔧 FFMPEG STDERR:\n", result.stderr.decode())

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return {"error": "Video generation failed"}, 500

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












