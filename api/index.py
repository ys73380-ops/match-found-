"""
Telegram Dating Bot — Swipe Matching Web App (VERCEL VERSION - FIXED)
======================================================================
✅ Step-by-step registration: Name → Age → Gender → Match
✅ Better UI with smooth transitions
✅ Proper validation
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
            match_info = {
                "name": target_profile.get("name", "Someone"),
                "age": target_profile.get("age"),
            }
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
# FRONTEND HTML (Embedded - Step-by-Step)
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
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%);color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow-x:hidden}
.header{padding:20px;text-align:center;width:100%}
.header h1{font-size:28px;background:linear-gradient(135deg,#ff6b9d,#c44fe2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:bold}

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

/* Swipe Cards */
.card-container{position:relative;width:90%;max-width:400px;height:500px;margin:10px auto;display:none}
.card{position:absolute;width:100%;height:100%;border-radius:24px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.5);cursor:grab;user-select:none;touch-action:none;transition:transform 0.1s}
.card:active{cursor:grabbing}
.card-avatar{width:100%;height:60%;display:flex;align-items:center;justify-content:center;font-size:100px;font-weight:bold;color:rgba(255,255,255,0.95);text-shadow:0 4px 20px rgba(0,0,0,0.3)}
.card-info{padding:25px;background:rgba(15,15,26,0.95);height:40%;backdrop-filter:blur(10px)}
.card-name{font-size:32px;font-weight:bold;margin-bottom:5px}
.card-age{font-size:22px;color:#ff6b9d;font-weight:600;margin-bottom:8px}
.card-gender{font-size:16px;color:#888;display:flex;align-items:center;gap:8px}
.card-gender::before{content:'';width:8px;height:8px;border-radius:50%;background:currentColor}

.swipe-label{position:absolute;top:40px;padding:10px 25px;border-radius:12px;font-size:28px;font-weight:bold;opacity:0;pointer-events:none;text-shadow:0 2px 10px rgba(0,0,0,0.3)}
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
.match-btn{padding:16px 50px;border-radius:30px;border:none;background:linear-gradient(135deg,#ff6b9d,#c44fe2);color:#fff;font-size:18px;font-weight:bold;cursor:pointer;box-shadow:0 10px 30px rgba(255,107,157,0.4)}

.loading{padding:60px;text-align:center;color:#888;font-size:16px}
.error-msg{color:#f87171;font-size:14px;text-align:center;margin-top:10px;min-height:20px}
</style>
</head>
<body>

<div class="header"><h1>💘 Swipe Match</h1></div>
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
    <button onclick="registerProfile()" id="btn3" disabled>🚀 Start Finding Matches</button>
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
  <button class="match-btn" onclick="closeMatch()">Keep Swiping</button>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();

let currentStep = 1;
let selectedGender = '';
let profiles = [], currentIndex = 0, startX = 0, currentX = 0, isDragging = false, activeCard = null;

const gradients = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#30cfd0,#330867)'
];

function updateProgress() {
  const percent = ((currentStep - 1) / 3) * 100;
  document.getElementById('progressFill').style.width = percent + '%';
}

function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  const step = document.getElementById('step' + n);
  if (step) step.classList.add('active');
  currentStep = n;
  updateProgress();
  
  // Auto focus
  setTimeout(() => {
    const input = step.querySelector('input');
    if (input && !input.value) input.focus();
  }, 100);
}

function nextStep(n) {
  // Validation
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
      loadProfiles();
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
      document.getElementById('progressFill').style.width = '100%';
      document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
      loadProfiles();
    } else {
      btn.textContent = '🚀 Start Finding Matches';
      btn.disabled = false;
      alert('Error aaya, dobara try karo.');
    }
  } catch (e) {
    btn.textContent = '🚀 Start Finding Matches';
    btn.disabled = false;
    alert('Network error!');
  }
}

async function loadProfiles() {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('loading').textContent = 'Finding matches for you...';
  
  const res = await fetch('/api/profiles/' + encodeURIComponent(tg.initData));
  const data = await res.json();
  profiles = data.profiles || [];
  
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
    document.getElementById('emptyText').innerHTML = '🎉 Sab profiles dekh liye!<br>Kal phir aao.';
    return;
  }
  
  const p = profiles[currentIndex];
  const card = document.createElement('div');
  card.className = 'card';
  card.style.background = gradients[currentIndex % gradients.length];
  
  const initial = (p.name || 'U').charAt(0).toUpperCase();
  const genderText = p.gender === 'male' ? 'Boy' : 'Girl';
  const genderEmoji = p.gender === 'male' ? '👨' : '👩';
  
  card.innerHTML = `
    <div class="swipe-label like">LIKE</div>
    <div class="swipe-label pass">NOPE</div>
    <div class="card-avatar">${initial}</div>
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
  
  const targetId = profiles[currentIndex].user_id;
  currentIndex++;
  
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
  
  activeCard = null;
}

function showMatch(info) {
  document.getElementById('matchName').textContent = `You and ${info.name} liked each other! 💕`;
  document.getElementById('matchModal').classList.add('show');
  if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}

function closeMatch() {
  document.getElementById('matchModal').classList.remove('show');
}

// Enter key support
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    if (currentStep === 1) nextStep(2);
    else if (currentStep === 2) nextStep(3);
  }
});

init();
</script>
</body>
</html>"""
