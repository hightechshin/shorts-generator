from flask import Blueprint, request, jsonify
from ..services.weather_summary_service import generate_weather_summary

weather_bp = Blueprint("weather", __name__)

@weather_bp.route("/weather-summary", methods=["POST"])
def weather_summary():
    try:
        data = request.get_json()
        lat = float(data["lat"])
        lon = float(data["lon"])
        time_iso = data["time"]

        summary = generate_weather_summary(lat, lon, time_iso)
        return jsonify({"summary": summary, "status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e), "status": "fail"}), 400
