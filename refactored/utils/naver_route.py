import requests
import os

# 🌱 .env에서 환경변수 불러오기 (Render에서 자동 적용됨)
NAVER_CLIENT_ID = os.getenv("NAVER_API_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_API_CLIENT_SECRET")

def get_naver_driving_info(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    client_id: str = NAVER_CLIENT_ID,
    client_secret: str = NAVER_CLIENT_SECRET
) -> dict:
    """
    네이버 길찾기 API 호출 → 거리/시간 추정
    환경변수 기반 client_id, client_secret 자동 연결됨
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"
    params = {
        "start": f"{start_lon},{start_lat}",  # ⚠️ 경도, 위도 순서
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
        print(f"❌ 네이버 길찾기 API 오류: {e}")
        return {"error": str(e), "status": "fail"}

