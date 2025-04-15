from flask import Blueprint, request
from ..services.video_service import handle_upload_and_generate, handle_get_signed_urls

video_bp = Blueprint("video", __name__)

@video_bp.route("/upload_and_generate", methods=["POST"])
def upload():
    return handle_upload_and_generate(request)

@video_bp.route("/get_signed_urls", methods=["POST"])
def get_signed():
    return handle_get_signed_urls(request)
