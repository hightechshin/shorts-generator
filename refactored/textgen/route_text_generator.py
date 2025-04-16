# textgen/route_text_generator.py

def generate_route_description(
    from_name: str,
    to_name: str,
    distance_km: float,
    duration_min: float,
    method: str = ""
) -> str:
    """
    거리/시간 정보를 바탕으로 경로 설명 문장 생성

    Args:
        from_name: 출발지 이름
        to_name: 도착지 이름
        distance_km: 거리 (킬로미터)
        duration_min: 소요 시간 (분)
        method: 사용한 경로 방식 (naver, haversine 등)

    Returns:
        설명 텍스트 (예: "서울에서 강남까지는 약 12.3km이며, 약 25분이 소요됩니다.")
    """

    # 부가 설명
    if method == "haversine":
        suffix = " (대략적인 거리와 시간입니다)"
    elif method == "naver":
        suffix = " (실시간 교통을 반영한 예상치입니다)"
    else:
        suffix = ""

    description = (
        f"{from_name}에서 {to_name}까지는 약 {distance_km:.1f}km이며, "
        f"예상 소요 시간은 약 {int(duration_min)}분입니다.{suffix}"
    )

    return description
