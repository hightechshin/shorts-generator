from flask import Flask
from .routes.video import video_bp
from .utils.scheduler import start_scheduler  # ✅ 스케줄러 임포트
from routes.weather import weather_bp

app = Flask(__name__)


app.register_blueprint(video_bp)
app.register_blueprint(weather_bp)


start_scheduler()  # ✅ 여기에서 한 번만 실행

@app.route("/")
def home():
    return "✅ Flask 리팩터링 구조 작동 중"

if __name__ == "__main__":
    app.run()
