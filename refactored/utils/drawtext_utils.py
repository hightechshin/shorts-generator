import textwrap

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
    base_y = max(
        overlay_y,
        headline_area["y"] + (headline_area["h"] - line_spacing * num_lines) // 2
    )
elif bottom_area:
    base_y = max(
        overlay_y,
        bottom_area["y"] + (bottom_area["h"] - line_spacing * num_lines) // 2
    )
else:
    base_y = overlay_y

# ✅ drawtext 필터 생성
for sub in subtitles:
    wrapped_lines = textwrap.wrap(sub["text"], width=14)
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
        base_y += line_spacing

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
