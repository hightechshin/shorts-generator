from flask import Flask
from routes.video import video_bp

app = Flask(__name__)
app.register_blueprint(video_bp)

@app.route("/")
def home():
    return "✅ Flask 리팩터링 구조 작동 중"

if __name__ == "__main__":
    app.run()