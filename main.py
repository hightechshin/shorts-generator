import os
import requests
import subprocess
import psutil
import uuid
import textwrap
import time
from flask import Flask, request
from datetime import datetime, timezone, timedelta
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SUPABASE_BUCKET = "uploads"
SUPABASE_STORAGE = "https://bxrpebzmcgftbnlfdrre.supabase.co/storage/v1"
SUPABASE_BASE = "https://bxrpebzmcgftbnlfdrre.supabase.co/storage/v1/object"
SUPABASE_PUBLIC = f"{SUPABASE_BASE}/public/{SUPABASE_BUCKET}"
SUPABASE_UPLOAD = f"{SUPABASE_BASE}/{SUPABASE_BUCKET}"
SUPABASE_SIGN = f"{SUPABASE_BASE}/sign/{SUPABASE_BUCKET}"
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_ROLE']
SUPABASE_REST = "https://bxrpebzmcgftbnlfdrre.supabase.co/rest/v1"
TTL_SECONDS = 3600

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

def get_signed_url(file_name):
    if file_name.startswith("uploads/"):
        file_name = file_name.replace("uploads/", "", 1)

    url = f"{SUPABASE_STORAGE}/object/sign/{SUPABASE_BUCKET}/{file_name}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post(url, headers=headers, json={"expiresIn": TTL_SECONDS})
    if res.status_code == 200:
        signed_path = res.json().get("signedURL")
        return f"{SUPABASE_STORAGE}{signed_path}"
    return None

from datetime import datetime, timedelta

def delete_expired_signed_urls():
    """Supabase DB에서 1시간 이상 지난 signed_* 필드를 삭제"""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    cutoff_iso = cutoff.isoformat()

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Supabase REST API - PATCH
    payload = {
        "video_signed_url": None,
        "audio_signed_url": None,
        "image_signed_url": None,
        "signed_created_at": None
    }

    # 필터: signed_created_at이 1시간보다 이전이면
    url = f"{SUPABASE_REST}/videos?signed_created_at=lt.{cutoff_iso}"

    res = requests.patch(url, headers=headers, json=payload)

    if res.status_code in [200, 204]:
        print("✅ TTL cleanup 완료")
    else:
        print("❌ TTL cleanup 실패:", res.text)

def supabase_get_video_by_uuid(uuid):
    res = requests.get(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    )
    return res.json()[0] if res.status_code == 200 and res.json() else None

def supabase_update_signed_urls(uuid, data: dict):
    res = requests.patch(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )
    return res.status_code in [200, 204]

@app.route("/upload_and_generate", methods=["POST"])
def upload_and_generate():
    image_url = fix_url(request.form.get("image_url"))
    audio_url = fix_url(request.form.get("mp3_url"))
    text = request.form.get("text")
    user_id = request.form.get("user_id")  # ✅ 요기 추가

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

        audio = AudioSegment.from_file(audio_path)
        audio_duration = audio.duration_seconds
        lines = textwrap.wrap(text.strip(), width=14)
        seconds_per_line = audio_duration / len(lines)
        subtitles = []
        for i, line in enumerate(lines):
            start = round(i * seconds_per_line, 2)
            end = round(start + seconds_per_line, 2)
            subtitles.append({"start": start, "end": end, "text": line})

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

        video_path = f"uploads/{video_name}"
        audio_path_db = f"uploads/{audio_name}"
        image_path_db = f"uploads/{image_name}"

        with open(output_path, "rb") as f:
            video_uploaded = upload_to_supabase(f.read(), video_name, "video/mp4")
        with open(audio_path, "rb") as f:
            audio_uploaded = upload_to_supabase(f.read(), audio_name, "audio/mpeg")
        with open(image_path, "rb") as f:
            image_uploaded = upload_to_supabase(f.read(), image_name, "image/jpeg")

        if not (video_uploaded and image_uploaded and audio_uploaded):
            return {"error": "Upload to Supabase failed"}, 500

        time.sleep(2)

        video_signed_url = get_signed_url(video_name)
        audio_signed_url = get_signed_url(audio_name)
        image_signed_url = get_signed_url(image_name)

        if not all([video_signed_url, audio_signed_url, image_signed_url]):
            return {"error": "Failed to generate one or more signed URLs"}, 500

        db_data = {
            "uuid": uid,
            "image_path": image_path_db,
            "audio_path": audio_path_db,
            "video_path": video_path,
            "image_signed_url": image_signed_url,
            "audio_signed_url": audio_signed_url,
            "video_signed_url": video_signed_url,
            "signed_created_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
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

        try:
            log_id = res.json()[0]["id"]
        except Exception as e:
            print("❌ Failed to get log_id:", res.text)
            log_id = None
        
        return {
            "video_url": video_signed_url,
            "image_url": image_signed_url,
            "audio_url": audio_signed_url,
            "log_id": log_id
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/get_signed_urls", methods=["POST"])
def get_signed_urls():
    data = request.json
    uuid = data.get("uuid")
    user_id = data.get("user_id")

    if not uuid:
        return {"error": "UUID is required"}, 400

    # 1. Supabase에서 영상 데이터 가져오기
    res = requests.get(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
        }
    )

    if res.status_code != 200 or not res.json():
        return {"error": "Video not found"}, 404

    video_row = res.json()[0]

     # 2. ✅ 유저 인증 체크
    if user_id != video_row["user_id"]:
        return {"error": "Unauthorized access"}, 403

    # 2. 필요한 경로 추출
    video_path = video_row.get("video_path")
    image_path = video_row.get("image_path")
    audio_path = video_row.get("audio_path")
    signed_created_at = video_row.get("signed_created_at")

    # 1. signed_created_at 만료 여부 체크
needs_refresh = False
if not signed_created_at:
    needs_refresh = True
else:
    try:
        last_time = datetime.fromisoformat(signed_created_at)
        if datetime.utcnow() - last_time > timedelta(hours=1):
            needs_refresh = True
    except:
        needs_refresh = True

# 2. 만료되었으면 signed_created_at 업데이트
if needs_refresh:
    signed_time = datetime.utcnow().isoformat()
    patch_res = requests.patch(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        },
        json={"signed_created_at": signed_time}
    )
    print("📦 PATCH 응답:", patch_res.status_code, patch_res.text)
        if patch_res.status_code not in [200, 204]:
        print("❌ signed_created_at 업데이트 실패:", patch_res.text)

        signed_created_at = signed_time  # 응답용으로 갱신

        # 3. signed URL 생성
        video_signed = get_signed_url(video_path)
        image_signed = get_signed_url(image_path)
        audio_signed = get_signed_url(audio_path)
    
        # 4. 최종 응답
        return {
            "video_url": video_signed,
            "image_url": image_signed,
            "audio_url": audio_signed,
            "signed_created_at": signed_created_at
        }, 200



@app.route("/cleanup_ttl", methods=["POST"])
def cleanup_ttl():
    try:
        delete_expired_signed_urls()
        return {"status": "cleanup completed"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/")
def home():
    return "✅ Shorts Generator Flask 서버 실행 중"







































