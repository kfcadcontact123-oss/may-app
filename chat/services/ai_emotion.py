import os
import json
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

# =============================
# LAZY INIT (QUAN TRỌNG)
# =============================
_initialized = False

def init_vertex():
    global _initialized
    if _initialized:
        return

    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if not creds_json:
        raise Exception("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON")

    creds_dict = json.loads(creds_json)

    credentials = service_account.Credentials.from_service_account_info(creds_dict)

    vertexai.init(
        project=creds_dict["project_id"],
        location="us-central1",
        credentials=credentials
    )

    _initialized = True


# =============================
# MODEL (GIỮ NGUYÊN)
# =============================



# =============================
# MAIN FUNCTION (CHỈ THÊM INIT)
# =============================
def detect_emotion(message):

    init_vertex()  # 🔥 THÊM DUY NHẤT DÒNG NÀY
    model = GenerativeModel("gemini-2.5-flash")
    prompt = f"""
Bạn là AI phân tích cảm xúc người dùng.

Phân loại cảm xúc thành 1 trong các nhãn sau:
- neutral
- stress
- sad
- very_sad
- critical

LUẬT:
- Dựa vào NGỮ CẢNH, không chỉ từ khóa
- Nếu có dấu hiệu tiêu cực nhẹ → stress
- Buồn kéo dài → sad
- Tuyệt vọng → very_sad
- Có ý định nguy hiểm → critical

Chỉ trả về 1 từ duy nhất.

User message:
"{message}"
"""

    response = model.generate_content(prompt)
    return response.text.strip().lower()