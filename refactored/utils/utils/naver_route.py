import requests

def get_naver_driving_info(
    start_lat: float, start_lon: float,
    end_lat: float, end_lon: float,
    client_id: str,
    client_secret: str
) -> dict:
    """
    네이버 길찾기 API 호출 → 거리/시간 추정
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"
    params = {
        "start": f"{start_lon},{start_lat}",
        "goal": f"{end_lon},{end_lat}",
        "option": "trafast"
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()

        route = data["route"].get("trafast")
        if not route:
            return {"error": "경로 없음"}

        summary = route[0]["summary"]
        return {
            "distance_km": round(summary["distance"] / 1000, 2),
            "duration_min": round(summary["duration"] / 60000),
            "status": "ok"
        }

    except Exception as e:
        return {"error": str(e), "status": "fail"}
