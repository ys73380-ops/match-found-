"""Web App - FIXED: robust chat, state handling, API errors and UI events."""

from __future__ import annotations

import os
import random
import re
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Chat Web App")

# Wildcard origins + credentials=True is unnecessary and can cause browser CORS issues.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


AI = {
    "GREETING": [
        "heyy 👋",
        "hii! how's your day going?",
        "hey! i was hoping someone nice would match me 😊",
        "hellooo",
        "hiii, how are you?",
    ],

    "HOW_R_U": [
        "i'm good 😊 what about you?",
        "pretty fine, just got home. you?",
        "a bit tired but i'm okay. how about you?",
        "doing great now that you messaged 😊",
    ],

    "DOING": [
        "just watching netflix, wbu?",
        "i was about to make coffee ☕ you?",
        "nothing much, just bored scrolling 😅",
        "just got back from work, so tired",
        "eating something rn, are you hungry too? lol",
    ],

    "NAME": [
        "i'm {name} 😊 what's your name?",
        "my name is {name}, and yours?",
        "{name} here 😄 you?",
    ],

    "AGE": [
        "i'm {age} 😊",
        "{age}! you?",
        "haha i'm {age}, don't tell anyone 😜",
    ],

    "LOCATION": [
        "i'm from {city}, {country} {flag} you?",
        "i live in {city} 😊 where are you from?",
        "{city} {flag} it's nice here. you tell me yours",
        "i live alone here, it's peaceful 😊 you?",
    ],

    "HOBBIES": [
        "i love music and long drives 🎵 what do you like?",
        "mostly cooking and movies 😊 you?",
        "i like going for coffee with friends ☕ wbu?",
        "photography and travelling ✈️ you?",
    ],

    "COMPLIMENT": [
        "aww stop it 😊 you're sweet too",
        "haha you're making me blush 🙈",
        "that's so nice of you to say 🥰",
        "aww thanks 😊 nobody says that to me",
    ],

    "COMPLIMENT_m": [
        "haha thanks 😊 you're cool too",
        "aww thanks, that's sweet of you",
        "lol thanks 😄",
    ],

    "FLIRT": [
        "haha slow down 😏 let's get to know each other first",
        "you're smooth lol 😂",
        "careful, i might actually believe you 😜",
        "hmm maybe 😊 buy me coffee first ☕",
    ],

    "FLIRT_m": [
        "haha you're funny 😂 let's talk a bit first",
        "you're cute, but let's talk a bit first 😊",
        "haha i'm a shy guy lol",
    ],

    "LOVE": [
        "we just met! let's take it slow 😊",
        "let's be friends first, then we'll see 😊",
        "haha that's sweet, but let's get to know each other first 😊",
    ],

    "LOVE_m": [
        "haha slow down 😅 let's get to know each other first",
        "i'm actually single but let's take it slow 😊",
    ],

    "SORRY": [
        "aww it's okay 😊",
        "sorry naaa 🥺 don't be mad... promise i'll talk properly now! 🌸",
        "it's fine, don't worry about it 😊",
    ],

    "EXCUSE": [
        "oh sorry! my mom was calling me, I had to go 😅",
        "sorry naa 🙈 my phone died, just came back",
        "I had some urgent work, sorry 😊 what were you saying?",
        "haha life happened 😅 sorry, I'm here now",
        "my internet was gone, sorry 😅 ab batao",
    ],

    "QUESTION": [
        "hmm good question 🤔 i'd say yes haha. what do you think?",
        "i think so, not sure though. you?",
        "honestly i never thought about it 😅 you tell me first",
    ],

    "FOOD": [
        "i love pizza and pasta 🍕 what about you?",
        "i'm a big foodie, i love trying new cafes 😊",
        "i can eat junk food all day haha",
    ],

    "WORK": [
        "i work in a private company, it's okay i guess. you?",
        "i'm studying right now. what do you do?",
        "work is so tiring these days 😅 what about you?",
    ],

    "SHORT_MSG": [
        "hmm and? 😊",
        "lol",
        "nice! tell me more",
        "oh really? 😄",
        "haha true",
    ],

    "EMOJI_ONLY": [
        "😂",
        "haha cute",
        "🥰",
        "your emoji game is strong lol",
    ],

    "DEFAULT": [
        "haha that's interesting, tell me more 😊",
        "oh nice! so what do you do for fun?",
        "i was just thinking the same thing lol",
        "you seem nice, most people here are weird 😅",
        "hmm i like that. btw where are you from?",
        "lol true. how's your day going?",
        "that's cool! i'm actually bored right now, entertain me 😜",
    ],
}


def safe_format(template: str, profile: Dict[str, Any]) -> str:
    try:
        return template.format(
            name=str(profile.get("name", "Friend")),
            age=int(profile.get("age", 22)),
            city=str(profile.get("city", "City")),
            country=str(profile.get("country", "Country")),
            flag=str(profile.get("flag", "🌍")),
        )
    except Exception:
        return template


def get_ai(text: str, gender: str, profile: Dict[str, Any]) -> str:
    try:
        m = (text or "").lower().strip()
        g = (gender or "female").lower().strip()

        if re.fullmatch(
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s]+",
            text or "",
        ):
            intent = "EMOJI_ONLY"

        elif len(m) < 5:
            intent = "SHORT_MSG"

        elif re.search(
            r"(why did you (leave|go)|where were you|you left|ghost|"
            r"kahan thi|wapas|came back|phone died)",
            m,
        ):
            intent = "EXCUSE"

        elif re.search(r"\b(sorry|gussa|angry|mad)\b", m):
            intent = "SORRY"

        elif re.search(
            r"\b(hi|hii|hey|hello|yo|namaste|hlo)\b",
            m,
        ):
            intent = "GREETING"

        elif re.search(
            r"(how are you|how r u|kaise ho)",
            m,
        ):
            intent = "HOW_R_U"

        elif re.search(
            r"(your name|ur name|whats your name|what's your name)",
            m,
        ):
            intent = "NAME"

        elif re.search(
            r"(how old|your age|ur age)",
            m,
        ):
            intent = "AGE"

        elif re.search(
            r"(where are you from|which city|where do you live|kahan se)",
            m,
        ):
            intent = "LOCATION"

        elif re.search(
            r"(what are you doing|wbu|wyd|kya kar rahi|kya kar rahe)",
            m,
        ):
            intent = "DOING"

        elif re.search(
            r"(hobby|hobbies|like to do|free time)",
            m,
        ):
            intent = "HOBBIES"

        elif re.search(
            r"(love you|i love|marry|meet you|miss you|sexy|hot|date)",
            m,
        ):
            intent = (
                "LOVE"
                if re.search(r"\b(love you|i love)\b", m)
                else "FLIRT"
            )

        elif re.search(
            r"(beautiful|cute|pretty|gorgeous|handsome|sweet|nice)",
            m,
        ):
            intent = "COMPLIMENT"

        elif re.search(
            r"(food|eat|hungry|pizza|dinner)",
            m,
        ):
            intent = "FOOD"

        elif re.search(
            r"(work|job|study|college)",
            m,
        ):
            intent = "WORK"

        elif "?" in m or re.search(
            r"\b(why|how|what|when|where|do you)\b",
            m,
        ):
            intent = "QUESTION"

        else:
            intent = "DEFAULT"

        if g == "male" and intent in {"COMPLIMENT", "FLIRT", "LOVE"}:
            key = f"{intent}_m"
        else:
            key = intent

        choices = AI.get(key) or AI["DEFAULT"]
        result = random.choice(choices)

        return safe_format(result, profile)

    except Exception:
        return "haha 😊"


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=500)
    gender: str = "female"
    name: str = "Friend"
    age: int = 22
    city: str = "City"
    country: str = "Country"
    flag: str = "🌍"


@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    try:
        message = (request.message or "").strip()[:500]

        if not message:
            return {
                "ok": True,
                "reply": "haha 😊",
            }

        profile = {
            "name": request.name,
            "age": request.age,
            "city": request.city,
            "country": request.country,
            "flag": request.flag,
        }

        reply = get_ai(
            message,
            request.gender,
            profile,
        )

        return {
            "ok": True,
            "reply": reply,
        }

    except Exception:
        return {
            "ok": False,
            "reply": "haha 😊",
        }


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "service": "chat",
    }


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(HTML)


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               maximum-scale=1.0,
               user-scalable=no">

<title>Chat</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>
*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    -webkit-tap-highlight-color:transparent
}

body{
    font-family:-apple-system,'Segoe UI',sans-serif;
    background:#0A0A12;
    color:#fff;
    height:100vh;
    height:100dvh;
    display:flex;
    flex-direction:column;
    overflow:hidden
}

.hd{
    background:linear-gradient(135deg,#FF007A,#7928CA);
    padding:12px 16px;
    display:flex;
    align-items:center;
    gap:12px;
    z-index:10
}

.av{
    position:relative;
    width:52px;
    height:52px;
    flex-shrink:0
}

.av img,
.ba img{
    width:100%;
    height:100%;
    border-radius:50%;
    object-fit:cover;
    border:2px solid rgba(255,255,255,.5)
}

.af{
    width:100%;
    height:100%;
    border-radius:50%;
    background:rgba(255,255,255,.2);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:24px;
    font-weight:700
}

.si{
    position:absolute;
    left:50%;
    top:42%;
    width:62%;
    transform:translate(-50%,-50%);
    pointer-events:none;
    filter:drop-shadow(0 2px 6px rgba(0,0,0,.4))
}

.st{
    position:absolute;
    left:50%;
    top:42%;
    transform:translate(-50%,-50%);
    font-size:32px;
    pointer-events:none
}

.ui{
    flex:1;
    min-width:0
}

.un{
    font-size:17px;
    font-weight:700;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis
}

.us{
    font-size:12px;
    display:flex;
    gap:5px;
    align-items:center;
    color:rgba(255,255,255,.9)
}

.od{
    width:8px;
    height:8px;
    background:#0f0;
    border-radius:50%
}

.od.off{
    background:#888
}

.mc{
    flex:1;
    overflow-y:auto;
    padding:16px;
    display:flex;
    flex-direction:column;
    gap:10px;
    overscroll-behavior:contain
}

.pc{
    align-self:center;
    text-align:center;
    background:#1a1a2e;
    border:1px solid rgba(255,255,255,.1);
    border-radius:20px;
    padding:18px 26px;
    margin-bottom:8px
}

.ba{
    position:relative;
    width:90px;
    height:90px;
    margin:0 auto 10px
}

.ba .st{
    font-size:56px
}

.pn{
    font-size:18px;
    font-weight:700
}

.ps{
    font-size:13px;
    color:#8B8B9E;
    margin-top:4px
}

.msg{
    max-width:80%;
    padding:11px 15px;
    border-radius:18px;
    font-size:15px;
    line-height:1.4;
    animation:fi .3s ease
}

.msg.s{
    align-self:flex-end;
    background:linear-gradient(135deg,#FF007A,#7928CA);
    border-bottom-right-radius:4px
}

.msg.r{
    align-self:flex-start;
    background:#1a1a2e;
    border:1px solid rgba(255,255,255,.1);
    border-bottom-left-radius:4px
}

.mt{
    font-size:10px;
    opacity:.6;
    margin-top:4px;
    display:block
}

.sys{
    align-self:center;
    background:rgba(255,255,255,.07);
    border:1px solid rgba(255,255,255,.12);
    color:#ccc;
    font-size:12px;
    padding:8px 16px;
    border-radius:14px;
    text-align:center;
    max-width:92%
}

.ncb{
    margin-top:8px;
    padding:9px 18px;
    border:none;
    border-radius:12px;
    background:linear-gradient(135deg,#FF007A,#7928CA);
    color:#fff;
    font-weight:700;
    font-size:12px;
    cursor:pointer
}

.ti{
    align-self:flex-start;
    padding:12px 16px;
    background:#1a1a2e;
    border-radius:18px;
    display:flex;
    gap:4px
}

.td{
    width:8px;
    height:8px;
    border-radius:50%;
    background:#888;
    animation:tb 1.4s infinite
}

.td:nth-child(2){
    animation-delay:.2s
}

.td:nth-child(3){
    animation-delay:.4s
}

.ic{
    background:#12121F;
    padding:12px 16px;
    display:flex;
    gap:10px;
    border-top:1px solid rgba(255,255,255,.1)
}

.ic input{
    flex:1;
    min-width:0;
    padding:13px 18px;
    border-radius:24px;
    border:2px solid rgba(255,255,255,.1);
    background:#0A0A12;
    color:#fff;
    font-size:15px;
    outline:none
}

.ic input:focus{
    border-color:rgba(255,0,122,.6)
}

.ic input:disabled{
    opacity:.4
}

.ic button{
    width:48px;
    height:48px;
    flex-shrink:0;
    border-radius:50%;
    border:none;
    background:linear-gradient(135deg,#FF007A,#7928CA);
    color:#fff;
    font-size:19px;
    cursor:pointer
}

.ic button:disabled{
    opacity:.5;
    cursor:not-allowed
}

@keyframes fi{
    from{
        opacity:0;
        transform:translateY(10px)
    }
    to{
        opacity:1;
        transform:translateY(0)
    }
}

@keyframes tb{
    0%,60%,100%{
        transform:translateY(0)
    }

    30%{
        transform:translateY(-8px)
    }
}
</style>
</head>

<body>

<div class="hd">
    <div class="av" id="hav"></div>

    <div class="ui">
        <div class="un" id="hn">...</div>

        <div class="us">
            <span class="od" id="od"></span>
            <span id="hs">Online</span>
        </div>
    </div>
</div>

<div class="mc" id="mc"></div>

<div class="ic">
    <input
        id="mi"
        placeholder="Type a message..."
        maxlength="500"
        autocomplete="off"
        enterkeyhint="send"
    >

    <button id="sb" type="button">➤</button>
</div>


<script>
'use strict';

const tg = window.Telegram?.WebApp;

if (tg) {
    try {
        tg.ready();
        tg.expand();
        tg.setHeaderColor('#FF007A');
        tg.setBackgroundColor('#0A0A12');
    } catch (e) {
        console.warn('Telegram WebApp setup failed:', e);
    }
}


/* ---------------------------------------------------------
   Helpers
--------------------------------------------------------- */

const $ = (id) => document.getElementById(id);

const pk = (arr) => {
    if (!Array.isArray(arr) || !arr.length) return '';
    return arr[Math.floor(Math.random() * arr.length)];
};

const pG = () => {
    const r = Math.random();

    if (r < 0.3) return 3;
    if (r < 0.7) return 5;
    return 8;
};

const dR = () => Math.random() < 0.78;

const rD = () => {
    const r = Math.random();

    if (r < 0.35) {
        return 12000 + Math.random() * 18000;
    }

    if (r < 0.75) {
        return 30000 + Math.random() * 45000;
    }

    return 75000 + Math.random() * 60000;
};

const wt = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const nw = () => new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
});

const tD = (text) => {
    return (
        2500 +
        Math.min((text || '').length * 70, 6000) +
        Math.random() * 2500
    );
};

const esc = (text) => {
    const div = document.createElement('div');
    div.textContent = String(text ?? '');
    return div.innerHTML;
};

const escAttr = (text) => {
    return esc(text)
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
};


/* ---------------------------------------------------------
   Profile
--------------------------------------------------------- */

const P = new URLSearchParams(location.search);

const C = {
    n: P.get('name') || 'Sofia',
    a: P.get('age') || '22',
    ci: P.get('city') || 'City',
    co: P.get('country') || 'Country',
    fl: P.get('flag') || '🌍',
    ph: P.get('photo') || '',
    pt: P.get('ptype') || 'face',
    sp: P.get('sp') || '',
    se: P.get('se') || '🌸',
    g: (P.get('gender') || 'female').toLowerCase()
};


/* ---------------------------------------------------------
   DOM
--------------------------------------------------------- */

const mc = $('mc');
const inp = $('mi');
const sb = $('sb');

document.title = 'Chat with ' + C.n;
$('hn').textContent = `${C.n}, ${C.a}`;


/* ---------------------------------------------------------
   State
--------------------------------------------------------- */

let st = 'active';
let um = 0;
let busy = false;
let us = false;
let h = [];
let ga = pG();


/*
   Old version used only the name as localStorage key.

   Problem:
   Two different profiles with same name could share
   the same chat history.

   Now profile-specific key is used.
*/
const HK = [
    'chat_v3',
    C.n,
    C.a,
    C.ci,
    C.co,
    C.g,
    C.ph
].map(v => encodeURIComponent(String(v))).join('_');


const CB = [
    "hey sorry! I had to go suddenly 😅",
    "sorry naa 🙈 my mom was calling me",
    "I'm back! did you miss me? 😜",
    "sorry, my phone died, just charged it 😅",
    "hey I'm back, sorry for leaving suddenly 😊"
];

const RN = [
    "hey you're back 😊",
    "oh you came back, nice 😄",
    "hey! I was just thinking about you 😊"
];

const LS = [
    'last seen just now',
    'last seen 1 min ago',
    'last seen recently'
];


/* ---------------------------------------------------------
   Telegram status
--------------------------------------------------------- */

function setS(text, online) {
    $('hs').textContent = text;
    $('od').classList.toggle('off', !online);
}


/* ---------------------------------------------------------
   Input controls
--------------------------------------------------------- */

function disableInput() {
    inp.disabled = true;
    sb.disabled = true;
}

function enableInput() {
    if (st !== 'active') return;

    inp.disabled = false;
    sb.disabled = false;
}


/* ---------------------------------------------------------
   Local storage
--------------------------------------------------------- */

function sv() {
    try {
        localStorage.setItem(
            HK,
            JSON.stringify({
                version: 3,
                m: h.slice(-80),
                s: st
            })
        );
    } catch (e) {
        console.warn('localStorage save failed:', e);
    }
}

function ld() {
    try {
        const raw = localStorage.getItem(HK);

        if (!raw) {
            return null;
        }

        const parsed = JSON.parse(raw);

        if (
            !parsed ||
            typeof parsed !== 'object' ||
            !Array.isArray(parsed.m)
        ) {
            return null;
        }

        return parsed;

    } catch (e) {
        console.warn('localStorage read failed:', e);

        try {
            localStorage.removeItem(HK);
        } catch (_) {}

        return null;
    }
}


/* ---------------------------------------------------------
   Avatar HTML
--------------------------------------------------------- */

function ov() {
    if (C.pt !== 'sticker') {
        return '';
    }

    if (C.sp) {
        return `
            <img
                class="si"
                src="${escAttr(C.sp)}"
                alt=""
                onerror="this.outerHTML='<span class=&quot;st&quot;>${esc(C.se)}</span>'"
            >
        `;
    }

    return `<span class="st">${esc(C.se)}</span>`;
}


function initials() {
    return esc((C.n || 'F').trim().charAt(0).toUpperCase() || 'F');
}


function avH() {
    if (!C.ph) {
        return `
            <div class="af">${initials()}</div>
            ${ov()}
        `;
    }

    return `
        <img
            src="${escAttr(C.ph)}"
            alt=""
            onerror="this.outerHTML='<div class=&quot;af&quot;>${initials()}</div>'"
        >
        ${ov()}
    `;
}


/* ---------------------------------------------------------
   Initial profile card
--------------------------------------------------------- */

$('hav').innerHTML = avH();

mc.innerHTML = `
    <div class="pc">
        <div class="ba">
            ${avH()}
        </div>

        <div class="pn">
            ${esc(C.n)}, ${esc(C.a)}
        </div>

        <div class="ps">
            📍 ${esc(C.ci)}, ${esc(C.co)} ${esc(C.fl)}
        </div>
    </div>
`;


/* ---------------------------------------------------------
   Render messages
--------------------------------------------------------- */

function dom(m) {
    if (!m || typeof m !== 'object') {
        return;
    }

    const d = document.createElement('div');

    if (m.t === 'sys') {
        d.className = 'sys';

        const text = document.createTextNode(
            String(m.x || '')
        );

        d.appendChild(text);

        if (m.b) {
            d.appendChild(document.createElement('br'));

            const button = document.createElement('button');

            button.className = 'ncb';
            button.type = 'button';
            button.textContent = '🔄 START NEW CHAT';

            d.appendChild(button);
        }

    } else {

        const type =
            m.t === 's'
                ? 's'
                : 'r';

        d.className = `msg ${type}`;

        const text = document.createElement('div');

        text.textContent = String(m.x || '');

        const time = document.createElement('span');

        time.className = 'mt';
        time.textContent = m.tm || '';

        d.appendChild(text);
        d.appendChild(time);
    }

    mc.appendChild(d);

    mc.scrollTop = mc.scrollHeight;
}


/* ---------------------------------------------------------
   Add message
--------------------------------------------------------- */

function ap(text, type) {
    const m = {
        t: type,
        x: String(text || ''),
        tm: nw()
    };

    dom(m);
    h.push(m);
    sv();
}


function aS(text, button = false) {
    const m = {
        t: 'sys',
        x: String(text || ''),
        b: Boolean(button)
    };

    dom(m);
    h.push(m);
    sv();
}


/* ---------------------------------------------------------
   Typing indicator
--------------------------------------------------------- */

function sT() {
    hT();

    const d = document.createElement('div');

    d.className = 'ti';
    d.id = 'ti';

    d.innerHTML = `
        <div class="td"></div>
        <div class="td"></div>
        <div class="td"></div>
    `;

    mc.appendChild(d);

    mc.scrollTop = mc.scrollHeight;
}


function hT() {
    const t = $('ti');

    if (t) {
        t.remove();
    }
}


/* ---------------------------------------------------------
   New chat
--------------------------------------------------------- */

function nC() {
    try {
        localStorage.removeItem(HK);
    } catch (e) {
        console.warn('Failed to remove chat:', e);
    }

    location.reload();
}


/* ---------------------------------------------------------
   API
--------------------------------------------------------- */

async function api(text) {

    const controller = new AbortController();

    const timeoutId = setTimeout(() => {
        controller.abort();
    }, 15000);

    try {

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                message: String(text || '').slice(0, 500),
                gender: C.g,
                name: C.n,
                age: Number(C.a) || 22,
                city: C.ci,
                country: C.co,
                flag: C.fl
            }),
            signal: controller.signal
        });

        if (!response.ok) {
            return 'haha 😊';
        }

        const data = await response.json();

        if (
            data &&
            data.ok &&
            typeof data.reply === 'string' &&
            data.reply.trim()
        ) {
            return data.reply.trim();
        }

        return 'haha 😊';

    } catch (error) {

        if (error?.name === 'AbortError') {
            console.warn('Chat API timed out.');
        } else {
            console.warn('Chat API failed:', error);
        }

        return 'haha 😊';

    } finally {
        clearTimeout(timeoutId);
    }
}


/* ---------------------------------------------------------
   Ghost / end chat
--------------------------------------------------------- */

async function tG(userText) {

    st = 'ghosting';
    disableInput();

    const r = Math.random();

    try {

        if (r < 0.5) {

            const reply = await api(userText);

            await wt(
                800 + Math.random() * 1500
            );

            sT();

            await wt(tD(reply));

            hT();

            ap(reply, 'r');

        } else {

            sT();

            await wt(
                3500 + Math.random() * 3000
            );

            hT();
        }

    } catch (e) {

        hT();

    }

    setS(pk(LS), false);

    await wt(
        4000 + Math.random() * 8000
    );

    if (st !== 'ghosting') {
        return;
    }

    aS(
        `⚠️ ${C.n} has ended the chat`,
        true
    );

    st = 'ended';

    sv();

    if (dR()) {
        sR(rD());
    } else {
        sN(
            30000 +
            Math.random() * 45000
        );
    }
}


/* ---------------------------------------------------------
   Return after ending
--------------------------------------------------------- */

function sR(delay) {

    setTimeout(async () => {

        if (st !== 'ended') {
            return;
        }

        aS(
            `✅ ${C.n} has joined the chat again`,
            false
        );

        setS('Online', true);

        const line = pk(CB);

        sT();

        await wt(tD(line));

        hT();

        ap(line, 'r');

        st = 'active';

        um += pG();

        busy = false;

        enableInput();

        sv();

        try {
            tg?.HapticFeedback?.notificationOccurred('success');
        } catch (_) {}

    }, delay);
}


/* ---------------------------------------------------------
   Permanently closed
--------------------------------------------------------- */

function sN(delay) {

    setTimeout(() => {

        if (st !== 'ended') {
            return;
        }

        setS('offline', false);

        aS(
            `❌ ${C.n} didn't come back online. Start a new chat 💫`,
            true
        );

        st = 'closed';

        disableInput();

        sv();

    }, delay);
}


/* ---------------------------------------------------------
   Send message
--------------------------------------------------------- */

async function send() {

    if (busy) {
        return;
    }

    if (st !== 'active') {
        return;
    }

    const text = inp.value.trim();

    if (!text) {
        return;
    }

    busy = true;
    us = true;

    sb.disabled = true;

    ap(text, 's');

    inp.value = '';

    um++;

    /*
       User reached ghost threshold.
       No normal AI response for this message.
    */
    if (um >= ga) {

        await tG(text);

        busy = false;

        return;
    }


    try {

        await wt(
            800 + Math.random() * 2200
        );

        if (st !== 'active') {
            return;
        }

        sT();

        const reply = await api(text);

        if (st !== 'active') {
            hT();
            return;
        }

        await wt(tD(reply));

        hT();

        ap(reply, 'r');

        try {
            tg?.HapticFeedback?.impactOccurred('light');
        } catch (_) {}

    } catch (e) {

        hT();

        if (st === 'active') {
            ap('haha 😊', 'r');
        }

    } finally {

        busy = false;

        if (st === 'active') {
            enableInput();
        }
    }
}


/* ---------------------------------------------------------
   Restore previous chat
--------------------------------------------------------- */

(function restore() {

    const old = ld();

    if (
        old &&
        Array.isArray(old.m) &&
        old.m.length
    ) {

        h = old.m
            .filter(Boolean)
            .slice(-80);

        h.forEach(dom);

        um = h.filter(
            m => m && m.t === 's'
        ).length;

        /*
           Restored states
        */

        if (old.s === 'ended') {

            st = 'ended';

            disableInput();

            setS(
                pk(LS),
                false
            );

            if (dR()) {

                sR(
                    5000 +
                    Math.random() * 10000
                );

            } else {

                sN(
                    15000 +
                    Math.random() * 20000
                );
            }

            return;
        }


        if (old.s === 'closed') {

            st = 'closed';

            disableInput();

            setS(
                'offline',
                false
            );

            return;
        }


        /*
           Active chat restored.
           us=true because we already have a conversation.
        */

        st = 'active';
        us = true;

        enableInput();


        /*
           Optional small re-engagement message.
        */

        setTimeout(
            async () => {

                if (
                    !us ||
                    um <= 0 ||
                    st !== 'active' ||
                    busy
                ) {
                    return;
                }

                const line = pk(RN);

                if (!line) {
                    return;
                }

                sT();

                await wt(tD(line));

                if (st !== 'active') {
                    hT();
                    return;
                }

                hT();

                ap(line, 'r');

            },
            2500 +
            Math.random() * 2500
        );

        return;
    }


    /*
       New chat:
       send an automatic opening message after a delay.
    */

    if (Math.random() < 0.85) {

        setTimeout(
            async () => {

                if (
                    us ||
                    st !== 'active' ||
                    h.length > 0
                ) {
                    return;
                }

                us = true;

                const firstMessage = pk([
                    "heyy 👋",
                    "hii 😊",
                    "hey! finally someone matched me 😄",
                    "hellooo, how are you?"
                ]);

                sT();

                await wt(tD(firstMessage));

                if (st !== 'active') {
                    hT();
                    return;
                }

                hT();

                ap(firstMessage, 'r');

            },
            2500 +
            Math.random() * 5500
        );
    }

})();


/* ---------------------------------------------------------
   Events
--------------------------------------------------------- */

/*
   Only ONE click event is used.
   Previous code had click + touchend which could result in
   duplicate calls on some mobile browsers.
*/

inp.addEventListener('keydown', (event) => {

    if (event.key === 'Enter') {

        event.preventDefault();

        if (!busy) {
            send();
        }
    }
});


sb.addEventListener('click', () => {
    send();
});


/*
   New-chat button is created dynamically,
   therefore event delegation is used.
*/

mc.addEventListener('click', (event) => {

    const target = event.target;

    if (
        target &&
        target.classList &&
        target.classList.contains('ncb')
    ) {
        nC();
    }
});


/*
   Don't aggressively open keyboard in Telegram mobile.
   Focus only on normal desktop-ish environments.
*/

setTimeout(() => {

    try {

        if (
            !inp.disabled &&
            !('ontouchstart' in window)
        ) {
            inp.focus();
        }

    } catch (_) {}

}, 500);

</script>

</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
