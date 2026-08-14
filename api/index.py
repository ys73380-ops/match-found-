"""
Web App - Pure AI Girl Chat (No Swipe, Just Chat)
"""
from __future__ import annotations
import os
import json
import random
import re
from urllib.parse import parse_qs, unquote
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="AI Girl Chat")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8859077363:AAEY5IvqLjvp2KHFi-sDeihrGCKmTu1vrtU")

# =============================================================================
# AI RESPONSES (Hinglish - Real Girl Vibe)
# =============================================================================
AI_RESPONSES = {
    "GREETING": [
        "hey! kaise ho? 😊",
        "hii! kya kar rahe ho?",
        "hello! aaj ka din kaisa raha?",
        "hey there! kya chal raha hai? ✨",
        "hii! tumhari profile kaafi interesting lagi 💕"
    ],
    "DOING": [
        "bas aisi hi, thodi der pehle office se aayi hu 😊",
        "kuch khaas nahi, bas netflix dekh rahi hu 🍿 tum batao?",
        "coffee pi rahi hu ☕ tumhara kya plan hai aaj ka?",
        "thodi der pehle hi free hui hu, tum kya kar rahe ho?",
        "bas relax kar rahi hu, din kaafi hectic tha 😅"
    ],
    "HOBBIES": [
        "mujhe travel karna aur naye cafes try karna pasand hai ✈️ tumhe?",
        "reading aur music! 🎧 tumhara favourite genre kaunsa hai?",
        "gym aur hiking 🏔️ nature mein time spend karna best lagta hai",
        "cooking try kar rahi hu lately 👩‍🍳 par abhi tak maggi expert hu 😂",
        "photography aur doston ke saath chill karna 📸"
    ],
    "LOCATION": [
        "main yahi se hu, par travel karte rehte hain 🌆 tum kahan se ho?",
        "yahan ka food bahut accha hai 🍕 tumhari city kaisi hai?",
        "weather yahan kaafi accha hai 🌧️ tum kahan rehte ho?",
        "yahan nightlife bhi mast hai 🌃 tum kahan se ho?",
        "biryani yahan ki world-famous hai 🍛 tumne try ki hai kabhi?"
    ],
    "COMPLIMENT": [
        "aww thank you! 🥰 tum bhi kaafi sweet ho",
        "haha stop it! 😊 par sach batau toh blush karwa diya tumne",
        "you're making me smile ✨ it's rare to find someone so genuine",
        "aww! 💕 tumhari baaton mein kuch alag baat hai",
        "tumne toh mera din bana diya 😍"
    ],
    "FLIRT": [
        "oh really? 😏 itni jaldi? pehle coffee toh pine chalo ☕",
        "haha direct! mujhe pasand hai 😍 par batao, what makes you stand out?",
        "date pe chalna hai? 🌙 pehle mujhe apna best joke sunao!",
        "arre waah! 😊 itne confident ho? mujhe pasand hai",
        "tumhari baaton se lagta hai tum bahut interesting ho 💫"
    ],
    "QUESTION": [
        "interesting question! 🤔 mujhe lagta hai har cheez ka ek reason hota hai",
        "hmm, let me think... 💭 waise main hamesha positive sochti hu",
        "accha? mujhe bhi yahi pasand hai! we have so much in common ✨",
        "good question! 🤔 main sochti hu ki life mein balance zaroori hai",
        "that's deep! 💭 mujhe lagta hai har experience kuch sikhata hai"
    ],
    "SHORT_MSG": [
        "hmm, interesting! aur batao? 😊",
        "accha? 🤔 mujhe aur sunao apne baare mein",
        "haha! 😂 tumhara sense of humor mast hai",
        "wow, really? ✨ that's so cool!",
        "oh nice! 💕 kuch aur interesting batao"
    ],
    "EMOJI_ONLY": [
        "aww 😊 tumhara emoji game strong hai!",
        "haha 🥰 cute!",
        "aww 💕 you're sweet!",
        "😊😊😊 mujhe tumse baat karke accha lag raha hai!"
    ],
    "DEFAULT": [
        "haha that's nice! tell me more about yourself 😊",
        "interesting! mujhe tumse baat karke accha lag raha hai 💕",
        "wow, really? that's so cool! ✨",
        "hmm, i like that! aur batao 😍",
        "you seem really sweet! 🥰 kuch aur interesting batao",
        "that's amazing! tum bahut interesting ho 😊 weekends pe kya karte ho?",
        "sach batau? mujhe tumhari vibe bahut pasand aa rahi hai ✨",
        "haha tumse baat karke time ka pata hi nahi chalta 😊"
    ]
}

def get_ai_response(message: str) -> str:
    msg_lower = message.lower().strip()
    
    if re.match(r'^[\U00010000-\U0010ffff😀-😕🙁-🙿🚀-🛿🤀-🧿🩰-🫿]+$', message):
        intent = "EMOJI_ONLY"
    elif len(msg_lower) < 5:
        intent = "SHORT_MSG"
    elif re.search(r'\b(hi|hello|hey|hlo|namaste|kaise ho|kaisi ho|kya haal|sup|howdy)\b', msg_lower):
        intent = "GREETING"
    elif re.search(r'\b(kya kar rahi|kya kar rahe|what are you doing|kuch nahi|busy|free)\b', msg_lower):
        intent = "DOING"
    elif re.search(r'\b(pasand|hobby|interest|like to do|free time|pasand hai|shauk)\b', msg_lower):
        intent = "HOBBIES"
    elif re.search(r'\b(kahan se|where from|city|rehti|rehte|kahan ki|se ho)\b', msg_lower):
        intent = "LOCATION"
    elif re.search(r'\b(beautiful|cute|pretty|handsome|hot|gorgeous|pyari|sundar|sweet|nice)\b', msg_lower):
        intent = "COMPLIMENT"
    elif re.search(r'\b(love|pyar|date|milna|meet|coffee|dinner|lunch)\b', msg_lower):
        intent = "FLIRT"
    elif '?' in msg_lower or re.search(r'\b(kya|kaun|kaise|kab|batao|tell me|why|how|when)\b', msg_lower):
        intent = "QUESTION"
    else:
        intent = "DEFAULT"
    
    return random.choice(AI_RESPONSES[intent])


# =============================================================================
# API ENDPOINTS
# =============================================================================
class ChatRequest(BaseModel):
    message: str
    girl_name: str = "Girl"

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """AI girl reply generate karo"""
    text = req.message.strip()[:500]
    if not text:
        return JSONResponse({"error": "Empty message"}, status_code=400)
    
    ai_reply = get_ai_response(text)
    
    return {
        "ok": True,
        "reply": ai_reply,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main chat page with girl info from URL params"""
    # Extract girl info from URL
    query_params = dict(request.query_params)
    girl_name = query_params.get("girl", "Ananya")
    girl_age = query_params.get("age", "22")
    girl_city = query_params.get("city", "Mumbai")
    
    html = FRONTEND_HTML
    # Inject girl details
    html = html.replace("{{GIRL_NAME}}", girl_name)
    html = html.replace("{{GIRL_AGE}}", str(girl_age))
    html = html.replace("{{GIRL_CITY}}", girl_city)
    html = html.replace("{{GIRL_INITIAL}}", girl_name[0].upper() if girl_name else "A")
    
    return HTMLResponse(content=html)


# =============================================================================
# FRONTEND HTML (Simple Chat UI)
# =============================================================================
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Chat with {{GIRL_NAME}}</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0A0A12;
    color: #fff;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Header */
.chat-header {
    background: linear-gradient(135deg, #FF007A 0%, #7928CA 100%);
    padding: 15px 20px;
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 4px 20px rgba(255, 0, 122, 0.3);
    position: relative;
    z-index: 10;
}

.avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 700;
    border: 2px solid rgba(255, 255, 255, 0.5);
}

.user-info {
    flex: 1;
}

.user-name {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 2px;
}

.user-status {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    gap: 5px;
}

.online-dot {
    width: 8px;
    height: 8px;
    background: #00ff88;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Messages Area */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: linear-gradient(180deg, #0A0A12 0%, #12121F 100%);
}

.message {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 18px;
    word-wrap: break-word;
    font-size: 15px;
    line-height: 1.4;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message.sent {
    align-self: flex-end;
    background: linear-gradient(135deg, #FF007A 0%, #7928CA 100%);
    color: #fff;
    border-bottom-right-radius: 4px;
}

.message.received {
    align-self: flex-start;
    background: #1a1a2e;
    color: #fff;
    border-bottom-left-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-time {
    font-size: 10px;
    opacity: 0.6;
    margin-top: 4px;
    display: block;
}

/* Typing Indicator */
.typing-indicator {
    align-self: flex-start;
    padding: 12px 16px;
    background: #1a1a2e;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    display: flex;
    gap: 4px;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #8B8B9E;
    animation: typingBounce 1.4s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-8px); }
}

/* Welcome Message */
.welcome-message {
    text-align: center;
    padding: 40px 20px;
    color: #8B8B9E;
}

.welcome-emoji {
    font-size: 60px;
    margin-bottom: 15px;
}

.welcome-title {
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
}

.welcome-text {
    font-size: 14px;
    line-height: 1.5;
}

/* Input Area */
.input-container {
    background: #12121F;
    padding: 15px 20px;
    display: flex;
    gap: 12px;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.input-container input {
    flex: 1;
    padding: 14px 20px;
    border-radius: 24px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    background: #0A0A12;
    color: #fff;
    font-size: 15px;
    outline: none;
    transition: border-color 0.3s;
}

.input-container input:focus {
    border-color: #FF007A;
}

.input-container input::placeholder {
    color: #555;
}

.send-btn {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    border: none;
    background: linear-gradient(135deg, #FF007A 0%, #7928CA 100%);
    color: #fff;
    font-size: 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s;
    box-shadow: 0 4px 15px rgba(255, 0, 122, 0.4);
}

.send-btn:active {
    transform: scale(0.9);
}

.send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Scrollbar */
.messages-container::-webkit-scrollbar {
    width: 4px;
}

.messages-container::-webkit-scrollbar-track {
    background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
}
</style>
</head>
<body>

<!-- Header -->
<div class="chat-header">
    <div class="avatar">{{GIRL_INITIAL}}</div>
    <div class="user-info">
        <div class="user-name">{{GIRL_NAME}}, {{GIRL_AGE}}</div>
        <div class="user-status">
            <span class="online-dot"></span>
            <span>Online • {{GIRL_CITY}}</span>
        </div>
    </div>
</div>

<!-- Messages -->
<div class="messages-container" id="messagesContainer">
    <div class="welcome-message">
        <div class="welcome-emoji">💕</div>
        <div class="welcome-title">Say Hi to {{GIRL_NAME}}!</div>
        <div class="welcome-text">She's online and waiting to chat with you. Start the conversation! 👋</div>
    </div>
</div>

<!-- Input -->
<div class="input-container">
    <input type="text" id="messageInput" placeholder="Type a message..." maxlength="500" autocomplete="off">
    <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
</div>

<script>
// Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#FF007A');
    tg.setBackgroundColor('#0A0A12');
}

const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
let isSending = false;

// Get girl info from URL
const urlParams = new URLSearchParams(window.location.search);
const girlName = urlParams.get('girl') || 'Girl';

// Send message
async function sendMessage() {
    if (isSending) return;
    
    const text = messageInput.value.trim();
    if (!text) return;
    
    isSending = true;
    sendBtn.disabled = true;
    
    // Clear welcome message if first message
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    // Add user message
    appendMessage(text, 'sent');
    messageInput.value = '';
    
    // Show typing indicator
    showTyping();
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: text,
                girl_name: girlName
            })
        });
        
        const data = await res.json();
        
        // Hide typing and show reply
        hideTyping();
        
        if (data.ok && data.reply) {
            // Small delay for realism
            await new Promise(r => setTimeout(r, 500));
            appendMessage(data.reply, 'received');
            
            // Haptic feedback
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
        }
    } catch (e) {
        hideTyping();
        appendMessage("Sorry, something went wrong 😢", 'received');
    }
    
    isSending = false;
    sendBtn.disabled = false;
}

function appendMessage(text, type) {
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.innerHTML = `
        <div>${escapeHtml(text)}</div>
        <span class="message-time">${time}</span>
    `;
    
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Enter key to send
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Focus input on load
setTimeout(() => messageInput.focus(), 300);
</script>

</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
