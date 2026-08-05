"""
Telegram Dating Bot — Swipe Matching Web App (VERCEL VERSION - FIXED)
======================================================================
✅ Step-by-step registration: Name → Age → Gender → Match Mode
✅ Find Real: Notifies user via bot when real matches found
✅ Find AI: Instant AI-generated match profiles to swipe & chat
✅ Better UI with smooth transitions & premium design
✅ Proper validation
✅ Telegram message notification when matches found
✅ Chat feature between matched users
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, quote, unquote

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN = "8859077363:AAEY5IvqLjvp2KHFi-sDeihrGCKmTu1vrtU"
KV_URL = "https://prompt-quetzal-219477.upstash.io"
KV_TOKEN = "ggAAAAAAA1lVAAIgcDECZqGNn4s9xuEezqSIxvU8XvbqsdNhFWCEEGpm8Lf0Zw"

app = FastAPI(title="Dating Swipe App")

# Fallback in-memory storage
_mem: dict[str, Any] = {}

# AI Match names pool
AI_MALE_NAMES = [
    "Arjun", "Rohan", "Aarav", "Vivaan", "Aditya", "Kabir", "Ishaan", "Reyansh",
    "Ayaan", "Vihaan", "Dhruv", "Arnav", "Shaurya", "Yash", "Krish", "Siddharth",
    "Raj", "Dev", "Ansh", "Kartik", "Neil", "Aarush", "Ranveer", "Samar"
]
AI_FEMALE_NAMES = [
    "Ananya", "Priya", "Isha", "Myra", "Aanya", "Saanvi", "Kiara", "Diya",
    "Riya", "Tara", "Avni", "Kavya", "Zara", "Nisha", "Meera", "Pooja",
    "Aisha", "Sneha", "Pihu", "Sara", "Simran", "Rhea", "Mahi", "Navya"
]
AI_BIOS = [
    "Music lover 🎵 | Coffee addict ☕",
    "Travel enthusiast ✈️ | Foodie 🍕",
    "Gym freak 💪 | Netflix binge-watcher 🎬",
    "Photography 📸 | Adventure seeker 🏔️",
    "Bookworm 📚 | Tea lover 🍵",
    "Dog person 🐕 | Sunset chaser 🌅",
    "Gamer 🎮 | Anime fan 🎌",
    "Dancer 💃 | Night owl 🦉",
    "Artist 🎨 | Dreamer ✨",
    "Tech geek 💻 | Startup enthusiast 🚀",
    "Yoga practitioner 🧘 | Healthy living 🥗",
    "Singer 🎤 | Party animal 🎉",
]


# ─────────────────────────────────────────────
# STORAGE (Vercel KV REST API)
# ─────────────────────────────────────────────
async def kv_get(key: str) -> Any:
    if not KV_URL:
        return _mem.get(key)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{KV_URL}/get/{quote(key)}",
                headers={"Authorization": f"Bearer {KV_TOKEN}"},
            )
            res = r.json().get("result")
            return json.loads(res) if res else None
    except Exception:
        return _mem.get(key)


async def kv_set(key: str, val: Any) -> None:
    _mem[key] = val
    if not KV_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(
                f"{KV_URL}/set/{quote(key)}/{quote(json.dumps(val))}",
                headers={"Authorization": f"Bearer {KV_TOKEN}"},
            )
    except Exception:
        pass


async def kv_profile_keys() -> list[str]:
    if not KV_URL:
        return [k for k in _mem if k.startswith("profile:")]
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{KV_URL}/keys/{quote('profile:*')}",
                headers={"Authorization": f"Bearer {KV_TOKEN}"},
            )
            return r.json().get("result", []) or []
    except Exception:
        return [k for k in _mem if k.startswith("profile:")]


# ─────────────────────────────────────────────
# TELEGRAM VERIFICATION
# ─────────────────────────────────────────────
def verify_telegram_user(init_data: str) -> Optional[dict]:
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash != received_hash:
            return None
        if time.time() - int(parsed.get("auth_date", 0)) > 86400:
            return None
        return json.loads(unquote(parsed.get("user", "{}")))
    except Exception:
        return None


# ─────────────────────────────────────────────
# TELEGRAM API
# ─────────────────────────────────────────────
async def send_telegram_message(user_id: int, text: str):
    """Send message to user via Telegram Bot API"""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": user_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
    except Exception:
        pass


# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────
class InitRequest(BaseModel):
    init_data: str

class RegisterRequest(BaseModel):
    init_data: str
    name: str
    age: int
    gender: str

class SwipeRequest(BaseModel):
    init_data: str
    target_id: int
    action: str

class MessageRequest(BaseModel):
    init_data: str
    to_user: int
    message: str

class FindRealRequest(BaseModel):
    init_data: str

class AIMessageRequest(BaseModel):
    init_data: str
    ai_profile_id: str
    message: str


# ─────────────────────────────────────────────
# AI PROFILE GENERATION
# ─────────────────────────────────────────────
def generate_ai_profiles(my_gender: str, count: int = 10) -> list[dict]:
    """Generate random AI profiles for the user to swipe on"""
    names = AI_FEMALE_NAMES if my_gender == "male" else AI_MALE_NAMES
    target_gender = "female" if my_gender == "male" else "male"
    
    selected_names = random.sample(names, min(count, len(names)))
    profiles = []
    for i, name in enumerate(selected_names):
        profiles.append({
            "user_id": f"ai_{random.randint(100000, 999999)}_{i}",
            "name": name,
            "age": random.randint(18, 30),
            "gender": target_gender,
            "bio": random.choice(AI_BIOS),
            "is_ai": True
        })
    return profiles


AI_RESPONSES = {
    "hi": ["Hey! 😊 Kaisi ho?", "Hello! 💕 Kya haal hai?", "Hi there! ✨ Nice to meet you!"],
    "hello": ["Hey! 😊 Kaise ho?", "Hello! 💕 Kya haal hai?", "Hiii! ✨ Bolo kya kar rahe ho?"],
    "kaise ho": ["Main theek hu! Tum batao? 😊", "Bahut accha! Tumhare baare mein batao 💕", "Great! Tum kaise ho? ✨"],
    "kya kar rahe ho": ["Tumse baat kar rahi hu! 😍", "Bas tumhara message ka wait kar rahi thi 💕", "Kuch nahi, tumse chat kar ke maza aa raha hai ✨"],
    "default": [
        "Haha that's nice! Tell me more about yourself 😊",
        "Interesting! Mujhe tumse baat karke accha lag raha hai 💕",
        "Wow, really? That's so cool! ✨",
        "Hmm, I like that! Aur batao 😍",
        "You seem really sweet! 🥰",
        "Haha! Tum toh bahut funny ho 😂💕",
        "Accha? Mujhe bhi yahi pasand hai! We have so much in common ✨",
        "That's amazing! Tum bahut interesting ho 😊",
    ]
}

def get_ai_response(message: str) -> str:
    """Generate a contextual AI response"""
    msg_lower = message.lower().strip()
    for key, responses in AI_RESPONSES.items():
        if key != "default" and key in msg_lower:
            return random.choice(responses)
    return random.choice(AI_RESPONSES["default"])


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=FRONTEND_HTML)


@app.post("/api/init")
async def api_init(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid Telegram user")
    uid = user.get("id")
    profile = await kv_get(f"profile:{uid}")
    return {
        "user_id": uid,
        "has_profile": bool(profile),
        "profile": profile,
        "tg_name": user.get("first_name", "User"),
    }


@app.post("/api/register")
async def api_register(req: RegisterRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid Telegram user")
    if not (13 <= req.age <= 100):
        raise HTTPException(400, "Age 13-100 ke beech honi chahiye")
    if req.gender not in ("male", "female"):
        raise HTTPException(400, "Gender male/female hona chahiye")
    profile = {
        "user_id": user.get("id"),
        "name": req.name.strip()[:50],
        "age": req.age,
        "gender": req.gender,
    }
    await kv_set(f"profile:{user.get('id')}", profile)
    return {"ok": True, "profile": profile}


@app.get("/api/profiles/{init_data}")
async def api_profiles(init_data: str):
    user = verify_telegram_user(init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        return {"profiles": []}

    my_swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    seen = set(my_swipes["liked"] + my_swipes["passed"] + [uid])

    candidates = []
    for key in await kv_profile_keys():
        p = await kv_get(key)
        if not p:
            continue
        pid = p["user_id"]
        if pid in seen:
            continue
        if my_profile["gender"] == "male" and p["gender"] != "female":
            continue
        if my_profile["gender"] == "female" and p["gender"] != "male":
            continue
        candidates.append(p)

    random.shuffle(candidates)
    return {"profiles": candidates[:20]}


@app.post("/api/swipe")
async def api_swipe(req: SwipeRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    uid = user.get("id")

    swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    matched = False
    match_info = None

    if req.action == "like":
        if req.target_id not in swipes["liked"]:
            swipes["liked"].append(req.target_id)
        target_swipes = await kv_get(f"swipes:{req.target_id}") or {"liked": [], "passed": []}
        if uid in target_swipes["liked"]:
            matched = True
            target_profile = await kv_get(f"profile:{req.target_id}") or {}
            my_profile = await kv_get(f"profile:{uid}") or {}
            match_info = {
                "name": target_profile.get("name", "Someone"),
                "age": target_profile.get("age"),
            }
            
            # Save matches
            for key_uid, other_uid in ((uid, req.target_id), (req.target_id, uid)):
                matches = await kv_get(f"matches:{key_uid}") or []
                matches.append({"partner_id": other_uid, "created_at": datetime.now(timezone.utc).isoformat()})
                await kv_set(f"matches:{key_uid}", matches)
            
            # Send Telegram notifications to both users
            await send_telegram_message(
                uid,
                f"🎉 <b>It's a Match!</b>\n\nYou matched with <b>{target_profile.get('name')}</b> ({target_profile.get('age')})!\n\nOpen the Web App to start chatting! 💕"
            )
            await send_telegram_message(
                req.target_id,
                f"🎉 <b>It's a Match!</b>\n\nYou matched with <b>{my_profile.get('name')}</b> ({my_profile.get('age')})!\n\nOpen the Web App to start chatting! 💕"
            )
    else:
        if req.target_id not in swipes["passed"]:
            swipes["passed"].append(req.target_id)

    await kv_set(f"swipes:{uid}", swipes)
    return {"matched": matched, "match_info": match_info}


@app.get("/api/matches/{init_data}")
async def api_matches(init_data: str):
    user = verify_telegram_user(init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    matches = await kv_get(f"matches:{uid}") or []
    result = []
    for m in matches:
        p = await kv_get(f"profile:{m['partner_id']}") or {}
        result.append({
            "user_id": m['partner_id'],
            "name": p.get("name", "User"), 
            "age": p.get("age"), 
            "gender": p.get("gender"),
            "created_at": m.get("created_at")
        })
    return {"matches": result}


@app.post("/api/send_message")
async def api_send_message(req: MessageRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    
    uid = user.get("id")
    to_user = req.to_user
    
    # Verify they are matched
    matches = await kv_get(f"matches:{uid}") or []
    matched_ids = [m['partner_id'] for m in matches]
    if to_user not in matched_ids:
        raise HTTPException(403, "You are not matched with this user")
    
    # Create chat ID (sorted to ensure same ID for both users)
    chat_id = f"chat:{min(uid, to_user)}:{max(uid, to_user)}"
    
    # Get existing messages
    messages = await kv_get(chat_id) or []
    
    # Add new message
    new_message = {
        "from": uid,
        "to": to_user,
        "text": req.message.strip()[:500],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    messages.append(new_message)
    
    # Save messages
    await kv_set(chat_id, messages)
    
    # Send Telegram notification to recipient
    sender_profile = await kv_get(f"profile:{uid}") or {}
    await send_telegram_message(
        to_user,
        f"💬 <b>New message from {sender_profile.get('name')}</b>\n\n\"{req.message.strip()[:100]}\"\n\nOpen the Web App to reply! 💕"
    )
    
    return {"ok": True, "message": new_message}


@app.get("/api/get_messages/{init_data}/{partner_id}")
async def api_get_messages(init_data: str, partner_id: int):
    user = verify_telegram_user(init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    
    uid = user.get("id")
    
    # Verify they are matched
    matches = await kv_get(f"matches:{uid}") or []
    matched_ids = [m['partner_id'] for m in matches]
    if partner_id not in matched_ids:
        raise HTTPException(403, "You are not matched with this user")
    
    # Create chat ID
    chat_id = f"chat:{min(uid, partner_id)}:{max(uid, partner_id)}"
    
    # Get messages
    messages = await kv_get(chat_id) or []
    
    return {"messages": messages, "user_id": uid}


# ─────────────────────────────────────────────
# NEW: Find Real - register for real match notifications
# ─────────────────────────────────────────────
@app.post("/api/find_real")
async def api_find_real(req: FindRealRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid Telegram user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        raise HTTPException(400, "Profile nahi mila")
    
    # Mark user as searching for real match
    await kv_set(f"searching:{uid}", {"active": True, "since": datetime.now(timezone.utc).isoformat()})
    
    # Check if there are any available real profiles right now
    my_swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    seen = set(my_swipes["liked"] + my_swipes["passed"] + [uid])
    candidates_count = 0
    for key in await kv_profile_keys():
        p = await kv_get(key)
        if not p:
            continue
        pid = p["user_id"]
        if pid in seen:
            continue
        if my_profile["gender"] == "male" and p["gender"] != "female":
            continue
        if my_profile["gender"] == "female" and p["gender"] != "male":
            continue
        candidates_count += 1
    
    # Send Telegram confirmation
    await send_telegram_message(
        uid,
        f"🔍 <b>Real Match Search Activated!</b>\n\n"
        f"Hi {my_profile.get('name')}! Hum aapke liye real matches dhundh rahe hain.\n\n"
        f"✅ Jaise hi koi match milega, hum aapko is bot ke through turant inform karenge!\n\n"
        f"📱 Apna Telegram notifications ON rakhein.\n\n"
        f"💡 Tab tak aap AI matches se practice kar sakte hain!"
    )
    
    return {
        "ok": True,
        "candidates_available": candidates_count,
        "message": "Aapki request register ho gayi hai! Jab koi match milega toh hum aapko bot ke through inform karenge."
    }


# ─────────────────────────────────────────────
# NEW: AI Profiles endpoint
# ─────────────────────────────────────────────
@app.post("/api/ai_profiles")
async def api_ai_profiles(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        return {"profiles": []}
    
    profiles = generate_ai_profiles(my_profile["gender"], count=10)
    return {"profiles": profiles}


# ─────────────────────────────────────────────
# NEW: AI Chat endpoint
# ─────────────────────────────────────────────
@app.post("/api/ai_chat")
async def api_ai_chat(req: AIMessageRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    
    uid = user.get("id")
    ai_id = req.ai_profile_id
    chat_key = f"ai_chat:{uid}:{ai_id}"
    
    messages = await kv_get(chat_key) or []
    
    # Add user message
    user_msg = {
        "from": uid,
        "to": ai_id,
        "text": req.message.strip()[:500],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_user": True
    }
    messages.append(user_msg)
    
    # Generate AI response
    ai_response = get_ai_response(req.message)
    ai_msg = {
        "from": ai_id,
        "to": uid,
        "text": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_user": False
    }
    messages.append(ai_msg)
    
    await kv_set(chat_key, messages)
    
    return {"ok": True, "user_message": user_msg, "ai_response": ai_msg, "all_messages": messages}


@app.get("/api/ai_messages/{init_data}/{ai_profile_id}")
async def api_ai_messages(init_data: str, ai_profile_id: str):
    user = verify_telegram_user(init_data)
    if not user:
        raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    chat_key = f"ai_chat:{uid}:{ai_profile_id}"
    messages = await kv_get(chat_key) or []
    return {"messages": messages, "user_id": uid}


# ═════════════════════════════════════════════
# FRONTEND HTML (Embedded - Step-by-Step)
# ═════════════════════════════════════════════
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>💘 Swipe Match</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%);color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow-x:hidden}
.header{padding:20px;text-align:center;width:100%}
.header h1{font-size:28px;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:bold}

/* Navigation Tabs */
.nav-tabs{display:none;width:90%;max-width:400px;margin:10px auto;background:rgba(26,26,46,0.8);border-radius:16px;padding:5px;gap:5px}
.nav-tabs.show{display:flex}
.nav-tab{flex:1;padding:12px;border:none;background:transparent;color:#888;font-size:14px;font-weight:600;border-radius:12px;cursor:pointer;transition:all 0.3s}
.nav-tab.active{background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff}

/* Progress Bar */
.progress-bar{width:90%;max-width:400px;height:6px;background:#2a2a3a;border-radius:10px;margin:10px auto;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,#ff6b9d,#c44fe2);transition:width 0.5s ease;width:0%}

/* Registration Steps */
.step{display:none;width:90%;max-width:400px;animation:fadeIn 0.4s ease}
.step.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}

.step-card{background:rgba(26,26,46,0.8);backdrop-filter:blur(10px);border-radius:24px;padding:30px;margin-top:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
.step-icon{font-size:60px;text-align:center;margin-bottom:15px}
.step h2{font-size:22px;text-align:center;margin-bottom:8px;color:#fff}
.step p{font-size:14px;text-align:center;color:#888;margin-bottom:25px}

.step input,.step select{width:100%;padding:16px 20px;margin-bottom:15px;border-radius:16px;border:2px solid transparent;background:#2a2a3a;color:#fff;font-size:16px;transition:border 0.3s}
.step input:focus,.step select:focus{outline:none;border-color:#ff6b9d}
.step input::placeholder{color:#666}

.step button{width:100%;padding:16px;border-radius:16px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:18px;font-weight:bold;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 10px 30px rgba(255,107,157,0.3)}
.step button:active{transform:scale(0.98)}
.step button:disabled{opacity:0.5;cursor:not-allowed}

.gender-options{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}
.gender-btn{padding:25px 15px;border-radius:16px;border:2px solid #2a2a3a;background:#1a1a2e;color:#fff;font-size:16px;cursor:pointer;transition:all 0.3s;text-align:center}
.gender-btn:active{transform:scale(0.95)}
.gender-btn.selected{border-color:#ff6b9d;background:linear-gradient(135deg,rgba(255,107,157,0.2),rgba(196,79,226,0.2))}
.gender-btn .emoji{font-size:40px;display:block;margin-bottom:8px}

/* Match Mode Selection */
.mode-options{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}
.mode-btn{padding:20px 15px;border-radius:16px;border:2px solid #2a2a3a;background:#1a1a2e;color:#fff;font-size:14px;cursor:pointer;transition:all 0.3s;text-align:center;position:relative;overflow:hidden}
.mode-btn:active{transform:scale(0.95)}
.mode-btn.selected{border-color:#4facfe;background:linear-gradient(135deg,rgba(79,172,254,0.15),rgba(0,242,254,0.15))}
.mode-btn.ai-selected{border-color:#c44fe2;background:linear-gradient(135deg,rgba(196,79,226,0.15),rgba(255,107,157,0.15))}
.mode-btn .mode-emoji{font-size:44px;display:block;margin-bottom:10px}
.mode-btn .mode-title{font-size:16px;font-weight:bold;display:block;margin-bottom:6px}
.mode-btn .mode-desc{font-size:11px;color:#888;display:block;line-height:1.4}
.mode-btn .mode-badge{position:absolute;top:8px;right:8px;padding:3px 8px;border-radius:8px;font-size:10px;font-weight:bold}
.mode-btn .badge-real{background:linear-gradient(135deg,#4facfe,#00f2fe);color:#fff}
.mode-btn .badge-ai{background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff}

/* Find Real Info Card */
.real-info-card{background:linear-gradient(135deg,rgba(79,172,254,0.1),rgba(0,242,254,0.1));border:1px solid rgba(79,172,254,0.3);border-radius:16px;padding:20px;margin-bottom:20px;text-align:center}
.real-info-card .info-icon{font-size:50px;margin-bottom:10px}
.real-info-card .info-title{font-size:16px;font-weight:bold;color:#4facfe;margin-bottom:8px}
.real-info-card .info-text{font-size:13px;color:#aaa;line-height:1.6}
.real-info-card .info-highlight{color:#4ade80;font-weight:bold}

/* Find Button */
.find-btn{width:100%;padding:18px;border-radius:16px;border:none;background:linear-gradient(135deg,#4facfe,#00f2fe);color:#fff;font-size:18px;font-weight:bold;cursor:pointer;transition:all 0.3s;box-shadow:0 10px 30px rgba(79,172,254,0.4);display:flex;align-items:center;justify-content:center;gap:10px}
.find-btn.ai-mode{background:linear-gradient(135deg,#c44fe2,#ff6b9d);box-shadow:0 10px 30px rgba(196,79,226,0.4)}
.find-btn:active{transform:scale(0.98)}
.find-btn:disabled{opacity:0.5;cursor:not-allowed}
.find-btn .search-icon{font-size:24px;animation:searchPulse 1.5s infinite}

@keyframes searchPulse{
  0%,100%{transform:scale(1);opacity:1}
  50%{transform:scale(1.2);opacity:0.7}
}

/* Searching Animation */
.searching-overlay{position:fixed;inset:0;background:rgba(15,15,26,0.95);display:none;align-items:center;justify-content:center;z-index:90;flex-direction:column;padding:20px}
.searching-overlay.show{display:flex;animation:fadeIn 0.3s}
.searching-spinner{width:80px;height:80px;border:6px solid rgba(255,255,255,0.1);border-top-color:#ff6b9d;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:30px}
@keyframes spin{to{transform:rotate(360deg)}}
.searching-text{font-size:24px;font-weight:bold;margin-bottom:10px;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.searching-subtext{font-size:16px;color:#888;text-align:center}

/* Notification */
.notification{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#4ade80,#22c55e);color:#fff;padding:18px 30px;border-radius:16px;font-size:16px;font-weight:bold;box-shadow:0 10px 40px rgba(74,222,128,0.4);z-index:200;opacity:0;pointer-events:none;transition:all 0.4s ease;max-width:90%;text-align:center}
.notification.show{opacity:1;transform:translateX(-50%) translateY(10px)}
.notification.info{background:linear-gradient(135deg,#4facfe,#00f2fe)}
.notification .notif-icon{font-size:28px;margin-bottom:8px;display:block;text-align:center}

/* Success Screen for Real Match Registration */
.success-screen{display:none;width:90%;max-width:400px;text-align:center;animation:fadeIn 0.5s ease}
.success-screen.show{display:block}
.success-card{background:rgba(26,26,46,0.8);backdrop-filter:blur(10px);border-radius:24px;padding:35px;margin-top:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);border:1px solid rgba(79,172,254,0.2)}
.success-icon{font-size:80px;margin-bottom:20px;animation:pulse 2s infinite}
.success-title{font-size:24px;font-weight:bold;background:linear-gradient(135deg,#4facfe,#00f2fe);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
.success-text{font-size:15px;color:#aaa;line-height:1.8;margin-bottom:25px}
.success-text .highlight{color:#4ade80;font-weight:bold}
.success-features{text-align:left;margin-bottom:25px}
.success-feature{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:14px;color:#ccc}
.success-feature:last-child{border-bottom:none}
.success-feature .feature-icon{font-size:22px;width:35px;text-align:center}
.try-ai-btn{width:100%;padding:16px;border-radius:16px;border:none;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-size:16px;font-weight:bold;cursor:pointer;transition:all 0.3s;box-shadow:0 10px 30px rgba(196,79,226,0.3);margin-bottom:10px}
.try-ai-btn:active{transform:scale(0.98)}
.go-home-btn{width:100%;padding:14px;border-radius:16px;border:2px solid #2a2a3a;background:transparent;color:#888;font-size:14px;cursor:pointer;transition:all 0.3s}
.go-home-btn:active{transform:scale(0.98)}

/* AI Badge on cards */
.ai-tag{position:absolute;top:15px;left:15px;padding:5px 12px;border-radius:20px;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-size:12px;font-weight:bold;z-index:5;display:flex;align-items:center;gap:5px}
.ai-tag::before{content:'🤖';font-size:14px}

/* Swipe Cards */
.card-container{position:relative;width:90%;max-width:400px;height:500px;margin:10px auto;display:none}
.card{position:absolute;width:100%;height:100%;border-radius:24px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.5);cursor:grab;user-select:none;touch-action:none;transition:transform 0.1s}
.card:active{cursor:grabbing}
.card-avatar{width:100%;height:60%;display:flex;align-items:center;justify-content:center;font-size:100px;font-weight:bold;color:rgba(255,255,255,0.95);text-shadow:0 4px 20px rgba(0,0,0,0.3);position:relative}
.card-bio{position:absolute;bottom:10px;left:20px;right:20px;text-align:center;font-size:13px;color:rgba(255,255,255,0.8);background:rgba(0,0,0,0.4);padding:8px 12px;border-radius:12px;backdrop-filter:blur(5px)}
.card-info{padding:25px;background:rgba(15,15,26,0.95);height:40%;backdrop-filter:blur(10px)}
.card-name{font-size:32px;font-weight:bold;margin-bottom:5px}
.card-age{font-size:22px;color:#ff6b9d;font-weight:600;margin-bottom:8px}
.card-gender{font-size:16px;color:#888;display:flex;align-items:center;gap:8px}
.card-gender::before{content:'';width:8px;height:8px;border-radius:50%;background:currentColor}

.swipe-label{position:absolute;top:40px;padding:10px 25px;border-radius:12px;font-size:28px;font-weight:bold;opacity:0;pointer-events:none;text-shadow:0 2px 10px rgba(0,0,0,0.3);z-index:10}
.swipe-label.like{right:25px;color:#4ade80;border:4px solid #4ade80;transform:rotate(15deg);background:rgba(74,222,128,0.1)}
.swipe-label.pass{left:25px;color:#f87171;border:4px solid #f87171;transform:rotate(-15deg);background:rgba(248,113,113,0.1)}

.buttons{display:none;gap:40px;margin:25px 0;justify-content:center}
.btn{width:75px;height:75px;border-radius:50%;border:none;font-size:34px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,0.3);transition:transform 0.2s}
.btn:active{transform:scale(0.9)}
.btn-pass{background:#2a2a3a;color:#f87171}
.btn-like{background:#2a2a3a;color:#4ade80}

.empty-state{display:none;text-align:center;padding:60px 30px;width:90%;max-width:400px}
.empty-state .emoji{font-size:80px;margin-bottom:25px}
.empty-state h3{font-size:24px;margin-bottom:10px;color:#fff}
.empty-state p{font-size:16px;color:#888;line-height:1.6}

/* Match Modal */
.match-modal{position:fixed;inset:0;background:rgba(0,0,0,0.95);display:none;align-items:center;justify-content:center;z-index:100;flex-direction:column;padding:20px}
.match-modal.show{display:flex;animation:fadeIn 0.3s}
.match-hearts{font-size:80px;margin-bottom:20px;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
.match-title{font-size:42px;font-weight:bold;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:15px}
.match-name{font-size:20px;text-align:center;color:#ccc;margin-bottom:30px}
.match-btn{padding:16px 50px;border-radius:30px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:18px;font-weight:bold;cursor:pointer;box-shadow:0 10px 30px rgba(255,107,157,0.4);margin-bottom:10px}
.match-chat-btn{padding:14px 50px;border-radius:30px;border:2px solid #c44fe2;background:transparent;color:#c44fe2;font-size:16px;font-weight:bold;cursor:pointer}

/* Matches Section */
.matches-section{display:none;width:90%;max-width:400px;margin:20px auto}
.matches-section.show{display:block}
.matches-header{font-size:22px;font-weight:bold;margin-bottom:20px;color:#fff}
.match-card{background:rgba(26,26,46,0.8);backdrop-filter:blur(10px);border-radius:16px;padding:20px;margin-bottom:15px;display:flex;align-items:center;gap:15px;cursor:pointer;transition:transform 0.2s;box-shadow:0 10px 30px rgba(0,0,0,0.3)}
.match-card:active{transform:scale(0.98)}
.match-card.ai-match{border:1px solid rgba(196,79,226,0.3)}
.match-avatar{width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:bold;color:#fff;flex-shrink:0}
.match-info{flex:1}
.match-info .match-name-text{font-size:18px;font-weight:bold;margin-bottom:5px}
.match-details{font-size:14px;color:#888}
.match-ai-badge{font-size:10px;padding:2px 8px;border-radius:8px;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-weight:bold;margin-left:8px}
.chat-btn{padding:10px 20px;border-radius:12px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:14px;font-weight:bold;cursor:pointer;flex-shrink:0}

/* Chat Section */
.chat-section{display:none;width:100%;height:calc(100vh - 140px);flex-direction:column}
.chat-section.show{display:flex}
.chat-header{background:rgba(26,26,46,0.95);backdrop-filter:blur(10px);padding:20px;display:flex;align-items:center;gap:15px;border-bottom:1px solid rgba(255,255,255,0.1)}
.back-btn{width:40px;height:40px;border-radius:50%;border:none;background:#2a2a3a;color:#fff;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.chat-user-info{flex:1}
.chat-user-name{font-size:18px;font-weight:bold}
.chat-user-status{font-size:12px;color:#4ade80}
.chat-ai-label{font-size:10px;padding:2px 8px;border-radius:8px;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-weight:bold}

.chat-messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:10px}
.message{max-width:75%;padding:12px 16px;border-radius:16px;word-wrap:break-word}
.message.sent{align-self:flex-end;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;border-bottom-right-radius:4px}
.message.received{align-self:flex-start;background:#2a2a3a;color:#fff;border-bottom-left-radius:4px}
.message-time{font-size:10px;opacity:0.7;margin-top:5px}

.chat-input{background:rgba(26,26,46,0.95);backdrop-filter:blur(10px);padding:15px 20px;display:flex;gap:10px;border-top:1px solid rgba(255,255,255,0.1)}
.chat-input input{flex:1;padding:14px 20px;border-radius:24px;border:2px solid transparent;background:#2a2a3a;color:#fff;font-size:16px}
.chat-input input:focus{outline:none;border-color:#ff6b9d}
.send-btn{width:50px;height:50px;border-radius:50%;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.send-btn:disabled{opacity:0.5;cursor:not-allowed}

.loading{padding:60px;text-align:center;color:#888;font-size:16px}
.error-msg{color:#f87171;font-size:14px;text-align:center;margin-top:10px;min-height:20px}

/* Typing indicator */
.typing-indicator{align-self:flex-start;padding:12px 16px;background:#2a2a3a;border-radius:16px;border-bottom-left-radius:4px;display:flex;gap:5px;align-items:center}
.typing-dot{width:8px;height:8px;border-radius:50%;background:#888;animation:typingBounce 1.4s infinite}
.typing-dot:nth-child(2){animation-delay:0.2s}
.typing-dot:nth-child(3){animation-delay:0.4s}
@keyframes typingBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
</style>
</head>
<body>

<div class="header"><h1>💘 Swipe Match</h1></div>
<div class="nav-tabs" id="navTabs">
  <button class="nav-tab active" onclick="showSection('swipe', this)">💘 Swipe</button>
  <button class="nav-tab" onclick="showSection('matches', this)">💬 Matches</button>
</div>
<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>

<!-- Loading -->
<div class="loading" id="loading">Loading...</div>

<!-- Step 1: Name -->
<div class="step" id="step1">
  <div class="step-card">
    <div class="step-icon">👋</div>
    <h2>Tumhara Naam Kya Hai?</h2>
    <p>Apna pehla naam batao</p>
    <input type="text" id="regName" placeholder="e.g. Rahul" maxlength="50" autocomplete="off">
    <div class="error-msg" id="nameError"></div>
    <button onclick="nextStep(2)" id="btn1">Continue →</button>
  </div>
</div>

<!-- Step 2: Age -->
<div class="step" id="step2">
  <div class="step-card">
    <div class="step-icon">🎂</div>
    <h2>Tumhari Age Kya Hai?</h2>
    <p>13-100 ke beech honi chahiye</p>
    <input type="number" id="regAge" placeholder="e.g. 24" min="13" max="100" autocomplete="off">
    <div class="error-msg" id="ageError"></div>
    <button onclick="nextStep(3)" id="btn2">Continue →</button>
  </div>
</div>

<!-- Step 3: Gender -->
<div class="step" id="step3">
  <div class="step-card">
    <div class="step-icon">👤</div>
    <h2>Tum Kaun Ho?</h2>
    <p>Apna gender select karo</p>
    <div class="gender-options">
      <button class="gender-btn" onclick="selectGender('male', this)">
        <span class="emoji">👨</span>
        Boy
      </button>
      <button class="gender-btn" onclick="selectGender('female', this)">
        <span class="emoji">👩</span>
        Girl
      </button>
    </div>
    <div class="error-msg" id="genderError"></div>
    <button onclick="registerProfile()" id="btn3" disabled>🚀 Continue →</button>
  </div>
</div>

<!-- Step 4: Match Mode Selection -->
<div class="step" id="step4">
  <div class="step-card">
    <div class="step-icon">✨</div>
    <h2>Kaise Match Dhundna Hai?</h2>
    <p>Real log ya AI se practice karo</p>
    <div class="mode-options">
      <button class="mode-btn" id="modeReal" onclick="selectMode('real', this)">
        <span class="mode-badge badge-real">REAL</span>
        <span class="mode-emoji">👥</span>
        <span class="mode-title">Find Real</span>
        <span class="mode-desc">Real logo se match karo</span>
      </button>
      <button class="mode-btn" id="modeAI" onclick="selectMode('ai', this)">
        <span class="mode-badge badge-ai">AI</span>
        <span class="mode-emoji">🤖</span>
        <span class="mode-title">Find AI</span>
        <span class="mode-desc">AI profiles se chat karo</span>
      </button>
    </div>
    
    <!-- Real mode info (hidden by default) -->
    <div id="realInfoCard" class="real-info-card" style="display:none">
      <div class="info-icon">🔔</div>
      <div class="info-title">Real Match Kaise Kaam Karta Hai?</div>
      <div class="info-text">
        Hum aapke liye <span class="info-highlight">real log</span> dhundhenge.<br>
        Jaise hi koi match milega, hum aapko <span class="info-highlight">bot ke dwara turant inform karenge!</span><br><br>
        📱 Apna Telegram notifications ON rakhein.
      </div>
    </div>
    
    <!-- AI mode info (hidden by default) -->
    <div id="aiInfoCard" class="real-info-card" style="display:none;border-color:rgba(196,79,226,0.3);background:linear-gradient(135deg,rgba(196,79,226,0.1),rgba(255,107,157,0.1))">
      <div class="info-icon">🤖</div>
      <div class="info-title" style="color:#c44fe2">AI Match Kaise Kaam Karta Hai?</div>
      <div class="info-text">
        AI profiles se <span class="info-highlight">swipe aur chat</span> karo.<br>
        Practice karo aur apna game strong banao! 💪<br><br>
        ⚡ Turant matches milenge — koi wait nahi!
      </div>
    </div>
    
    <div class="error-msg" id="modeError"></div>
    <button onclick="startMatchMode()" id="btn4" disabled style="margin-top:10px">🚀 Let's Go!</button>
  </div>
</div>

<!-- Searching Overlay -->
<div class="searching-overlay" id="searchingOverlay">
  <div class="searching-spinner"></div>
  <div class="searching-text" id="searchingTitle">Searching for matches...</div>
  <div class="searching-subtext" id="searchingSubtext">Please wait while we find perfect matches for you</div>
</div>

<!-- Notification -->
<div class="notification" id="notification">
  <span class="notif-icon" id="notifIcon">✨</span>
  <div id="notifText">Matches found!</div>
</div>

<!-- Real Match Success Screen -->
<div class="success-screen" id="realSuccessScreen">
  <div class="success-card">
    <div class="success-icon">✅</div>
    <div class="success-title">Request Registered!</div>
    <div class="success-text">
      Aapki real match request <span class="highlight">successfully register</span> ho gayi hai!<br><br>
      Jaise hi koi <span class="highlight">match milega</span>, hum aapko <span class="highlight">bot ke dwara turant inform</span> karenge! 🔔
    </div>
    <div class="success-features">
      <div class="success-feature">
        <span class="feature-icon">🔍</span>
        <span>Hum real profiles dhundh rahe hain</span>
      </div>
      <div class="success-feature">
        <span class="feature-icon">🔔</span>
        <span>Match milte hi Telegram notification</span>
      </div>
      <div class="success-feature">
        <span class="feature-icon">💬</span>
        <span>Match ke baad direct chat</span>
      </div>
      <div class="success-feature">
        <span class="feature-icon">📱</span>
        <span>Notifications ON rakhein!</span>
      </div>
    </div>
    <button class="try-ai-btn" onclick="switchToAI()">🤖 Tab tak AI se Practice Karo</button>
    <button class="go-home-btn" onclick="goHome()">🏠 Home jaao</button>
  </div>
</div>

<!-- Swipe Screen -->
<div class="card-container" id="cardContainer"></div>
<div class="buttons" id="buttons">
  <button class="btn btn-pass" onclick="swipe('pass')">✖️</button>
  <button class="btn btn-like" onclick="swipe('like')">❤️</button>
</div>

<!-- Empty State -->
<div class="empty-state" id="emptyState">
  <div class="emoji">😢</div>
  <h3>Koi Matches Nahi Mile</h3>
  <p id="emptyText">Abhi koi profiles nahi hai.<br>Thodi der baad wapas aao!</p>
</div>

<!-- Match Modal -->
<div class="match-modal" id="matchModal">
  <div class="match-hearts">💕</div>
  <div class="match-title">It's a Match!</div>
  <div class="match-name" id="matchName"></div>
  <button class="match-btn" onclick="closeMatch()" id="matchKeepBtn">Keep Swiping</button>
  <button class="match-chat-btn" onclick="matchOpenChat()" id="matchChatBtn" style="display:none;margin-top:10px">💬 Start Chat</button>
</div>

<!-- Matches Section -->
<div class="matches-section" id="matchesSection">
  <div class="matches-header">Your Matches 💕</div>
  <div id="matchesList"></div>
</div>

<!-- Chat Section -->
<div class="chat-section" id="chatSection">
  <div class="chat-header">
    <button class="back-btn" onclick="exitChat()">←</button>
    <div class="match-avatar" id="chatAvatar" style="width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;color:#fff"></div>
    <div class="chat-user-info">
      <div class="chat-user-name" id="chatUserName">User</div>
      <div class="chat-user-status" id="chatUserStatus">Online</div>
    </div>
    <span class="chat-ai-label" id="chatAiLabel" style="display:none">🤖 AI</span>
  </div>
  <div class="chat-messages" id="chatMessages"></div>
  <div class="chat-input">
    <input type="text" id="chatInput" placeholder="Type a message..." maxlength="500">
    <button class="send-btn" onclick="sendMessage()" id="sendBtn">➤</button>
  </div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();

let currentStep = 1;
let selectedGender = '';
let selectedMode = ''; // 'real' or 'ai'
let matchMode = ''; // active mode after selection
let profiles = [], currentIndex = 0, startX = 0, currentX = 0, isDragging = false, activeCard = null;
let currentChatPartner = null;
let messagePollInterval = null;
let isAIMode = false;
let aiMatchedProfiles = []; // AI profiles that user liked
let lastMatchedAIProfile = null;

const gradients = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#30cfd0,#330867)'
];

function updateProgress() {
  const percent = ((currentStep - 1) / 4) * 100;
  document.getElementById('progressFill').style.width = percent + '%';
}

function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById('realSuccessScreen').classList.remove('show');
  const step = document.getElementById('step' + n);
  if (step) step.classList.add('active');
  currentStep = n;
  updateProgress();
  
  setTimeout(() => {
    if (!step) return;
    const input = step.querySelector('input');
    if (input && !input.value) input.focus();
  }, 100);
}

function nextStep(n) {
  if (currentStep === 1) {
    const name = document.getElementById('regName').value.trim();
    if (!name) {
      document.getElementById('nameError').textContent = '❌ Naam likhna zaroori hai!';
      return;
    }
    if (name.length < 2) {
      document.getElementById('nameError').textContent = '❌ Naam bahut chhota hai!';
      return;
    }
    document.getElementById('nameError').textContent = '';
  }
  
  if (currentStep === 2) {
    const age = parseInt(document.getElementById('regAge').value);
    if (!age || isNaN(age)) {
      document.getElementById('ageError').textContent = '❌ Age likhna zaroori hai!';
      return;
    }
    if (age < 13 || age > 100) {
      document.getElementById('ageError').textContent = '❌ Age 13-100 ke beech honi chahiye!';
      return;
    }
    document.getElementById('ageError').textContent = '';
  }
  
  showStep(n);
}

function selectGender(gender, btn) {
  selectedGender = gender;
  document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('btn3').disabled = false;
  document.getElementById('genderError').textContent = '';
}

function selectMode(mode, btn) {
  selectedMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => {
    b.classList.remove('selected');
    b.classList.remove('ai-selected');
  });
  
  if (mode === 'real') {
    btn.classList.add('selected');
    document.getElementById('realInfoCard').style.display = 'block';
    document.getElementById('aiInfoCard').style.display = 'none';
    document.getElementById('btn4').style.background = 'linear-gradient(135deg,#4facfe,#00f2fe)';
    document.getElementById('btn4').innerHTML = '🔍 Find Real Matches';
  } else {
    btn.classList.add('ai-selected');
    document.getElementById('realInfoCard').style.display = 'none';
    document.getElementById('aiInfoCard').style.display = 'block';
    document.getElementById('btn4').style.background = 'linear-gradient(135deg,#c44fe2,#ff6b9d)';
    document.getElementById('btn4').innerHTML = '🤖 Start AI Matching';
  }
  
  document.getElementById('btn4').disabled = false;
  document.getElementById('modeError').textContent = '';
}

async function init() {
  try {
    const res = await fetch('/api/init', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({init_data: tg.initData})
    });
    if (!res.ok) throw new Error('Auth failed');
    const data = await res.json();
    document.getElementById('loading').style.display = 'none';
    
    if (!data.has_profile) {
      document.getElementById('regName').value = data.tg_name || '';
      showStep(1);
    } else {
      document.getElementById('progressFill').style.width = '100%';
      document.querySelector('.progress-bar').style.display = 'none';
      document.getElementById('navTabs').classList.add('show');
      showSection('swipe');
      showStep(4); // Show mode selection
    }
  } catch (e) {
    document.getElementById('loading').innerHTML = '❌ Error aaya. Bot se dobara kholo.';
  }
}

async function registerProfile() {
  if (!selectedGender) {
    document.getElementById('genderError').textContent = '❌ Gender select karo!';
    return;
  }
  
  const name = document.getElementById('regName').value.trim();
  const age = parseInt(document.getElementById('regAge').value);
  
  const btn = document.getElementById('btn3');
  btn.textContent = 'Saving...';
  btn.disabled = true;
  
  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({init_data: tg.initData, name, age, gender: selectedGender})
    });
    if (res.ok) {
      showStep(4);
    } else {
      btn.textContent = '🚀 Continue →';
      btn.disabled = false;
      alert('Error aaya, dobara try karo.');
    }
  } catch (e) {
    btn.textContent = '🚀 Continue →';
    btn.disabled = false;
    alert('Network error!');
  }
}

async function startMatchMode() {
  if (!selectedMode) {
    document.getElementById('modeError').textContent = '❌ Ek mode select karo!';
    return;
  }
  
  matchMode = selectedMode;
  
  if (selectedMode === 'real') {
    await findRealMatches();
  } else {
    await findAIMatches();
  }
}

async function findRealMatches() {
  const btn = document.getElementById('btn4');
  btn.disabled = true;
  btn.innerHTML = '⏳ Registering...';
  
  document.getElementById('searchingOverlay').classList.add('show');
  document.getElementById('searchingTitle').textContent = 'Registering your request...';
  document.getElementById('searchingSubtext').textContent = 'Hum aapko real matches ke liye register kar rahe hain';
  
  if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
  
  try {
    const res = await fetch('/api/find_real', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({init_data: tg.initData})
    });
    const data = await res.json();
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    document.getElementById('searchingOverlay').classList.remove('show');
    
    // Also try to load real profiles if any available
    if (data.candidates_available > 0) {
      showNotification('✨', `${data.candidates_available} real profiles available! Check Swipe tab.`, 'info');
      
      // Load real profiles for swiping too
      const profileRes = await fetch('/api/profiles/' + encodeURIComponent(tg.initData));
      const profileData = await profileRes.json();
      profiles = profileData.profiles || [];
      isAIMode = false;
      
      await new Promise(resolve => setTimeout(resolve, 2500));
      document.getElementById('notification').classList.remove('show');
      
      document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
      document.querySelector('.progress-bar').style.display = 'none';
      document.getElementById('navTabs').classList.add('show');
      
      if (profiles.length > 0) {
        document.getElementById('cardContainer').style.display = 'block';
        document.getElementById('buttons').style.display = 'flex';
        renderCard();
      } else {
        showRealSuccessScreen();
      }
    } else {
      // No real profiles available right now, show success screen
      showNotification('✅', 'Request registered! Bot se inform karenge.', 'info');
      await new Promise(resolve => setTimeout(resolve, 2500));
      document.getElementById('notification').classList.remove('show');
      
      showRealSuccessScreen();
    }
    
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  } catch (e) {
    document.getElementById('searchingOverlay').classList.remove('show');
    showNotification('❌', 'Error! Dobara try karo.');
    await new Promise(resolve => setTimeout(resolve, 2000));
    document.getElementById('notification').classList.remove('show');
    btn.disabled = false;
    btn.innerHTML = '🔍 Find Real Matches';
  }
}

function showRealSuccessScreen() {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.querySelector('.progress-bar').style.display = 'none';
  document.getElementById('navTabs').classList.add('show');
  document.getElementById('realSuccessScreen').classList.add('show');
}

async function switchToAI() {
  document.getElementById('realSuccessScreen').classList.remove('show');
  selectedMode = 'ai';
  matchMode = 'ai';
  await findAIMatches();
}

function goHome() {
  document.getElementById('realSuccessScreen').classList.remove('show');
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.querySelector('.progress-bar').style.display = 'none';
  document.getElementById('navTabs').classList.add('show');
  showStep(4);
  selectedMode = '';
  document.querySelectorAll('.mode-btn').forEach(b => {
    b.classList.remove('selected');
    b.classList.remove('ai-selected');
  });
  document.getElementById('realInfoCard').style.display = 'none';
  document.getElementById('aiInfoCard').style.display = 'none';
  document.getElementById('btn4').disabled = true;
  document.getElementById('btn4').innerHTML = '🚀 Let\'s Go!';
  document.getElementById('btn4').style.background = 'linear-gradient(135deg,#ff6b9d,#c44fe2)';
}

async function findAIMatches() {
  const btn = document.getElementById('btn4');
  btn.disabled = true;
  btn.innerHTML = '⏳ Generating...';
  
  document.getElementById('searchingOverlay').classList.add('show');
  document.getElementById('searchingTitle').textContent = 'Creating AI profiles...';
  document.getElementById('searchingSubtext').textContent = 'AI matches generate ho rahe hain ✨';
  
  if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
  
  try {
    const res = await fetch('/api/ai_profiles', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({init_data: tg.initData})
    });
    const data = await res.json();
    profiles = data.profiles || [];
    isAIMode = true;
    currentIndex = 0;
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    document.getElementById('searchingOverlay').classList.remove('show');
    
    if (profiles.length > 0) {
      showNotification('🤖', `${profiles.length} AI matches ready! Let's go! 🎉`);
      if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    document.getElementById('notification').classList.remove('show');
    
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.querySelector('.progress-bar').style.display = 'none';
    document.getElementById('navTabs').classList.add('show');
    
    if (profiles.length > 0) {
      document.getElementById('cardContainer').style.display = 'block';
      document.getElementById('buttons').style.display = 'flex';
      renderCard();
    } else {
      document.getElementById('emptyState').style.display = 'block';
    }
  } catch (e) {
    document.getElementById('searchingOverlay').classList.remove('show');
    showNotification('❌', 'Error! Dobara try karo.');
    await new Promise(resolve => setTimeout(resolve, 2000));
    document.getElementById('notification').classList.remove('show');
    btn.disabled = false;
    btn.innerHTML = '🤖 Start AI Matching';
  }
}

function showNotification(icon, text, type) {
  const notif = document.getElementById('notification');
  document.getElementById('notifIcon').textContent = icon;
  document.getElementById('notifText').textContent = text;
  notif.classList.remove('info');
  if (type === 'info') notif.classList.add('info');
  notif.classList.add('show');
}

function showSection(section, tabBtn) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if (tabBtn) tabBtn.classList.add('active');
  else document.querySelector('.nav-tab').classList.add('active');
  
  document.getElementById('cardContainer').style.display = 'none';
  document.getElementById('buttons').style.display = 'none';
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('matchesSection').classList.remove('show');
  document.getElementById('chatSection').classList.remove('show');
  document.getElementById('realSuccessScreen').classList.remove('show');
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  
  if (section === 'swipe') {
    if (profiles.length > 0 && currentIndex < profiles.length) {
      document.getElementById('cardContainer').style.display = 'block';
      document.getElementById('buttons').style.display = 'flex';
    } else if (matchMode) {
      document.getElementById('emptyState').style.display = 'block';
      document.getElementById('emptyText').innerHTML = isAIMode
        ? '🤖 Sab AI profiles dekh liye!<br><button onclick="reloadAI()" style="margin-top:15px;padding:12px 30px;border-radius:16px;border:none;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-size:16px;font-weight:bold;cursor:pointer">🔄 Naye AI Profiles Load Karo</button>'
        : '😢 Abhi koi profiles nahi hai.<br>Thodi der baad wapas aao!';
    } else {
      showStep(4);
    }
  } else if (section === 'matches') {
    document.getElementById('matchesSection').classList.add('show');
    loadMatches();
  }
}

async function reloadAI() {
  selectedMode = 'ai';
  matchMode = 'ai';
  document.getElementById('emptyState').style.display = 'none';
  await findAIMatches();
}

async function loadMatches() {
  const matchesList = document.getElementById('matchesList');
  matchesList.innerHTML = '<div class="loading">Loading matches...</div>';
  
  try {
    // Load real matches
    const res = await fetch('/api/matches/' + encodeURIComponent(tg.initData));
    const data = await res.json();
    const realMatches = (data.matches || []).map(m => ({...m, isAI: false}));
    
    // Add AI matches
    const allMatches = [
      ...aiMatchedProfiles.map(p => ({
        user_id: p.user_id,
        name: p.name,
        age: p.age,
        gender: p.gender,
        isAI: true,
        bio: p.bio
      })),
      ...realMatches
    ];
    
    if (allMatches.length === 0) {
      matchesList.innerHTML = '<div style="text-align:center;padding:40px 20px"><div style="font-size:60px;margin-bottom:15px">💔</div><div style="font-size:18px;font-weight:bold;margin-bottom:8px">No matches yet</div><div style="font-size:14px;color:#888">Keep swiping to find your match!</div></div>';
      return;
    }
    
    matchesList.innerHTML = allMatches.map(m => {
      const gIdx = typeof m.user_id === 'string' ? m.user_id.split('_')[1] % gradients.length : m.user_id % gradients.length;
      return `
        <div class="match-card ${m.isAI ? 'ai-match' : ''}" onclick="${m.isAI ? `openAIChat('${m.user_id}', '${escapeAttr(m.name)}', '${m.gender}')` : `openChat(${m.user_id}, '${escapeAttr(m.name)}', '${m.gender}')`}">
          <div class="match-avatar" style="background:${gradients[gIdx]}">
            ${m.name.charAt(0).toUpperCase()}
          </div>
          <div class="match-info">
            <div class="match-name-text">${escapeHtml(m.name)} ${m.isAI ? '<span class="match-ai-badge">🤖 AI</span>' : ''}</div>
            <div class="match-details">${m.age} years old • ${m.gender === 'male' ? '👨 Boy' : '👩 Girl'}</div>
          </div>
          <button class="chat-btn">💬 Chat</button>
        </div>
      `;
    }).join('');
  } catch (e) {
    matchesList.innerHTML = '<div class="error-msg">Error loading matches</div>';
  }
}

function openChat(userId, name, gender) {
  currentChatPartner = {userId, name, gender, isAI: false};
  
  document.getElementById('matchesSection').classList.remove('show');
  document.getElementById('chatSection').classList.add('show');
  document.getElementById('navTabs').classList.remove('show');
  
  const gIdx = userId % gradients.length;
  document.getElementById('chatAvatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('chatAvatar').style.background = gradients[gIdx];
  document.getElementById('chatUserName').textContent = name;
  document.getElementById('chatUserStatus').textContent = 'Online';
  document.getElementById('chatAiLabel').style.display = 'none';
  
  loadMessages();
  startMessagePolling();
}

function openAIChat(aiId, name, gender) {
  currentChatPartner = {userId: aiId, name, gender, isAI: true};
  
  document.getElementById('matchesSection').classList.remove('show');
  document.getElementById('chatSection').classList.add('show');
  document.getElementById('navTabs').classList.remove('show');
  
  const numId = parseInt(aiId.split('_')[1]) || 0;
  const gIdx = numId % gradients.length;
  document.getElementById('chatAvatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('chatAvatar').style.background = gradients[gIdx];
  document.getElementById('chatUserName').textContent = name;
  document.getElementById('chatUserStatus').textContent = '🤖 AI Match';
  document.getElementById('chatAiLabel').style.display = 'inline';
  
  loadAIMessages();
}

function exitChat() {
  currentChatPartner = null;
  stopMessagePolling();
  document.getElementById('chatSection').classList.remove('show');
  document.getElementById('navTabs').classList.add('show');
  document.getElementById('matchesSection').classList.add('show');
}

async function loadMessages() {
  if (!currentChatPartner || currentChatPartner.isAI) return;
  
  const chatMessages = document.getElementById('chatMessages');
  chatMessages.innerHTML = '<div class="loading">Loading messages...</div>';
  
  try {
    const res = await fetch(`/api/get_messages/${encodeURIComponent(tg.initData)}/${currentChatPartner.userId}`);
    const data = await res.json();
    const messages = data.messages || [];
    const userId = data.user_id;
    
    if (messages.length === 0) {
      chatMessages.innerHTML = '<div style="text-align:center;padding:40px;color:#888"><div style="font-size:50px;margin-bottom:10px">💬</div><div style="font-size:16px">Start the conversation!</div><div style="font-size:14px;margin-top:5px">Say hi to your match</div></div>';
      return;
    }
    
    chatMessages.innerHTML = messages.map(m => {
      const isSent = m.from === userId;
      const time = new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      return `
        <div class="message ${isSent ? 'sent' : 'received'}">
          <div>${escapeHtml(m.text)}</div>
          <div class="message-time">${time}</div>
        </div>
      `;
    }).join('');
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (e) {
    chatMessages.innerHTML = '<div class="error-msg">Error loading messages</div>';
  }
}

async function loadAIMessages() {
  if (!currentChatPartner || !currentChatPartner.isAI) return;
  
  const chatMessages = document.getElementById('chatMessages');
  chatMessages.innerHTML = '<div class="loading">Loading messages...</div>';
  
  try {
    const res = await fetch(`/api/ai_messages/${encodeURIComponent(tg.initData)}/${currentChatPartner.userId}`);
    const data = await res.json();
    const messages = data.messages || [];
    const userId = data.user_id;
    
    if (messages.length === 0) {
      chatMessages.innerHTML = '<div style="text-align:center;padding:40px;color:#888"><div style="font-size:50px;margin-bottom:10px">🤖💬</div><div style="font-size:16px">Start chatting with AI!</div><div style="font-size:14px;margin-top:5px;color:#c44fe2">Say hi to your AI match</div></div>';
      return;
    }
    
    chatMessages.innerHTML = messages.map(m => {
      const isSent = m.is_user;
      const time = new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      return `
        <div class="message ${isSent ? 'sent' : 'received'}">
          <div>${escapeHtml(m.text)}</div>
          <div class="message-time">${time}</div>
        </div>
      `;
    }).join('');
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (e) {
    chatMessages.innerHTML = '<div class="error-msg">Error loading messages</div>';
  }
}

async function sendMessage() {
  if (!currentChatPartner) return;
  
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  
  const sendBtn = document.getElementById('sendBtn');
  sendBtn.disabled = true;
  
  if (currentChatPartner.isAI) {
    await sendAIMessage(text);
  } else {
    await sendRealMessage(text);
  }
  
  sendBtn.disabled = false;
}

async function sendRealMessage(text) {
  const input = document.getElementById('chatInput');
  
  try {
    const res = await fetch('/api/send_message', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        init_data: tg.initData,
        to_user: currentChatPartner.userId,
        message: text
      })
    });
    
    if (res.ok) {
      input.value = '';
      loadMessages();
    } else {
      alert('Error sending message');
    }
  } catch (e) {
    alert('Network error!');
  }
}

async function sendAIMessage(text) {
  const input = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');
  
  // Immediately show user message
  const userTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  const userMsgDiv = document.createElement('div');
  userMsgDiv.className = 'message sent';
  userMsgDiv.innerHTML = `<div>${escapeHtml(text)}</div><div class="message-time">${userTime}</div>`;
  
  // Remove empty state if present
  const emptyState = chatMessages.querySelector('[style*="text-align:center"]');
  if (emptyState) emptyState.remove();
  
  chatMessages.appendChild(userMsgDiv);
  input.value = '';
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Show typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'typing-indicator';
  typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  try {
    const res = await fetch('/api/ai_chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        init_data: tg.initData,
        ai_profile_id: currentChatPartner.userId,
        message: text
      })
    });
    
    const data = await res.json();
    
    // Remove typing indicator
    typingDiv.remove();
    
    if (data.ok && data.ai_response) {
      // Add AI response with slight delay for realism
      await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
      
      const aiTime = new Date(data.ai_response.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      const aiMsgDiv = document.createElement('div');
      aiMsgDiv.className = 'message received';
      aiMsgDiv.innerHTML = `<div>${escapeHtml(data.ai_response.text)}</div><div class="message-time">${aiTime}</div>`;
      chatMessages.appendChild(aiMsgDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    }
  } catch (e) {
    typingDiv.remove();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-msg';
    errorDiv.textContent = 'Error sending message';
    chatMessages.appendChild(errorDiv);
  }
}

function startMessagePolling() {
  stopMessagePolling();
  if (currentChatPartner && !currentChatPartner.isAI) {
    messagePollInterval = setInterval(() => {
      if (currentChatPartner && !currentChatPartner.isAI) {
        loadMessages();
      }
    }, 3000);
  }
}

function stopMessagePolling() {
  if (messagePollInterval) {
    clearInterval(messagePollInterval);
    messagePollInterval = null;
  }
}

async function loadProfiles() {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('loading').textContent = 'Finding matches for you...';
  
  const res = await fetch('/api/profiles/' + encodeURIComponent(tg.initData));
  const data = await res.json();
  profiles = data.profiles || [];
  isAIMode = false;
  
  document.getElementById('loading').style.display = 'none';
  
  if (profiles.length === 0) {
    document.getElementById('emptyState').style.display = 'block';
  } else {
    document.getElementById('cardContainer').style.display = 'block';
    document.getElementById('buttons').style.display = 'flex';
    renderCard();
  }
}

function renderCard() {
  const container = document.getElementById('cardContainer');
  container.innerHTML = '';
  
  if (currentIndex >= profiles.length) {
    container.style.display = 'none';
    document.getElementById('buttons').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
    document.getElementById('emptyText').innerHTML = isAIMode
      ? '🤖 Sab AI profiles dekh liye!<br><button onclick="reloadAI()" style="margin-top:15px;padding:12px 30px;border-radius:16px;border:none;background:linear-gradient(135deg,#c44fe2,#ff6b9d);color:#fff;font-size:16px;font-weight:bold;cursor:pointer">🔄 Naye AI Profiles Load Karo</button>'
      : '🎉 Sab profiles dekh liye!<br>Kal phir aao.';
    return;
  }
  
  const p = profiles[currentIndex];
  const card = document.createElement('div');
  card.className = 'card';
  card.style.background = gradients[currentIndex % gradients.length];
  
  const initial = (p.name || 'U').charAt(0).toUpperCase();
  const genderText = p.gender === 'male' ? 'Boy' : 'Girl';
  const genderEmoji = p.gender === 'male' ? '👨' : '👩';
  const aiTag = p.is_ai ? '<div class="ai-tag">AI Match</div>' : '';
  const bioHtml = p.bio ? `<div class="card-bio">${escapeHtml(p.bio)}</div>` : '';
  
  card.innerHTML = `
    ${aiTag}
    <div class="swipe-label like">LIKE</div>
    <div class="swipe-label pass">NOPE</div>
    <div class="card-avatar">${initial}${bioHtml}</div>
    <div class="card-info">
      <div class="card-name">${escapeHtml(p.name)}</div>
      <div class="card-age">${p.age} years old</div>
      <div class="card-gender" style="color:${p.gender === 'male' ? '#4facfe' : '#f093fb'}">${genderEmoji} ${genderText}</div>
    </div>`;
  
  card.addEventListener('touchstart', dragStart, {passive: true});
  card.addEventListener('touchmove', dragMove, {passive: false});
  card.addEventListener('touchend', dragEnd);
  card.addEventListener('mousedown', dragStart);
  
  container.appendChild(card);
  activeCard = card;
}

function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

function escapeAttr(t) {
  return t.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function dragStart(e) {
  isDragging = true;
  startX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
  if (e.type === 'mousedown') {
    document.addEventListener('mousemove', dragMove);
    document.addEventListener('mouseup', dragEnd);
  }
}

function dragMove(e) {
  if (!isDragging || !activeCard) return;
  if (e.type === 'touchmove') e.preventDefault();
  
  currentX = (e.type === 'touchmove' ? e.touches[0].clientX : e.clientX) - startX;
  const rotation = currentX / 25;
  activeCard.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;
  
  const likeLabel = activeCard.querySelector('.swipe-label.like');
  const passLabel = activeCard.querySelector('.swipe-label.pass');
  likeLabel.style.opacity = currentX > 60 ? Math.min((currentX - 60) / 100, 1) : 0;
  passLabel.style.opacity = currentX < -60 ? Math.min((-currentX - 60) / 100, 1) : 0;
}

function dragEnd() {
  if (!isDragging || !activeCard) return;
  isDragging = false;
  document.removeEventListener('mousemove', dragMove);
  document.removeEventListener('mouseup', dragEnd);
  
  if (currentX > 120) animateOut('like');
  else if (currentX < -120) animateOut('pass');
  else {
    activeCard.style.transition = 'transform 0.3s';
    activeCard.style.transform = 'translateX(0) rotate(0)';
  }
  currentX = 0;
}

function swipe(action) {
  if (activeCard) animateOut(action);
}

function animateOut(action) {
  if (!activeCard) return;
  const card = activeCard;
  const dir = action === 'like' ? 1 : -1;
  
  card.style.transition = 'transform 0.4s, opacity 0.4s';
  card.style.transform = `translateX(${dir * 600}px) rotate(${dir * 30}deg)`;
  card.style.opacity = '0';
  
  const profile = profiles[currentIndex];
  currentIndex++;
  
  if (isAIMode) {
    // AI mode: auto-match on like
    setTimeout(() => {
      if (action === 'like') {
        // AI always matches back
        aiMatchedProfiles.push(profile);
        lastMatchedAIProfile = profile;
        showAIMatch(profile);
      }
      renderCard();
    }, 350);
  } else {
    // Real mode: call API
    const targetId = profile.user_id;
    setTimeout(async () => {
      try {
        const res = await fetch('/api/swipe', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({init_data: tg.initData, target_id: targetId, action})
        });
        const data = await res.json();
        if (data.matched && data.match_info) showMatch(data.match_info);
      } catch (e) {}
      renderCard();
    }, 350);
  }
  
  activeCard = null;
}

function showMatch(info) {
  document.getElementById('matchName').textContent = `You and ${info.name} liked each other! 💕`;
  document.getElementById('matchKeepBtn').textContent = 'Keep Swiping';
  document.getElementById('matchChatBtn').style.display = 'none';
  document.getElementById('matchModal').classList.add('show');
  if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}

function showAIMatch(profile) {
  document.getElementById('matchName').textContent = `You and ${profile.name} matched! 🤖💕`;
  document.getElementById('matchKeepBtn').textContent = 'Keep Swiping';
  document.getElementById('matchChatBtn').style.display = 'inline-block';
  document.getElementById('matchModal').classList.add('show');
  if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}

function closeMatch() {
  document.getElementById('matchModal').classList.remove('show');
}

function matchOpenChat() {
  document.getElementById('matchModal').classList.remove('show');
  if (lastMatchedAIProfile) {
    openAIChat(lastMatchedAIProfile.user_id, lastMatchedAIProfile.name, lastMatchedAIProfile.gender);
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    if (currentChatPartner) {
      sendMessage();
    } else if (currentStep === 1) {
      nextStep(2);
    } else if (currentStep === 2) {
      nextStep(3);
    }
  }
});

init();
</script>
</body>
</html>"""
