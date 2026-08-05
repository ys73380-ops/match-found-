"""
Telegram Dating Bot — Swipe Matching Web App (VERCEL VERSION - 10 LAKH PROFESSIONAL)
======================================================================================
✅ Advanced AI Intent-Detection Chat Engine
✅ Hinge-Style Prompts for Realistic AI Profiles
✅ Ultra-Premium Glassmorphism UI & 3D Swipe Physics
✅ Robust FastAPI Architecture with Upstash KV
✅ Telegram WebApp HMAC Validation & Notifications
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, quote, unquote

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────
# CONFIG (Environment Variables with Fallback)
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8859077363:AAEY5IvqLjvp2KHFi-sDeihrGCKmTu1vrtU")
KV_URL = os.environ.get("KV_URL", "https://prompt-quetzal-219477.upstash.io")
KV_TOKEN = os.environ.get("KV_TOKEN", "ggAAAAAAA1lVAAIgcDECZqGNn4s9xuEezqSIxvU8XvbqsdNhFWCEEGpm8Lf0Zw")

app = FastAPI(title="Premium Dating Swipe App")

# Fallback in-memory storage for local/dev
_mem: dict[str, Any] = {}

# ─────────────────────────────────────────────
# AI DATA POOLS
# ─────────────────────────────────────────────
AI_MALE_NAMES = ["Arjun", "Rohan", "Aarav", "Vivaan", "Aditya", "Kabir", "Ishaan", "Reyansh", "Ayaan", "Vihaan", "Dhruv", "Arnav", "Shaurya", "Yash", "Krish", "Siddharth", "Raj", "Dev", "Ansh", "Kartik", "Neil", "Aarush", "Ranveer", "Samar"]
AI_FEMALE_NAMES = ["Ananya", "Priya", "Isha", "Myra", "Aanya", "Saanvi", "Kiara", "Diya", "Riya", "Tara", "Avni", "Kavya", "Zara", "Nisha", "Meera", "Pooja", "Aisha", "Sneha", "Pihu", "Sara", "Simran", "Rhea", "Mahi", "Navya"]

AI_BIOS = [
    "Music lover 🎵 | Coffee addict ☕", "Travel enthusiast ✈️ | Foodie 🍕",
    "Gym freak 💪 | Netflix binge-watcher 🎬", "Photography 📸 | Adventure seeker 🏔️",
    "Bookworm 📚 | Tea lover 🍵", "Dog person 🐕 | Sunset chaser 🌅",
    "Gamer 🎮 | Anime fan 🎌", "Dancer 💃 | Night owl 🦉",
    "Artist 🎨 | Dreamer ✨", "Tech geek 💻 | Startup enthusiast 🚀"
]

AI_PROMPTS = [
    {"q": "My simple pleasure", "a": "Finding the perfect cup of chai ☕"},
    {"q": "I'm looking for", "a": "Someone who laughs at my bad jokes 😂"},
    {"q": "Together, we could", "a": "Plan a spontaneous road trip 🚗"},
    {"q": "My favorite story", "a": "The time I got lost in Rome and found the best pizza 🍕"},
    {"q": "Sunday mornings are for", "a": "Sleeping in and making pancakes 🥞"},
    {"q": "Unpopular opinion", "a": "Pineapple absolutely belongs on pizza 🍍"},
    {"q": "I geek out on", "a": "True crime podcasts and astrophysics 🌌"},
    {"q": "My most controversial opinion", "a": "Friends is overrated, HIMYM is the real king 👑"}
]

# ─────────────────────────────────────────────
# ADVANCED AI CHAT ENGINE (Intent Detection)
# ─────────────────────────────────────────────
AI_INTENTS = {
    "GREETING": ["Hey! 😊 Kaisi ho? Aaj ka din kaisa raha?", "Hello! 💕 Kya haal hai? Mujhe tumhara message dekh ke accha laga.", "Hiii! ✨ Bolo, kya kar rahe ho aaj kal?"],
    "DOING": ["Bas kuch nahi, tumse baat kar rahi hu! 😍 Tum batao?", "Coffee pi rahi hu aur music sun rahi hu ☕ Tumhara kya plan hai aaj?", "Netflix pe ek nayi series dekh rahi hu 🎬 Tumhe kya pasand hai dekhna?"],
    "HOBBIES": ["Mujhe travel karna aur naye cafes explore karna bahut pasand hai ✈️ Tumhe kya karna pasand hai?", "Photography aur reading! 📸 Books mein kho jana mujhe accha lagta hai. Tumhara koi secret talent?", "Gym aur hiking! 🏔️ Nature mein time spend karna best hai. Tum free time mein kya karte ho?"],
    "LOCATION": ["Main Mumbai se hu, par travel karte rehte hain 🌆 Tum kahan se ho?", "Delhi ki hu! Yahan ka food bahut miss karta hu jab bahar hoti hu 🍕 Tumhari city kaisi hai?", "Bangalore! Weather yahan kaafi accha hai 🌧️ Tum kahan rehte ho?"],
    "COMPLIMENT": ["Aww, thank you! 🥰 Tum bhi bahut sweet ho. Aisa kyu lag raha hai aaj?", "Haha stop it! 😊 Par sach batau toh mujhe blush karwa diya tumne. Tumhara din kaisa ja raha hai?", "You're making me smile! ✨ It's rare to find someone so genuine."],
    "FLIRT": ["Oh really? 😏 Itni jaldi? Pehle coffee toh pine chalo ☕", "Haha, direct! Mujhe pasand hai 😍 Par batao, what makes you stand out?", "Date pe chalna hai? 🌙 Pehle mujhe apna best joke sunao!"],
    "QUESTION": ["Interesting question! 🤔 Mujhe lagta hai har cheez ka ek reason hota hai. Tum kya sochte ho?", "Hmm, let me think... 💭 Waise main hamesha positive sochti hu. Tumhara perspective kya hai?", "Accha? Mujhe bhi yahi pasand hai! We have so much in common ✨ Aur batao apne baare mein."],
    "DEFAULT": ["Haha that's nice! Tell me more about yourself 😊", "Interesting! Mujhe tumse baat karke accha lag raha hai 💕", "Wow, really? That's so cool! ✨", "Hmm, I like that! Aur batao 😍", "You seem really sweet! 🥰 Kuch aur interesting batao apne baare mein.", "That's amazing! Tum bahut interesting ho 😊 Weekends pe kya karte ho normally?"]
}

def get_ai_response(message: str) -> str:
    msg_lower = message.lower().strip()
    if re.search(r'\b(hi|hello|hey|hlo|namaste|kaise ho|kaisi ho|kya haal)\b', msg_lower): intent = "GREETING"
    elif re.search(r'\b(kya kar rahi|kya kar rahe|what are you doing|kuch nahi)\b', msg_lower): intent = "DOING"
    elif re.search(r'\b(pasand|hobby|interest|like to do|free time)\b', msg_lower): intent = "HOBBIES"
    elif re.search(r'\b(kahan se|where from|city|rehti|rehte)\b', msg_lower): intent = "LOCATION"
    elif re.search(r'\b(beautiful|cute|pretty|handsome|hot|gorgeous|pyari|sundar)\b', msg_lower): intent = "COMPLIMENT"
    elif re.search(r'\b(love|pyar|date|milna|meet)\b', msg_lower): intent = "FLIRT"
    elif '?' in msg_lower or re.search(r'\b(kya|kaun|kaise|kab|batao)\b', msg_lower): intent = "QUESTION"
    else: intent = "DEFAULT"
    return random.choice(AI_INTENTS[intent])

# ─────────────────────────────────────────────
# STORAGE (Vercel KV REST API with Fallback)
# ─────────────────────────────────────────────
async def kv_get(key: str) -> Any:
    if not KV_URL: return _mem.get(key)
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{KV_URL}/get/{quote(key)}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            res = r.json().get("result")
            return json.loads(res) if res else None
    except Exception: return _mem.get(key)

async def kv_set(key: str, val: Any) -> None:
    _mem[key] = val
    if not KV_URL: return
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(f"{KV_URL}/set/{quote(key)}/{quote(json.dumps(val))}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
    except Exception: pass

async def kv_profile_keys() -> list[str]:
    if not KV_URL: return [k for k in _mem if k.startswith("profile:")]
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{KV_URL}/keys/{quote('profile:*')}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            return r.json().get("result", []) or []
    except Exception: return [k for k in _mem if k.startswith("profile:")]

# ─────────────────────────────────────────────
# TELEGRAM VERIFICATION & API
# ─────────────────────────────────────────────
def verify_telegram_user(init_data: str) -> Optional[dict]:
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", None)
        if not received_hash: return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash != received_hash or time.time() - int(parsed.get("auth_date", 0)) > 86400: return None
        return json.loads(unquote(parsed.get("user", "{}")))
    except Exception: return None

async def send_telegram_message(user_id: int, text: str):
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": user_id, "text": text, "parse_mode": "HTML"})
    except Exception: pass

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────
class InitRequest(BaseModel): init_data: str
class RegisterRequest(BaseModel): init_data: str; name: str; age: int; gender: str
class SwipeRequest(BaseModel): init_data: str; target_id: int; action: str
class MessageRequest(BaseModel): init_data: str; to_user: int; message: str
class FindRealRequest(BaseModel): init_data: str
class AIMessageRequest(BaseModel): init_data: str; ai_profile_id: str; message: str

# ─────────────────────────────────────────────
# AI PROFILE GENERATION (Hinge-Style Prompts)
# ─────────────────────────────────────────────
def generate_ai_profiles(my_gender: str, count: int = 10) -> list[dict]:
    names = AI_FEMALE_NAMES if my_gender == "male" else AI_MALE_NAMES
    target_gender = "female" if my_gender == "male" else "male"
    selected_names = random.sample(names, min(count, len(names)))
    profiles = []
    for i, name in enumerate(selected_names):
        profiles.append({
            "user_id": f"ai_{random.randint(100000, 999999)}_{i}",
            "name": name, "age": random.randint(18, 28), "gender": target_gender,
            "bio": random.choice(AI_BIOS), "is_ai": True,
            "prompts": random.sample(AI_PROMPTS, 2)
        })
    return profiles

# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(): return HTMLResponse(content=FRONTEND_HTML)

@app.post("/api/init")
async def api_init(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid Telegram user")
    uid = user.get("id")
    profile = await kv_get(f"profile:{uid}")
    return {"user_id": uid, "has_profile": bool(profile), "profile": profile, "tg_name": user.get("first_name", "User")}

@app.post("/api/register")
async def api_register(req: RegisterRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid Telegram user")
    if not (13 <= req.age <= 100): raise HTTPException(400, "Age 13-100 ke beech honi chahiye")
    if req.gender not in ("male", "female"): raise HTTPException(400, "Gender male/female hona chahiye")
    profile = {"user_id": user.get("id"), "name": req.name.strip()[:50], "age": req.age, "gender": req.gender}
    await kv_set(f"profile:{user.get('id')}", profile)
    return {"ok": True, "profile": profile}

@app.get("/api/profiles/{init_data}")
async def api_profiles(init_data: str):
    user = verify_telegram_user(init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile: return {"profiles": []}
    my_swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    seen = set(my_swipes["liked"] + my_swipes["passed"] + [uid])
    candidates = []
    for key in await kv_profile_keys():
        p = await kv_get(key)
        if not p: continue
        pid = p["user_id"]
        if pid in seen: continue
        if my_profile["gender"] == p["gender"]: continue
        candidates.append(p)
    random.shuffle(candidates)
    return {"profiles": candidates[:20]}

@app.post("/api/swipe")
async def api_swipe(req: SwipeRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    matched, match_info = False, None
    if req.action == "like":
        if req.target_id not in swipes["liked"]: swipes["liked"].append(req.target_id)
        target_swipes = await kv_get(f"swipes:{req.target_id}") or {"liked": [], "passed": []}
        if uid in target_swipes["liked"]:
            matched = True
            target_profile = await kv_get(f"profile:{req.target_id}") or {}
            my_profile = await kv_get(f"profile:{uid}") or {}
            match_info = {"name": target_profile.get("name", "Someone"), "age": target_profile.get("age")}
            for key_uid, other_uid in ((uid, req.target_id), (req.target_id, uid)):
                matches = await kv_get(f"matches:{key_uid}") or []
                matches.append({"partner_id": other_uid, "created_at": datetime.now(timezone.utc).isoformat()})
                await kv_set(f"matches:{key_uid}", matches)
            await send_telegram_message(uid, f"🎉 <b>It's a Match!</b>\n\nYou matched with <b>{target_profile.get('name')}</b> ({target_profile.get('age')})!\n\nOpen the Web App to start chatting! 💕")
            await send_telegram_message(req.target_id, f"🎉 <b>It's a Match!</b>\n\nYou matched with <b>{my_profile.get('name')}</b> ({my_profile.get('age')})!\n\nOpen the Web App to start chatting! 💕")
    else:
        if req.target_id not in swipes["passed"]: swipes["passed"].append(req.target_id)
    await kv_set(f"swipes:{uid}", swipes)
    return {"matched": matched, "match_info": match_info}

@app.get("/api/matches/{init_data}")
async def api_matches(init_data: str):
    user = verify_telegram_user(init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    matches = await kv_get(f"matches:{uid}") or []
    result = []
    for m in matches:
        p = await kv_get(f"profile:{m['partner_id']}") or {}
        result.append({"user_id": m['partner_id'], "name": p.get("name", "User"), "age": p.get("age"), "gender": p.get("gender"), "created_at": m.get("created_at")})
    return {"matches": result}

@app.post("/api/send_message")
async def api_send_message(req: MessageRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    to_user = req.to_user
    matches = await kv_get(f"matches:{uid}") or []
    if to_user not in [m['partner_id'] for m in matches]: raise HTTPException(403, "You are not matched with this user")
    chat_id = f"chat:{min(uid, to_user)}:{max(uid, to_user)}"
    messages = await kv_get(chat_id) or []
    new_message = {"from": uid, "to": to_user, "text": req.message.strip()[:500], "timestamp": datetime.now(timezone.utc).isoformat()}
    messages.append(new_message)
    await kv_set(chat_id, messages)
    sender_profile = await kv_get(f"profile:{uid}") or {}
    await send_telegram_message(to_user, f"💬 <b>New message from {sender_profile.get('name')}</b>\n\n\"{req.message.strip()[:100]}\"\n\nOpen the Web App to reply! 💕")
    return {"ok": True, "message": new_message}

@app.get("/api/get_messages/{init_data}/{partner_id}")
async def api_get_messages(init_data: str, partner_id: int):
    user = verify_telegram_user(init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    matches = await kv_get(f"matches:{uid}") or []
    if partner_id not in [m['partner_id'] for m in matches]: raise HTTPException(403, "You are not matched with this user")
    chat_id = f"chat:{min(uid, partner_id)}:{max(uid, partner_id)}"
    return {"messages": await kv_get(chat_id) or [], "user_id": uid}

@app.post("/api/find_real")
async def api_find_real(req: FindRealRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid Telegram user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile: raise HTTPException(400, "Profile nahi mila")
    await kv_set(f"searching:{uid}", {"active": True, "since": datetime.now(timezone.utc).isoformat()})
    await send_telegram_message(uid, f"🔍 <b>Real Match Search Activated!</b>\n\nHi {my_profile.get('name')}! Hum aapke liye real matches dhundh rahe hain.\n\n✅ Jaise hi koi match milega, hum aapko is bot ke through turant inform karenge!\n\n📱 Apna Telegram notifications ON rakhein.")
    return {"ok": True, "message": "Aapki request register ho gayi hai!"}

@app.post("/api/ai_profiles")
async def api_ai_profiles(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile: return {"profiles": []}
    return {"profiles": generate_ai_profiles(my_profile["gender"], count=10)}

@app.post("/api/ai_chat")
async def api_ai_chat(req: AIMessageRequest):
    user = verify_telegram_user(req.init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    chat_key = f"ai_chat:{uid}:{req.ai_profile_id}"
    messages = await kv_get(chat_key) or []
    user_msg = {"from": uid, "to": req.ai_profile_id, "text": req.message.strip()[:500], "timestamp": datetime.now(timezone.utc).isoformat(), "is_user": True}
    messages.append(user_msg)
    ai_response = get_ai_response(req.message)
    ai_msg = {"from": req.ai_profile_id, "to": uid, "text": ai_response, "timestamp": datetime.now(timezone.utc).isoformat(), "is_user": False}
    messages.append(ai_msg)
    await kv_set(chat_key, messages)
    return {"ok": True, "user_message": user_msg, "ai_response": ai_msg, "all_messages": messages}

@app.get("/api/ai_messages/{init_data}/{ai_profile_id}")
async def api_ai_messages(init_data: str, ai_profile_id: str):
    user = verify_telegram_user(init_data)
    if not user: raise HTTPException(403, "Invalid user")
    uid = user.get("id")
    return {"messages": await kv_get(f"ai_chat:{uid}:{ai_profile_id}") or [], "user_id": uid}

# ═════════════════════════════════════════════
# FRONTEND HTML (Ultra-Premium UI)
# ═════════════════════════════════════════════
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>💘 Premium Swipe</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root {
  --bg-primary: #0A0A12; --bg-secondary: #12121F; --glass: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.08); --accent-pink: #FF007A; --accent-purple: #7928CA;
  --accent-blue: #00DFD8; --text-primary: #FFFFFF; --text-secondary: #8B8B9E;
  --gradient-main: linear-gradient(135deg, #FF007A 0%, #7928CA 100%);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg-primary);color:var(--text-primary);min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow-x:hidden}
.header{padding:20px;text-align:center;width:100%}
.header h1{font-size:28px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;letter-spacing:-0.5px}
.nav-tabs{display:none;width:90%;max-width:400px;margin:10px auto;background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:20px;padding:6px;gap:6px}
.nav-tabs.show{display:flex}
.nav-tab{flex:1;padding:14px;border:none;background:transparent;color:var(--text-secondary);font-size:14px;font-weight:600;border-radius:16px;cursor:pointer;transition:all 0.3s}
.nav-tab.active{background:var(--gradient-main);color:#fff;box-shadow:0 4px 15px rgba(255,0,122,0.3)}
.progress-bar{width:90%;max-width:400px;height:4px;background:var(--bg-secondary);border-radius:10px;margin:10px auto;overflow:hidden}
.progress-fill{height:100%;background:var(--gradient-main);transition:width 0.5s cubic-bezier(0.4, 0, 0.2, 1);width:0%}
.step{display:none;width:90%;max-width:400px;animation:fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1)}
.step.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.step-card{background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:32px;padding:35px 25px;margin-top:20px;box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.step-icon{font-size:64px;text-align:center;margin-bottom:20px}
.step h2{font-size:26px;text-align:center;margin-bottom:10px;font-weight:800;letter-spacing:-0.5px}
.step p{font-size:15px;text-align:center;color:var(--text-secondary);margin-bottom:30px;line-height:1.5}
.step input,.step select{width:100%;padding:18px 22px;margin-bottom:20px;border-radius:20px;border:2px solid var(--glass-border);background:var(--bg-secondary);color:#fff;font-size:16px;transition:border 0.3s}
.step input:focus,.step select:focus{outline:none;border-color:var(--accent-pink)}
.step input::placeholder{color:#555}
.step button{width:100%;padding:18px;border-radius:20px;border:none;background:var(--gradient-main);color:#fff;font-size:17px;font-weight:700;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 10px 30px rgba(255,0,122,0.25)}
.step button:active{transform:scale(0.98)}
.step button:disabled{opacity:0.4;cursor:not-allowed;filter:grayscale(0.5)}
.gender-options,.mode-options{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:25px}
.gender-btn,.mode-btn{padding:25px 15px;border-radius:24px;border:2px solid var(--glass-border);background:var(--bg-secondary);color:#fff;font-size:16px;cursor:pointer;transition:all 0.3s;text-align:center}
.gender-btn:active,.mode-btn:active{transform:scale(0.96)}
.gender-btn.selected,.mode-btn.selected{border-color:var(--accent-pink);background:linear-gradient(135deg,rgba(255,0,122,0.15),rgba(121,40,202,0.15))}
.gender-btn .emoji,.mode-btn .mode-emoji{font-size:44px;display:block;margin-bottom:10px}
.mode-btn .mode-title{font-size:17px;font-weight:700;display:block;margin-bottom:6px}
.mode-btn .mode-desc{font-size:12px;color:var(--text-secondary);display:block;line-height:1.4}
.mode-btn .mode-badge{position:absolute;top:10px;right:10px;padding:4px 10px;border-radius:10px;font-size:10px;font-weight:800}
.badge-real{background:var(--accent-blue);color:#000}
.badge-ai{background:var(--gradient-main);color:#fff}
.info-card{background:var(--bg-secondary);border:1px solid var(--glass-border);border-radius:20px;padding:22px;margin-bottom:25px;text-align:center}
.info-card .info-title{font-size:16px;font-weight:700;margin-bottom:10px}
.info-card .info-text{font-size:13px;color:var(--text-secondary);line-height:1.6}
.info-highlight{color:var(--accent-pink);font-weight:600}
.card-container{position:relative;width:92%;max-width:420px;height:600px;margin:10px auto;display:none;perspective:1000px}
.card{position:absolute;width:100%;height:100%;border-radius:32px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,0.6);cursor:grab;user-select:none;touch-action:none;transition:transform 0.1s linear;will-change:transform}
.card:active{cursor:grabbing}
.card-avatar{width:100%;height:55%;display:flex;align-items:center;justify-content:center;font-size:120px;font-weight:800;color:rgba(255,255,255,0.9);text-shadow:0 10px 30px rgba(0,0,0,0.4);position:relative}
.card-bio{position:absolute;bottom:15px;left:20px;right:20px;text-align:center;font-size:14px;color:rgba(255,255,255,0.9);background:rgba(0,0,0,0.5);padding:10px 16px;border-radius:16px;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1)}
.card-info{padding:25px;background:var(--bg-secondary);height:45%;border-top:1px solid var(--glass-border)}
.card-name{font-size:34px;font-weight:800;margin-bottom:6px;letter-spacing:-1px}
.card-age{font-size:22px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:700;margin-bottom:12px}
.card-prompts{display:flex;flex-direction:column;gap:12px;margin-top:15px}
.card-prompt{background:var(--glass);border:1px solid var(--glass-border);padding:12px 16px;border-radius:16px}
.prompt-q{font-size:11px;color:var(--text-secondary);margin-bottom:4px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px}
.prompt-a{font-size:15px;color:#fff;font-weight:500}
.swipe-label{position:absolute;top:50px;padding:12px 30px;border-radius:16px;font-size:32px;font-weight:900;opacity:0;pointer-events:none;text-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:10;letter-spacing:1px}
.swipe-label.like{right:30px;color:#00DFD8;border:5px solid #00DFD8;transform:rotate(15deg)}
.swipe-label.pass{left:30px;color:#FF007A;border:5px solid #FF007A;transform:rotate(-15deg)}
.buttons{display:none;gap:50px;margin:30px 0;justify-content:center}
.btn{width:80px;height:80px;border-radius:50%;border:none;font-size:36px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 15px 40px rgba(0,0,0,0.4);transition:transform 0.2s;background:var(--bg-secondary);border:2px solid var(--glass-border)}
.btn:active{transform:scale(0.9)}
.btn-pass{color:#FF007A}
.btn-like{color:#00DFD8}
.empty-state{display:none;text-align:center;padding:80px 30px;width:90%;max-width:400px}
.empty-state .emoji{font-size:90px;margin-bottom:30px}
.empty-state h3{font-size:28px;margin-bottom:12px;font-weight:800}
.empty-state p{font-size:16px;color:var(--text-secondary);line-height:1.6}
.match-modal{position:fixed;inset:0;background:rgba(10,10,18,0.95);backdrop-filter:blur(20px);display:none;align-items:center;justify-content:center;z-index:100;flex-direction:column;padding:20px}
.match-modal.show{display:flex;animation:fadeIn 0.4s}
.match-hearts{font-size:100px;margin-bottom:30px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}
.match-title{font-size:46px;font-weight:900;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:20px;letter-spacing:-1px}
.match-name{font-size:20px;text-align:center;color:var(--text-secondary);margin-bottom:40px;font-weight:500}
.match-btn{padding:18px 60px;border-radius:30px;border:none;background:var(--gradient-main);color:#fff;font-size:18px;font-weight:700;cursor:pointer;box-shadow:0 15px 40px rgba(255,0,122,0.3)}
.matches-section{display:none;width:90%;max-width:400px;margin:20px auto}
.matches-section.show{display:block}
.matches-header{font-size:26px;font-weight:800;margin-bottom:25px;letter-spacing:-0.5px}
.match-card{background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:24px;padding:20px;margin-bottom:15px;display:flex;align-items:center;gap:18px;cursor:pointer;transition:transform 0.2s}
.match-card:active{transform:scale(0.98)}
.match-avatar{width:65px;height:65px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:800;color:#fff;flex-shrink:0}
.match-info{flex:1}
.match-name-text{font-size:19px;font-weight:700;margin-bottom:6px}
.match-details{font-size:14px;color:var(--text-secondary)}
.chat-btn{padding:12px 24px;border-radius:16px;border:none;background:var(--gradient-main);color:#fff;font-size:14px;font-weight:700;cursor:pointer;flex-shrink:0}
.chat-section{display:none;width:100%;height:calc(100vh - 120px);flex-direction:column}
.chat-section.show{display:flex}
.chat-header{background:var(--bg-secondary);padding:20px;display:flex;align-items:center;gap:15px;border-bottom:1px solid var(--glass-border)}
.back-btn{width:45px;height:45px;border-radius:50%;border:none;background:var(--glass);color:#fff;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.chat-user-info{flex:1}
.chat-user-name{font-size:19px;font-weight:700}
.chat-user-status{font-size:13px;color:#00DFD8;font-weight:500}
.chat-messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px}
.message{max-width:80%;padding:14px 18px;border-radius:20px;word-wrap:break-word;font-size:15px;line-height:1.4}
.message.sent{align-self:flex-end;background:var(--gradient-main);color:#fff;border-bottom-right-radius:6px}
.message.received{align-self:flex-start;background:var(--bg-secondary);color:#fff;border-bottom-left-radius:6px;border:1px solid var(--glass-border)}
.message-time{font-size:10px;opacity:0.6;margin-top:6px;display:block}
.chat-input{background:var(--bg-secondary);padding:15px 20px;display:flex;gap:12px;border-top:1px solid var(--glass-border)}
.chat-input input{flex:1;padding:16px 22px;border-radius:24px;border:2px solid var(--glass-border);background:var(--bg-primary);color:#fff;font-size:16px}
.chat-input input:focus{outline:none;border-color:var(--accent-pink)}
.send-btn{width:55px;height:55px;border-radius:50%;border:none;background:var(--gradient-main);color:#fff;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.typing-indicator{align-self:flex-start;padding:14px 18px;background:var(--bg-secondary);border-radius:20px;border-bottom-left-radius:6px;display:flex;gap:6px;align-items:center;border:1px solid var(--glass-border)}
.typing-dot{width:8px;height:8px;border-radius:50%;background:var(--text-secondary);animation:typingBounce 1.4s infinite}
.typing-dot:nth-child(2){animation-delay:0.2s}
.typing-dot:nth-child(3){animation-delay:0.4s}
@keyframes typingBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
.notification{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);color:#fff;padding:16px 28px;border-radius:20px;font-size:15px;font-weight:600;box-shadow:0 15px 40px rgba(0,0,0,0.5);z-index:200;opacity:0;pointer-events:none;transition:all 0.4s cubic-bezier(0.4, 0, 0.2, 1);max-width:90%;text-align:center}
.notification.show{opacity:1;transform:translateX(-50%) translateY(10px)}
.searching-overlay{position:fixed;inset:0;background:rgba(10,10,18,0.95);backdrop-filter:blur(20px);display:none;align-items:center;justify-content:center;z-index:90;flex-direction:column;padding:20px}
.searching-overlay.show{display:flex}
.searching-spinner{width:80px;height:80px;border:6px solid var(--glass-border);border-top-color:var(--accent-pink);border-radius:50%;animation:spin 1s linear infinite;margin-bottom:30px}
@keyframes spin{to{transform:rotate(360deg)}}
.searching-text{font-size:26px;font-weight:800;margin-bottom:12px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.searching-subtext{font-size:16px;color:var(--text-secondary);text-align:center}
.loading{padding:80px;text-align:center;color:var(--text-secondary);font-size:16px}
.error-msg{color:#FF007A;font-size:13px;text-align:center;margin-top:5px;min-height:20px;font-weight:600}
.success-screen{display:none;width:90%;max-width:400px;text-align:center}
.success-screen.show{display:block}
.success-card{background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:32px;padding:40px 25px;margin-top:20px}
.success-icon{font-size:90px;margin-bottom:25px}
.success-title{font-size:28px;font-weight:800;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:15px}
.success-text{font-size:15px;color:var(--text-secondary);line-height:1.7;margin-bottom:30px}
.highlight{color:var(--accent-pink);font-weight:700}
.try-ai-btn{width:100%;padding:18px;border-radius:20px;border:none;background:var(--gradient-main);color:#fff;font-size:16px;font-weight:700;cursor:pointer;margin-bottom:12px}
.go-home-btn{width:100%;padding:16px;border-radius:20px;border:2px solid var(--glass-border);background:transparent;color:var(--text-secondary);font-size:14px;font-weight:600;cursor:pointer}
.ai-tag{position:absolute;top:20px;left:20px;padding:6px 14px;border-radius:12px;background:var(--gradient-main);color:#fff;font-size:12px;font-weight:800;z-index:5;display:flex;align-items:center;gap:6px;box-shadow:0 4px 15px rgba(255,0,122,0.4)}
</style>
</head>
<body>
<div class="header"><h1>💘 Premium Swipe</h1></div>
<div class="nav-tabs" id="navTabs">
  <button class="nav-tab active" onclick="showSection('swipe', this)">💘 Swipe</button>
  <button class="nav-tab" onclick="showSection('matches', this)">💬 Matches</button>
</div>
<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
<div class="loading" id="loading">Loading...</div>

<div class="step" id="step1"><div class="step-card"><div class="step-icon">👋</div><h2>Tumhara Naam?</h2><p>Apna pehla naam batao</p><input type="text" id="regName" placeholder="e.g. Rahul" maxlength="50" autocomplete="off"><div class="error-msg" id="nameError"></div><button onclick="nextStep(2)" id="btn1">Continue →</button></div></div>
<div class="step" id="step2"><div class="step-card"><div class="step-icon">🎂</div><h2>Tumhari Age?</h2><p>13-100 ke beech honi chahiye</p><input type="number" id="regAge" placeholder="e.g. 24" min="13" max="100" autocomplete="off"><div class="error-msg" id="ageError"></div><button onclick="nextStep(3)" id="btn2">Continue →</button></div></div>
<div class="step" id="step3"><div class="step-card"><div class="step-icon">👤</div><h2>Tum Kaun Ho?</h2><p>Apna gender select karo</p><div class="gender-options"><button class="gender-btn" onclick="selectGender('male', this)"><span class="emoji">👨</span>Boy</button><button class="gender-btn" onclick="selectGender('female', this)"><span class="emoji">👩</span>Girl</button></div><div class="error-msg" id="genderError"></div><button onclick="registerProfile()" id="btn3" disabled>🚀 Continue →</button></div></div>

<div class="step" id="step4">
  <div class="step-card">
    <div class="step-icon">✨</div><h2>Match Mode?</h2><p>Real log ya AI se practice karo</p>
    <div class="mode-options">
      <button class="mode-btn" id="modeReal" onclick="selectMode('real', this)" style="position:relative"><span class="mode-badge badge-real">REAL</span><span class="mode-emoji">👥</span><span class="mode-title">Find Real</span><span class="mode-desc">Real logo se match karo</span></button>
      <button class="mode-btn" id="modeAI" onclick="selectMode('ai', this)" style="position:relative"><span class="mode-badge badge-ai">AI</span><span class="mode-emoji">🤖</span><span class="mode-title">Find AI</span><span class="mode-desc">AI profiles se chat karo</span></button>
    </div>
    <div id="realInfoCard" class="info-card" style="display:none"><div class="info-title">🔔 Real Match Kaise Kaam Karta Hai?</div><div class="info-text">Hum aapke liye <span class="info-highlight">real log</span> dhundhenge.<br>Jaise hi koi match milega, hum aapko <span class="info-highlight">bot ke dwara turant inform karenge!</span></div></div>
    <div id="aiInfoCard" class="info-card" style="display:none"><div class="info-title">🤖 AI Match Kaise Kaam Karta Hai?</div><div class="info-text">AI profiles se <span class="info-highlight">swipe aur chat</span> karo.<br>Practice karo aur apna game strong banao! 💪<br>⚡ Turant matches milenge — koi wait nahi!</div></div>
    <div class="error-msg" id="modeError"></div>
    <button onclick="startMatchMode()" id="btn4" disabled style="margin-top:15px">🚀 Let's Go!</button>
  </div>
</div>

<div class="searching-overlay" id="searchingOverlay"><div class="searching-spinner"></div><div class="searching-text" id="searchingTitle">Searching...</div><div class="searching-subtext" id="searchingSubtext">Please wait</div></div>
<div class="notification" id="notification"><div id="notifText">Matches found!</div></div>

<div class="success-screen" id="realSuccessScreen">
  <div class="success-card">
    <div class="success-icon">✅</div><div class="success-title">Request Registered!</div>
    <div class="success-text">Aapki real match request <span class="highlight">successfully register</span> ho gayi hai!<br>Jaise hi koi <span class="highlight">match milega</span>, hum aapko <span class="highlight">bot ke dwara turant inform</span> karenge! 🔔</div>
    <button class="try-ai-btn" onclick="switchToAI()">🤖 Tab tak AI se Practice Karo</button>
    <button class="go-home-btn" onclick="goHome()">🏠 Home jaao</button>
  </div>
</div>

<div class="card-container" id="cardContainer"></div>
<div class="buttons" id="buttons"><button class="btn btn-pass" onclick="swipe('pass')">✖️</button><button class="btn btn-like" onclick="swipe('like')">❤️</button></div>
<div class="empty-state" id="emptyState"><div class="emoji">😢</div><h3>Koi Matches Nahi Mile</h3><p id="emptyText">Abhi koi profiles nahi hai.</p></div>

<div class="match-modal" id="matchModal"><div class="match-hearts">💕</div><div class="match-title">It's a Match!</div><div class="match-name" id="matchName"></div><button class="match-btn" onclick="closeMatch()" id="matchKeepBtn">Keep Swiping</button></div>

<div class="matches-section" id="matchesSection"><div class="matches-header">Your Matches 💕</div><div id="matchesList"></div></div>

<div class="chat-section" id="chatSection">
  <div class="chat-header"><button class="back-btn" onclick="exitChat()">←</button><div class="match-avatar" id="chatAvatar" style="width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;color:#fff"></div><div class="chat-user-info"><div class="chat-user-name" id="chatUserName">User</div><div class="chat-user-status" id="chatUserStatus">Online</div></div></div>
  <div class="chat-messages" id="chatMessages"></div>
  <div class="chat-input"><input type="text" id="chatInput" placeholder="Type a message..." maxlength="500"><button class="send-btn" onclick="sendMessage()" id="sendBtn">➤</button></div>
</div>

<script>
const tg = window.Telegram.WebApp; tg.ready(); tg.expand(); tg.setHeaderColor('#0A0A12'); tg.setBackgroundColor('#0A0A12');
let currentStep = 1, selectedGender = '', selectedMode = '', matchMode = '';
let profiles = [], currentIndex = 0, startX = 0, startY = 0, currentX = 0, isDragging = false, activeCard = null;
let currentChatPartner = null, messagePollInterval = null, isAIMode = false, aiMatchedProfiles = [], lastMatchedAIProfile = null;
const gradients = ['linear-gradient(135deg,#FF007A,#7928CA)','linear-gradient(135deg,#00DFD8,#007CF0)','linear-gradient(135deg,#FF4D4D,#F9CB28)','linear-gradient(135deg,#7928CA,#FF007A)','linear-gradient(135deg,#43e97b,#38f9d7)'];

function updateProgress() { document.getElementById('progressFill').style.width = ((currentStep - 1) / 4) * 100 + '%'; }
function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById('realSuccessScreen').classList.remove('show');
  const step = document.getElementById('step' + n); if (step) step.classList.add('active');
  currentStep = n; updateProgress();
}
function nextStep(n) {
  if (currentStep === 1) { const n = document.getElementById('regName').value.trim(); if (!n || n.length < 2) { document.getElementById('nameError').textContent = '❌ Valid naam likho!'; return; } document.getElementById('nameError').textContent = ''; }
  if (currentStep === 2) { const a = parseInt(document.getElementById('regAge').value); if (!a || a < 13 || a > 100) { document.getElementById('ageError').textContent = '❌ Age 13-100 honi chahiye!'; return; } document.getElementById('ageError').textContent = ''; }
  showStep(n);
}
function selectGender(g, btn) { selectedGender = g; document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('selected')); btn.classList.add('selected'); document.getElementById('btn3').disabled = false; }
function selectMode(m, btn) {
  selectedMode = m; document.querySelectorAll('.mode-btn').forEach(b => { b.classList.remove('selected'); }); btn.classList.add('selected');
  document.getElementById('realInfoCard').style.display = m === 'real' ? 'block' : 'none';
  document.getElementById('aiInfoCard').style.display = m === 'ai' ? 'block' : 'none';
  document.getElementById('btn4').disabled = false;
}
async function init() {
  try {
    const res = await fetch('/api/init', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData}) });
    if (!res.ok) throw new Error('Auth failed'); const data = await res.json();
    document.getElementById('loading').style.display = 'none';
    if (!data.has_profile) { document.getElementById('regName').value = data.tg_name || ''; showStep(1); }
    else { document.querySelector('.progress-bar').style.display = 'none'; document.getElementById('navTabs').classList.add('show'); showStep(4); }
  } catch (e) { document.getElementById('loading').innerHTML = '❌ Error. Bot se dobara kholo.'; }
}
async function registerProfile() {
  const btn = document.getElementById('btn3'); btn.textContent = 'Saving...'; btn.disabled = true;
  try {
    const res = await fetch('/api/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData, name: document.getElementById('regName').value.trim(), age: parseInt(document.getElementById('regAge').value), gender: selectedGender}) });
    if (res.ok) showStep(4); else alert('Error aaya');
  } catch (e) { alert('Network error!'); } finally { btn.textContent = '🚀 Continue →'; btn.disabled = false; }
}
async function startMatchMode() { matchMode = selectedMode; selectedMode === 'real' ? await findRealMatches() : await findAIMatches(); }
async function findRealMatches() {
  document.getElementById('searchingOverlay').classList.add('show');
  try {
    await fetch('/api/find_real', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData}) });
    await new Promise(r => setTimeout(r, 1500)); document.getElementById('searchingOverlay').classList.remove('show');
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active')); document.querySelector('.progress-bar').style.display = 'none'; document.getElementById('navTabs').classList.add('show');
    document.getElementById('realSuccessScreen').classList.add('show');
  } catch (e) { document.getElementById('searchingOverlay').classList.remove('show'); }
}
function switchToAI() { document.getElementById('realSuccessScreen').classList.remove('show'); selectedMode = 'ai'; matchMode = 'ai'; findAIMatches(); }
function goHome() { document.getElementById('realSuccessScreen').classList.remove('show'); showStep(4); }
async function findAIMatches() {
  document.getElementById('searchingOverlay').classList.add('show');
  try {
    const res = await fetch('/api/ai_profiles', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData}) });
    const data = await res.json(); profiles = data.profiles || []; isAIMode = true; currentIndex = 0;
    await new Promise(r => setTimeout(r, 1200)); document.getElementById('searchingOverlay').classList.remove('show');
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active')); document.querySelector('.progress-bar').style.display = 'none'; document.getElementById('navTabs').classList.add('show');
    if (profiles.length > 0) { document.getElementById('cardContainer').style.display = 'block'; document.getElementById('buttons').style.display = 'flex'; renderCard(); }
  } catch (e) { document.getElementById('searchingOverlay').classList.remove('show'); }
}
function showSection(s, tab) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active')); if (tab) tab.classList.add('active');
  document.getElementById('cardContainer').style.display = 'none'; document.getElementById('buttons').style.display = 'none'; document.getElementById('emptyState').style.display = 'none';
  document.getElementById('matchesSection').classList.remove('show'); document.getElementById('chatSection').classList.remove('show'); document.getElementById('realSuccessScreen').classList.remove('show');
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  if (s === 'swipe') { if (profiles.length > 0 && currentIndex < profiles.length) { document.getElementById('cardContainer').style.display = 'block'; document.getElementById('buttons').style.display = 'flex'; } else { document.getElementById('emptyState').style.display = 'block'; } }
  else if (s === 'matches') { document.getElementById('matchesSection').classList.add('show'); loadMatches(); }
}
async function loadMatches() {
  const matchesList = document.getElementById('matchesList'); matchesList.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const res = await fetch('/api/matches/' + encodeURIComponent(tg.initData)); const data = await res.json();
    const allMatches = [...aiMatchedProfiles.map(p => ({...p, isAI: true})), ...(data.matches || []).map(m => ({...m, isAI: false}))];
    if (allMatches.length === 0) { matchesList.innerHTML = '<div style="text-align:center;padding:60px 20px"><div style="font-size:70px;margin-bottom:20px">💔</div><div style="font-size:20px;font-weight:700;margin-bottom:10px">No matches yet</div><div style="font-size:15px;color:var(--text-secondary)">Keep swiping!</div></div>'; return; }
    matchesList.innerHTML = allMatches.map(m => {
      const gIdx = typeof m.user_id === 'string' ? m.user_id.split('_')[1] % gradients.length : m.user_id % gradients.length;
      return `<div class="match-card" onclick="${m.isAI ? `openAIChat('${m.user_id}', '${escapeAttr(m.name)}')` : `openChat(${m.user_id}, '${escapeAttr(m.name)}')`}"><div class="match-avatar" style="background:${gradients[gIdx]}">${m.name.charAt(0).toUpperCase()}</div><div class="match-info"><div class="match-name-text">${escapeHtml(m.name)} ${m.isAI ? '<span style="font-size:10px;background:var(--gradient-main);padding:2px 6px;border-radius:6px;margin-left:6px">AI</span>' : ''}</div><div class="match-details">${m.age} years old</div></div><button class="chat-btn">💬 Chat</button></div>`;
    }).join('');
  } catch (e) { matchesList.innerHTML = '<div class="error-msg">Error loading</div>'; }
}
function openChat(id, n) {
  currentChatPartner = {userId: id, name: n, isAI: false}; document.getElementById('matchesSection').classList.remove('show'); document.getElementById('chatSection').classList.add('show'); document.getElementById('navTabs').classList.remove('show');
  document.getElementById('chatAvatar').textContent = n.charAt(0).toUpperCase(); document.getElementById('chatAvatar').style.background = gradients[id % gradients.length]; document.getElementById('chatUserName').textContent = n; document.getElementById('chatUserStatus').textContent = 'Online';
  loadMessages(); startMessagePolling();
}
function openAIChat(id, n) {
  currentChatPartner = {userId: id, name: n, isAI: true}; document.getElementById('matchesSection').classList.remove('show'); document.getElementById('chatSection').classList.add('show'); document.getElementById('navTabs').classList.remove('show');
  document.getElementById('chatAvatar').textContent = n.charAt(0).toUpperCase(); document.getElementById('chatAvatar').style.background = gradients[parseInt(id.split('_')[1]) % gradients.length]; document.getElementById('chatUserName').textContent = n; document.getElementById('chatUserStatus').textContent = '🤖 AI Match';
  loadAIMessages();
}
function exitChat() { currentChatPartner = null; stopMessagePolling(); document.getElementById('chatSection').classList.remove('show'); document.getElementById('navTabs').classList.add('show'); document.getElementById('matchesSection').classList.add('show'); }
async function loadMessages() {
  const chatMessages = document.getElementById('chatMessages'); chatMessages.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const res = await fetch(`/api/get_messages/${encodeURIComponent(tg.initData)}/${currentChatPartner.userId}`); const data = await res.json(); const messages = data.messages || [];
    if (messages.length === 0) { chatMessages.innerHTML = '<div style="text-align:center;padding:60px;color:var(--text-secondary)"><div style="font-size:60px;margin-bottom:15px">💬</div><div style="font-size:18px;font-weight:600">Say hi!</div></div>'; return; }
    chatMessages.innerHTML = messages.map(m => `<div class="message ${m.from === data.user_id ? 'sent' : 'received'}"><div>${escapeHtml(m.text)}</div><span class="message-time">${new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span></div>`).join('');
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (e) {}
}
async function loadAIMessages() {
  const chatMessages = document.getElementById('chatMessages'); chatMessages.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const res = await fetch(`/api/ai_messages/${encodeURIComponent(tg.initData)}/${currentChatPartner.userId}`); const data = await res.json(); const messages = data.messages || [];
    if (messages.length === 0) { chatMessages.innerHTML = '<div style="text-align:center;padding:60px;color:var(--text-secondary)"><div style="font-size:60px;margin-bottom:15px">🤖</div><div style="font-size:18px;font-weight:600">Say hi to AI!</div></div>'; return; }
    chatMessages.innerHTML = messages.map(m => `<div class="message ${m.is_user ? 'sent' : 'received'}"><div>${escapeHtml(m.text)}</div><span class="message-time">${new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span></div>`).join('');
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (e) {}
}
async function sendMessage() {
  if (!currentChatPartner) return; const input = document.getElementById('chatInput'); const text = input.value.trim(); if (!text) return;
  document.getElementById('sendBtn').disabled = true;
  if (currentChatPartner.isAI) await sendAIMessage(text); else await sendRealMessage(text);
  document.getElementById('sendBtn').disabled = false;
}
async function sendRealMessage(t) {
  try { await fetch('/api/send_message', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData, to_user: currentChatPartner.userId, message: t}) }); document.getElementById('chatInput').value = ''; loadMessages(); } catch (e) {}
}
async function sendAIMessage(t) {
  const chatMessages = document.getElementById('chatMessages'); const userMsgDiv = document.createElement('div'); userMsgDiv.className = 'message sent'; userMsgDiv.innerHTML = `<div>${escapeHtml(t)}</div><span class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>`;
  chatMessages.appendChild(userMsgDiv); document.getElementById('chatInput').value = ''; chatMessages.scrollTop = chatMessages.scrollHeight;
  const typingDiv = document.createElement('div'); typingDiv.className = 'typing-indicator'; typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>'; chatMessages.appendChild(typingDiv); chatMessages.scrollTop = chatMessages.scrollHeight;
  try {
    const res = await fetch('/api/ai_chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData, ai_profile_id: currentChatPartner.userId, message: t}) });
    const data = await res.json(); typingDiv.remove();
    if (data.ok) { await new Promise(r => setTimeout(r, 800)); const aiMsgDiv = document.createElement('div'); aiMsgDiv.className = 'message received'; aiMsgDiv.innerHTML = `<div>${escapeHtml(data.ai_response.text)}</div><span class="message-time">${new Date(data.ai_response.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>`; chatMessages.appendChild(aiMsgDiv); chatMessages.scrollTop = chatMessages.scrollHeight; }
  } catch (e) { typingDiv.remove(); }
}
function startMessagePolling() { stopMessagePolling(); if (currentChatPartner && !currentChatPartner.isAI) messagePollInterval = setInterval(loadMessages, 3000); }
function stopMessagePolling() { if (messagePollInterval) clearInterval(messagePollInterval); }
function renderCard() {
  const container = document.getElementById('cardContainer'); container.innerHTML = '';
  if (currentIndex >= profiles.length) { container.style.display = 'none'; document.getElementById('buttons').style.display = 'none'; document.getElementById('emptyState').style.display = 'block'; return; }
  const p = profiles[currentIndex]; const card = document.createElement('div'); card.className = 'card'; card.style.background = gradients[currentIndex % gradients.length];
  const promptsHtml = p.prompts ? p.prompts.map(pr => `<div class="card-prompt"><div class="prompt-q">${escapeHtml(pr.q)}</div><div class="prompt-a">${escapeHtml(pr.a)}</div></div>`).join('') : '';
  card.innerHTML = `${p.is_ai ? '<div class="ai-tag">🤖 AI Match</div>' : ''}<div class="swipe-label like">LIKE</div><div class="swipe-label pass">NOPE</div><div class="card-avatar">${p.name.charAt(0).toUpperCase()}${p.bio ? `<div class="card-bio">${escapeHtml(p.bio)}</div>` : ''}</div><div class="card-info"><div class="card-name">${escapeHtml(p.name)}</div><div class="card-age">${p.age} years old</div><div class="card-prompts">${promptsHtml}</div></div>`;
  card.addEventListener('touchstart', dragStart, {passive: true}); card.addEventListener('touchmove', dragMove, {passive: false}); card.addEventListener('touchend', dragEnd); card.addEventListener('mousedown', dragStart);
  container.appendChild(card); activeCard = card;
}
function escapeHtml(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
function escapeAttr(t) { return t.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
function dragStart(e) { isDragging = true; startX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX; startY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY; if (e.type === 'mousedown') { document.addEventListener('mousemove', dragMove); document.addEventListener('mouseup', dragEnd); } }
function dragMove(e) {
  if (!isDragging || !activeCard) return; if (e.type === 'touchmove') e.preventDefault();
  currentX = (e.type === 'touchmove' ? e.touches[0].clientX : e.clientX) - startX;
  const rotation = currentX * 0.08; activeCard.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;
  activeCard.querySelector('.swipe-label.like').style.opacity = Math.min(Math.max(currentX / 100, 0), 1);
  activeCard.querySelector('.swipe-label.pass').style.opacity = Math.min(Math.max(-currentX / 100, 0), 1);
}
function dragEnd() {
  if (!isDragging || !activeCard) return; isDragging = false; document.removeEventListener('mousemove', dragMove); document.removeEventListener('mouseup', dragEnd);
  if (currentX > 120) animateOut('like'); else if (currentX < -120) animateOut('pass'); else { activeCard.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'; activeCard.style.transform = 'translateX(0) rotate(0)'; } currentX = 0;
}
function swipe(a) { if (activeCard) animateOut(a); }
function animateOut(action) {
  if (!activeCard) return; const card = activeCard; const dir = action === 'like' ? 1 : -1;
  card.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s'; card.style.transform = `translateX(${dir * 600}px) rotate(${dir * 30}deg)`; card.style.opacity = '0';
  const profile = profiles[currentIndex]; currentIndex++;
  if (isAIMode) { setTimeout(() => { if (action === 'like') { aiMatchedProfiles.push(profile); lastMatchedAIProfile = profile; showAIMatch(profile); } renderCard(); }, 350); }
  else {
    const targetId = profile.user_id;
    setTimeout(async () => {
      try {
        const res = await fetch('/api/swipe', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({init_data: tg.initData, target_id: targetId, action})
        });
        const data = await res.json(); if (data.matched && data.match_info) showMatch(data.match_info);
      } catch (e) {}
      renderCard();
    }, 350);
  }
  activeCard = null;
}
function showMatch(i) { document.getElementById('matchName').textContent = `You and ${i.name} liked each other! 💕`; document.getElementById('matchModal').classList.add('show'); if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success'); }
function showAIMatch(p) { document.getElementById('matchName').textContent = `You and ${p.name} matched! 🤖💕`; document.getElementById('matchModal').classList.add('show'); if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success'); }
function closeMatch() { document.getElementById('matchModal').classList.remove('show'); }
document.addEventListener('keydown', (e) => { if (e.key === 'Enter') { if (currentChatPartner) sendMessage(); else if (currentStep === 1) nextStep(2); else if (currentStep === 2) nextStep(3); } });
init();
</script>
</body>
</html>"""
