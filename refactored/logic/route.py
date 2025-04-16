from ..utils.naver_route import get_naver_driving_info
from ..utils.haversine import estimate_haversine_route

def get_route_estimate(start_lat, start_lon, end_lat, end_lon, use_naver=True, client_id="", client_secret=""):
    """
    유료 사용자면 Naver API 사용, 아니면 Haversine으로 fallback
    """
    if use_naver and client_id and client_secret:
        res = get_naver_driving_info(start_lat, start_lon, end_lat, end_lon, client_id, client_secret)
        if res.get("status") == "ok":
            return res

    return estimate_haversine_route(start_lat, start_lon, end_lat, end_lon)
