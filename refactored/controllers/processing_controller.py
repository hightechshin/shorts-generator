from utils.logger import log  # 선택사항

from logic.weather import get_weather_summary  # 호출 시점에만 import
from logic.route import get_route_estimate
from textgen.route_text_generator import generate_route_description

from content_type_rules import get_required_fields_by_type

def process_parsed_result(parsed: dict, options: dict) -> dict:
    """
    GPT 파싱 결과를 받아 어떤 데이터/텍스트 조립을 실행할지 결정
    :param parsed: GPT 파싱 결과 (content_type, location, time 등 포함)
    :param options: 유료 여부, API key 등
    :return: 필요한 요약 텍스트, distance, duration 등 포함된 dict
    """

    content_type = parsed.get("content_type", "")
    coord_from = parsed.get("from_coord")
    coord_to = parsed.get("to_coord")
    location_name_from = parsed.get("location_from_name", "출발지")
    location_name_to = parsed.get("location_to_name", "도착지")
    target_time = parsed.get("time_iso", None)
    weather_context = ""
    route_context = ""

    results = {}

    needs = get_required_fields_by_type(content_type)

    # 날씨 API 조건 분기
    if needs.get("need_weather") and coord_from and target_time:
        log("🌤 날씨 정보 호출")
        weather_context = get_weather_summary(coord_from, target_time)
        results["weather_summary"] = weather_context

    # 거리/이동 시간 계산 조건 분기
    if needs.get("need_route") and coord_from and coord_to:
        log("🛣 경로 계산 시작")
        route_data = get_route_estimate(
            start_lat=coord_from["lat"],
            start_lon=coord_from["lon"],
            end_lat=coord_to["lat"],
            end_lon=coord_to["lon"],
            use_naver=options.get("is_paid", False),
            client_id=options.get("naver_client_id", ""),
            client_secret=options.get("naver_client_secret", "")
        )
        results.update(route_data)

        # 설명 문장 자동 생성
        route_sentence = generate_route_description(
            from_name=location_name_from,
            to_name=location_name_to,
            distance_km=route_data["distance_km"],
            duration_min=route_data["duration_min"],
            method=route_data["method"]
        )
        results["route_text"] = route_sentence

    results["content_type"] = content_type
    results["used_fields"] = needs
    return results
