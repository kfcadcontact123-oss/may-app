from vertexai.generative_models import GenerativeModel

model = GenerativeModel("gemini-2.5-flash")

def detect_emotion(message):

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