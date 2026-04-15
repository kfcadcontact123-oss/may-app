from google.cloud import texttospeech
from google.oauth2 import service_account
import hashlib
import os
import json
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "media", "voice_cache")


def get_tts_client():
    try:
        if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
            path = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]

            credentials = service_account.Credentials.from_service_account_file(path)
            return texttospeech.TextToSpeechClient(credentials=credentials)

        return texttospeech.TextToSpeechClient()

    except Exception as e:
        logger.warning(f"TTS init failed: {e}")
        return None


# tạo client 1 lần
client = get_tts_client()


def get_cache_path(text):
    def normalize_text(text):
        return text.strip().lower()
    key = hashlib.md5(normalize_text(text).encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.mp3")


def format_may_voice(text):
    return f"{text}"


def synthesize_voice(text):

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = get_cache_path(text)

    # 👉 nếu đã có cache → dùng luôn
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()

    # 👉 nếu client lỗi → không crash
    if client is None:
        logger.warning("TTS client unavailable")
        return b""  # trả audio rỗng thay vì crash

    formatted_text = format_may_voice(text)

    input_text = texttospeech.SynthesisInput(text=formatted_text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="vi-VN",
        name="vi-VN-Neural2-A"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.05,
        pitch=2.5
    )

    try:
        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )
    except Exception as e:
        logger.warning(f"TTS synthesize failed: {e}")
        return b""  # fallback nhẹ

    # 👉 save cache (fail cũng không chết)
    try:
        with open(path, "wb") as f:
            f.write(response.audio_content)
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")

    return response.audio_content