# logic/weather.py

from ..utils.openmeteo_weather import get_openmeteo_forecast
from ..textgen.weather_text_generator import generate_weather_description

def get_weather_summary(coord: dict, target_time: str) -> dict:
    """
    coord = {"lat": ..., "lon": ...}
    target_time = ISO 형식 문자열
    """
    forecast = get_openmeteo_forecast(coord["lat"], coord["lon"], target_time)

    if "error" in forecast:
        return {"summary": "", "error": forecast["error"]}

    description = generate_weather_description(
        temperature=forecast["temperature"],
        humidity=forecast["humidity"],
        windspeed=forecast["windspeed"]
    )

    return {
        "summary": description,
        "raw": forecast
    }
