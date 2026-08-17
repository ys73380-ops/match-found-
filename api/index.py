from __future__ import annotations

import os
import random
import re
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Natural AI Chat")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AI RESPONSE BANK
# Casual English around A2-B1 level.
# The bot is intended to be presented as an AI.
# =========================================================

AI = {

    "GREETING": [
        "heyy 👋",
        "hii 😊 how are you?",
        "hey, how's your day going?",
        "helloo 😄",
        "hii, nice to meet you",
    ],

    "HOW_R_U": [
        "i'm good 😊 what about you?",
        "pretty good, you?",
        "i'm okay, just a little tired",
        "doing good haha, what about you?",
        "not bad 😊 how are you?",
    ],

    "DOING": [
        "just chilling rn, what about you?",
        "nothing much, just using my phone",
        "i was watching something haha",
        "just relaxing a bit",
        "not doing much right now, you?",
    ],

    "NAME": [
        "my name is {name}, what's yours?",
        "i'm {name} 😊 and you?",
        "{name} here haha, what should i call you?",
    ],

    "AGE": [
        "i'm {age} 😊 how old are you?",
        "{age} haha, and you?",
        "i'm {age}, what about you?",
    ],

    "LOCATION": [
        "i'm from {city}, {country} {flag}. what about you?",
        "i live in {city} 😊 where are you from?",
        "{city} {flag}, you?",
        "i'm in {city}. it's nice here haha",
    ],

    "HOBBIES": [
        "i like music and movies mostly, what about you?",
        "i like cooking sometimes and watching movies 😊",
        "mostly music, games and going out with friends",
        "i like travelling when i get time",
    ],

    "COMPLIMENT": [
        "haha thank you 😊",
        "aww that's sweet",
        "thank youu 😄",
        "haha you're nice",
        "that's really nice of you",
    ],

    "COMPLIMENT_M": [
        "haha thanks bro 😄",
        "thanks, that's nice of you",
        "haha thank you",
    ],

    "FLIRT": [
        "haha you're moving fast 😄",
        "slow down a little, we just met",
        "you're funny haha",
        "maybe, let's talk first 😊",
        "haha we should get to know each other first",
    ],

    "FLIRT_M": [
        "haha you're funny 😄",
        "slow down bro, we just met",
        "let's talk first haha",
        "you're nice, i like your vibe",
    ],

    "LOVE": [
        "haha that's a bit fast 😄",
        "we just met, let's talk more first",
        "that's sweet, but let's take it slow",
        "haha you don't even know me yet",
    ],

    "LOVE_M": [
        "haha slow down 😄",
        "we just met, let's talk first",
        "that's sweet, but let's take it easy",
    ],

    "SORRY": [
        "it's okay 😊",
        "no problem, don't worry",
        "haha it's fine",
        "don't worry about it",
    ],

    "EXCUSE": [
        "sorry, i was away for a bit",
        "my phone was busy, i'm back now 😅",
        "i got distracted for a while haha",
        "sorry, had to do something",
        "i wasn't here for a bit, what happened?",
    ],

    "QUESTION": [
        "hmm i think so haha, what do you think?",
        "maybe, i'm not really sure 😅",
        "i think yes, probably",
        "not sure about that, what do you think?",
        "good question haha",
    ],

    "FOOD": [
        "i like pizza and pasta 🍕",
        "i love burgers too haha",
        "i'm a big foodie 😄",
        "probably pizza, easy answer haha",
        "i like trying new food",
    ],

    "WORK": [
        "i'm studying right now",
        "i work a little and study too",
        "work is kinda tiring these days haha",
        "i'm still figuring out what i want to do",
        "mostly study and regular stuff",
    ],

    "SHORT_MSG": [
        "hmm 😊",
        "lol",
        "haha okay",
        "nice 😄",
        "really?",
        "ohh okay",
        "and then?",
    ],

    "EMOJI_ONLY": [
        "😂",
        "haha",
        "cute 😄",
        "🥰",
        "lol 😂",
        "haha nice",
    ],

    "DEFAULT": [
        "haha that's interesting",
        "oh really? tell me more",
        "i get what you mean",
        "hmm maybe you're right",
        "that's nice 😊",
        "haha true",
        "i never thought about it like that",
        "sounds good to me",
        "ohh okay, and then?",
        "yeah, i understand",
    ],
}


# =========================================================
# RESPONSE STYLE
# =========================================================

def vary_punctuation(text: str) -> str:
    """
    Small punctuation variation for casual writing.
    This keeps responses natural without trying to impersonate
    a real person.
    """

    if not text:
        return text

    r = random.random()

    # Keep some replies exactly as they are
    if r < 0.45:
        return text

    # Remove final period sometimes
    if r < 0.65:
        text = re.sub(r"\.$", "", text)

    # Casual lower-case continuation
    if r < 0.82 and len(text) > 12:
        text = text.replace(". ", ", ")

    return text


def get_ai(
    text: str,
    gender: str,
    profile: Dict[str, Any],
) -> str:

    try:
        m = (text or "").lower().strip()
        g = (gender or "female").lower().strip()

        emoji_only = re.fullmatch(
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s]+",
            text or "",
        )

        if emoji_only:
            intent = "EMOJI_ONLY"

        elif len(m) < 5:
            intent = "SHORT_MSG"

        elif re.search(
            r"(why did you (leave|go)|where were you|you left|"
            r"ghost|kahan thi|wapas|came back|phone died)",
            m,
        ):
            intent = "EXCUSE"

        elif re.search(
            r"\b(sorry|gussa|angry|mad)\b",
            m,
        ):
            intent = "SORRY"

        elif re.search(
            r"\b(hi|hii|hey|hello|yo|namaste|hlo)\b",
            m,
        ):
            intent = "GREETING"

        elif re.search(
            r"(how are you|how r u|how are u|kaise ho)",
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
            r"(love you|i love|marry|meet you|miss you|date|sexy|hot)",
            m,
        ):
            if re.search(r"\b(love you|i love)\b", m):
                intent = "LOVE"
            else:
                intent = "FLIRT"

        elif re.search(
            r"(beautiful|cute|pretty|gorgeous|handsome|sweet|nice)",
            m,
        ):
            intent = "COMPLIMENT"

        elif re.search(
            r"(food|eat|hungry|pizza|dinner|lunch|breakfast)",
            m,
        ):
            intent = "FOOD"

        elif re.search(
            r"(work|job|study|college|school)",
            m,
        ):
            intent = "WORK"

        elif (
            "?" in m
            or re.search(
                r"\b(why|how|what|when|where|do you)\b",
                m,
            )
        ):
            intent = "QUESTION"

        else:
            intent = "DEFAULT"

        if g == "male":
            if intent == "COMPLIMENT":
                key = "COMPLIMENT_M"
            elif intent == "FLIRT":
                key = "FLIRT_M"
            elif intent == "LOVE":
                key = "LOVE_M"
            else:
                key = intent
        else:
            key = intent

        choices = AI.get(
            key,
            AI["DEFAULT"],
        )

        reply = random.choice(choices)

        try:
            reply = reply.format(
                name=str(profile.get("name", "Friend")),
                age=int(profile.get("age", 22)),
                city=str(profile.get("city", "City")),
                country=str(profile.get("country", "Country")),
                flag=str(profile.get("flag", "🌍")),
            )
        except Exception:
            pass

        return vary_punctuation(reply)

    except Exception:
        return "haha 😊"


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):

    message: str = Field(
        default="",
        max_length=500,
    )

    gender: str = "female"
    name: str = "Friend"
    age: int = 22
    city: str = "City"
    country: str = "Country"
    flag: str = "🌍"


# =========================================================
# API
# =========================================================

@app.post("/api/chat")
async def api_chat(request: ChatRequest):

    try:

        text = (
            request.message or ""
        ).strip()[:500]

        if not text:
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
            text,
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


# =========================================================
# HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0,
             maximum-scale=1.0,
             user-scalable=no"
>

<title>AI Chat</title>

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
    animation:fi .25s ease
}

.msg.s{
    align-self:flex-end;
    background:linear-gradient(
        135deg,
        #FF007A,
        #7928CA
    );
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
    background:linear-gradient(
        135deg,
        #FF007A,
        #7928CA
    );
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
    border-color:rgba(255,0,122,.55)
}

.ic button{
    width:48px;
    height:48px;
    flex-shrink:0;
    border-radius:50%;
    border:none;
    background:linear-gradient(
        135deg,
        #FF007A,
        #7928CA
    );
    color:#fff;
    font-size:19px;
    cursor:pointer
}

@keyframes fi{
    from{
        opacity:0;
        transform:translateY(8px)
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

        <div class="un" id="hn">
            ...
        </div>

        <div class="us">

            <span
                class="od"
                id="od"
            ></span>

            <span id="hs">
                Online
            </span>

        </div>

    </div>

</div>


<div
    class="mc"
    id="mc"
></div>


<div class="ic">

    <input
        id="mi"
        placeholder="Type a message..."
        maxlength="500"
        autocomplete="off"
        enterkeyhint="send"
    >

    <button
        id="sb"
        type="button"
    >
        ➤
    </button>

</div>


<script>

"use strict";


/* =========================================================
   TELEGRAM
========================================================= */

const tg = window.Telegram?.WebApp;

if (tg) {

    try {

        tg.ready();
        tg.expand();

        tg.setHeaderColor("#FF007A");
        tg.setBackgroundColor("#0A0A12");

    } catch(e) {}

}


/* =========================================================
   PARAMS
========================================================= */

const P = new URLSearchParams(
    location.search
);


const C = {

    n:
        P.get("name") ||
        "Sofia",

    a:
        P.get("age") ||
        "22",

    ci:
        P.get("city") ||
        "City",

    co:
        P.get("country") ||
        "Country",

    fl:
        P.get("flag") ||
        "🌍",

    ph:
        P.get("photo") ||
        "",

    pt:
        P.get("ptype") ||
        "face",

    sp:
        P.get("sp") ||
        "",

    se:
        P.get("se") ||
        "🌸",

    g:
        (
            P.get("gender") ||
            "female"
        ).toLowerCase()

};


document.title =
    "AI Chat with " +
    C.n;


/* =========================================================
   DOM
========================================================= */

const mc = document.getElementById("mc");
const inp = document.getElementById("mi");
const sb = document.getElementById("sb");

const hs = document.getElementById("hs");
const od = document.getElementById("od");


/* =========================================================
   STATE
========================================================= */

let state = "active";

let messageHistory = [];

let sendQueue = [];

let queueRunning = false;

let unavailableTimer = null;

let replyTimer = null;


/* =========================================================
   HELPERS
========================================================= */

const wait = ms =>
    new Promise(resolve =>
        setTimeout(resolve,ms)
    );


const random = arr => {

    if (!arr.length) {
        return "";
    }

    return arr[
        Math.floor(
            Math.random() *
            arr.length
        )
    ];

};


const esc = text => {

    const d =
        document.createElement("div");

    d.textContent =
        String(text ?? "");

    return d.innerHTML;

};


const randomDelay = () => {

    const r = Math.random();

    if (r < 0.25) {
        return 500 + Math.random() * 900;
    }

    if (r < 0.60) {
        return 1200 + Math.random() * 1800;
    }

    if (r < 0.90) {
        return 2500 + Math.random() * 4000;
    }

    return 5000 + Math.random() * 8000;

};


const typingDelay = text => {

    return (
        900 +
        Math.min(
            String(text || "").length * 45,
            4000
        ) +
        Math.random() * 1800
    );

};


/* =========================================================
   LOCAL STORAGE
========================================================= */

const CHAT_KEY = [

    "natural_ai_chat",

    encodeURIComponent(C.n),

    encodeURIComponent(C.a),

    encodeURIComponent(C.ci),

    encodeURIComponent(C.co),

    encodeURIComponent(C.g),

].join("_");


function saveChat(){

    try {

        localStorage.setItem(

            CHAT_KEY,

            JSON.stringify({

                v:2,

                state,

                messages:
                    messageHistory.slice(-100)

            })

        );

    } catch(e) {

        console.warn(
            "save failed",
            e
        );

    }

}


function loadChat(){

    try {

        const raw =
            localStorage.getItem(
                CHAT_KEY
            );

        if (!raw) {
            return null;
        }

        const data =
            JSON.parse(raw);

        if (
            !data ||
            !Array.isArray(
                data.messages
            )
        ) {
            return null;
        }

        return data;

    } catch(e) {

        try {

            localStorage.removeItem(
                CHAT_KEY
            );

        } catch(_) {}

        return null;

    }

}


/* =========================================================
   PROFILE
========================================================= */

function avatarHTML(){

    let inside = "";

    if (C.ph) {

        inside += `
            <img
                src="${esc(C.ph)}"
                alt=""
                onerror="
                    this.outerHTML =
                    '<div class=&quot;af&quot;>
                    ${esc(
                        (C.n || "F")
                        .charAt(0)
                        .toUpperCase()
                    )}
                    </div>'
                "
            >
        `;

    } else {

        inside += `
            <div class="af">
                ${esc(
                    (C.n || "F")
                    .charAt(0)
                    .toUpperCase()
                )}
            </div>
        `;

    }

    return inside;

}


document.getElementById(
    "hav"
).innerHTML =
    avatarHTML();


document.getElementById(
    "hn"
).textContent =
    C.n + ", " + C.a;


mc.innerHTML = `

    <div class="pc">

        <div class="ba">
            ${avatarHTML()}
        </div>

        <div class="pn">
            ${esc(C.n)}, ${esc(C.a)}
        </div>

        <div class="ps">
            📍 ${esc(C.ci)},
            ${esc(C.co)}
            ${esc(C.fl)}
        </div>

    </div>
`;


/* =========================================================
   STATUS
========================================================= */

function setStatus(
    text,
    online = true
){

    hs.textContent = text;

    od.classList.toggle(
        "off",
        !online
    );

}


/* =========================================================
   MESSAGE RENDER
========================================================= */

function renderMessage(m){

    if (!m) {
        return;
    }

    const d =
        document.createElement("div");


    if (m.type === "system") {

        d.className =
            "sys";

        d.textContent =
            m.text || "";

    } else {

        d.className =
            "msg " +
            (
                m.type === "sent"
                    ? "s"
                    : "r"
            );


        const text =
            document.createElement(
                "div"
            );

        text.textContent =
            m.text || "";


        const time =
            document.createElement(
                "span"
            );

        time.className =
            "mt";

        time.textContent =
            m.time || "";


        d.appendChild(text);

        d.appendChild(time);

    }


    mc.appendChild(d);

    mc.scrollTop =
        mc.scrollHeight;

}


function addMessage(
    text,
    type
){

    const message = {

        type,

        text:
            String(text || ""),

        time:
            new Date()
            .toLocaleTimeString(
                [],
                {
                    hour:"2-digit",
                    minute:"2-digit"
                }
            )

    };


    renderMessage(
        message
    );


    messageHistory.push(
        message
    );


    saveChat();

}


/* =========================================================
   SYSTEM MESSAGE
========================================================= */

function addSystem(
    text,
    newChat = false
){

    const d =
        document.createElement(
            "div"
        );

    d.className =
        "sys";


    d.textContent =
        text;


    if (newChat) {

        const br =
            document.createElement(
                "br"
            );


        const btn =
            document.createElement(
                "button"
            );


        btn.className =
            "ncb";

        btn.type =
            "button";

        btn.textContent =
            "🔄 START NEW CHAT";


        d.appendChild(br);

        d.appendChild(btn);

    }


    mc.appendChild(d);

    mc.scrollTop =
        mc.scrollHeight;


    messageHistory.push({

        type:"system",

        text,

        time:""

    });


    saveChat();

}


/* =========================================================
   TYPING INDICATOR
========================================================= */

function showTyping(){

    hideTyping();


    const d =
        document.createElement(
            "div"
        );


    d.id = "typing";

    d.className =
        "ti";


    d.innerHTML = `

        <div class="td"></div>
        <div class="td"></div>
        <div class="td"></div>

    `;


    mc.appendChild(d);

    mc.scrollTop =
        mc.scrollHeight;

}


function hideTyping(){

    const d =
        document.getElementById(
            "typing"
        );

    if (d) {
        d.remove();
    }

}


/* =========================================================
   API
========================================================= */

async function askAI(
    text
){

    const controller =
        new AbortController();


    const timeout =
        setTimeout(
            () =>
                controller.abort(),
            15000
        );


    try {

        const response =
            await fetch(
                "/api/chat",
                {

                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            message:text,

                            gender:C.g,

                            name:C.n,

                            age:
                                Number(C.a) ||
                                22,

                            city:C.ci,

                            country:C.co,

                            flag:C.fl

                        }),

                    signal:
                        controller.signal

                }
            );


        if (!response.ok) {

            return "hmm give me a sec 😅";

        }


        const data =
            await response.json();


        if (
            data &&
            data.ok &&
            data.reply
        ) {

            return String(
                data.reply
            ).trim();

        }


        return "hmm okay 😊";


    } catch(e){

        console.warn(
            "API error:",
            e
        );

        return (
            Math.random() < 0.5
                ? "sorry, one sec 😅"
                : "wait haha, my connection is being weird"
        );

    } finally {

        clearTimeout(timeout);

    }

}


/* =========================================================
   TELEGRAM NOTIFICATION
========================================================= */

function notifyReturn(){

    try {

        if (
            tg &&
            tg.HapticFeedback
        ){

            tg.HapticFeedback
                .notificationOccurred(
                    "success"
                );

        }

    } catch(e){}


    /*
       Popup only when Telegram WebApp
       is actually available.
    */

    try {

        if (
            tg &&
            typeof tg.showPopup ===
            "function"
        ){

            tg.showPopup({

                title:"Chat resumed",

                message:
                    `${C.n} is back online.`,

                buttons:[
                    {
                        type:"ok"
                    }
                ]

            });

        }

    } catch(e){}

}


/* =========================================================
   BOT MESSAGE PROCESSOR
========================================================= */

async function processQueue(){

    if (queueRunning) {
        return;
    }


    queueRunning = true;


    while (
        sendQueue.length &&
        state === "active"
    ){

        const item =
            sendQueue.shift();


        /*
           Different response delay
           every time.
        */

        await wait(
            randomDelay()
        );


        if (
            state !== "active"
        ) {
            break;
        }


        showTyping();


        const reply =
            await askAI(
                item.text
            );


        await wait(
            typingDelay(reply)
        );


        if (
            state !== "active"
        ){

            hideTyping();

            break;

        }


        hideTyping();


        addMessage(
            reply,
            "received"
        );

    }


    queueRunning = false;

}


/* =========================================================
   USER CAN ALWAYS SEND
========================================================= */

function send(){

    if (
        state !== "active"
    ){

        return;

    }


    const text =
        inp.value.trim();


    if (!text) {
        return;
    }


    /*
       User message appears immediately.
       Input does NOT get disabled.
    */

    addMessage(
        text,
        "sent"
    );


    inp.value = "";


    sendQueue.push({

        text,

        timestamp:
            Date.now()

    });


    processQueue();

}


/* =========================================================
   TEMPORARY AVAILABILITY
========================================================= */

async function startTemporaryAway(){

    if (
        state !== "active"
    ){

        return;

    }


    state =
        "away";


    hideTyping();


    setStatus(
        "away",
        false
    );


    addSystem(
        `${C.n} is away for a while`
    );


    /*
       15 sec - 70 sec
       random comeback.
    */

    const awayTime =
        15000 +
        Math.random() *
        55000;


    unavailableTimer =
        setTimeout(
            async () => {

                if (
                    state !== "away"
                ){
                    return;
                }


                state =
                    "active";


                setStatus(
                    "Online",
                    true
                );


                addSystem(
                    `✅ ${C.n} is back online`
                );


                notifyReturn();


                await wait(
                    1000 +
                    Math.random() *
                    2500
                );


                if (
                    state !== "active"
                ){
                    return;
                }


                const backReplies = [

                    "hey, i'm back 😊",

                    "sorry i was away for a bit",

                    "back now haha, what were you saying?",

                    "i'm here again 😄",

                    "sorry, got busy for a while"

                ];


                showTyping();


                await wait(
                    typingDelay(
                        "back"
                    )
                );


                hideTyping();


                addMessage(
                    random(
                        backReplies
                    ),
                    "received"
                );


                processQueue();

            },

            awayTime
        );

}


/* =========================================================
   RANDOM TEMPORARY AWAY
========================================================= */

function scheduleAway(){

    if (
        state !== "active"
    ){
        return;
    }


    /*
       Not too frequent.
       Sometimes several minutes can pass.
    */

    const next =
        45000 +
        Math.random() *
        180000;


    setTimeout(
        () => {

            if (
                state !== "active"
            ){
                return;
            }


            /*
               18% chance
            */

            if (
                Math.random() < 0.18
            ){

                startTemporaryAway();

            }


            scheduleAway();

        },

        next
    );

}


/* =========================================================
   NEW CHAT
========================================================= */

function newChat(){

    try {

        localStorage.removeItem(
            CHAT_KEY
        );

    } catch(e){}


    location.reload();

}


/* =========================================================
   RESTORE
========================================================= */

(function restore(){

    const old =
        loadChat();


    if (
        old &&
        Array.isArray(
            old.messages
        ) &&
        old.messages.length
    ){

        messageHistory =
            old.messages
                .slice(-100);


        /*
           clear automatically generated
           profile card only remains at top.
        */

        messageHistory.forEach(
            renderMessage
        );


        if (
            old.state === "away"
        ){

            state =
                "active";

            setStatus(
                "Online",
                true
            );

        }
        else if (
            old.state === "closed"
        ){

            state =
                "closed";

            setStatus(
                "offline",
                false
            );

        }


        scheduleAway();

        return;

    }


    /*
       First message
    */

    if (
        Math.random() < 0.82
    ){

        setTimeout(
            async () => {

                if (
                    state !== "active" ||
                    messageHistory.length
                ){

                    return;

                }


                const first = random([

                    "heyy 👋",

                    "hii 😊",

                    "hey, how are you?",

                    "helloo, what's up?",

                    "hii, nice to meet you"

                ]);


                showTyping();


                await wait(
                    typingDelay(first)
                );


                hideTyping();


                addMessage(
                    first,
                    "received"
                );

            },

            2200 +
            Math.random() * 5000
        );

    }


    scheduleAway();

})();


/* =========================================================
   EVENTS
========================================================= */

sb.addEventListener(
    "click",
    send
);


inp.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter"
        ){

            event.preventDefault();

            send();

        }

    }
);


/* =========================================================
   NEW CHAT BUTTON
========================================================= */

mc.addEventListener(
    "click",
    event => {

        const target =
            event.target;


        if (
            target &&
            target.classList &&
            target.classList.contains(
                "ncb"
            )
        ){

            newChat();

        }

    }
);


/* =========================================================
   PAGE VISIBILITY
========================================================= */

document.addEventListener(
    "visibilitychange",
    () => {

        /*
           Nothing is blocked when user
           switches apps or tabs.
        */

        if (
            document.visibilityState ===
            "visible"
        ){

            if (
                state === "active"
            ){

                setStatus(
                    "Online",
                    true
                );

            }

        }

    }
);


/* =========================================================
   INITIAL FOCUS
========================================================= */

setTimeout(
    () => {

        try {

            if (
                !("ontouchstart" in window) &&
                !inp.disabled
            ){

                inp.focus();

            }

        } catch(e){}

    },

    500
);

</script>

</body>
</html>
"""


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
