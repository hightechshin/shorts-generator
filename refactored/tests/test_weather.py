from utils.openmeteo_weather import get_openmeteo_forecast

def test_weather_fetch():
    res = get_openmeteo_forecast(
        37.57, 126.98, "2025-04-16T15:00"
    )

    assert "temperature" in res
    assert "humidity" in res
    assert "windspeed" in res

