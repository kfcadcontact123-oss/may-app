console.log("CHAT.JS LOADED");

/* =========================
   🔥 PERSIST STATE (FIX RESET)
========================= */

const todayKey = new Date().toISOString().slice(0, 10);

// reset mỗi ngày
const lastDate = localStorage.getItem("voiceDate");
if (lastDate !== todayKey) {
    localStorage.setItem("voiceDate", todayKey);
    localStorage.setItem("voiceCount", "0");
    localStorage.setItem("playedMessages", JSON.stringify([]));
}

let voiceCount = parseInt(localStorage.getItem("voiceCount") || "0");

let playedMessages = new Set(
    JSON.parse(localStorage.getItem("playedMessages") || "[]")
);

const MAX_VOICE = 10;

let currentAudio = null;
let isPlaying = false;


/* =========================
   🔊 PLAY VOICE
========================= */

function playVoice(btn, text) {

    if (isPlaying) return;

    const url = `/chat/voice/api/?text=${encodeURIComponent(text)}`;

    isPlaying = true;

    btn.classList.add("loading");
    btn.textContent = "Đang tạo audio...";
    btn.disabled = true;

    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = url;
    audio.preload = "auto";
    audio.style.display = "block";
    audio.style.marginTop = "6px";
    audio.style.width = "100%";

    const messageDiv = btn.parentElement;

    document.querySelectorAll(".message.playing")
        .forEach(m => m.classList.remove("playing"));

    messageDiv.classList.add("playing");

    const oldAudio = messageDiv.querySelector("audio");
    if (oldAudio) oldAudio.remove();

    messageDiv.appendChild(audio);
    currentAudio = audio;

    audio.onloadeddata = () => {
        btn.classList.remove("loading");
        btn.classList.add("ready");
        btn.textContent = "▶ Nghe lại";
        audio.play();
    };

    audio.onended = () => {
        isPlaying = false;
        btn.disabled = false;
        messageDiv.classList.remove("playing");
    };

    audio.onpause = () => {
        isPlaying = false;
        btn.disabled = false;
    };

    audio.onerror = async () => {
    isPlaying = false;
    btn.disabled = false;

    try {
        const res = await fetch(audio.src);

        // nếu backend trả JSON (limit)
        if (res.headers.get("content-type")?.includes("application/json")) {
            const data = await res.json();

            if (data.error) {
                alert(data.error);
                btn.textContent = "🚫 Hết lượt";
                return;
            }
        }

    } catch (e) {
        console.error("Voice error check failed:", e);
    }

    btn.textContent = "❌ Lỗi";
};
}


/* =========================
   COOKIE
========================= */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


/* =========================
   MAIN
========================= */

document.addEventListener("DOMContentLoaded", () => {
    // =========================
// 🔥 FIX BUTTON CŨ (CRITICAL)
// =========================
document.querySelectorAll(".voice-btn").forEach(btn => {

    const text = btn.dataset.text ||
        btn.parentElement.querySelector("span")?.textContent;

    if (!text) return;

    btn.textContent = "⏳ Đang kiểm tra...";
    btn.disabled = true;

    fetch(`/chat/voice/check/?text=${encodeURIComponent(text)}`)
        .then(res => res.json())
        .then(data => {
            if (data.exists) {
                btn.textContent = "▶ Nghe lại";
            } else {
                btn.textContent = "🔊 Nghe";
            }
            btn.disabled = false;
        })
        .catch(() => {
            btn.textContent = "🔊 Nghe";
            btn.disabled = false;
        });

});
    const input = document.getElementById("chat-input");
    const box = document.getElementById("chat-box");
    const sendBtn = document.getElementById("send-btn");

    if (!input || !box) return;

    /* =========================
       AUTO RESIZE
    ========================= */

    function autoResize() {
        input.style.height = "auto";
        input.style.height = input.scrollHeight + "px";
    }

    input.addEventListener("input", autoResize);

    /* =========================
       CLICK VOICE (EVENT DELEGATION)
    ========================= */

    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".voice-btn");
        if (!btn) return;

        const text = btn.dataset.text ||
            btn.parentElement.querySelector("span")?.textContent;

        if (!text) return;

        playVoice(btn, text);
    });

    /* =========================
       SCROLL
    ========================= */

    function scrollToBottomInstant() {
        box.scrollTop = box.scrollHeight;
    }

    requestAnimationFrame(scrollToBottomInstant);
    setTimeout(scrollToBottomInstant, 120);

    function smoothScroll() {
        box.scrollTo({
            top: box.scrollHeight,
            behavior: "smooth"
        });
    }

    /* =========================
       SEND MESSAGE
    ========================= */

    async function sendMessage() {

        const message = input.value.trim();
        if (!message) return;

        input.value = "";
        input.style.height = "auto";

        addUserMessage(message);
        showTyping();
        function pollMessage(messageId) {

    const interval = setInterval(async () => {

        try {
            const res = await fetch(`/chat/status/${messageId}/`);
            const data = await res.json();

            console.log("POLL:", data); // debug

            // 🔥 FIX QUAN TRỌNG
            if (!data || !data.response) {
                return; // chưa có data → tiếp tục poll
            }

            if (data.response === "__thinking__") {
                return; // vẫn đang xử lý
            }

            // ✅ chỉ chạy khi có response thật
            clearInterval(interval);

            removeTyping();
            typeBotMessage(data.response);

        } catch (e) {
            console.error("Polling error:", e);
        }

    }, 1500);
}

        try {
            const res = await fetch("/chat/api/", {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ message })
            });
            if (!res.ok) {
    const text = await res.text();
    console.error("SERVER RESPONSE:", text);
    throw new Error("Server error");
}

            const data = await res.json();

            pollMessage(data.message_id);

        } catch (e) {
            removeTyping();
            typeBotMessage("Không kết nối được với máy chủ AI.");
        }
    }

    input.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.onclick = sendMessage;

    /* =========================
       UI
    ========================= */

    function addUserMessage(text) {
        const div = document.createElement("div");
        div.className = "message user";
        div.textContent = text;
        box.appendChild(div);
        smoothScroll();
    }

    function showTyping() {
        const typing = document.createElement("div");
        typing.id = "typing";
        typing.className = "typing";
        typing.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>`;
        box.appendChild(typing);
        smoothScroll();
    }

    function removeTyping() {
        document.getElementById("typing")?.remove();
    }

    function typeBotMessage(text) {
        

    const div = document.createElement("div");
    div.className = "message bot";

    const span = document.createElement("span");
    div.appendChild(span);

    const btn = document.createElement("button");
    btn.className = "voice-btn";

    // 🔥 ban đầu loading check
    btn.textContent = "⏳ Đang kiểm tra...";
    btn.disabled = true;
    btn.dataset.text = text;

    div.appendChild(btn);
    box.appendChild(div);

    // =========================
    // 🔥 CHECK BACKEND CACHE
    // =========================
    fetch(`/chat/voice/check/?text=${encodeURIComponent(text)}`)
        .then(res => res.json())
        .then(data => {
            if (data.exists) {
                btn.textContent = "▶ Nghe lại";
            } else {
                btn.textContent = "🔊 Nghe";
            }
            btn.disabled = false;
        })
        .catch(() => {
            btn.textContent = "🔊 Nghe";
            btn.disabled = false;
        });

    // =========================
    // TYPE EFFECT
    // =========================
    let i = 0;

    function type() {
        if (i < text.length) {
            span.textContent += text.charAt(i);
            i++;
            smoothScroll();
            setTimeout(type, 15);
        }
    }

    type();
}
});


/* =========================
   HARD RESET UI
========================= */

window.addEventListener("pageshow", () => {
    const widget = document.getElementById("chat-widget");
    if (!widget) return;

    widget.classList.remove("chat-expanding", "chat-expand-full");
    widget.removeAttribute("style");

    void widget.offsetHeight;
});