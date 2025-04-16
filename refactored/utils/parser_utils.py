import os
import json
import requests

def parse_user_prompt(user_input: str) -> dict:
    prompt = f"""
    다음 문장에서 핵심 키워드를 JSON으로 추출해주세요.
    반드시 JSON만 반환하고, 들여쓰기 없이 한 줄로 출력하세요.

    항목:
    - time: 시간 또는 날짜
    - location: 장소
    - emotion: 감정 또는 기분 상태
    - action: 사용자의 주된 행동
    - intent: 말하는 의도 (변명, 하소연, 전달 등)
    - content_type: 콘텐츠 유형 (단막이야기, 광고, 뉴스, 일기, 하소연 중 하나)
    - headline: 영상의 제목
    - bottomline: 결론 또는 마무리 문장

    문장: "{user_input}"
    """.strip()

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
                            headers=headers, json=payload)
        res.raise_for_status()
        content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        return json.loads(content)

    except json.JSONDecodeError:
        return {"error": "❌ JSON 파싱 실패", "raw": content}
    except Exception as e:
        return {"error": str(e)}

