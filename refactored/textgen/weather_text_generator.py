def generate_weather_description(
    min_temp: float,
    max_temp: float,
    avg_humidity: float = None,
    wind_speed: float = None
) -> str:
    """
    날씨 요약 수치 → 설명 문장 조립
    """

    temp_part = f"오늘은 기온이 {min_temp}도에서 {max_temp}도 사이였고"
    
    humidity_part = ""
    if avg_humidity is not None:
        if avg_humidity >= 80:
            humidity_part = "습도가 높아 다소 답답한 느낌이 있었고"
        elif avg_humidity >= 60:
            humidity_part = "습도는 약간 높은 편이었으며"
        else:
            humidity_part = "습도는 쾌적한 수준이었고"

    wind_part = ""
    if wind_speed is not None:
        if wind_speed >= 7:
            wind_part = "바람은 강하게 불었습니다."
        elif wind_speed >= 3:
            wind_part = "바람은 약간 불었고"
        else:
            wind_part = "바람은 거의 없었습니다."

    # 문장 조립
    sentence = f"{temp_part}, {humidity_part} {wind_part}".strip()

    # 마침표 정리
    if not sentence.endswith("."):
        sentence += "."

    return sentence
