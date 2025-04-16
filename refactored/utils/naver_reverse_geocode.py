import requests
import os
from dotenv import load_dotenv
load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_API_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_API_CLIENT_SECRET")

def reverse_geocode_naver(lat: float, lon: float, client_id: str = NAVER_CLIENT_ID, client_secret: str = NAVER_CLIENT_SECRET) -> dict:
    """
    네이버 지도 API로 좌표를 주소로 변환
    :return: {'address': '서울특별시 중구 세종대로 110'} 같은 형태
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
    params = {
        "coords": f"{lon},{lat}",
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
        data = res.json()

        # ✅ 주소 텍스트 추출
        results = data.get("results", [])
        if not results:
            return {"address": "주소 없음"}

        for item in results:
            if item["name"] == "roadaddr" and "roadAddress" in item:
                return {"address": item["roadAddress"]["address"]}

        for item in results:
            if item["name"] == "admaddr" and "region" in item:
                region = item["region"]
                address = " ".join([
                    region["area1"]["name"],
                    region["area2"]["name"],
                    region["area3"]["name"]
                ])
                return {"address": address}

        return {"address": "주소 추출 실패"}

    except Exception as e:
        print(f"❌ 네이버 역지오코드 실패: {e}")
        return {"address": "오류 발생"}
}
