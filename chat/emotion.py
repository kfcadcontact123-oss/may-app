def detect_emotion(text):
    text = text.lower()

    # 🔥 NGUY HIỂM
    if any(w in text for w in [
        "không muốn sống", "muốn chết", "biến mất",
        "vô nghĩa", "không còn lý do sống"
    ]):
        return "critical"

    # 😵 KIỆT SỨC
    if any(w in text for w in [
        "kiệt sức", "không còn sức", "mệt mỏi",
        "quá mệt", "hết năng lượng"
    ]):
        return "exhausted"

    # 😰 STRESS
    if any(w in text for w in [
        "stress", "áp lực", "lo lắng", "căng thẳng"
    ]):
        return "stress"

    # 😢 BUỒN
    if any(w in text for w in [
        "buồn", "cô đơn", "trống rỗng", "chán"
    ]):
        return "sad"

    return "neutral"