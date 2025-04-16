from math import radians, sin, cos, sqrt, atan2

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 좌표 간 하버사인 거리 계산 (km 단위)
    """
    R = 6371.0  # 지구 반지름 (km)
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 2)

def estimate_travel_time_min(distance_km: float, speed_kmh: float = 40.0) -> int:
    """
    거리(km)와 평균 속도(km/h)를 기반으로 예상 소요 시간 계산 (분 단위)
    """
    return round((distance_km / speed_kmh) * 60)
