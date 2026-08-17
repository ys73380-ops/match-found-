from __future__ import annotations

import os
import random
import re
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="AI Chat Web App")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AI RESPONSE BANK
# No emojis in AI replies
# English level: simple A2 - low B1
# =========================================================

AI = {

    "GREETING": [
        "hey",
        "hii, how are you?",
        "hey, how is your day going?",
        "helloo",
        "hii, nice to meet you",
        "hey, what's up?",
    ],

    "HOW_R_U": [
        "i'm good, what about you?",
        "pretty good, you?",
        "i'm okay, just a little tired",
        "doing good, what about you?",
        "not bad, how are you?",
        "i'm fine, just relaxing",
    ],

    "DOING": [
        "just chilling right now, what about you?",
        "nothing much, just using my phone",
        "i was watching something",
        "just relaxing a bit",
        "not doing much right now, you?",
        "just sitting here and talking",
    ],

    "NAME": [
        "my name is {name}, what's yours?",
        "i'm {name}, and you?",
        "{name} here, what should i call you?",
        "my name is {name}. yours?",
    ],

    "AGE": [
        "i'm {age}, how old are you?",
        "{age}, what about you?",
        "i'm {age}. and you?",
        "i'm {age}, how old are you?",
    ],

    "LOCATION": [
        "i'm from {city}, {country}. what about you?",
        "i live in {city}. where are you from?",
        "{city}. what about you?",
        "i'm in {city}. it's nice here",
        "i live in {city}, where do you live?",
    ],

    "HOBBIES": [
        "i like music and movies mostly, what about you?",
        "i like cooking sometimes and watching movies",
        "mostly music, games and going out with friends",
        "i like travelling when i get time",
        "i watch movies a lot when i'm free",
    ],

    "COMPLIMENT": [
        "thank you",
        "that's sweet of you",
        "thank you, that's nice",
        "haha, you're nice",
        "that's really nice of you",
    ],

    "COMPLIMENT_M": [
        "thanks",
        "thanks, that's nice of you",
        "haha thank you",
        "appreciate that",
    ],

    "FLIRT": [
        "you're moving fast",
        "slow down a little, we just met",
        "you're funny",
        "maybe, let's talk first",
        "we should get to know each other first",
        "haha, you are smooth",
    ],

    "FLIRT_M": [
        "you're funny",
        "slow down, we just met",
        "let's talk first",
        "you're nice, i like your vibe",
        "haha, not so fast",
    ],

    "LOVE": [
        "that's a bit fast",
        "we just met, let's talk more first",
        "that's sweet, but let's take it slow",
        "you don't even know me yet",
        "let's get to know each other first",
    ],

    "LOVE_M": [
        "slow down, we just met",
        "let's talk first",
        "that's sweet, but let's take it easy",
        "we should know each other first",
    ],

    "SORRY": [
        "it's okay",
        "no problem, don't worry",
        "it's fine",
        "don't worry about it",
        "that's okay",
    ],

    "EXCUSE": [
        "sorry, i was away for a bit",
        "my phone was busy, i'm back now",
        "i got distracted for a while",
        "sorry, i had to do something",
        "i wasn't here for a bit, what happened?",
    ],

    "QUESTION": [
        "hmm, i think so. what do you think?",
        "maybe, i'm not really sure",
        "i think yes, probably",
        "not sure about that, what do you think?",
        "good question",
        "i never really thought about that",
    ],

    "FOOD": [
        "i like pizza and pasta",
        "i love burgers too",
        "i'm a big foodie",
        "probably pizza, easy answer",
        "i like trying new food",
        "i eat almost everything",
    ],

    "WORK": [
        "i'm studying right now",
        "i work a little and study too",
        "work is kind of tiring these days",
        "i'm still figuring out what i want to do",
        "mostly study and regular stuff",
    ],

    "SHORT_MSG": [
        "hmm",
        "lol",
        "haha okay",
        "nice",
        "really?",
        "ohh okay",
        "and then?",
        "true",
    ],

    "DEFAULT": [
        "haha that's interesting",
        "oh really? tell me more",
        "i get what you mean",
        "hmm maybe you're right",
        "that's nice",
        "haha true",
        "i never thought about it like that",
        "sounds good to me",
        "ohh okay, and then?",
        "yeah, i understand",
        "that makes sense",
        "i know what you mean",
    ],
}


# =========================================================
# PUNCTUATION
# =========================================================

def vary_punctuation(text: str) -> str:
    if not text:
        return text

    r = random.random()

    if r < 0.30:
        return text

    if r < 0.55:
        return re.sub(r"\.$", "", text)

    if r < 0.75 and ". " in text:
        text = text.replace(". ", ", ", 1)

    if r < 0.90 and text.endswith("?"):
        return text

    return text


# =========================================================
# AI INTENT
# =========================================================

def get_ai(
    text: str,
    gender: str,
    profile: Dict[str, Any],
) -> str:

    try:

        m = (
            text or ""
        ).lower().strip()

        g = (
            gender or "female"
        ).lower().strip()


        if len(m) < 5:

            intent = "SHORT_MSG"


        elif re.search(
            r"(why did you (leave|go)|where were you|"
            r"you left|ghost|kahan thi|wapas|"
            r"came back|phone died)",
            m,
        ):

            intent = "EXCUSE"


        elif re.search(
            r"\b(sorry|gussa|angry|mad)\b",
            m,
        ):

            intent = "SORRY"


        elif re.search(
            r"\b(hi|hii|hey|hello|yo|"
            r"namaste|hlo)\b",
            m,
        ):

            intent = "GREETING"


        elif re.search(
            r"(how are you|how r u|how are u|kaise ho)",
            m,
        ):

            intent = "HOW_R_U"


        elif re.search(
            r"(your name|ur name|whats your name|"
            r"what's your name)",
            m,
        ):

            intent = "NAME"


        elif re.search(
            r"(how old|your age|ur age)",
            m,
        ):

            intent = "AGE"


        elif re.search(
            r"(where are you from|which city|"
            r"where do you live|kahan se)",
            m,
        ):

            intent = "LOCATION"


        elif re.search(
            r"(what are you doing|wbu|wyd|"
            r"kya kar rahi|kya kar rahe)",
            m,
        ):

            intent = "DOING"


        elif re.search(
            r"(hobby|hobbies|like to do|free time)",
            m,
        ):

            intent = "HOBBIES"


        elif re.search(
            r"(love you|i love|marry|meet you|"
            r"miss you|date|sexy|hot)",
            m,
        ):

            if re.search(
                r"\b(love you|i love)\b",
                m,
            ):
                intent = "LOVE"
            else:
                intent = "FLIRT"


        elif re.search(
            r"(beautiful|cute|pretty|"
            r"gorgeous|handsome|sweet|nice)",
            m,
        ):

            intent = "COMPLIMENT"


        elif re.search(
            r"(food|eat|hungry|pizza|"
            r"dinner|lunch|breakfast)",
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
                r"\b(why|how|what|when|where|"
                r"do you)\b",
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


        reply = random.choice(
            choices
        )


        try:

            reply = reply.format(
                name=str(
                    profile.get(
                        "name",
                        "Friend"
                    )
                ),
                age=int(
                    profile.get(
                        "age",
                        22
                    )
                ),
                city=str(
                    profile.get(
                        "city",
                        "City"
                    )
                ),
                country=str(
                    profile.get(
                        "country",
                        "Country"
                    )
                ),
                flag="",
            )

        except Exception:
            pass


        return vary_punctuation(
            reply
        )


    except Exception:

        return "haha"


# =========================================================
# MODEL
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
    flag: str = ""


# =========================================================
# API
# =========================================================

@app.post("/api/chat")
async def api_chat(
    request: ChatRequest
):

    try:

        text = (
            request.message or ""
        ).strip()[:500]


        if not text:

            return {
                "ok": True,
                "reply": "haha",
            }


        profile = {

            "name": request.name,

            "age": request.age,

            "city": request.city,

            "country": request.country,

            "flag": "",

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
            "reply": "haha",
        }


@app.get("/api/health")
async def health():

    return {
        "ok": True,
        "service": "chat",
    }


@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    return HTMLResponse(
        HTML
    )


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

<script
    src="https://telegram.org/js/telegram-web-app.js"
></script>


<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    -webkit-tap-highlight-color:transparent
}


body{
    font-family:-apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:#0A0A12;
    color:#fff;

    height:100vh;
    height:100dvh;

    display:flex;
    flex-direction:column;

    overflow:hidden;
}


/* =====================================================
HEADER
===================================================== */

.hd{
    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    padding:12px 16px;

    display:flex;
    align-items:center;

    gap:12px;

    z-index:20;
}


.av{
    position:relative;

    width:52px;
    height:52px;

    flex-shrink:0;
}


.av img,
.ba img{
    width:100%;
    height:100%;

    border-radius:50%;

    object-fit:cover;

    border:2px solid
        rgba(255,255,255,.5);
}


.af{
    width:100%;
    height:100%;

    border-radius:50%;

    background:
        rgba(255,255,255,.18);

    display:flex;

    align-items:center;
    justify-content:center;

    font-size:24px;
    font-weight:700;
}


.ui{
    flex:1;
    min-width:0;
}


.un{
    font-size:17px;
    font-weight:700;

    white-space:nowrap;

    overflow:hidden;

    text-overflow:ellipsis;
}


.us{
    font-size:12px;

    display:flex;
    align-items:center;

    gap:5px;

    color:
        rgba(255,255,255,.88);
}


.od{
    width:8px;
    height:8px;

    background:#20ff40;

    border-radius:50%;
}


.od.off{
    background:#888;
}


/* =====================================================
MESSAGE AREA
===================================================== */

.mc{
    flex:1;

    overflow-y:auto;

    padding:16px;

    display:flex;

    flex-direction:column;

    gap:10px;

    overscroll-behavior:contain;
}


.pc{
    align-self:center;

    text-align:center;

    background:#1A1A2E;

    border:
        1px solid
        rgba(255,255,255,.1);

    border-radius:20px;

    padding:18px 26px;

    margin-bottom:8px;
}


.ba{
    position:relative;

    width:90px;
    height:90px;

    margin:
        0 auto 10px;
}


.pn{
    font-size:18px;
    font-weight:700;
}


.ps{
    font-size:13px;

    color:#8B8B9E;

    margin-top:4px;
}


.msg{
    max-width:80%;

    padding:11px 15px;

    border-radius:18px;

    font-size:15px;

    line-height:1.4;

    animation:
        fi .25s ease;
}


.msg.s{
    align-self:flex-end;

    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    border-bottom-right-radius:4px;
}


.msg.r{
    align-self:flex-start;

    background:#1A1A2E;

    border:
        1px solid
        rgba(255,255,255,.1);

    border-bottom-left-radius:4px;
}


.mt{
    font-size:10px;

    opacity:.55;

    margin-top:4px;

    display:block;
}


/* =====================================================
SYSTEM
===================================================== */

.sys{
    align-self:center;

    background:
        rgba(255,255,255,.07);

    border:
        1px solid
        rgba(255,255,255,.12);

    color:#ccc;

    font-size:12px;

    padding:8px 16px;

    border-radius:14px;

    text-align:center;

    max-width:92%;
}


.ncb{
    margin-top:8px;

    padding:9px 18px;

    border:none;

    border-radius:12px;

    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    color:#fff;

    font-weight:700;

    font-size:12px;

    cursor:pointer;
}


/* =====================================================
TYPING
===================================================== */

.ti{
    align-self:flex-start;

    padding:12px 16px;

    background:#1A1A2E;

    border-radius:18px;

    display:flex;

    gap:4px;
}


.td{
    width:8px;
    height:8px;

    border-radius:50%;

    background:#888;

    animation:
        tb 1.4s infinite;
}


.td:nth-child(2){
    animation-delay:.2s;
}


.td:nth-child(3){
    animation-delay:.4s;
}


/* =====================================================
BOTTOM BAR
===================================================== */

.ic{
    position:relative;

    background:#12121F;

    padding:9px 14px;

    display:flex;

    align-items:flex-end;

    gap:8px;

    border-top:
        1px solid
        rgba(255,255,255,.1);

    z-index:30;
}


.toolBtn{
    width:42px;
    height:42px;

    border:none;

    border-radius:50%;

    background:#202033;

    color:#fff;

    font-size:20px;

    cursor:pointer;

    flex-shrink:0;
}


.ic input{
    flex:1;

    min-width:0;

    padding:12px 16px;

    border-radius:24px;

    border:
        2px solid
        rgba(255,255,255,.1);

    background:#0A0A12;

    color:#fff;

    font-size:15px;

    outline:none;
}


.ic input:focus{
    border-color:
        rgba(255,0,122,.55);
}


.sendBtn{
    width:45px;
    height:45px;

    flex-shrink:0;

    border-radius:50%;

    border:none;

    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    color:#fff;

    font-size:19px;

    cursor:pointer;
}


/* =====================================================
PICKER PANEL
===================================================== */

.picker{
    position:absolute;

    left:10px;
    right:10px;

    bottom:64px;

    display:none;

    background:#171725;

    border:
        1px solid
        rgba(255,255,255,.1);

    border-radius:18px;

    padding:12px;

    box-shadow:
        0 12px 40px
        rgba(0,0,0,.45);

    z-index:100;
}


.picker.show{
    display:block;
}


.pickerHead{
    display:flex;

    gap:8px;

    margin-bottom:10px;
}


.pickerTab{
    flex:1;

    padding:9px;

    border:none;

    border-radius:10px;

    background:#222238;

    color:#aaa;

    font-weight:600;

    cursor:pointer;
}


.pickerTab.active{
    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    color:#fff;
}


/* =====================================================
EMOJI GRID
===================================================== */

.emojiGrid{
    display:grid;

    grid-template-columns:
        repeat(8, 1fr);

    gap:6px;

    max-height:180px;

    overflow-y:auto;
}


.emojiBtn{
    border:none;

    background:#222238;

    border-radius:10px;

    font-size:23px;

    height:38px;

    cursor:pointer;
}


.emojiBtn:active{
    transform:scale(.9);
}


/* =====================================================
STICKER GRID
===================================================== */

.stickerGrid{
    display:grid;

    grid-template-columns:
        repeat(3,1fr);

    gap:8px;

    max-height:190px;

    overflow-y:auto;
}


.stickerBtn{
    height:85px;

    border:none;

    border-radius:16px;

    background:#222238;

    cursor:pointer;

    position:relative;

    overflow:hidden;

    display:flex;

    align-items:center;

    justify-content:center;
}


.stickerFace{
    width:55px;
    height:55px;

    display:flex;

    align-items:center;
    justify-content:center;

    font-size:38px;

    animation:
        stickerFloat
        1.8s
        ease-in-out
        infinite;
}


.stickerBtn:nth-child(2)
.stickerFace{
    animation-delay:.25s;
}


.stickerBtn:nth-child(3)
.stickerFace{
    animation-delay:.45s;
}


.stickerBtn:nth-child(4)
.stickerFace{
    animation-delay:.65s;
}


.stickerBtn:nth-child(5)
.stickerFace{
    animation-delay:.85s;
}


.stickerBtn:nth-child(6)
.stickerFace{
    animation-delay:1s;
}


/* =====================================================
SENT STICKERS
===================================================== */

.stickerMessage{
    max-width:180px;

    align-self:flex-end;

    padding:8px;

    border-radius:18px;

    background:
        linear-gradient(
            135deg,
            #FF007A,
            #7928CA
        );

    animation:
        fi .25s ease;
}


.sentSticker{
    width:120px;
    height:100px;

    display:flex;

    align-items:center;
    justify-content:center;

    font-size:68px;

    animation:
        sentStickerFloat
        1.5s
        ease-in-out
        infinite;
}


.stickerTime{
    text-align:right;

    font-size:10px;

    opacity:.55;

    margin-right:5px;
}


/* =====================================================
ANIMATIONS
===================================================== */

@keyframes fi{

    from{
        opacity:0;

        transform:
            translateY(8px);
    }

    to{
        opacity:1;

        transform:
            translateY(0);
    }

}


@keyframes tb{

    0%,60%,100%{
        transform:
            translateY(0);
    }

    30%{
        transform:
            translateY(-8px);
    }

}


@keyframes stickerFloat{

    0%,100%{
        transform:
            translateY(0)
            rotate(-3deg);
    }

    50%{
        transform:
            translateY(-8px)
            rotate(3deg)
            scale(1.05);
    }

}


@keyframes sentStickerFloat{

    0%,100%{
        transform:
            scale(1)
            rotate(-3deg);
    }

    50%{
        transform:
            scale(1.08)
            rotate(3deg);
    }

}


/* =====================================================
RESPONSIVE
===================================================== */

@media(max-width:420px){

    .emojiGrid{
        grid-template-columns:
            repeat(7,1fr);
    }

    .toolBtn{
        width:40px;
        height:40px;
    }

    .sendBtn{
        width:43px;
        height:43px;
    }

}

</style>

</head>


<body>


<!-- =====================================================
HEADER
===================================================== -->

<div class="hd">

    <div
        class="av"
        id="hav"
    ></div>


    <div class="ui">

        <div
            class="un"
            id="hn"
        >
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


<!-- =====================================================
CHAT
===================================================== -->

<div
    class="mc"
    id="mc"
></div>


<!-- =====================================================
BOTTOM AREA
===================================================== -->

<div class="ic">


    <!-- EMOJI -->

    <button
        class="toolBtn"
        id="emojiBtn"
        type="button"
        title="Emoji"
    >
        😊
    </button>


    <!-- STICKER -->

    <button
        class="toolBtn"
        id="stickerBtn"
        type="button"
        title="Stickers"
    >
        🧸
    </button>


    <input
        id="mi"
        placeholder="Type a message..."
        maxlength="500"
        autocomplete="off"
        enterkeyhint="send"
    >


    <button
        class="sendBtn"
        id="sb"
        type="button"
    >
        ➤
    </button>


    <!-- =================================================
    PICKER
    ================================================= -->

    <div
        class="picker"
        id="picker"
    >


        <div class="pickerHead">

            <button
                class="pickerTab active"
                id="emojiTab"
                type="button"
            >
                Emoji
            </button>


            <button
                class="pickerTab"
                id="stickerTab"
                type="button"
            >
                Stickers
            </button>

        </div>


        <!-- EMOJI -->

        <div
            id="emojiPanel"
        >

            <div
                class="emojiGrid"
                id="emojiGrid"
            ></div>

        </div>


        <!-- STICKERS -->

        <div
            id="stickerPanel"
            style="display:none"
        >

            <div
                class="stickerGrid"
                id="stickerGrid"
            ></div>

        </div>


    </div>

</div>


<script>

"use strict";


/* =========================================================
TELEGRAM
========================================================= */

const tg =
    window.Telegram?.WebApp;


if(tg){

    try{

        tg.ready();

        tg.expand();

        tg.setHeaderColor(
            "#FF007A"
        );

        tg.setBackgroundColor(
            "#0A0A12"
        );

    }catch(e){}

}


/* =========================================================
PARAMETERS
========================================================= */

const P =
    new URLSearchParams(
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
        "",

    ph:
        P.get("photo") ||
        "",

    g:
        (
            P.get("gender") ||
            "female"
        ).toLowerCase()

};


document.title =
    "Chat with " +
    C.n;


/* =========================================================
DOM
========================================================= */

const mc =
    document.getElementById(
        "mc"
    );

const inp =
    document.getElementById(
        "mi"
    );

const sb =
    document.getElementById(
        "sb"
    );

const picker =
    document.getElementById(
        "picker"
    );

const emojiBtn =
    document.getElementById(
        "emojiBtn"
    );

const stickerBtn =
    document.getElementById(
        "stickerBtn"
    );

const emojiTab =
    document.getElementById(
        "emojiTab"
    );

const stickerTab =
    document.getElementById(
        "stickerTab"
    );

const emojiPanel =
    document.getElementById(
        "emojiPanel"
    );

const stickerPanel =
    document.getElementById(
        "stickerPanel"
    );

const emojiGrid =
    document.getElementById(
        "emojiGrid"
    );

const stickerGrid =
    document.getElementById(
        "stickerGrid"
    );


/* =========================================================
STATE
========================================================= */

let state =
    "active";

let messageHistory =
    [];

let sendQueue =
    [];

let queueRunning =
    false;

let awayTimer =
    null;


/* =========================================================
HELPERS
========================================================= */

const wait =
    ms =>
        new Promise(
            r => setTimeout(r, ms)
        );


const random =
    arr =>
        arr[
            Math.floor(
                Math.random() *
                arr.length
            )
        ];


const esc =
    text => {

        const d =
            document.createElement(
                "div"
            );

        d.textContent =
            String(
                text ?? ""
            );

        return d.innerHTML;

    };


const timeNow =
    () =>
        new Date()
        .toLocaleTimeString(
            [],
            {
                hour:"2-digit",
                minute:"2-digit"
            }
        );


const randomDelay =
    () => {

        const r =
            Math.random();

        if(r < .25)
            return 450 +
                Math.random()*750;

        if(r < .60)
            return 1000 +
                Math.random()*1700;

        if(r < .90)
            return 2200 +
                Math.random()*3500;

        return 4500 +
            Math.random()*7000;

    };


const typingDelay =
    text =>
        800 +
        Math.min(
            String(text || "")
                .length * 45,
            3500
        ) +
        Math.random()*1600;


/* =========================================================
LOCAL STORAGE
========================================================= */

const CHAT_KEY =
    [
        "chat_v4",
        encodeURIComponent(C.n),
        encodeURIComponent(C.a),
        encodeURIComponent(C.ci),
        encodeURIComponent(C.co),
        encodeURIComponent(C.g)
    ].join("_");


function saveChat(){

    try{

        localStorage.setItem(

            CHAT_KEY,

            JSON.stringify({

                version:4,

                state,

                messages:
                    messageHistory
                    .slice(-100)

            })

        );

    }catch(e){

        console.warn(
            "Save failed",
            e
        );

    }

}


function loadChat(){

    try{

        const raw =
            localStorage.getItem(
                CHAT_KEY
            );

        if(!raw)
            return null;


        const data =
            JSON.parse(raw);


        if(
            !data ||
            !Array.isArray(
                data.messages
            )
        )
            return null;


        return data;

    }catch(e){

        return null;

    }

}


/* =========================================================
AVATAR
========================================================= */

function avatarHTML(){

    const first =
        (
            C.n ||
            "F"
        )
        .charAt(0)
        .toUpperCase();


    if(!C.ph){

        return `
            <div class="af">
                ${esc(first)}
            </div>
        `;

    }


    return `
        <img
            src="${esc(C.ph)}"
            alt=""
            onerror="
                this.outerHTML =
                '<div class=&quot;af&quot;>
                ${esc(first)}
                </div>'
        >
    `;

}


document.getElementById(
    "hav"
).innerHTML =
    avatarHTML();


document.getElementById(
    "hn"
).textContent =
    `${C.n}, ${C.a}`;


mc.innerHTML = `

    <div class="pc">

        <div class="ba">
            ${avatarHTML()}
        </div>

        <div class="pn">
            ${esc(C.n)},
            ${esc(C.a)}
        </div>

        <div class="ps">
            ${esc(C.ci)},
            ${esc(C.co)}
        </div>

    </div>

`;


/* =========================================================
STATUS
========================================================= */

function setStatus(
    text,
    online=true
){

    document.getElementById(
        "hs"
    ).textContent =
        text;


    document.getElementById(
        "od"
    )
    .classList
    .toggle(
        "off",
        !online
    );

}


/* =========================================================
MESSAGES
========================================================= */

function renderMessage(m){

    if(!m)
        return;


    /* Sticker */

    if(
        m.type ===
        "sticker"
    ){

        const wrap =
            document.createElement(
                "div"
            );

        wrap.className =
            "stickerMessage";


        const sticker =
            document.createElement(
                "div"
            );

        sticker.className =
            "sentSticker";

        sticker.textContent =
            m.sticker ||
            "⭐";


        const time =
            document.createElement(
                "div"
            );

        time.className =
            "stickerTime";

        time.textContent =
            m.time ||
            "";


        wrap.appendChild(
            sticker
        );

        wrap.appendChild(
            time
        );


        mc.appendChild(
            wrap
        );


        mc.scrollTop =
            mc.scrollHeight;

        return;

    }


    /* System */

    if(
        m.type ===
        "system"
    ){

        const d =
            document.createElement(
                "div"
            );

        d.className =
            "sys";

        d.textContent =
            m.text || "";


        mc.appendChild(
            d
        );

        mc.scrollTop =
            mc.scrollHeight;

        return;

    }


    /* Text */

    const d =
        document.createElement(
            "div"
        );


    d.className =
        "msg " +
        (
            m.type ===
            "sent"
                ? "s"
                : "r"
        );


    const body =
        document.createElement(
            "div"
        );

    body.textContent =
        m.text || "";


    const time =
        document.createElement(
            "span"
        );

    time.className =
        "mt";

    time.textContent =
        m.time || "";


    d.appendChild(
        body
    );

    d.appendChild(
        time
    );


    mc.appendChild(
        d
    );


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
            timeNow()

    };


    renderMessage(
        message
    );


    messageHistory.push(
        message
    );


    saveChat();

}


function addSticker(
    sticker
){

    const message = {

        type:
            "sticker",

        sticker,

        time:
            timeNow()

    };


    renderMessage(
        message
    );


    messageHistory.push(
        message
    );


    saveChat();

}


function addSystem(
    text
){

    const message = {

        type:
            "system",

        text:

            String(
                text || ""
            ),

        time:""

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
TYPING
========================================================= */

function showTyping(){

    hideTyping();


    const d =
        document.createElement(
            "div"
        );


    d.id =
        "typing";

    d.className =
        "ti";


    d.innerHTML = `

        <div class="td"></div>
        <div class="td"></div>
        <div class="td"></div>

    `;


    mc.appendChild(
        d
    );


    mc.scrollTop =
        mc.scrollHeight;

}


function hideTyping(){

    const d =
        document.getElementById(
            "typing"
        );

    if(d)
        d.remove();

}


/* =========================================================
EMOJIS
========================================================= */

const EMOJIS = [

    "😀","😃","😄","😁",
    "😆","😅","😂","🤣",
    "😊","🙂","🙃","😉",
    "😌","😍","🥰","😘",
    "😗","😙","😚","😋",
    "😛","😝","😜","🤪",
    "🤨","🧐","🤓","😎",
    "🤩","🥳","😏","😒",
    "😞","😔","😟","😕",
    "🙁","☹️","😣","😖",
    "😫","😩","🥺","😢",
    "😭","😤","😠","😡",
    "🤬","🤯","😳","🥵",
    "🥶","😱","😨","😰",
    "😥","😓","🤗","🤔",
    "🫣","🤭","🤫","🤥",
    "😶","😐","😑","😬",
    "🙄","😯","😦","😧",
    "😮","😲","🥱","😴",
    "🤤","😪","😵","🤐",
    "🤢","🤮","🤧","😷",
    "❤️","🧡","💛","💚",
    "💙","💜","🖤","🤍",
    "💔","💕","💞","💓",
    "💗","💖","💘","💝",
    "👍","👎","👏","🙌",
    "🙏","🤝","👋","✌️",
    "🤞","🤟","🤘","👌",
    "💪","👀","🫶","🔥",
    "✨","⭐","💯","🎉",
    "🎊","✅","❌","💀"

];


EMOJIS.forEach(
    emoji => {

        const btn =
            document.createElement(
                "button"
            );


        btn.className =
            "emojiBtn";

        btn.type =
            "button";

        btn.textContent =
            emoji;


        btn.addEventListener(
            "click",
            () => {

                sendEmoji(
                    emoji
                );

            }
        );


        emojiGrid.appendChild(
            btn
        );

    }
);


/* =========================================================
ANIMATED STICKERS
========================================================= */

const STICKERS = [

    "😂",
    "🥰",
    "😎",
    "😴",
    "😭",
    "🔥",
    "❤️",
    "⭐",
    "🙈",

];


STICKERS.forEach(
    sticker => {

        const btn =
            document.createElement(
                "button"
            );


        btn.className =
            "stickerBtn";

        btn.type =
            "button";


        const face =
            document.createElement(
                "div"
            );


        face.className =
            "stickerFace";

        face.textContent =
            sticker;


        btn.appendChild(
            face
        );


        btn.addEventListener(
            "click",
            () => {

                sendSticker(
                    sticker
                );

                closePicker();

            }
        );


        stickerGrid.appendChild(
            btn
        );

    }
);


/* =========================================================
SEND EMOJI
========================================================= */

function sendEmoji(
    emoji
){

    inp.value += emoji;

    inp.focus();

}


/* =========================================================
SEND STICKER
========================================================= */

function sendSticker(
    sticker
){

    if(
        state !==
        "active"
    ){

        return;

    }


    addSticker(
        sticker
    );


    /*
       Optional tiny delay,
       then continue normal AI queue.
    */

    sendQueue.push({

        text:
            `[sticker:${sticker}]`,

        timestamp:
            Date.now()

    });


    processQueue();

}


/* =========================================================
PICKER
========================================================= */

function openEmoji(){

    picker.classList.add(
        "show"
    );

    emojiPanel.style.display =
        "block";

    stickerPanel.style.display =
        "none";

    emojiTab.classList.add(
        "active"
    );

    stickerTab.classList.remove(
        "active"
    );

}


function openSticker(){

    picker.classList.add(
        "show"
    );

    emojiPanel.style.display =
        "none";

    stickerPanel.style.display =
        "block";

    stickerTab.classList.add(
        "active"
    );

    emojiTab.classList.remove(
        "active"
    );

}


function closePicker(){

    picker.classList.remove(
        "show"
    );

}


emojiBtn.addEventListener(
    "click",
    () => {

        if(
            picker.classList.contains(
                "show"
            ) &&
            emojiPanel.style.display !==
            "none"
        ){

            closePicker();

        }else{

            openEmoji();

        }

    }
);


stickerBtn.addEventListener(
    "click",
    () => {

        if(
            picker.classList.contains(
                "show"
            ) &&
            stickerPanel.style.display !==
            "none"
        ){

            closePicker();

        }else{

            openSticker();

        }

    }
);


emojiTab.addEventListener(
    "click",
    openEmoji
);


stickerTab.addEventListener(
    "click",
    openSticker
);


/* Close picker if user taps outside */

document.addEventListener(
    "click",
    e => {

        if(
            picker.classList.contains(
                "show"
            )
        ){

            const inside =
                picker.contains(
                    e.target
                );

            const emoji =
                emojiBtn.contains(
                    e.target
                );

            const sticker =
                stickerBtn.contains(
                    e.target
                );


            if(
                !inside &&
                !emoji &&
                !sticker
            ){

                closePicker();

            }

        }

    }
);


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


    try{

        const response =
            await fetch(
                "/api/chat",
                {

                    method:
                        "POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            message:
                                text,

                            gender:
                                C.g,

                            name:
                                C.n,

                            age:
                                Number(C.a) ||
                                22,

                            city:
                                C.ci,

                            country:
                                C.co,

                            flag:
                                ""

                        }),

                    signal:
                        controller.signal

                }
            );


        if(
            !response.ok
        ){

            return "hmm, give me a sec";

        }


        const data =
            await response.json();


        if(
            data &&
            data.ok &&
            data.reply
        ){

            return String(
                data.reply
            ).trim();

        }


        return "okay";

    }catch(e){

        return random([

            "sorry, one sec",

            "wait a minute",

            "my connection is being weird",

            "give me a sec"

        ]);

    }finally{

        clearTimeout(
            timeout
        );

    }

}


/* =========================================================
QUEUE
========================================================= */

async function processQueue(){

    if(
        queueRunning
    ){

        return;

    }


    queueRunning =
        true;


    while(
        sendQueue.length &&
        state === "active"
    ){

        const item =
            sendQueue.shift();


        /*
           Sticker message should still
           cause a normal chat response.
        */

        const queryText =
            item.text.startsWith(
                "[sticker:"
            )
            ? "reacts to sticker"
            : item.text;


        await wait(
            randomDelay()
        );


        if(
            state !== "active"
        ){

            break;

        }


        showTyping();


        const reply =
            await askAI(
                queryText
            );


        await wait(
            typingDelay(
                reply
            )
        );


        if(
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


    queueRunning =
        false;

}


/* =========================================================
SEND TEXT
========================================================= */

function send(){

    if(
        state !== "active"
    ){

        return;

    }


    const text =
        inp.value.trim();


    if(
        !text
    ){

        return;

    }


    closePicker();


    addMessage(
        text,
        "sent"
    );


    inp.value =
        "";


    sendQueue.push({

        text,

        timestamp:
            Date.now()

    });


    processQueue();

}


/* =========================================================
TEMPORARY AWAY
========================================================= */

function startAway(){

    if(
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


    const delay =
        15000 +
        Math.random() *
        55000;


    awayTimer =
        setTimeout(
            async () => {

                if(
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
                    `${C.n} is back online`
                );


                try{

                    tg?.HapticFeedback
                        ?.notificationOccurred(
                            "success"
                        );

                }catch(e){}


                try{

                    if(
                        tg &&
                        typeof tg.showPopup ===
                        "function"
                    ){

                        tg.showPopup({

                            title:
                                "Chat resumed",

                            message:
                                `${C.n} is back online.`,

                            buttons:[
                                {
                                    type:
                                        "ok"
                                }
                            ]

                        });

                    }

                }catch(e){}


                await wait(
                    900 +
                    Math.random()*2200
                );


                if(
                    state !==
                    "active"
                ){

                    return;

                }


                showTyping();


                await wait(
                    1200 +
                    Math.random()*2200
                );


                hideTyping();


                addMessage(
                    random([

                        "hey, i'm back",

                        "sorry, i was away for a bit",

                        "back now, what were you saying?",

                        "i'm here again",

                        "sorry, got busy for a while"

                    ]),
                    "received"
                );


                processQueue();

            },
            delay
        );

}


/* =========================================================
SCHEDULE AWAY
========================================================= */

function scheduleAway(){

    const delay =
        50000 +
        Math.random() *
        180000;


    setTimeout(
        () => {

            if(
                state ===
                "active" &&
                Math.random() < .18
            ){

                startAway();

            }


            scheduleAway();

        },
        delay
    );

}


/* =========================================================
RESTORE
========================================================= */

(function restore(){

    const old =
        loadChat();


    if(
        old &&
        old.messages &&
        old.messages.length
    ){

        messageHistory =
            old.messages.slice(
                -100
            );


        messageHistory.forEach(
            renderMessage
        );


        if(
            old.state ===
            "away"
        ){

            state =
                "active";

            setStatus(
                "Online",
                true
            );

        }


        if(
            old.state ===
            "closed"
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
       First automatic message
    */

    if(
        Math.random() < .82
    ){

        setTimeout(
            async () => {

                if(
                    state !==
                    "active" ||
                    messageHistory.length
                ){

                    return;

                }


                const first =
                    random([

                        "hey",

                        "hii, how are you?",

                        "hey, what's up?",

                        "helloo",

                        "hii, nice to meet you"

                    ]);


                showTyping();


                await wait(
                    typingDelay(
                        first
                    )
                );


                hideTyping();


                addMessage(
                    first,
                    "received"
                );


            },
            2200 +
            Math.random()*5000
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
    e => {

        if(
            e.key === "Enter"
        ){

            e.preventDefault();

            send();

        }

    }
);


mc.addEventListener(
    "click",
    e => {

        const target =
            e.target;


        if(
            target &&
            target.classList &&
            target.classList.contains(
                "ncb"
            )
        ){

            try{

                localStorage.removeItem(
                    CHAT_KEY
                );

            }catch(_){}


            location.reload();

        }

    }
);


/* =========================================================
PAGE VISIBILITY
========================================================= */

document.addEventListener(
    "visibilitychange",
    () => {

        if(
            document.visibilityState ===
            "visible" &&
            state ===
            "active"
        ){

            setStatus(
                "Online",
                true
            );

        }

    }
);


/* =========================================================
FOCUS
========================================================= */

setTimeout(
    () => {

        try{

            if(
                !("ontouchstart" in window)
            ){

                inp.focus();

            }

        }catch(e){}

    },
    500
);

</script>

</body>

</html>
"""


# =========================================================
# RUN
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
