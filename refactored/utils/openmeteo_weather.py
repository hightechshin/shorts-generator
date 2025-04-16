# utils/openmeteo_weather.py

import requests
from datetime import datetime
from dateutil import parser

def get_nearest_weather(lat: float, lon: float, target_iso: str, timezone: str = "Asia/Seoul") -> dict:
    """
    Open-Meteo API를 호출하고 target_iso 시간에 가장 가까운 날씨 데이터를 반환
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
        times = data.get("hourly", {}).get("time", [])
        temps = data.get("hourly", {}).get("temperature_2m", [])
        humids = data.get("hourly", {}).get("humidity_2m", [])
        winds = data.get("hourly", {}).get("windspeed_10m", [])

        if not times:
            return {"error": "날씨 데이터 없음"}

        # 🕒 가장 가까운 시간 찾기
        target_dt = parser.isoparse(target_iso)
        min_diff = float("inf")
        index = -1

        for i, t in enumerate(times):
            dt = parser.isoparse(t)
            diff = abs((dt - target_dt).total_seconds())
            if diff < min_diff:
                min_diff = diff
                index = i

        return {
            "temperature": temps[index],
            "humidity": humids[index],
            "windspeed": winds[index],
            "time": times[index]
        }

    except Exception as e:
        print(f"❌ Open-Meteo 호출 실패: {e}")
        return {"error": str(e)}
