from logic.route import get_route_estimate

def test_haversine_logic():
    res = get_route_estimate(
        37.57, 126.98, 37.49, 127.02,
        use_naver=False
    )

    assert "distance_km" in res
    assert "duration_min" in res
    assert res["method"] == "haversine"

