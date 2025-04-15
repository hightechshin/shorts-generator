from typing import Dict, List
import statistics

def summarize_hourly_weather(data: Dict) -> str:
    """
    Open-Meteo API의 hourly 데이터에서 요약 문장 생성 (오늘 하루 기준)
    :param data: API 응답의 'hourly' 필드
    :return: 자연어 요약 문자열
    """

    try:
        temp_list: List[float] = data.get("temperature_2m", [])
        humidity_list: List[float] = data.get("relative_humidity_2m", [])
        wind_list: List[float] = data.get("windspeed_10m", [])

        if not temp_list:
            return "날씨 데이터를 불러오는 데 실패했습니다."

        avg_temp = round(statistics.mean(temp_list), 1)
        max_temp = max(temp_list)
        min_temp = min(temp_list)

        avg_humidity = round(statistics.mean(humidity_list), 1) if humidity_list else None
        max_wind = max(wind_list) if wind_list else None

        # 조건 기반 설명
        temp_phrase = f"기온은 {min_temp}도에서 {max_temp}도 사이로 변동했고,"
        humidity_phrase = f"습도는 평균 {avg_humidity}% 수준이며," if avg_humidity else ""
        wind_phrase = (
            f"바람은 다소 강하게 불었어요." if max_wind and max_wind > 5
            else "바람은 약했습니다." if max_wind
            else ""
        )

        return f"오늘 {temp_phrase} {humidity_phrase} {wind_phrase}".strip()

    except Exception as e:
        return f"날씨 요약 생성 중 오류 발생: {e}"
