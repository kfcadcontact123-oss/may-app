from .models import UserMemory, ChatMessage
from .local_ai import generate_local_reply
from .memory import store_memory, get_relevant_memory
from chat.services.ai_emotion import detect_emotion
from chat.services.ai_style import get_style_prompt
from stress_app.stress_engine import calculate_stress
from django.conf import settings
from stress_app.utils import get_yesterday_stress

import vertexai
from vertexai.generative_models import GenerativeModel

# =============================
# INIT
# =============================
vertexai.init(
    project=settings.GOOGLE_CLOUD_PROJECT,
    location="us-central1"
)

MODEL_NAME = "gemini-2.5-flash"

# =============================
# SYSTEM STYLE (MÂY CORE)
# =============================
SYSTEM_STYLE = """
Bạn là Mây — một người bạn đồng hành cảm xúc.

QUY TẮC:
- Nói tự nhiên như người thật
- Không robot, không khô
- Không trả lời cụt
- Luôn trọn câu
- Đồng cảm trước, lời khuyên sau
- Giữ vibe ấm áp, nhẹ nhàng

Không đóng vai bác sĩ.
"""

# =============================
# MODEL CACHE
# =============================
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = GenerativeModel(MODEL_NAME)
        except Exception:
            _model = None
    return _model


# =============================
# HISTORY
# =============================
def get_chat_history(user, limit=4):
    messages = (
        ChatMessage.objects
        .filter(user=user)
        .order_by("-created_at")[:limit]
    )

    history = ""
    for m in reversed(messages):
        history += f"User: {m.message}\nMây: {m.response}\n"

    return history


# =============================
# MEMORY
# =============================
def get_user_memory(user):
    memory, _ = UserMemory.objects.get_or_create(user=user)
    return memory


# =============================
# SAFE EXTRACT
# =============================
def extract_text(response):
    try:
        texts = []

        for cand in response.candidates:
            parts = cand.content.parts
            for p in parts:
                if hasattr(p, "text") and p.text:
                    texts.append(p.text)

        full_text = " ".join(texts).strip()

        return full_text if full_text else None

    except Exception as e:
        print("EXTRACT ERROR:", e)
        return None

# =============================
# MAIN AI
# =============================
def generate_ai_reply(user, message=None, mode="chat", extra_context=""):

    try:
        model = get_model()
        if not model:
            return generate_local_reply(message or extra_context)

        memory = get_user_memory(user)
        history = get_chat_history(user)
        long_memory = get_relevant_memory(user)

        age = memory.age if hasattr(memory, "age") else None
        style = get_style_prompt(age)

        # =============================
        # MODE: CHAT
        # =============================
        if mode == "chat":

            if not message:
                return "Bạn chưa nhập gì mà."

            emotion = detect_emotion(message)
            calculate_stress(user, emotion)

            mode_rules = ""

            if emotion in ["sad", "very_sad"]:
                mode_rules = "Ưu tiên đồng cảm, nói nhẹ."
            elif emotion == "critical":
                mode_rules = "Cực kỳ nhẹ nhàng, giữ user lại."

            prompt = f"""
{SYSTEM_STYLE}

STYLE:
{style}

{mode_rules}

MEMORY:
{memory.summary}

LONG MEMORY:
{long_memory}

HISTORY:
{history}

User: "{message}"

Mây:
"""

        # =============================
        # MODE: RECAP (🔥 QUAN TRỌNG)
        # =============================
        elif mode == "recap":
            prompt = f"""
{SYSTEM_STYLE}

Ngữ cảnh:
{extra_context}

Nhiệm vụ:
Viết một tin nhắn recap nhẹ nhàng về ngày hôm nay.

Yêu cầu:
- Nhắc trạng thái stress (tăng / giảm / ổn định)
- Giọng ấm áp như một người bạn
- Nói về cảm xúc tổng thể
- Gợi ý 1 điều nhỏ cho ngày mai

Không phân tích sâu.
Không liệt kê.

Mây:
"""
        elif mode == "recap_feel":
            prompt = f"""
{SYSTEM_STYLE}

Viết 1 câu ngắn (tối đa 15 từ) mô tả cảm xúc CỦA NGƯỜI DÙNG trong ngày hôm nay.

QUAN TRỌNG:
- Chủ thể phải là "bạn"
- Không dùng "Mây"
- Không dùng "tôi"
- Không dùng "mình"
- Không nói về bản thân người nói
- Không lời khuyên
- Chỉ 1 câu duy nhất

Ví dụ:
"Hôm nay bạn có vẻ hơi mệt nhưng vẫn đang cố gắng."
"Hôm nay bạn cảm thấy nhẹ nhàng và dễ chịu hơn."

Mây:
"""

        else:
            return "Mode không hợp lệ."

        # =============================
        # CALL MODEL
        # =============================
        response = model.generate_content(
            prompt,
            generation_config={
        "max_output_tokens": 1500,   # 🔥 TĂNG MẠNH
        "temperature": 0.7,
        "top_p": 0.95,
        "candidate_count": 1,        # 🔥 QUAN TRỌNG
        }
        )

        text = extract_text(response)

        if not text:
            return generate_local_reply(message or extra_context)

        text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])

        # 🔥 SAVE MEMORY (chỉ chat)
        if mode == "chat" and message:
            store_memory(user, message)

        return text

    except Exception as e:
        print("AI ERROR:", e)
        return generate_local_reply(message or extra_context)