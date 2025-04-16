# utils/openmeteo_weather.py

import requests
from dateutil import parser

def get_openmeteo_forecast(lat: float, lon: float, target_iso: str, timezone: str = "Asia/Seoul") -> dict:
    """
    Open-Meteo에서 예보 데이터를 받아 target 시간에 가장 가까운 값을 반환합니다.

    반환 예시:
    {
        "temperature": 18.7,
        "humidity": 62,
        "windspeed": 3.8,
        "time": "2025-04-17T16:00"
    }
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,humidity_2m,windspeed_10m"
        f"&timezone={timezone}"
    )

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humids = hourly.get("humidity_2m", [])
        winds = hourly.get("windspeed_10m", [])

        if not times or not temps or not humids or not winds:
            return {"error": "날씨 데이터 누락"}

        target_dt = parser.isoparse(target_iso)
        closest_index = min(
            range(len(times)),
            key=lambda i: abs(parser.isoparse(times[i]) - target_dt)
        )

        return {
            "temperature": temps[closest_index],
            "humidity": humids[closest_index],
            "windspeed": winds[closest_index],
            "time": times[closest_index]
        }

    except Exception as e:
        print(f"❌ Open-Meteo forecast API 실패: {e}")
        return {"error": str(e)}
