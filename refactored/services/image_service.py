import random
import requests

def get_image_url(is_paid: bool, prompt: str = "", default_pool=None) -> str:
    """
    유료/무료 여부에 따라 이미지 URL 반환
    유료: DALL·E API로 생성
    무료: 기본 이미지 중 랜덤 선택
    """
    if not is_paid:
        return random.choice(default_pool or DEFAULT_IMAGE_POOL)

    # 유료 → DALL·E API 호출
    try:
        dalle_url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer YOUR_OPENAI_KEY",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        res = requests.post(dalle_url, headers=headers, json=payload)
        res.raise_for_status()
        img_url = res.json()["data"][0]["url"]
        return img_url
    except Exception as e:
        print("❌ DALL·E 오류 fallback → 기본 이미지 사용:", e)
        return random.choice(default_pool or DEFAULT_IMAGE_POOL)
