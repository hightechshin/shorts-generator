from flask import Blueprint, request, jsonify
from .services.route_service import get_route_estimate

route_bp = Blueprint("route", __name__)

@route_bp.route("/route-estimate", methods=["POST"])
def route_estimate():
    try:
        data = request.get_json()

        start_lat = float(data["start_lat"])
        start_lon = float(data["start_lon"])
        end_lat = float(data["end_lat"])
        end_lon = float(data["end_lon"])
        use_naver = bool(data.get("use_naver", False))

        client_id = data.get("client_id", "")
        client_secret = data.get("client_secret", "")

        result = get_route_estimate(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            use_naver=use_naver,
            client_id=client_id,
            client_secret=client_secret
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e), "status": "fail"}), 400
