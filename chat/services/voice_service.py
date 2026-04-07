from google.cloud import texttospeech
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "media", "voice_cache")

def get_cache_path(text):
    def normalize_text(text):
        return text.strip().lower()
    key = hashlib.md5(normalize_text(text).encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.mp3")


def format_may_voice(text):
    # giữ đơn giản trước, không phá logic
    return f"{text}"


def synthesize_voice(text):

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = get_cache_path(text)

    # 👉 nếu đã có file → dùng lại
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()

    client = texttospeech.TextToSpeechClient()

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

    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    # 👉 save cache
    with open(path, "wb") as f:
        f.write(response.audio_content)

    return response.audio_content