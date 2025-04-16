def assemble_prompt(parsed: dict, controller_result: dict) -> str:
    """
    파싱 결과 + 보조 정보 → GPT용 프롬프트 조립
    """
    content_type = parsed.get("content_type", "")
    time_text = parsed.get("time_text", "")
    location_text = parsed.get("location_text", "")
    emotion = parsed.get("emotion", "")
    action = parsed.get("action", "")
    intent = parsed.get("intent", "")
    headline = parsed.get("headline", "")
    bottomline = parsed.get("bottomline", "")

    weather_text = controller_result.get("weather_text", "")
    route_text = controller_result.get("route_text", "")

    base = ""

    # 콘텐츠 타입에 따라 프롬프트 뼈대 달라짐
    if content_type == "하소연":
        base = (
            f"{time_text}에 {location_text}에서 {action} 하려 했는데, "
            f"{intent} 상황이 발생했어요. {emotion} 기분이 들었어요."
        )
    elif content_type == "광고":
        base = (
            f"{location_text}에서 경험한 걸 공유합니다. "
            f"{headline} — {bottomline}"
        )
    elif content_type == "일기":
        base = (
            f"{time_text}, {location_text}에서 {action} 했습니다. "
            f"그때 {emotion} 기분이 들었어요."
        )
    else:
        base = f"{time_text}, {location_text}에서 있었던 일입니다."

    # 보조 정보 삽입
    if weather_text:
        base += f" 날씨는 {weather_text}"
    if route_text:
        base += f" 이동 정보: {route_text}"

    return base.strip()
