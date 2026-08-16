"""Web App - FIXED: chat send bug resolved, robust error handling"""
from __future__ import annotations
import os, random, re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI = {
 "GREETING": ["heyy 👋","hii! how's your day going?","hey! i was hoping someone nice would match me 😊","hellooo","hiii, how are you?"],
 "HOW_R_U": ["i'm good 😊 what about you?","pretty fine, just got home. you?","a bit tired but i'm okay. how about you?","doing great now that you messaged 😊"],
 "DOING": ["just watching netflix, wbu?","i was about to make coffee ☕ you?","nothing much, just bored scrolling 😅","just got back from work, so tired","eating something rn, are you hungry too? lol"],
 "NAME": ["i'm {name} 😊 what's your name?","my name is {name}, and yours?","{name} here 😄 you?"],
 "AGE": ["i'm {age} 😊","{age}! you?","haha i'm {age}, don't tell anyone 😜"],
 "LOCATION": ["i'm from {city}, {country} {flag} you?","i live in {city} 😊 where are you from?","{city} {flag} it's nice here. you tell me yours","i live alone here, it's peaceful 😊 you?"],
 "HOBBIES": ["i love music and long drives 🎵 what do you like?","mostly cooking and movies 😊 you?","i like going for coffee with friends ☕ wbu?","photography and travelling ✈️ you?"],
 "COMPLIMENT": ["aww stop it 😊 you're sweet too","haha you're making me blush 🙈","that's so nice of you to say 🥰","aww thanks 😊 nobody says that to me"],
 "COMPLIMENT_m": ["haha thanks 😊 you're cool too","aww thanks, that's sweet of you","lol thanks man 😄"],
 "FLIRT": ["haha slow down 😏 let's get to know each other first","you're smooth lol 😂","careful, i might actually believe you 😜","hmm maybe 😊 buy me coffee first ☕"],
 "FLIRT_m": ["haha you're funny 😂 let's be friends first","you're cute, but let's talk a bit first 😊","haha i'm a shy guy lol"],
 "LOVE": ["haha i have a boyfriend, sorry 😅","we just met! let's take it slow 😊","let's be friends first, then we'll see 😊"],
 "LOVE_m": ["haha slow down 😅 let's know each other first","i'm actually single but let's take it slow 😊"],
 "SORRY": ["aww it's okay 😊","sorry naaa 🥺 don't be mad... promise i'll talk properly now! 🌸 now smile?","it's fine, don't worry about it 😊"],
 "EXCUSE": ["oh sorry! my mom was calling me, I had to go 😅","sorry naa 🙈 my phone died, just came back","I had some urgent work, sorry 😊 what were you saying?","haha life happened 😅 sorry, I'm here now","my internet was gone, sorry 😅 ab batao"],
 "QUESTION": ["hmm good question 🤔 i'd say yes haha. what do you think?","i think so, not sure though. you?","honestly i never thought about it 😅 you tell me first"],
 "FOOD": ["i love pizza and pasta 🍕 what about you?","i'm a big foodie, i love trying new cafes 😊","i can eat junk food all day haha"],
 "WORK": ["i work in a private company, it's okay i guess. you?","i'm studying right now. what do you do?","work is so tiring these days 😅 what about you?"],
 "SHORT_MSG": ["hmm and? 😊","lol","nice! tell me more","oh really? 😄","haha true"],
 "EMOJI_ONLY": ["😂","haha cute","🥰","your emoji game is strong lol"],
 "DEFAULT": ["haha that's interesting, tell me more 😊","oh nice! so what do you do for fun?","i was just thinking the same thing lol","you seem nice, most people here are weird 😅","hmm i like that. btw where are you from?","lol true. how's your day going?","that's cool! i'm actually bored right now, entertain me 😜"]
}

def get_ai(t, g, p):
    try:
        m = t.lower().strip()
        if re.fullmatch(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s]+', t): i="EMOJI_ONLY"
        elif len(m)<5: i="SHORT_MSG"
        elif re.search(r'(why did you (leave|go)|where were you|you left|ghost|kahan thi|wapas|came back|phone died)', m): i="EXCUSE"
        elif re.search(r'\b(sorry|gussa|angry|mad)\b', m): i="SORRY"
        elif re.search(r'\b(hi|hii|hey|hello|yo|namaste|hlo)\b', m): i="GREETING"
        elif re.search(r'(how are you|how r u|kaise ho)', m): i="HOW_R_U"
        elif re.search(r'(your name|ur name|whats your name)', m): i="NAME"
        elif re.search(r'(how old|your age|ur age)', m): i="AGE"
        elif re.search(r'(where are you from|which city|where do you live|kahan se)', m): i="LOCATION"
        elif re.search(r'(what are you doing|wbu|wyd|kya kar rahi)', m): i="DOING"
        elif re.search(r'(hobby|hobbies|like to do|free time)', m): i="HOBBIES"
        elif re.search(r'(love you|i love|marry|meet you|miss you|sexy|hot|date)', m): i="FLIRT" if not re.search(r'\b(love you|i love)\b', m) else "LOVE"
        elif re.search(r'(beautiful|cute|pretty|gorgeous|handsome|sweet|nice)', m): i="COMPLIMENT"
        elif re.search(r'(food|eat|hungry|pizza|dinner)', m): i="FOOD"
        elif re.search(r'(work|job|study|college)', m): i="WORK"
        elif '?' in m or re.search(r'\b(why|how|what|when|where|do you)\b', m): i="QUESTION"
        else: i="DEFAULT"
        k = i+"_m" if g=="male" and i in ("COMPLIMENT","FLIRT","LOVE") else i
        return random.choice(AI[k]).format(name=p.get("name","Friend"), age=p.get("age",22), city=p.get("city","City"), country=p.get("country","Country"), flag=p.get("flag","🌍"))
    except Exception:
        return "haha 😊"

class CR(BaseModel):
    message: str = ""
    gender: str = "female"
    name: str = "Friend"
    age: int = 22
    city: str = "City"
    country: str = "Country"
    flag: str = "🌍"

@app.post("/api/chat")
async def api_chat(r: CR):
    try:
        t = (r.message or "").strip()[:500]
        if not t:
            return {"ok": True, "reply": "haha 😊"}
        reply = get_ai(t, r.gender, {"name":r.name, "age":r.age, "city":r.city, "country":r.country, "flag":r.flag})
        return {"ok": True, "reply": reply}
    except Exception as e:
        return {"ok": True, "reply": "haha 😊"}

@app.get("/api/health")
async def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(HTML)

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>Chat</title><script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}body{font-family:-apple-system,'Segoe UI',sans-serif;background:#0A0A12;color:#fff;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.hd{background:linear-gradient(135deg,#FF007A,#7928CA);padding:12px 16px;display:flex;align-items:center;gap:12px;z-index:10}.av{position:relative;width:52px;height:52px;flex-shrink:0}
.av img,.ba img{width:100%;height:100%;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.5)}.af{width:100%;height:100%;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700}
.si{position:absolute;left:50%;top:42%;width:62%;transform:translate(-50%,-50%);pointer-events:none;filter:drop-shadow(0 2px 6px rgba(0,0,0,.4))}.st{position:absolute;left:50%;top:42%;transform:translate(-50%,-50%);font-size:32px;pointer-events:none}
.ui{flex:1}.un{font-size:17px;font-weight:700}.us{font-size:12px;display:flex;gap:5px;align-items:center;color:rgba(255,255,255,.9)}.od{width:8px;height:8px;background:#0f0;border-radius:50%}.od.off{background:#888}
.mc{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px}.pc{align-self:center;text-align:center;background:#1a1a2e;border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:18px 26px;margin-bottom:8px}
.ba{position:relative;width:90px;height:90px;margin:0 auto 10px}.ba .st{font-size:56px}.pn{font-size:18px;font-weight:700}.ps{font-size:13px;color:#8B8B9E;margin-top:4px}
.msg{max-width:80%;padding:11px 15px;border-radius:18px;font-size:15px;line-height:1.4;animation:fi .3s}.msg.s{align-self:flex-end;background:linear-gradient(135deg,#FF007A,#7928CA);border-bottom-right-radius:4px}.msg.r{align-self:flex-start;background:#1a1a2e;border:1px solid rgba(255,255,255,.1);border-bottom-left-radius:4px}
.mt{font-size:10px;opacity:.6;margin-top:4px;display:block}.sys{align-self:center;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:#ccc;font-size:12px;padding:8px 16px;border-radius:14px;text-align:center;max-width:92%}
.ncb{margin-top:8px;padding:9px 18px;border:none;border-radius:12px;background:linear-gradient(135deg,#FF007A,#7928CA);color:#fff;font-weight:700;font-size:12px;cursor:pointer}
.ti{align-self:flex-start;padding:12px 16px;background:#1a1a2e;border-radius:18px;display:flex;gap:4px}.td{width:8px;height:8px;border-radius:50%;background:#888;animation:tb 1.4s infinite}.td:nth-child(2){animation-delay:.2s}.td:nth-child(3){animation-delay:.4s}
.ic{background:#12121F;padding:12px 16px;display:flex;gap:10px;border-top:1px solid rgba(255,255,255,.1)}.ic input{flex:1;padding:13px 18px;border-radius:24px;border:2px solid rgba(255,255,255,.1);background:#0A0A12;color:#fff;font-size:15px;outline:none}.ic input:disabled{opacity:.4}
.ic button{width:48px;height:48px;border-radius:50%;border:none;background:linear-gradient(135deg,#FF007A,#7928CA);color:#fff;font-size:19px;cursor:pointer}.ic button:disabled{opacity:.5}
@keyframes fi{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes tb{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
</style></head><body>
<div class="hd"><div class="av" id="hav"></div><div class="ui"><div class="un" id="hn">...</div><div class="us"><span class="od" id="od"></span><span id="hs">Online</span></div></div></div>
<div class="mc" id="mc"></div>
<div class="ic"><input id="mi" placeholder="Type a message..." maxlength="500" autocomplete="off"><button id="sb">➤</button></div>
<script>
const tg=window.Telegram?.WebApp;if(tg){tg.ready();tg.expand();try{tg.setHeaderColor('#FF007A');tg.setBackgroundColor('#0A0A12');}catch(e){}}
const P=new URLSearchParams(location.search),C={n:P.get('name')||'Sofia',a:P.get('age')||'22',ci:P.get('city')||'City',co:P.get('country')||'Country',fl:P.get('flag')||'🌍',ph:P.get('photo')||'',pt:P.get('ptype')||'face',sp:P.get('sp')||'',se:P.get('se')||'🌸',g:P.get('gender')||'female'};
document.title='Chat with '+C.n;const $=id=>document.getElementById(id);$('hn').textContent=C.n+', '+C.a;
// ✅ FIX: pk/pG/dR/rD/esc/wt/nw/tD AB SABSE PEHLE define hote hain (pehle yeh crash karta tha)
const pk=a=>a[Math.floor(Math.random()*a.length)],pG=()=>{const r=Math.random();return r<.3?3:r<.7?5:8},dR=()=>Math.random()<.78;
const rD=()=>{const r=Math.random();return r<.35?12e3+Math.random()*18e3:r<.75?3e4+Math.random()*45e3:75e3+Math.random()*6e4};
const esc=t=>{const d=document.createElement('div');d.textContent=t;return d.innerHTML},wt=ms=>new Promise(r=>setTimeout(r,ms)),nw=()=>new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),tD=t=>2500+Math.min((t||'').length*70,6000)+Math.random()*2500;
let st='active',um=0,busy=false,us=false,h=[],ga=pG();const HK='wcv7_'+C.n,mc=$('mc'),inp=$('mi'),sb=$('sb');
const CB=["hey sorry! I had to go suddenly 😅","sorry naa 🙈 my mom was calling me","I'm back! did you miss me? 😜","sorry, my phone died, just charged it 😅","hey I'm back, sorry for leaving suddenly 😊"];
const RN=["hey you're back 😊","oh you came back, nice 😄","hey! I was just thinking about you 😊"],LS=['last seen just now','last seen 1 min ago','last seen recently'];
function setS(t,o){$('hs').textContent=t;$('od').classList.toggle('off',!o)}function dI(){inp.disabled=true;sb.disabled=true}function eI(){inp.disabled=false;sb.disabled=false}
function sv(){try{localStorage.setItem(HK,JSON.stringify({m:h.slice(-60),s:st}))}catch(e){}}function ld(){try{return JSON.parse(localStorage.getItem(HK))}catch(e){return null}}
function ov(){if(C.pt!=='sticker')return '';if(C.sp)return '<img class="si" src="'+C.sp+'" onerror="this.outerHTML=\'<span class=st>'+C.se+'</span>\'">';return '<span class="st">'+C.se+'</span>'}
function avH(){if(!C.ph)return '<div class="af">'+C.n[0].toUpperCase()+'</div>'+ov();return '<img src="'+C.ph+'" onerror="this.outerHTML=\'<div class=af>'+C.n[0].toUpperCase()+'</div>\'">'+ov()}
$('hav').innerHTML=avH();mc.innerHTML='<div class="pc"><div class="ba">'+avH()+'</div><div class="pn">'+esc(C.n)+', '+esc(C.a)+'</div><div class="ps">📍 '+esc(C.ci)+', '+esc(C.co)+' '+C.fl+'</div></div>';
function dom(m){const d=document.createElement('div');if(m.t==='sys'){d.className='sys';d.innerHTML=esc(m.x)+(m.b?'<br><button class="ncb">🔄 START NEW CHAT</button>':'');}else{d.className='msg '+m.t;d.innerHTML='<div>'+esc(m.x)+'</div><span class="mt">'+(m.tm||'')+'</span>';}mc.appendChild(d);mc.scrollTop=mc.scrollHeight;}
function ap(t,ty){const m={t:ty,x:t,tm:nw()};dom(m);h.push(m);sv();}function aS(t,b){const m={t:'sys',x:t,b:!!b};dom(m);h.push(m);sv();}
function sT(){const d=document.createElement('div');d.className='ti';d.id='ti';d.innerHTML='<div class="td"></div><div class="td"></div><div class="td"></div>';mc.appendChild(d);mc.scrollTop=mc.scrollHeight;}function hT(){const t=$('ti');if(t)t.remove();}
function nC(){try{localStorage.removeItem(HK);}catch(e){}location.reload();}
async function api(t){
  const ctrl=new AbortController();const tid=setTimeout(()=>ctrl.abort(),15000);
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t,gender:C.g,name:C.n,age:Number(C.a)||22,city:C.ci,country:C.co,flag:C.fl}),signal:ctrl.signal});
    clearTimeout(tid);
    if(!r.ok) return "haha 😊";
    try{const d=await r.json();return (d.ok&&d.reply)?d.reply:"haha 😊";}catch(e){return "haha 😊";}
  }catch(e){clearTimeout(tid);return "haha 😊";}
}
async function tG(ut){st='ghosting';dI();const r=Math.random();try{if(r<.5){const rp=await api(ut);await wt(800+Math.random()*1500);sT();await wt(tD(rp));hT();ap(rp,'r');}else{sT();await wt(3500+Math.random()*3000);hT();}}catch(e){hT();}setS(pk(LS),false);await wt(4000+Math.random()*8000);aS('⚠️ '+C.n+' has ended the chat',true);st='ended';sv();if(dR())sR(rD());else sN(3e4+Math.random()*45e3);}
function sR(dl){setTimeout(async()=>{if(st!=='ended')return;aS('✅ '+C.n+' has joined the chat again',false);setS('Online',true);const l=pk(CB);sT();await wt(tD(l));hT();ap(l,'r');eI();st='active';ga=um+pG();sv();if(tg?.HapticFeedback)tg.HapticFeedback.notificationOccurred('success');},dl);}
function sN(dl){setTimeout(()=>{if(st!=='ended')return;setS('offline',false);aS('❌ '+C.n+" didn't come back online. Start a new chat 💫",true);st='closed';sv();},dl);}
async function send(){
  if(busy||st!=='active')return;
  const t=inp.value.trim();if(!t)return;
  busy=true;us=true;sb.disabled=true;
  ap(t,'s');inp.value='';um++;
  if(um>=ga){busy=false;tG(t);return;}
  await wt(800+Math.random()*2200);sT();
  try{
    const rp=await api(t);
    await wt(tD(rp));hT();ap(rp,'r');
    if(tg?.HapticFeedback)try{tg.HapticFeedback.impactOccurred('light');}catch(e){}
  }catch(e){hT();ap("haha 😊",'r');}
  busy=false;if(st==='active')sb.disabled=false;
}
(function(){const ht=ld();if(ht&&ht.m&&ht.m.length){h=ht.m;h.forEach(dom);um=h.filter(m=>m.t==='s').length;if(ht.s==='ended'){st='ended';dI();setS(pk(LS),false);if(dR())sR(5e3+Math.random()*1e4);else sN(15e3+Math.random()*2e4);}else if(ht.s==='closed'){st='closed';dI();setS('offline',false);}else{st='active';setTimeout(async()=>{if(us&&um>0&&st==='active'){const l=pk(RN);sT();await wt(tD(l));hT();ap(l,'r');}},2500+Math.random()*2500);}}else{if(Math.random()<.85){setTimeout(async()=>{if(us)return;us=true;const f=pk(["heyy 👋","hii 😊","hey! finally someone matched me 😄","hellooo, how are you?"]);sT();await wt(tD(f));hT();ap(f,'r');},2500+Math.random()*5500);}}})();
// ✅ FIX: onclick attribute ki jagah proper event listeners
inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();send();}});
sb.addEventListener('click', send);
sb.addEventListener('touchend', (e) => { e.preventDefault(); send(); });
mc.addEventListener('click', (e) => { if(e.target && e.target.classList.contains('ncb')){ nC(); } });
setTimeout(()=>{if(!inp.disabled)inp.focus();},400);
</script></body></html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
