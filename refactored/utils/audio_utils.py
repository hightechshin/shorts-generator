# 📁 utils/audio_utils.py
from pydub import AudioSegment

def get_audio_duration(audio_path):
    """MP3 또는 오디오 파일의 길이를 초 단위로 반환"""
    audio = AudioSegment.from_file(audio_path)
    return round(audio.duration_seconds, 2)
