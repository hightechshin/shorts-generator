import requests

def reverse_geocode_naver(lat: float, lon: float, client_id: str, client_secret: str) -> dict:
    """
    네이버 지도 API로 좌표를 주소로 변환
    :param lat: 위도
    :param lon: 경도
    :param client_id: 네이버 API client ID
    :param client_secret: 네이버 API secret
    :return: 주소 정보가 담긴 dict
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
    params = {
        "coords": f"{lon},{lat}",  # ⚠️ 반드시 경도, 위도 순서
        "orders": "roadaddr,admaddr",
        "output": "json"
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ 네이버 역지오코드 실패: {e}")
        return {}
