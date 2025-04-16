import requests

def dispatch_to_video_api(data: dict) -> dict:
    """
    영상 제작 서버로 최종 데이터 POST 전송
    """
    try:
        res = requests.post("https://your-render-server.com/upload_and_generate", json=data)
        res.raise_for_status()
        return res.json()  # 영상 URL or uuid 반환 예상

    except Exception as e:
        print("❌ 영상 생성 API 호출 실패:", e)
        return {"error": str(e)}
