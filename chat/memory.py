from .models import MemoryChunk
from .emotion import detect_emotion


def is_important(message: str) -> bool:
    text = message.lower().strip()

    # 🔥 quá ngắn → bỏ
    if len(text) < 10:
        return False

    emotion = detect_emotion(text)

    # 🔥 nếu có cảm xúc mạnh → giữ
    if emotion in ["sad", "very_sad", "stress", "critical"]:
        return True

    # 🔥 nếu có thông tin cá nhân (heuristic nhẹ)
    personal_signals = [
        "tôi", "mình", "gia đình", "công việc",
        "bạn bè", "người yêu", "học", "thi"
    ]

    if any(k in text for k in personal_signals):
        return True

    return False


def calculate_importance(message: str) -> float:
    emotion = detect_emotion(message)

    base = 0.5

    if emotion == "critical":
        base = 1.0
    elif emotion in ["very_sad", "stress"]:
        base = 0.85
    elif emotion == "sad":
        base = 0.75

    # 🔥 bonus nếu message dài (thường meaningful hơn)
    length_bonus = min(len(message) / 200, 0.2)

    return round(base + length_bonus, 2)


def store_memory(user, message):
    if not is_important(message):
        return

    MemoryChunk.objects.create(
        user=user,
        content=message,
        importance=calculate_importance(message)
    )


def get_relevant_memory(user, limit=5):
    memories = (
        MemoryChunk.objects
        .filter(user=user)
        .order_by("-importance", "-created_at")[:limit]
    )

    # 🔥 tránh trùng nội dung
    unique = []
    seen = set()

    for m in memories:
        if m.content not in seen:
            unique.append(m.content)
            seen.add(m.content)

    return "\n".join(unique[:limit])