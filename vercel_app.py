"""
Telegram Dating Bot — Swipe Matching Web App (VERCEL VERSION)
==============================================================
Serverless FastAPI app. Storage = Vercel KV (free).
HTML frontend code ke andar embedded hai (koi static folder nahi chahiye).
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
# CONFIG (Vercel Dashboard → Settings → Environment Variables me set karo)
# ─────────────────────────────────────────────
BOT_TOKEN =("8859077363:AAEY5IvqLjvp2KHFi-sDeihrGCKmTu1vrtU")
KV_URL =("https://prompt-quetzal-219477.upstash.io")
KV_TOKEN =("ggAAAAAAA1lVAAIgcDECZqGNn4s9xuEezqSIxvU8XvbqsdNhFWCEEGpm8Lf0Zw")

app = FastAPI(title="Dating Swipe App")

# Fallback in-memory storage (agar KV set nahi hai to app crash nahi hogi)
_mem: dict[str, Any] = {}


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
        # Matching: opposite gender
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
        # Mutual like check
        target_swipes = await kv_get(f"swipes:{req.target_id}") or {"liked": [], "passed": []}
        if uid in target_swipes["liked"]:
            matched = True
            target_profile = await kv_get(f"profile:{req.target_id}") or {}
            match_info = {
                "name": target_profile.get("name", "Someone"),
                "age": target_profile.get("age"),
            }
            # Match save karo (dono ke liye)
            for key_uid, other_uid in ((uid, req.target_id), (req.target_id, uid)):
                matches = await kv_get(f"matches:{key_uid}") or []
                matches.append({"partner_id": other_uid, "created_at": datetime.now(timezone.utc).isoformat()})
                await kv_set(f"matches:{key_uid}", matches)
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
        result.append({"name": p.get("name", "User"), "age": p.get("age"), "gender": p.get("gender")})
    return {"matches": result}


# ═════════════════════════════════════════════
# FRONTEND HTML (Embedded)
# ═════════════════════════════════════════════
FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>💘 Swipe Match</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f0f1a;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow:hidden}
.header{padding:20px;text-align:center}
.header h1{font-size:24px;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.card-container{position:relative;width:90%;max-width:400px;height:480px;margin:10px auto}
.card{position:absolute;width:100%;height:100%;border-radius:24px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5);cursor:grab;user-select:none;touch-action:none}
.card-avatar{width:100%;height:65%;display:flex;align-items:center;justify-content:center;font-size:80px;font-weight:bold;color:rgba(255,255,255,.9)}
.card-info{padding:20px;background:rgba(15,15,26,.95);height:35%}
.card-name{font-size:28px;font-weight:bold;margin-bottom:4px}
.card-age{font-size:20px;color:#ff6b9d;font-weight:600}
.card-gender{font-size:14px;color:#888;margin-top:8px}
.swipe-label{position:absolute;top:30px;padding:8px 20px;border-radius:12px;font-size:32px;font-weight:bold;opacity:0;pointer-events:none}
.swipe-label.like{right:20px;color:#4ade80;border:4px solid #4ade80;transform:rotate(15deg)}
.swipe-label.pass{left:20px;color:#f87171;border:4px solid #f87171;transform:rotate(-15deg)}
.buttons{display:flex;gap:30px;margin:20px 0}
.btn{width:70px;height:70px;border-radius:50%;border:none;font-size:32px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.3)}
.btn-pass{background:#2a2a3a;color:#f87171}
.btn-like{background:#2a2a3a;color:#4ade80}
.empty-state{text-align:center;padding:60px 20px;color:#888}
.empty-state .emoji{font-size:60px;margin-bottom:20px}
.match-modal{position:fixed;inset:0;background:rgba(0,0,0,.9);display:none;align-items:center;justify-content:center;z-index:100;flex-direction:column}
.match-modal.show{display:flex}
.match-title{font-size:48px;font-weight:bold;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.match-name{font-size:24px;margin:20px 0}
.match-btn{padding:15px 40px;border-radius:30px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:18px;font-weight:bold;cursor:pointer;margin-top:20px}
/* Register Form */
.reg-box{width:90%;max-width:400px;background:#1a1a2e;border-radius:24px;padding:30px;margin-top:20px}
.reg-box h2{margin-bottom:20px;text-align:center}
.reg-box input,.reg-box select{width:100%;padding:14px;margin-bottom:15px;border-radius:12px;border:none;background:#2a2a3a;color:#fff;font-size:16px}
.reg-box button{width:100%;padding:15px;border-radius:12px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:18px;font-weight:bold;cursor:pointer}
.loading{padding:60px;text-align:center;color:#888}
</style>
</head>
<body>
<div class="header"><h1>💘 Swipe Match</h1></div>

<div class="loading" id="loading">Loading...</div>

<!-- Register Screen -->
<div class="reg-box" id="regBox" style="display:none">
  <h2>✨ Profile Banao</h2>
  <input id="regName" placeholder="Apna Naam" maxlength="50">
  <input id="regAge" type="number" placeholder="Age" min="13" max="100">
  <select id="regGender">
    <option value="">Gender select karo</option>
    <option value="male">👨 Boy</option>
    <option value="female">👩 Girl</option>
  </select>
  <button onclick="register()">🚀 Start Swiping</button>
</div>

<!-- Swipe Screen -->
<div class="card-container" id="cardContainer" style="display:none"></div>
<div class="buttons" id="buttons" style="display:none">
  <button class="btn btn-pass" onclick="swipe('pass')">✖️</button>
  <button class="btn btn-like" onclick="swipe('like')">❤️</button>
</div>
<div class="empty-state" id="emptyState" style="display:none">
  <div class="emoji">😢</div><p id="emptyText">Abhi koi profiles nahi hai.</p>
</div>

<!-- Match Modal -->
<div class="match-modal" id="matchModal">
  <div class="match-title">🎉 It's a Match!</div>
  <div class="match-name" id="matchName"></div>
  <button class="match-btn" onclick="closeMatch()">Keep Swiping</button>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();

let profiles = [], currentIndex = 0, startX = 0, currentX = 0, isDragging = false, activeCard = null;
const gradients = [
  'linear-gradient(135deg,#667eea,#764ba2)','linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)','linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)','linear-gradient(135deg,#30cfd0,#330867)'
];

async function init() {
  try {
    const res = await fetch('/api/init', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({init_data: tg.initData})});
    if (!res.ok) throw new Error('Auth failed');
    const data = await res.json();
    document.getElementById('loading').style.display = 'none';
    if (!data.has_profile) {
      document.getElementById('regBox').style.display = 'block';
      document.getElementById('regName').value = data.tg_name || '';
    } else {
      loadProfiles();
    }
  } catch (e) {
    document.getElementById('loading').innerHTML = '❌ Error. Bot se dobara kholo.';
  }
}

async function register() {
  const name = document.getElementById('regName').value.trim();
  const age = parseInt(document.getElementById('regAge').value);
  const gender = document.getElementById('regGender').value;
  if (!name || !age || !gender) { alert('Sab fields bharo!'); return; }
  const res = await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({init_data: tg.initData, name, age, gender})});
  if (res.ok) {
    document.getElementById('regBox').style.display = 'none';
    loadProfiles();
  } else { alert('Error aaya, dobara try karo.'); }
}

async function loadProfiles() {
  const res = await fetch('/api/profiles/' + encodeURIComponent(tg.initData));
  const data = await res.json();
  profiles = data.profiles || [];
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
    document.getElementById('emptyText').innerHTML = '🎉 Sab profiles dekh liye!';
    return;
  }
  const p = profiles[currentIndex];
  const card = document.createElement('div');
  card.className = 'card';
  card.style.background = gradients[currentIndex % gradients.length];
  const initial = (p.name || 'U').charAt(0).toUpperCase();
  const genderText = p.gender === 'male' ? '👨 Boy' : '👩 Girl';
  card.innerHTML = `
    <div class="swipe-label like">LIKE</div>
    <div class="swipe-label pass">PASS</div>
    <div class="card-avatar">${initial}</div>
    <div class="card-info">
      <div class="card-name">${escapeHtml(p.name)}</div>
      <div class="card-age">${p.age} years</div>
      <div class="card-gender">${genderText}</div>
    </div>`;
  card.addEventListener('touchstart', dragStart, {passive:true});
  card.addEventListener('touchmove', dragMove, {passive:false});
  card.addEventListener('touchend', dragEnd);
  card.addEventListener('mousedown', dragStart);
  container.appendChild(card);
  activeCard = card;
}

function escapeHtml(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function dragStart(e){isDragging=true;startX=e.type==='touchstart'?e.touches[0].clientX:e.clientX;
  if(e.type==='mousedown'){document.addEventListener('mousemove',dragMove);document.addEventListener('mouseup',dragEnd)}}
function dragMove(e){if(!isDragging||!activeCard)return;if(e.type==='touchmove')e.preventDefault();
  currentX=(e.type==='touchmove'?e.touches[0].clientX:e.clientX)-startX;
  activeCard.style.transform=`translateX(${currentX}px) rotate(${currentX/20}deg)`;
  activeCard.querySelector('.swipe-label.like').style.opacity=currentX>50?Math.min((currentX-50)/100,1):0;
  activeCard.querySelector('.swipe-label.pass').style.opacity=currentX<-50?Math.min((-currentX-50)/100,1):0}
function dragEnd(){if(!isDragging||!activeCard)return;isDragging=false;
  document.removeEventListener('mousemove',dragMove);document.removeEventListener('mouseup',dragEnd);
  if(currentX>100)animateOut('like');else if(currentX<-100)animateOut('pass');
  else{activeCard.style.transition='transform .3s';activeCard.style.transform='translateX(0)'}
  currentX=0}
function swipe(a){if(activeCard)animateOut(a)}

function animateOut(action) {
  if (!activeCard) return;
  const card = activeCard;
  const dir = action === 'like' ? 1 : -1;
  card.style.transition = 'transform .4s, opacity .4s';
  card.style.transform = `translateX(${dir*500}px) rotate(${dir*30}deg)`;
  card.style.opacity = '0';
  const targetId = profiles[currentIndex].user_id;
  currentIndex++;
  setTimeout(async () => {
    try {
      const res = await fetch('/api/swipe', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({init_data: tg.initData, target_id: targetId, action})});
      const data = await res.json();
      if (data.matched && data.match_info) showMatch(data.match_info);
    } catch (e) {}
    renderCard();
  }, 300);
  activeCard = null;
}

function showMatch(info){
  document.getElementById('matchName').textContent = `You and ${info.name} liked each other! 💕`;
  document.getElementById('matchModal').classList.add('show');
}
function closeMatch(){document.getElementById('matchModal').classList.remove('show')}

init();
</script>
</body>
</html>"""
