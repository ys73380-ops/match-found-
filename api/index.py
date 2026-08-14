"""
Telegram Dating Bot — Swipe Matching Web App
FIXED VERSION: AI Match + AI Chat 100% Working
================================================
✅ AI profiles real girls jaisi
✅ Auto match on LIKE
✅ Real chat endpoint ke through AI chat
✅ Direct AI reply save (no background task failure)
✅ Upstash KV JSON command support
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from html import escape as html_escape
from typing import Any, Optional
from urllib.parse import parse_qsl, unquote

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN = (
    os.environ.get("BOT_TOKEN")
    or os.environ.get("TELEGRAM_BOT_TOKEN")
    or "8859077363:AAEY5IvqLjvp2KHFi-sDeihrGCKmTu1vrtU"
)

KV_URL = (
    os.environ.get("KV_URL")
    or os.environ.get("UPSTASH_REDIS_REST_URL")
    or "https://prompt-quetzal-219477.upstash.io"
)

KV_TOKEN = (
    os.environ.get("KV_TOKEN")
    or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    or "ggAAAAAAA1lVAAIgcDECZqGNn4s9xuEezqSIxvU8XvbqsdNhFWCEEGpm8Lf0Zw"
)

app = FastAPI(title="Premium Dating Swipe App")

# Local/dev fallback memory
_mem: dict[str, Any] = {}

AI_ID_MIN = 900000000
AI_ID_MAX = 999999999

# ─────────────────────────────────────────────
# AI DATA
# ─────────────────────────────────────────────
AI_FEMALE_NAMES = [
    "Ananya", "Priya", "Isha", "Myra", "Aanya", "Saanvi", "Kiara", "Diya",
    "Riya", "Tara", "Avni", "Kavya", "Zara", "Nisha", "Meera", "Pooja",
    "Aisha", "Sneha", "Pihu", "Sara", "Simran", "Rhea", "Mahi", "Navya",
    "Shruti", "Neha", "Roshni", "Tanya", "Vanya", "Kriti"
]

AI_BIOS = [
    "Music lover 🎵 | Coffee addict ☕",
    "Travel enthusiast ✈️ | Foodie 🍕",
    "Gym freak 💪 | Netflix binge-watcher 🎬",
    "Photography 📸 | Adventure seeker 🏔️",
    "Bookworm 📚 | Tea lover 🍵",
    "Dog person 🐕 | Sunset chaser 🌅",
    "Dancer 💃 | Night owl 🦉",
    "Artist 🎨 | Dreamer ✨",
    "Cafe hopper ☕ | Soulful music 🎧",
    "Beach vibes 🌊 | Late night drives 🚗"
]

AI_PROMPTS = [
    {"q": "My simple pleasure", "a": "Finding the perfect cup of chai ☕"},
    {"q": "I'm looking for", "a": "Someone who laughs at my bad jokes 😂"},
    {"q": "Together, we could", "a": "Plan a spontaneous road trip 🚗"},
    {"q": "Sunday mornings are for", "a": "Sleeping in and making pancakes 🥞"},
    {"q": "Unpopular opinion", "a": "Pineapple absolutely belongs on pizza 🍍"},
    {"q": "I geek out on", "a": "True crime podcasts and astrophysics 🌌"},
    {"q": "My most controversial opinion", "a": "Friends is overrated, HIMYM is the real king 👑"}
]

AI_RESPONSES = {
    "GREETING": [
        "hey! kaise ho?",
        "hii 😊 kya kar rahe ho?",
        "hello! aaj ka din kaisa raha?",
        "hey there ✨ kya chal raha hai?",
        "hii! tumhari profile kaafi interesting lagi"
    ],
    "DOING": [
        "bas aisi hi, thodi der pehle office se aayi hu",
        "kuch khaas nahi, bas netflix dekh rahi hu 🍿 tum batao?",
        "coffee pi rahi hu ☕ tumhara kya plan hai aaj ka?",
        "thodi der pehle hi free hui hu, tum kya kar rahe ho?",
        "bas relax kar rahi hu, din kaafi hectic tha"
    ],
    "HOBBIES": [
        "mujhe travel karna aur naye cafes try karna pasand hai ✈️ tumhe?",
        "reading aur music! 🎧 tumhara favourite genre kaunsa hai?",
        "gym aur hiking 🏔️ nature mein time spend karna best lagta hai",
        "cooking try kar rahi hu lately 👩‍🍳 par abhi tak maggi expert hu 😂",
        "photography aur doston ke saath chill karna 📸"
    ],
    "LOCATION": [
        "main mumbai se hu, par travel karte rehte hain 🌆 tum kahan se ho?",
        "delhi ki hu! yahan ka food bahut miss karta hu jab bahar hoti hu 🍕",
        "bangalore! weather yahan kaafi accha hai 🌧️ tum kahan rehte ho?",
        "pune se hu! IT hub hai par nightlife bhi mast hai 🌃",
        "hyderabad ki hu! biryani yahan ki world-famous hai 🍛"
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


def get_ai_response(message: str, is_hidden_ai: bool = False) -> str:
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

    response = random.choice(AI_RESPONSES[intent])

    # Hidden AI mode: thoda natural, kam emoji
    if is_hidden_ai and random.random() < 0.35:
        response = re.sub(r'[✨💕🥰😊😍💫]+', '', response).strip()
        if not response:
            response = random.choice(AI_RESPONSES["DEFAULT"])

    return response


# ─────────────────────────────────────────────
# KV STORAGE (Upstash JSON command + memory fallback)
# ─────────────────────────────────────────────
async def kv_command(*args) -> Any:
    if not KV_URL or not KV_TOKEN:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                KV_URL.rstrip("/"),
                json=list(args),
                headers={"Authorization": f"Bearer {KV_TOKEN}"}
            )
            data = res.json()
            if isinstance(data, dict) and data.get("error"):
                return None
            return data.get("result")
    except Exception:
        return None


async def kv_get(key: str) -> Any:
    # Always update memory fallback
    if not KV_URL or not KV_TOKEN:
        return _mem.get(key)

    try:
        result = await kv_command("GET", key)
        if result is None:
            return _mem.get(key)
        return json.loads(result)
    except Exception:
        return _mem.get(key)


async def kv_set(key: str, value: Any) -> None:
    _mem[key] = value

    if not KV_URL or not KV_TOKEN:
        return

    try:
        await kv_command("SET", key, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass


async def kv_profile_keys() -> list[str]:
    if not KV_URL or not KV_TOKEN:
        return [k for k in _mem.keys() if k.startswith("profile:")]

    try:
        result = await kv_command("KEYS", "profile:*")
        if isinstance(result, list):
            return result
        return [k for k in _mem.keys() if k.startswith("profile:")]
    except Exception:
        return [k for k in _mem.keys() if k.startswith("profile:")]


# ─────────────────────────────────────────────
# TELEGRAM VALIDATION
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

        auth_date = int(parsed.get("auth_date", 0))
        if calculated_hash != received_hash or time.time() - auth_date > 86400:
            return None

        user_json = unquote(parsed.get("user", "{}"))
        return json.loads(user_json)
    except Exception:
        return None


async def send_telegram_message(user_id: int, text: str):
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(
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
# HELPERS
# ─────────────────────────────────────────────
def is_ai_id(user_id: Any) -> bool:
    try:
        uid = int(user_id)
        return AI_ID_MIN <= uid <= AI_ID_MAX
    except Exception:
        return False


def generate_ai_profiles(count: int = 10) -> list[dict]:
    names = random.sample(AI_FEMALE_NAMES, min(count, len(AI_FEMALE_NAMES)))
    profiles = []
    used_ids = set()

    for name in names:
        ai_id = random.randint(AI_ID_MIN, AI_ID_MAX)
        while ai_id in used_ids:
            ai_id = random.randint(AI_ID_MIN, AI_ID_MAX)
        used_ids.add(ai_id)

        profiles.append({
            "user_id": ai_id,
            "name": name,
            "age": random.randint(18, 26),
            "gender": "female",
            "bio": random.choice(AI_BIOS),
            "prompts": random.sample(AI_PROMPTS, 2),
            "is_ai": True
        })

    return profiles


async def ensure_ai_profile(user_id: int) -> dict:
    profile = await kv_get(f"profile:{user_id}")
    if profile:
        profile["is_ai"] = True
        return profile

    profile = {
        "user_id": int(user_id),
        "name": random.choice(AI_FEMALE_NAMES),
        "age": random.randint(19, 25),
        "gender": "female",
        "bio": random.choice(AI_BIOS),
        "prompts": random.sample(AI_PROMPTS, 2),
        "is_ai": True
    }
    await kv_set(f"profile:{user_id}", profile)
    return profile


async def ensure_match(uid: int, partner_id: int) -> None:
    matches = await kv_get(f"matches:{uid}") or []
    partner_id = int(partner_id)

    exists = False
    for m in matches:
        try:
            if int(m.get("partner_id")) == partner_id:
                exists = True
                break
        except Exception:
            pass

    if not exists:
        matches.append({
            "partner_id": partner_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await kv_set(f"matches:{uid}", matches)


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


class GetMessagesRequest(BaseModel):
    init_data: str
    partner_id: int


class FindRealRequest(BaseModel):
    init_data: str


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=FRONTEND_HTML)


@app.get("/health")
async def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/init")
async def api_init(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid Telegram user")

    uid = int(user.get("id"))
    profile = await kv_get(f"profile:{uid}")

    return {
        "user_id": uid,
        "has_profile": bool(profile),
        "profile": profile,
        "tg_name": user.get("first_name", "User")
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

    uid = int(user.get("id"))
    profile = {
        "user_id": uid,
        "name": req.name.strip()[:50],
        "age": req.age,
        "gender": req.gender
    }

    await kv_set(f"profile:{uid}", profile)
    return {"ok": True, "profile": profile}


@app.post("/api/profiles")
async def api_profiles(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        return {"profiles": []}

    my_swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    seen = set(my_swipes.get("liked", []) + my_swipes.get("passed", []) + [uid])

    candidates = []
    for key in await kv_profile_keys():
        profile = await kv_get(key)
        if not profile:
            continue

        # AI profiles real swipe deck me mat dikhao
        if profile.get("is_ai"):
            continue

        pid = profile.get("user_id")
        try:
            pid = int(pid)
        except Exception:
            continue

        if pid in seen:
            continue

        if my_profile.get("gender") == profile.get("gender"):
            continue

        candidates.append(profile)

    random.shuffle(candidates)
    return {"profiles": candidates[:20]}


@app.post("/api/ai_profiles")
async def api_ai_profiles(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        return {"profiles": []}

    profiles = generate_ai_profiles(count=10)

    # Save AI profiles so swipe/chat/match can find them
    for profile in profiles:
        await kv_set(f"profile:{profile['user_id']}", profile)

    return {"profiles": profiles}


@app.post("/api/swipe")
async def api_swipe(req: SwipeRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    target_id = int(req.target_id)

    swipes = await kv_get(f"swipes:{uid}") or {"liked": [], "passed": []}
    if "liked" not in swipes:
        swipes["liked"] = []
    if "passed" not in swipes:
        swipes["passed"] = []

    matched = False
    match_info = None

    target_profile = await kv_get(f"profile:{target_id}") or {}
    target_is_ai = bool(target_profile.get("is_ai")) or is_ai_id(target_id)

    if target_is_ai:
        target_profile = await ensure_ai_profile(target_id)

    if req.action == "like":
        if target_id not in swipes["liked"]:
            swipes["liked"].append(target_id)

        if target_is_ai:
            # AI always likes back => instant match
            matched = True
            match_info = {
                "name": target_profile.get("name", "Girl"),
                "age": target_profile.get("age", 22)
            }

            await ensure_match(uid, target_id)

            await send_telegram_message(
                uid,
                f"🎉 <b>It's a Match!</b>\n\n"
                f"You matched with <b>{html_escape(str(target_profile.get('name', 'Girl')))}</b> "
                f"({html_escape(str(target_profile.get('age', 22)))})!\n\n"
                f"Open the Web App to start chatting! 💕"
            )
        else:
            target_swipes = await kv_get(f"swipes:{target_id}") or {"liked": [], "passed": []}
            if uid in target_swipes.get("liked", []):
                matched = True
                match_info = {
                    "name": target_profile.get("name", "Someone"),
                    "age": target_profile.get("age")
                }

                my_profile = await kv_get(f"profile:{uid}") or {}

                await ensure_match(uid, target_id)
                await ensure_match(target_id, uid)

                await send_telegram_message(
                    uid,
                    f"🎉 <b>It's a Match!</b>\n\n"
                    f"You matched with <b>{html_escape(str(target_profile.get('name', 'Someone')))}</b>!\n\n"
                    f"Open the Web App to start chatting! 💕"
                )

                await send_telegram_message(
                    target_id,
                    f"🎉 <b>It's a Match!</b>\n\n"
                    f"You matched with <b>{html_escape(str(my_profile.get('name', 'Someone')))}</b>!\n\n"
                    f"Open the Web App to start chatting! 💕"
                )
    else:
        if target_id not in swipes["passed"]:
            swipes["passed"].append(target_id)

    await kv_set(f"swipes:{uid}", swipes)

    return {
        "matched": matched,
        "match_info": match_info
    }


@app.post("/api/matches")
async def api_matches(req: InitRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    raw_matches = await kv_get(f"matches:{uid}") or []

    result = []
    seen = set()

    for m in raw_matches:
        pid = m.get("partner_id")

        try:
            pid = int(pid)
        except Exception:
            continue

        if pid in seen:
            continue

        seen.add(pid)

        profile = await kv_get(f"profile:{pid}") or {}
        if not profile and is_ai_id(pid):
            profile = await ensure_ai_profile(pid)

        result.append({
            "user_id": pid,
            "name": profile.get("name", "Girl"),
            "age": profile.get("age", 22),
            "gender": profile.get("gender", "female"),
            "created_at": m.get("created_at")
        })

    return {"matches": result}


@app.post("/api/get_messages")
async def api_get_messages(req: GetMessagesRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    partner_id = int(req.partner_id)

    target_profile = await kv_get(f"profile:{partner_id}") or {}
    target_is_ai = bool(target_profile.get("is_ai")) or is_ai_id(partner_id)

    if target_is_ai:
        await ensure_ai_profile(partner_id)
        await ensure_match(uid, partner_id)
    else:
        matches = await kv_get(f"matches:{uid}") or []
        matched_ids = []
        for m in matches:
            try:
                matched_ids.append(int(m.get("partner_id")))
            except Exception:
                pass

        if partner_id not in matched_ids:
            raise HTTPException(403, "You are not matched with this user")

    chat_id = f"chat:{min(uid, partner_id)}:{max(uid, partner_id)}"
    messages = await kv_get(chat_id) or []

    return {
        "messages": messages,
        "user_id": uid
    }


@app.post("/api/send_message")
async def api_send_message(req: MessageRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid user")

    uid = int(user.get("id"))
    to_user = int(req.to_user)
    text = req.message.strip()[:500]

    if not text:
        raise HTTPException(400, "Empty message")

    target_profile = await kv_get(f"profile:{to_user}") or {}
    target_is_ai = bool(target_profile.get("is_ai")) or is_ai_id(to_user)

    if target_is_ai:
        target_profile = await ensure_ai_profile(to_user)
        await ensure_match(uid, to_user)
    else:
        matches = await kv_get(f"matches:{uid}") or []
        matched_ids = []
        for m in matches:
            try:
                matched_ids.append(int(m.get("partner_id")))
            except Exception:
                pass

        if to_user not in matched_ids:
            raise HTTPException(403, "You are not matched with this user")

    chat_id = f"chat:{min(uid, to_user)}:{max(uid, to_user)}"
    messages = await kv_get(chat_id) or []

    user_message = {
        "from": uid,
        "to": to_user,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    messages.append(user_message)
    await kv_set(chat_id, messages)

    # AI reply direct yahi generate karo, background task fail nahi hoga
    if target_is_ai:
        await asyncio.sleep(random.uniform(0.9, 1.9))

        ai_text = get_ai_response(text, is_hidden_ai=True)

        ai_reply = {
            "from": to_user,
            "to": uid,
            "text": ai_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        messages.append(ai_reply)
        await kv_set(chat_id, messages)

        return {
            "ok": True,
            "message": user_message,
            "ai_reply": ai_reply
        }

    # Real user notification
    sender_profile = await kv_get(f"profile:{uid}") or {}
    await send_telegram_message(
        to_user,
        f"💬 <b>New message from {html_escape(str(sender_profile.get('name', 'Someone')))}</b>\n\n"
        f"\"{html_escape(text[:100])}\"\n\n"
        f"Open the Web App to reply! 💕"
    )

    return {
        "ok": True,
        "message": user_message
    }


@app.post("/api/find_real")
async def api_find_real(req: FindRealRequest):
    user = verify_telegram_user(req.init_data)
    if not user:
        raise HTTPException(403, "Invalid Telegram user")

    uid = int(user.get("id"))
    my_profile = await kv_get(f"profile:{uid}")
    if not my_profile:
        raise HTTPException(400, "Profile nahi mila")

    await kv_set(f"searching:{uid}", {
        "active": True,
        "since": datetime.now(timezone.utc).isoformat()
    })

    await send_telegram_message(
        uid,
        f"🔍 <b>Real Match Search Activated!</b>\n\n"
        f"Hi {html_escape(str(my_profile.get('name', 'User')))}! "
        f"Hum aapke liye real matches dhundh rahe hain.\n\n"
        f"✅ Jaise hi koi match milega, hum aapko bot ke through turant inform karenge!\n\n"
        f"📱 Telegram notifications ON rakhein."
    )

    return {"ok": True, "message": "Aapki request register ho gayi hai!"}


# ═════════════════════════════════════════════
# FRONTEND
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
  --bg-primary:#0A0A12; --bg-secondary:#12121F; --glass:rgba(255,255,255,0.03);
  --glass-border:rgba(255,255,255,0.08); --accent-pink:#FF007A; --accent-purple:#7928CA;
  --accent-blue:#00DFD8; --text-primary:#fff; --text-secondary:#8B8B9E;
  --gradient-main:linear-gradient(135deg,#FF007A 0%,#7928CA 100%);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg-primary);color:var(--text-primary);min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow-x:hidden}
.header{padding:20px;text-align:center;width:100%}
.header h1{font-size:28px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}
.nav-tabs{display:none;width:90%;max-width:400px;margin:10px auto;background:var(--glass);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:20px;padding:6px;gap:6px}
.nav-tabs.show{display:flex}
.nav-tab{flex:1;padding:14px;border:none;background:transparent;color:var(--text-secondary);font-size:14px;font-weight:600;border-radius:16px;cursor:pointer}
.nav-tab.active{background:var(--gradient-main);color:#fff}
.progress-bar{width:90%;max-width:400px;height:4px;background:var(--bg-secondary);border-radius:10px;margin:10px auto;overflow:hidden}
.progress-fill{height:100%;background:var(--gradient-main);width:0%}
.step{display:none;width:90%;max-width:400px}
.step.active{display:block}
.step-card{background:var(--glass);border:1px solid var(--glass-border);border-radius:32px;padding:35px 25px;margin-top:20px}
.step-icon{font-size:64px;text-align:center;margin-bottom:20px}
.step h2{font-size:26px;text-align:center;margin-bottom:10px}
.step p{font-size:15px;text-align:center;color:var(--text-secondary);margin-bottom:30px}
.step input{width:100%;padding:18px 22px;margin-bottom:20px;border-radius:20px;border:2px solid var(--glass-border);background:var(--bg-secondary);color:#fff;font-size:16px}
.step button{width:100%;padding:18px;border-radius:20px;border:none;background:var(--gradient-main);color:#fff;font-size:17px;font-weight:700;cursor:pointer}
.gender-options,.mode-options{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:25px}
.gender-btn,.mode-btn{padding:25px 15px;border-radius:24px;border:2px solid var(--glass-border);background:var(--bg-secondary);color:#fff;cursor:pointer;text-align:center}
.gender-btn.selected,.mode-btn.selected{border-color:var(--accent-pink)}
.gender-btn .emoji,.mode-btn .mode-emoji{font-size:44px;display:block;margin-bottom:10px}
.mode-btn{position:relative}
.mode-badge{position:absolute;top:10px;right:10px;padding:4px 10px;border-radius:10px;font-size:10px;font-weight:800}
.badge-real{background:var(--accent-blue);color:#000}
.badge-ai{background:var(--gradient-main);color:#fff}
.info-card{background:var(--bg-secondary);border:1px solid var(--glass-border);border-radius:20px;padding:22px;margin-bottom:25px;text-align:center}
.info-title{font-size:16px;font-weight:700;margin-bottom:10px}
.info-text{font-size:13px;color:var(--text-secondary);line-height:1.6}
.info-highlight{color:var(--accent-pink);font-weight:600}
.card-container{position:relative;width:92%;max-width:420px;height:600px;margin:10px auto;display:none}
.card{position:absolute;width:100%;height:100%;border-radius:32px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,0.6);cursor:grab;user-select:none;touch-action:none}
.card-avatar{width:100%;height:55%;display:flex;align-items:center;justify-content:center;font-size:120px;font-weight:800;color:rgba(255,255,255,0.9);position:relative}
.card-bio{position:absolute;bottom:15px;left:20px;right:20px;text-align:center;font-size:14px;color:#fff;background:rgba(0,0,0,0.5);padding:10px 16px;border-radius:16px}
.card-info{padding:25px;background:var(--bg-secondary);height:45%;border-top:1px solid var(--glass-border)}
.card-name{font-size:34px;font-weight:800;margin-bottom:6px}
.card-age{font-size:22px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:700;margin-bottom:12px}
.card-prompts{display:flex;flex-direction:column;gap:12px;margin-top:15px}
.card-prompt{background:var(--glass);border:1px solid var(--glass-border);padding:12px 16px;border-radius:16px}
.prompt-q{font-size:11px;color:var(--text-secondary);margin-bottom:4px;font-weight:700;text-transform:uppercase}
.prompt-a{font-size:15px;color:#fff}
.swipe-label{position:absolute;top:50px;padding:12px 30px;border-radius:16px;font-size:32px;font-weight:900;opacity:0;z-index:10}
.swipe-label.like{right:30px;color:#00DFD8;border:5px solid #00DFD8;transform:rotate(15deg)}
.swipe-label.pass{left:30px;color:#FF007A;border:5px solid #FF007A;transform:rotate(-15deg)}
.buttons{display:none;gap:50px;margin:30px 0;justify-content:center}
.btn{width:80px;height:80px;border-radius:50%;border:none;font-size:36px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:var(--bg-secondary);border:2px solid var(--glass-border)}
.btn-pass{color:#FF007A}
.btn-like{color:#00DFD8}
.empty-state{display:none;text-align:center;padding:80px 30px;width:90%;max-width:400px}
.match-modal{position:fixed;inset:0;background:rgba(10,10,18,0.95);display:none;align-items:center;justify-content:center;z-index:100;flex-direction:column;padding:20px}
.match-modal.show{display:flex}
.match-hearts{font-size:100px;margin-bottom:30px}
.match-title{font-size:46px;font-weight:900;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:20px}
.match-name{font-size:20px;text-align:center;color:var(--text-secondary);margin-bottom:40px}
.match-btn{padding:18px 60px;border-radius:30px;border:none;background:var(--gradient-main);color:#fff;font-size:18px;font-weight:700;cursor:pointer}
.matches-section{display:none;width:90%;max-width:400px;margin:20px auto}
.matches-section.show{display:block}
.matches-header{font-size:26px;font-weight:800;margin-bottom:25px}
.match-card{background:var(--glass);border:1px solid var(--glass-border);border-radius:24px;padding:20px;margin-bottom:15px;display:flex;align-items:center;gap:18px;cursor:pointer}
.match-avatar{width:65px;height:65px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:800;color:#fff;flex-shrink:0}
.match-info{flex:1}
.match-name-text{font-size:19px;font-weight:700;margin-bottom:6px}
.match-details{font-size:14px;color:var(--text-secondary)}
.chat-btn{padding:12px 24px;border-radius:16px;border:none;background:var(--gradient-main);color:#fff;font-size:14px;font-weight:700;cursor:pointer}
.chat-section{display:none;width:100%;height:calc(100vh - 120px);flex-direction:column}
.chat-section.show{display:flex}
.chat-header{background:var(--bg-secondary);padding:20px;display:flex;align-items:center;gap:15px;border-bottom:1px solid var(--glass-border)}
.back-btn{width:45px;height:45px;border-radius:50%;border:none;background:var(--glass);color:#fff;font-size:22px;cursor:pointer}
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
.send-btn{width:55px;height:55px;border-radius:50%;border:none;background:var(--gradient-main);color:#fff;font-size:22px;cursor:pointer}
.typing-indicator{align-self:flex-start;padding:14px 18px;background:var(--bg-secondary);border-radius:20px;display:flex;gap:6px;border:1px solid var(--glass-border)}
.typing-dot{width:8px;height:8px;border-radius:50%;background:var(--text-secondary);animation:typingBounce 1.4s infinite}
.typing-dot:nth-child(2){animation-delay:0.2s}
.typing-dot:nth-child(3){animation-delay:0.4s}
@keyframes typingBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
.searching-overlay{position:fixed;inset:0;background:rgba(10,10,18,0.95);display:none;align-items:center;justify-content:center;z-index:90;flex-direction:column;padding:20px}
.searching-overlay.show{display:flex}
.searching-spinner{width:80px;height:80px;border:6px solid var(--glass-border);border-top-color:var(--accent-pink);border-radius:50%;animation:spin 1s linear infinite;margin-bottom:30px}
@keyframes spin{to{transform:rotate(360deg)}}
.searching-text{font-size:26px;font-weight:800;margin-bottom:12px;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.searching-subtext{font-size:16px;color:var(--text-secondary)}
.loading{padding:80px;text-align:center;color:var(--text-secondary)}
.error-msg{color:#FF007A;font-size:13px;text-align:center;margin-top:5px;min-height:20px;font-weight:600}
.success-screen{display:none;width:90%;max-width:400px;text-align:center}
.success-screen.show{display:block}
.success-card{background:var(--glass);border:1px solid var(--glass-border);border-radius:32px;padding:40px 25px;margin-top:20px}
.success-icon{font-size:90px;margin-bottom:25px}
.success-title{font-size:28px;font-weight:800;background:var(--gradient-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:15px}
.success-text{font-size:15px;color:var(--text-secondary);line-height:1.7;margin-bottom:30px}
.highlight{color:var(--accent-pink);font-weight:700}
.try-ai-btn{width:100%;padding:18px;border-radius:20px;border:none;background:var(--gradient-main);color:#fff;font-size:16px;font-weight:700;cursor:pointer;margin-bottom:12px}
.go-home-btn{width:100%;padding:16px;border-radius:20px;border:2px solid var(--glass-border);background:transparent;color:var(--text-secondary);font-size:14px;font-weight:600;cursor:pointer}
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

<div class="step" id="step1">
  <div class="step-card">
    <div class="step-icon">👋</div>
    <h2>Tumhara Naam?</h2>
    <p>Apna pehla naam batao</p>
    <input type="text" id="regName" placeholder="e.g. Rahul" maxlength="50">
    <div class="error-msg" id="nameError"></div>
    <button onclick="nextStep(2)">Continue →</button>
  </div>
</div>

<div class="step" id="step2">
  <div class="step-card">
    <div class="step-icon">🎂</div>
    <h2>Tumhari Age?</h2>
    <p>13-100 ke beech honi chahiye</p>
    <input type="number" id="regAge" placeholder="e.g. 24" min="13" max="100">
    <div class="error-msg" id="ageError"></div>
    <button onclick="nextStep(3)">Continue →</button>
  </div>
</div>

<div class="step" id="step3">
  <div class="step-card">
    <div class="step-icon">👤</div>
    <h2>Tum Kaun Ho?</h2>
    <p>Apna gender select karo</p>
    <div class="gender-options">
      <button class="gender-btn" onclick="selectGender('male', this)"><span class="emoji">👨</span>Boy</button>
      <button class="gender-btn" onclick="selectGender('female', this)"><span class="emoji">👩</span>Girl</button>
    </div>
    <div class="error-msg" id="genderError"></div>
    <button onclick="registerProfile()" id="btn3" disabled>🚀 Continue →</button>
  </div>
</div>

<div class="step" id="step4">
  <div class="step-card">
    <div class="step-icon">✨</div>
    <h2>Match Mode?</h2>
    <p>Real log ya AI se practice karo</p>

    <div class="mode-options">
      <button class="mode-btn" onclick="selectMode('real', this)">
        <span class="mode-badge badge-real">REAL</span>
        <span class="mode-emoji">👥</span>
        <span style="font-size:17px;font-weight:700;display:block">Find Real</span>
        <span style="font-size:12px;color:var(--text-secondary);display:block">Real logo se match karo</span>
      </button>

      <button class="mode-btn" onclick="selectMode('ai', this)">
        <span class="mode-badge badge-ai">AI</span>
        <span class="mode-emoji">💖</span>
        <span style="font-size:17px;font-weight:700;display:block">Find Girls</span>
        <span style="font-size:12px;color:var(--text-secondary);display:block">Instant match & chat</span>
      </button>
    </div>

    <div id="realInfoCard" class="info-card" style="display:none">
      <div class="info-title">🔔 Real Match Kaise Kaam Karta Hai?</div>
      <div class="info-text">
        Hum aapke liye <span class="info-highlight">real log</span> dhundhenge.<br>
        Jaise hi koi match milega, hum aapko <span class="info-highlight">bot ke dwara inform karenge!</span>
      </div>
    </div>

    <div id="aiInfoCard" class="info-card" style="display:none">
      <div class="info-title">💖 Girls Mode Kaise Kaam Karta Hai?</div>
      <div class="info-text">
        Profiles dekho, like karo aur <span class="info-highlight">instant match</span> karo.<br>
        Match ke baad <span class="info-highlight">real jaisi chat</span> start ho jayegi 💕
      </div>
    </div>

    <div class="error-msg" id="modeError"></div>
    <button onclick="startMatchMode()" id="btn4" disabled style="margin-top:15px">🚀 Let's Go!</button>
  </div>
</div>

<div class="searching-overlay" id="searchingOverlay">
  <div class="searching-spinner"></div>
  <div class="searching-text">Searching...</div>
  <div class="searching-subtext">Please wait</div>
</div>

<div class="success-screen" id="realSuccessScreen">
  <div class="success-card">
    <div class="success-icon">✅</div>
    <div class="success-title">Request Registered!</div>
    <div class="success-text">
      Aapki real match request <span class="highlight">successfully register</span> ho gayi hai!<br>
      Jaise hi koi <span class="highlight">match milega</span>, hum aapko inform karenge! 🔔
    </div>
    <button class="try-ai-btn" onclick="switchToAI()">💖 Tab tak Girls Mode Try Karo</button>
    <button class="go-home-btn" onclick="goHome()">🏠 Home jaao</button>
  </div>
</div>

<div class="card-container" id="cardContainer"></div>

<div class="buttons" id="buttons">
  <button class="btn btn-pass" onclick="swipe('pass')">✖️</button>
  <button class="btn btn-like" onclick="swipe('like')">❤️</button>
</div>

<div class="empty-state" id="emptyState">
  <div style="font-size:90px;margin-bottom:30px">😢</div>
  <h3>Koi Profiles Nahi Mile</h3>
  <p>Abhi koi profiles nahi hai.</p>
</div>

<div class="match-modal" id="matchModal">
  <div class="match-hearts">💕</div>
  <div class="match-title">It's a Match!</div>
  <div class="match-name" id="matchName"></div>
  <button class="match-btn" onclick="closeMatch()">Keep Swiping</button>
</div>

<div class="matches-section" id="matchesSection">
  <div class="matches-header">Your Matches 💕</div>
  <div id="matchesList"></div>
</div>

<div class="chat-section" id="chatSection">
  <div class="chat-header">
    <button class="back-btn" onclick="exitChat()">←</button>
    <div class="match-avatar" id="chatAvatar" style="width:50px;height:50px;border-radius:50%;font-size:24px;font-weight:bold"></div>
    <div class="chat-user-info">
      <div class="chat-user-name" id="chatUserName">User</div>
      <div class="chat-user-status">Online</div>
    </div>
  </div>

  <div class="chat-messages" id="chatMessages"></div>

  <div class="chat-input">
    <input type="text" id="chatInput" placeholder="Type a message..." maxlength="500">
    <button class="send-btn" onclick="sendMessage()" id="sendBtn">➤</button>
  </div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();
tg.setHeaderColor('#0A0A12');
tg.setBackgroundColor('#0A0A12');

let currentStep = 1;
let selectedGender = '';
let selectedMode = '';
let matchMode = '';

let profiles = [];
let currentIndex = 0;
let startX = 0;
let currentX = 0;
let isDragging = false;
let activeCard = null;

let currentChatPartner = null;
let messagePollInterval = null;
let typingIndicatorVisible = false;
let lastMessageCount = 0;
let isSendingMessage = false;

const gradients = [
  'linear-gradient(135deg,#FF007A,#7928CA)',
  'linear-gradient(135deg,#00DFD8,#007CF0)',
  'linear-gradient(135deg,#FF4D4D,#F9CB28)',
  'linear-gradient(135deg,#7928CA,#FF007A)',
  'linear-gradient(135deg,#43e97b,#38f9d7)'
];

function apiHeaders() {
  return {'Content-Type': 'application/json'};
}

function updateProgress() {
  document.getElementById('progressFill').style.width = ((currentStep - 1) / 4) * 100 + '%';
}

function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById('realSuccessScreen').classList.remove('show');
  const step = document.getElementById('step' + n);
  if (step) step.classList.add('active');
  currentStep = n;
  updateProgress();
}

function nextStep(n) {
  if (currentStep === 1) {
    const name = document.getElementById('regName').value.trim();
    if (!name || name.length < 2) {
      document.getElementById('nameError').textContent = '❌ Valid naam likho!';
      return;
    }
    document.getElementById('nameError').textContent = '';
  }

  if (currentStep === 2) {
    const age = parseInt(document.getElementById('regAge').value);
    if (!age || age < 13 || age > 100) {
      document.getElementById('ageError').textContent = '❌ Age 13-100 honi chahiye!';
      return;
    }
    document.getElementById('ageError').textContent = '';
  }

  showStep(n);
}

function selectGender(g, btn) {
  selectedGender = g;
  document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('btn3').disabled = false;
}

function selectMode(m, btn) {
  selectedMode = m;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');

  document.getElementById('realInfoCard').style.display = m === 'real' ? 'block' : 'none';
  document.getElementById('aiInfoCard').style.display = m === 'ai' ? 'block' : 'none';
  document.getElementById('btn4').disabled = false;
}

async function init() {
  try {
    const res = await fetch('/api/init', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({init_data: tg.initData || ''})
    });

    if (!res.ok) throw new Error('Auth failed');

    const data = await res.json();
    document.getElementById('loading').style.display = 'none';

    if (!data.has_profile) {
      document.getElementById('regName').value = data.tg_name || '';
      showStep(1);
    } else {
      document.querySelector('.progress-bar').style.display = 'none';
      document.getElementById('navTabs').classList.add('show');
      showStep(4);
    }
  } catch (e) {
    document.getElementById('loading').innerHTML = '❌ Error. Bot se dobara kholo.';
  }
}

async function registerProfile() {
  const btn = document.getElementById('btn3');
  btn.textContent = 'Saving...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({
        init_data: tg.initData || '',
        name: document.getElementById('regName').value.trim(),
        age: parseInt(document.getElementById('regAge').value),
        gender: selectedGender
      })
    });

    if (res.ok) {
      showStep(4);
    } else {
      alert('Error aaya');
    }
  } catch (e) {
    alert('Network error!');
  } finally {
    btn.textContent = '🚀 Continue →';
    btn.disabled = false;
  }
}

async function startMatchMode() {
  matchMode = selectedMode;
  if (selectedMode === 'real') {
    await findRealMatches();
  } else {
    await findAIMatches();
  }
}

async function findRealMatches() {
  document.getElementById('searchingOverlay').classList.add('show');

  try {
    await fetch('/api/find_real', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({init_data: tg.initData || ''})
    });

    await new Promise(r => setTimeout(r, 1500));
    document.getElementById('searchingOverlay').classList.remove('show');

    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.querySelector('.progress-bar').style.display = 'none';
    document.getElementById('navTabs').classList.add('show');
    document.getElementById('realSuccessScreen').classList.add('show');
  } catch (e) {
    document.getElementById('searchingOverlay').classList.remove('show');
  }
}

function switchToAI() {
  document.getElementById('realSuccessScreen').classList.remove('show');
  selectedMode = 'ai';
  matchMode = 'ai';
  findAIMatches();
}

function goHome() {
  document.getElementById('realSuccessScreen').classList.remove('show');
  showStep(4);
}

async function findAIMatches() {
  document.getElementById('searchingOverlay').classList.add('show');

  try {
    const res = await fetch('/api/ai_profiles', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({init_data: tg.initData || ''})
    });

    const data = await res.json();
    profiles = data.profiles || [];
    currentIndex = 0;

    await new Promise(r => setTimeout(r, 1200));
    document.getElementById('searchingOverlay').classList.remove('show');

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
  }
}

function showSection(s, tab) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if (tab) tab.classList.add('active');

  document.getElementById('cardContainer').style.display = 'none';
  document.getElementById('buttons').style.display = 'none';
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('matchesSection').classList.remove('show');
  document.getElementById('chatSection').classList.remove('show');
  document.getElementById('realSuccessScreen').classList.remove('show');
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));

  if (s === 'swipe') {
    if (profiles.length > 0 && currentIndex < profiles.length) {
      document.getElementById('cardContainer').style.display = 'block';
      document.getElementById('buttons').style.display = 'flex';
    } else {
      document.getElementById('emptyState').style.display = 'block';
    }
  } else if (s === 'matches') {
    document.getElementById('matchesSection').classList.add('show');
    loadMatches();
  }
}

async function loadMatches() {
  const matchesList = document.getElementById('matchesList');
  matchesList.innerHTML = '<div class="loading">Loading...</div>';

  try {
    const res = await fetch('/api/matches', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({init_data: tg.initData || ''})
    });

    const data = await res.json();
    const allMatches = data.matches || [];

    if (allMatches.length === 0) {
      matchesList.innerHTML = `
        <div style="text-align:center;padding:60px 20px">
          <div style="font-size:70px;margin-bottom:20px">💔</div>
          <div style="font-size:20px;font-weight:700;margin-bottom:10px">No matches yet</div>
          <div style="font-size:15px;color:var(--text-secondary)">Keep swiping!</div>
        </div>
      `;
      return;
    }

    matchesList.innerHTML = allMatches.map(m => {
      const id = Number(m.user_id);
      if (!Number.isFinite(id)) return '';

      const gIdx = id % gradients.length;
      return `
        <div class="match-card" onclick="openChat(${id}, '${escapeAttr(m.name)}')">
          <div class="match-avatar" style="background:${gradients[gIdx]}">${escapeHtml(m.name.charAt(0).toUpperCase())}</div>
          <div class="match-info">
            <div class="match-name-text">${escapeHtml(m.name)}</div>
            <div class="match-details">${escapeHtml(String(m.age || 22))} years old</div>
          </div>
          <button class="chat-btn">💬 Chat</button>
        </div>
      `;
    }).join('');
  } catch (e) {
    matchesList.innerHTML = '<div class="error-msg">Error loading matches</div>';
  }
}

function openChat(id, name) {
  currentChatPartner = {
    userId: Number(id),
    name: name
  };

  lastMessageCount = 0;

  document.getElementById('matchesSection').classList.remove('show');
  document.getElementById('chatSection').classList.add('show');
  document.getElementById('navTabs').classList.remove('show');

  document.getElementById('chatAvatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('chatAvatar').style.background = gradients[id % gradients.length];
  document.getElementById('chatUserName').textContent = name;

  loadMessages();
  startMessagePolling();
}

function exitChat() {
  currentChatPartner = null;
  stopMessagePolling();

  document.getElementById('chatSection').classList.remove('show');
  document.getElementById('navTabs').classList.add('show');
  document.getElementById('matchesSection').classList.add('show');
}

async function loadMessages() {
  if (!currentChatPartner || isSendingMessage) return;

  const chatMessages = document.getElementById('chatMessages');

  try {
    const res = await fetch('/api/get_messages', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({
        init_data: tg.initData || '',
        partner_id: currentChatPartner.userId
      })
    });

    if (!res.ok) return;

    const data = await res.json();
    const messages = data.messages || [];

    const previousCount = lastMessageCount;
    lastMessageCount = messages.length;

    if (messages.length === 0) {
      chatMessages.innerHTML = `
        <div style="text-align:center;padding:60px;color:var(--text-secondary)">
          <div style="font-size:60px;margin-bottom:15px">💬</div>
          <div style="font-size:18px;font-weight:600">Say hi!</div>
        </div>
      `;
      return;
    }

    chatMessages.innerHTML = messages.map(m => {
      const cls = m.from === data.user_id ? 'sent' : 'received';
      const time = new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      return `
        <div class="message ${cls}">
          <div>${escapeHtml(m.text)}</div>
          <span class="message-time">${time}</span>
        </div>
      `;
    }).join('');

    chatMessages.scrollTop = chatMessages.scrollHeight;

    if (messages.length > previousCount) {
      hideTypingIndicator();
    }
  } catch (e) {}
}

function appendSentMessage(text) {
  const chatMessages = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message sent';
  div.innerHTML = `
    <div>${escapeHtml(text)}</div>
    <span class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendReceivedMessage(text, timestamp) {
  const chatMessages = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message received';
  div.innerHTML = `
    <div>${escapeHtml(text)}</div>
    <span class="message-time">${new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
  if (!currentChatPartner || isSendingMessage) return;

  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  document.getElementById('sendBtn').disabled = true;
  await sendRealMessage(text);
  document.getElementById('sendBtn').disabled = false;
}

async function sendRealMessage(text) {
  isSendingMessage = true;

  appendSentMessage(text);
  lastMessageCount++;

  document.getElementById('chatInput').value = '';
  showTypingIndicator();

  try {
    const res = await fetch('/api/send_message', {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({
        init_data: tg.initData || '',
        to_user: currentChatPartner.userId,
        message: text
      })
    });

    const data = await res.json();

    if (data && data.ai_reply) {
      appendReceivedMessage(data.ai_reply.text, data.ai_reply.timestamp);
      lastMessageCount++;
      hideTypingIndicator();
    } else {
      hideTypingIndicator();
    }

    setTimeout(loadMessages, 700);
  } catch (e) {
    hideTypingIndicator();
  } finally {
    isSendingMessage = false;
  }
}

function showTypingIndicator() {
  if (!currentChatPartner || typingIndicatorVisible) return;

  typingIndicatorVisible = true;

  const chatMessages = document.getElementById('chatMessages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'typing-indicator';
  typingDiv.id = 'realTypingIndicator';
  typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
  typingIndicatorVisible = false;
  const typingEl = document.getElementById('realTypingIndicator');
  if (typingEl) typingEl.remove();
}

function startMessagePolling() {
  stopMessagePolling();

  messagePollInterval = setInterval(async () => {
    if (!isSendingMessage) {
      await loadMessages();
    }
  }, 5000);
}

function stopMessagePolling() {
  if (messagePollInterval) clearInterval(messagePollInterval);
}

function renderCard() {
  const container = document.getElementById('cardContainer');
  container.innerHTML = '';

  if (currentIndex >= profiles.length) {
    container.style.display = 'none';
    document.getElementById('buttons').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
    return;
  }

  const p = profiles[currentIndex];
  const card = document.createElement('div');
  card.className = 'card';
  card.style.background = gradients[currentIndex % gradients.length];

  const promptsHtml = p.prompts ? p.prompts.map(pr => `
    <div class="card-prompt">
      <div class="prompt-q">${escapeHtml(pr.q)}</div>
      <div class="prompt-a">${escapeHtml(pr.a)}</div>
    </div>
  `).join('') : '';

  card.innerHTML = `
    <div class="swipe-label like">LIKE</div>
    <div class="swipe-label pass">NOPE</div>
    <div class="card-avatar">
      ${escapeHtml(p.name.charAt(0).toUpperCase())}
      ${p.bio ? `<div class="card-bio">${escapeHtml(p.bio)}</div>` : ''}
    </div>
    <div class="card-info">
      <div class="card-name">${escapeHtml(p.name)}</div>
      <div class="card-age">${escapeHtml(String(p.age))} years old</div>
      <div class="card-prompts">${promptsHtml}</div>
    </div>
  `;

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
  return String(t).replace(/'/g, "\\'").replace(/"/g, '&quot;');
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

  const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
  currentX = clientX - startX;

  const rotation = currentX * 0.08;
  activeCard.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;

  activeCard.querySelector('.swipe-label.like').style.opacity = Math.min(Math.max(currentX / 100, 0), 1);
  activeCard.querySelector('.swipe-label.pass').style.opacity = Math.min(Math.max(-currentX / 100, 0), 1);
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

  const targetId = Number(profile.user_id);

  setTimeout(async () => {
    try {
      const res = await fetch('/api/swipe', {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({
          init_data: tg.initData || '',
          target_id: targetId,
          action: action
        })
      });

      const data = await res.json();

      if (data.matched && data.match_info) {
        showMatch(data.match_info);
      }
    } catch (e) {}

    renderCard();
  }, 350);

  activeCard = null;
}

function showMatch(info) {
  document.getElementById('matchName').textContent = `You and ${info.name} liked each other! 💕`;
  document.getElementById('matchModal').classList.add('show');

  if (tg.HapticFeedback) {
    tg.HapticFeedback.notificationOccurred('success');
  }
}

function closeMatch() {
  document.getElementById('matchModal').classList.remove('show');
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    if (currentChatPartner) sendMessage();
    else if (currentStep === 1) nextStep(2);
    else if (currentStep === 2) nextStep(3);
  }
});

init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
