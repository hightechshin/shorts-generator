# 📁 services/video_service.py
import os
import uuid
import requests
import textwrap
from datetime import datetime
from flask import request
from ..utils.audio_utils import get_audio_duration
from ..utils.drawtext_utils import generate_drawtext_filters
from ..utils.supabase_utils import (
    fix_url, upload_to_supabase, get_signed_url, supabase_update_signed_urls
)
from ..config import SUPABASE_REST, SUPABASE_SERVICE_KEY, UPLOAD_FOLDER, OUTPUT_FOLDER

def handle_upload_and_generate(req):
    image_url = fix_url(req.form.get("image_url"))
    audio_url = fix_url(req.form.get("mp3_url"))
    text = req.form.get("text")
    user_id = req.form.get("user_id")
    template_id = req.form.get("template_id")

    if not image_url or not audio_url or not text or not template_id:
        return {"error": "image_url, mp3_url, text, template_id are required"}, 400

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

        template_res = requests.get(
            f"{SUPABASE_REST}/templates?select=*&template_id=eq.{template_id}",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        )
        if template_res.status_code != 200 or not template_res.json():
            return {"error": "Failed to fetch template from DB"}, 400

        template = template_res.json()[0]
        headline_area = template.get("headline_area", {})
        bottom_area = template.get("bottom_area", {})
        overlay_area = template.get("video_area", {})
        font_family = template.get("font_family", "Noto Sans KR")
        font_size = template.get("font_size", 54)
        font_color = template.get("font_color", "#FFFFFF")
        box_color = template.get("box_color", "#000000AA")
        overlay_x = overlay_area.get("x", 0)
        overlay_y = overlay_area.get("y", 0)
        overlay_width = overlay_area.get("w", 1080)
        overlay_height = overlay_area.get("h", 1080)

        template_image_url = fix_url(template.get("frame_url"))
        r_tpl = requests.get(template_image_url)
        template_name = f"{uid}_tpl.jpg"
        template_path = os.path.join(UPLOAD_FOLDER, template_name)
        with open(template_path, "wb") as f:
            f.write(r_tpl.content)

        drawtext_filters = generate_drawtext_filters(
            text=text,
            duration=duration,
            font_path="NotoSansKR-VF.ttf",
            font_size=font_size,
            font_color=font_color,
            box_color=box_color,
            overlay_y=overlay_y,
            video_area=overlay_area,
            headline_area=headline_area,
            bottom_area=bottom_area
        )

        filter_complex = (
            f"[1:v]scale={overlay_width}:{overlay_height}[scaled];"
            f"[0:v][scaled]overlay={overlay_x}:{overlay_y}," + ",".join(drawtext_filters)
        )

        command = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duration), "-i", template_path,
            "-loop", "1", "-t", str(duration), "-i", image_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "2:a",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            output_path
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=180)
        if process.returncode != 0:
            return {"error": "FFmpeg failed", "ffmpeg_output": stderr.decode()}, 500

        for path, name, mime in [
            (output_path, video_name, "video/mp4"),
            (audio_path, audio_name, "audio/mpeg"),
            (image_path, image_name, "image/jpeg")
        ]:
            with open(path, "rb") as f:
                if not upload_to_supabase(f.read(), name, mime):
                    return {"error": "Upload to Supabase failed"}, 500

        video_signed_url = get_signed_url(video_name)
        audio_signed_url = get_signed_url(audio_name)
        image_signed_url = get_signed_url(image_name)

        if not all([video_signed_url, audio_signed_url, image_signed_url]):
            return {"error": "Failed to generate signed URLs"}, 500

        db_data = {
            "uuid": uid,
            "image_path": f"uploads/{image_name}",
            "audio_path": f"uploads/{audio_name}",
            "video_path": f"uploads/{video_name}",
            "image_signed_url": image_signed_url,
            "audio_signed_url": audio_signed_url,
            "video_signed_url": video_signed_url,
            "signed_created_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "text": text,
            "template_id": template_id,
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

        log_id = res.json()[0]["uuid"] if res.ok else None

        return {
            "video_url": video_signed_url,
            "image_url": image_signed_url,
            "audio_url": audio_signed_url,
            "log_id": log_id
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500
