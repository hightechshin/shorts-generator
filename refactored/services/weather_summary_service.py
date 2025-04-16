from datetime import datetime
from ..utils.openmeteo_weather import get_openmeteo_forecast
from ..utils.weather_summary_util import summarize_hourly_weather

def generate_weather_summary(lat: float, lon: float, time_iso: str) -> str:
    """
    위도/경도 + ISO 시간 기반으로 날씨 요약문 생성
    """
    target_time = datetime.fromisoformat(time_iso)
    forecast = get_openmeteo_forecast(lat, lon, target_time)
    hourly_data = forecast.get("hourly", {})

    summary = summarize_hourly_weather(hourly_data)
    return summary
