from ..utils.naver_route import get_naver_driving_info
from ..utils.haversine import estimate_haversine_route

def get_route_estimate(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    use_naver: bool = False,
    client_id: str = "",
    client_secret: str = ""
) -> dict:
    """
    유료/무료 사용자에 따라 자동 분기하여 거리/이동시간 계산
    """

    if use_naver and client_id and client_secret:
        # 유료 사용자 → 네이버 API 사용
        naver_result = get_naver_driving_info(
            start_lat, start_lon, end_lat, end_lon, client_id, client_secret
        )

        if naver_result.get("status") == "ok":
            naver_result["method"] = "naver"
            return naver_result
        else:
            # 실패 시 fallback
            fallback_dist = haversine_km(start_lat, start_lon, end_lat, end_lon)
            fallback_time = estimate_travel_time_min(fallback_dist)
            return {
                "distance_km": fallback_dist,
                "duration_min": fallback_time,
                "method": "fallback-haversine",
                "error": naver_result.get("error", "네이버 API 실패")
            }

    else:
        # 무료 사용자 → 하버사인 추정
        distance = haversine_km(start_lat, start_lon, end_lat, end_lon)
        duration = estimate_travel_time_min(distance)

        return {
            "distance_km": distance,
            "duration_min": duration,
            "method": "haversine"
        }
