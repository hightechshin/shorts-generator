# 📁 services/video_service.py
import os
import uuid
import requests
import textwrap
from datetime import datetime
from flask import request
from ..utils.audio_utils import get_audio_duration
from ..utils.supabase_utils import (
    fix_url, upload_to_supabase, get_signed_url, supabase_update_signed_urls
)
from ..config import SUPABASE_REST, SUPABASE_SERVICE_KEY, UPLOAD_FOLDER, OUTPUT_FOLDER

def handle_upload_and_generate(req):
    image_url = fix_url(request.form.get("image_url"))
    audio_url = fix_url(request.form.get("mp3_url"))
    text = request.form.get("text")
    user_id = request.form.get("user_id")
    template_id = request.form.get("template_id")  # ✅ 추가됨

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

        audio = AudioSegment.from_file(audio_path)
        audio_duration = audio.duration_seconds
        duration = round(audio_duration, 2)  # 🔥 duration 값을 명시적으로 설정


        # ✅ 템플릿 정보 가져오기
        template_res = requests.get(
            f"{SUPABASE_REST}/templates?select=*&template_id=eq.{template_id}",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
            }
        )

        if template_res.status_code != 200 or not template_res.json():
            return {"error": "Failed to fetch template from DB"}, 400

        template = template_res.json()[0]

        headline_area_raw = template.get("headline_area")
        bottom_area_raw = template.get("bottom_area")
        overlay_area_raw = template.get("video_area")
        
        try:
            headline_area = json.loads(headline_area_raw) if isinstance(headline_area_raw, str) else headline_area_raw
            bottom_area = json.loads(bottom_area_raw) if isinstance(bottom_area_raw, str) else bottom_area_raw
            overlay_area = json.loads(overlay_area_raw) if isinstance(overlay_area_raw, str) else overlay_area_raw
        except Exception as e:
            return {"error": f"Template JSON parsing error: {str(e)}"}, 500
            
        font_family = template.get("font_family", "Noto Sans KR")
        font_size = template.get("font_size", 54)
        font_color = template.get("font_color", "#FFFFFF")
        box_color = template.get("box_color", "#000000AA")
        video_area = template.get("video_area", {})
        overlay_x = video_area.get("x", 0)
        overlay_y = video_area.get("y", 0)
        overlay_width = video_area.get("w", 1080)
        overlay_height = video_area.get("h", 1080)

        template_image_url = fix_url(template.get("frame_url"))

        # 템플릿 이미지 다운로드
        r_tpl = requests.get(template_image_url)
        template_name = f"{uid}_tpl.jpg"
        template_path = os.path.join(UPLOAD_FOLDER, template_name)
        with open(template_path, "wb") as f:
            f.write(r_tpl.content)

        lines = textwrap.wrap(text.strip(), width=14)
        seconds_per_line = audio_duration / len(lines)

        # drawtext 생성 함수
        subtitles = []
        for i, line in enumerate(lines):
            start = round(i * seconds_per_line, 2)
            end = round(start + seconds_per_line, 2)
            subtitles.append({"start": start, "end": end, "text": line})
        
        font_path = "NotoSansKR-VF.ttf"
        drawtext_filters = []
        
        # ✅ dummy drawtext: 최소 하나는 출력되게
        drawtext_filters.append(
            "drawtext=fontfile='NotoSansKR-VF.ttf':text=' ':"
            "fontcolor=white:fontsize=1:x=10:y=10:enable='between(t,0,0.5)'"
        )
        
        line_spacing = font_size + 8
        num_lines = len(subtitles)
        
        # ✅ y 좌표 기준점 계산
        if headline_area:
            base_y = max(overlay_y, headline_area["y"] + (headline_area["h"] - line_spacing * num_lines) // 2)
        elif bottom_area:
            base_y = max(overlay_y, bottom_area["y"] + (bottom_area["h"] - line_spacing * num_lines) // 2)
        else:
            base_y = overlay_y
        
        # ✅ drawtext 필터 생성
        for sub in subtitles:
            wrapped_lines = textwrap.wrap(sub["text"], width=14)  # 공백 포함 기준 14자
            for i, line in enumerate(wrapped_lines):
                y_position = base_y
                safe_text = line.replace("'", r"\'").replace(",", r"\,")
                alpha_expr = (
                    f"if(lt(t,{sub['start']}),0,"
                    f"if(lt(t,{sub['start']}+0.5),(t-{sub['start']})/0.5,"
                    f"if(lt(t,{sub['end']}-0.5),1,(1-(t-{sub['end']}+0.5)/0.5))))"
                )
        
                drawtext = (
                    f"drawtext=fontfile='{font_path}':"
                    f"text='{safe_text}':"
                    f"fontcolor={font_color}:fontsize={font_size}:"
                    f"x=(w-text_w)/2:y={y_position}:"
                    f"alpha='{alpha_expr}':"
                    f"borderw=4:bordercolor=black:box=1:boxcolor={box_color}:boxborderw=20:"
                    f"enable='between(t,{sub['start']},{sub['end']})'"
                )
                drawtext_filters.append(drawtext)
                base_y += line_spacing  # 다음 줄로 y 위치 이동
        
        # ✅ 최종 filter_complex 조립
        filter_complex = (
            f"[1:v]scale={overlay_width}:{overlay_height}[scaled];"
            f"[0:v][scaled]overlay={overlay_x}:{overlay_y}," +
            ",".join(drawtext_filters)
        )



        print("🎯 drawtext filter:", drawtext)

        
        print("🧩 TEMPLATE DEBUG ===========================")
        print("📌 template_id:", template_id)
        print("📥 template loaded:", template.get("frame_url"))
        print("🖼️ overlay area:", template.get("video_area"))
        print("🖋️ headline_area:", template.get("headline_area"))
        print("🖋️ bottom_area:", template.get("bottom_area"))
        print("🔤 font:", template.get("font_family"), template.get("font_size"), template.get("font_color"))
        print("🧱 box_color:", template.get("box_color"))
        print("--------------------------------------------")
        print("📂 image_path:", image_path, "| size:", os.path.getsize(image_path))
        print("📂 audio_path:", audio_path, "| size:", os.path.getsize(audio_path))
        print("--------------------------------------------")
      
        print("============================================")
        audio = AudioSegment.from_file(audio_path)
        audio_duration = audio.duration_seconds
        duration = round(audio_duration, 2)  # 🔥 duration 값을 명시적으로 설정


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



        
        print("🎬 FFmpeg Command:")
        print(" ".join(command))
        print(f"📏 overlay width, height: {overlay_width} {overlay_height}")
        print(f"📍 overlay position: {overlay_x} {overlay_y}")
        print("🎞️ Final output path:", output_path)


        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=180)

        # ✅ stderr 로그 출력
        print("🧨 FFmpeg STDERR ======================")
        print(stderr.decode())
        print("======================================")

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

        try:
            log_id = res.json()[0]["uuid"]
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

# 📁 services/video_service.py (계속)
def handle_get_signed_urls(request):
    from ..utils.supabase_utils import (
        supabase_get_video_by_uuid,
        supabase_update_signed_urls,
        get_signed_url
    )

    data = request.json
    uuid = data.get("uuid")
    user_id = data.get("user_id")

    if not uuid:
        return {"error": "UUID is required"}, 400

    video_row = supabase_get_video_by_uuid(uuid)
    if not video_row:
        return {"error": "Video not found"}, 404

    if user_id != video_row.get("user_id"):
        return {"error": "Unauthorized access"}, 403

    video_path = video_row.get("video_path")
    image_path = video_row.get("image_path")
    audio_path = video_row.get("audio_path")
    signed_created_at = video_row.get("signed_created_at")

    video_old = video_row.get("video_signed_url")
    image_old = video_row.get("image_signed_url")
    audio_old = video_row.get("audio_signed_url")

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

    if needs_refresh:
        signed_time = datetime.utcnow().isoformat()
        video_signed = get_signed_url(video_path)
        image_signed = get_signed_url(image_path)
        audio_signed = get_signed_url(audio_path)

        if not all([video_signed, image_signed, audio_signed]):
            return {"error": "Failed to generate signed URLs"}, 500

        patch_res = supabase_update_signed_urls(uuid, {
            "signed_created_at": signed_time,
            "video_signed_url": video_signed,
            "image_signed_url": image_signed,
            "audio_signed_url": audio_signed
        })

        if not patch_res:
            return {"error": "Failed to update signed URLs in DB"}, 500

        return {
            "video_url": video_signed,
            "image_url": image_signed,
            "audio_url": audio_signed,
            "signed_created_at": signed_time
        }, 200

    else:
        return {
            "video_url": video_old,
            "image_url": image_old,
            "audio_url": audio_old,
            "signed_created_at": signed_created_at
        }, 200

