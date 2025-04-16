def get_required_fields_by_type(content_type: str) -> dict:
    rules = {
        "단막이야기": {
            "need_weather": False,
            "need_route": False,
            "need_location": True,
            "need_time": True,
            "need_emotion": True
        },
        "광고": {
            "need_weather": True,
            "need_route": True,
            "need_location": True,
            "need_time": True,
            "need_emotion": False
        },
        "뉴스": {
            "need_weather": True,
            "need_route": True,
            "need_location": True,
            "need_time": True,
            "need_emotion": False
        },
        "일기": {
            "need_weather": True,
            "need_route": False,
            "need_location": True,
            "need_time": True,
            "need_emotion": True
        },
        "하소연": {
            "need_weather": True,
            "need_route": True,
            "need_location": True,
            "need_time": True,
            "need_emotion": True
        }
    }
    return rules.get(content_type, {})
