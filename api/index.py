"""
Web App - FULL RANDOM ghosting & comeback (kabhi aati hai, kabhi nahi)
"""
from __future__ import annotations
import os, random, re
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="World Chat App")

AI_RESPONSES = {
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

def get_ai_response(text: str, gender: str, profile: dict) -> str:
    msg = text.lower().strip()
    if re.match(r'^[\U00010000-\U0010ffff😀-😕🙁--]+$', text): intent = "EMOJI_ONLY"
    elif len(msg) < 5: intent = "SHORT_MSG"
    elif re.search(r'(why did you (leave|go)|where were you|you left|you disappeared|ghost|kahan thi|kahan the|wapas|came back|phone died)', msg): intent = "EXCUSE"
    elif re.search(r'\b(sorry|gussa|angry|mad|maf)\b', msg): intent = "SORRY"
    elif re.search(r'\b(hi|hii|hey|hello|helloo|yo|namaste|hlo)\b', msg): intent = "GREETING"
    elif re.search(r'(how are you|how r u|kaise ho|how was your day|how\'s your day)', msg): intent = "HOW_R_U"
    elif re.search(r'(your name|ur name|whats your name|who are you)', msg): intent = "NAME"
    elif re.search(r'(how old|your age|ur age|kitne saal)', msg): intent = "AGE"
    elif re.search(r'(where are you from|which city|where do you live|your city|kahan se|which country)', msg): intent = "LOCATION"
    elif re.search(r'(what are you doing|wbu|wyd|what about you|kya kar rahi|kya kar rahe)', msg): intent = "DOING"
    elif re.search(r'(hobby|hobbies|like to do|free time|interest)', msg): intent = "HOBBIES"
    elif re.search(r'(love you|i love|marry|meet you|miss you|sexy|hot|boyfriend|girlfriend|date)', msg): intent = "FLIRT" if not re.search(r'\b(love you|i love)\b', msg) else "LOVE"
    elif re.search(r'(beautiful|cute|pretty|gorgeous|handsome|sweet|nice|awesome|amazing)', msg): intent = "COMPLIMENT"
    elif re.search(r'(food|eat|hungry|pizza|dinner|lunch|breakfast)', msg): intent = "FOOD"
    elif re.search(r'(work|job|study|college|school|profession)', msg): intent = "WORK"
    elif '?' in msg or re.search(r'\b(why|how|what|when|where|do you|can you)\b', msg): intent = "QUESTION"
    else: intent = "DEFAULT"
    key = intent
    if gender == "male" and intent in ("COMPLIMENT", "FLIRT", "LOVE"): key = intent + "_m"
    return random.choice(AI_RESPONSES[key]).format(
        name=profile.get("name","Friend"), age=profile.get("age",22), city=profile.get("city","My City"),
        country=profile.get("country","My Country"), flag=profile.get("flag","🌍"))

class ChatRequest(BaseModel):
    message: str
    gender: str = "female"
    name: str = "Friend"
    age: int = 22
    city: str = "City"
    country: str = "Country"
    flag: str = "🌍"

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    text = req.message.strip()[:500]
    if not text: return JSONResponse({"error": "Empty"}, status_code=400)
    profile = {"name": req.name, "age": req.age, "city": req.city, "country": req.country, "flag": req.flag}
    return {"ok": True, "reply": get_ai_response(text, req.gender, profile)}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=FRONTEND_HTML)

FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Chat</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0A0A12;color:#fff;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.chat-header{background:linear-gradient(135deg,#FF007A 0%,#7928CA 100%);padding:12px 16px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 20px rgba(255,0,122,.3);z-index:10}
.avatar-wrap{position:relative;width:52px;height:52px;flex-shrink:0}
.avatar-wrap img{width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.5)}
.avatar-fallback{width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;border:2px solid rgba(255,255,255,.5)}
.sticker{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:32px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))}
.user-info{flex:1}
.user-name{font-size:17px;font-weight:700;margin-bottom:2px}
.user-status{font-size:12px;color:rgba(255,255,255,.9);display:flex;align-items:center;gap:5px}
.online-dot{width:8px;height:8px;background:#00ff88;border-radius:50%;animation:pulse 2s infinite}
.online-dot.off{background:#888;animation:none}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.messages-container{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:linear-gradient(180deg,#0A0A12 0%,#12121F 100%)}
.profile-card{align-self:center;text-align:center;background:#1a1a2e;border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:18px 26px;margin-bottom:8px}
.profile-card .big-avatar{position:relative;width:90px;height:90px;margin:0 auto 10px}
.profile-card .big-avatar img{width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid #FF007A}
.profile-card .big-avatar .sticker{font-size:56px}
.profile-card .pc-name{font-size:18px;font-weight:700}
.profile-card .pc-sub{font-size:13px;color:#8B8B9E;margin-top:4px}
.message{max-width:80%;padding:11px 15px;border-radius:18px;word-wrap:break-word;font-size:15px;line-height:1.4;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.message.sent{align-self:flex-end;background:linear-gradient(135deg,#FF007A,#7928CA);border-bottom-right-radius:4px}
.message.received{align-self:flex-start;background:#1a1a2e;border:1px solid rgba(255,255,255,.1);border-bottom-left-radius:4px}
.message-time{font-size:10px;opacity:.6;margin-top:4px;display:block}
.system-msg{align-self:center;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:#c9c9d6;font-size:12px;padding:8px 16px;border-radius:14px;text-align:center;max-width:92%;animation:fadeIn .4s ease}
.new-chat-btn{margin-top:8px;padding:9px 18px;border:none;border-radius:12px;background:linear-gradient(135deg,#FF007A,#7928CA);color:#fff;font-weight:700;font-size:12px;cursor:pointer;box-shadow:0 4px 12px rgba(255,0,122,.35)}
.typing-indicator{align-self:flex-start;padding:12px 16px;background:#1a1a2e;border-radius:18px;border-bottom-left-radius:4px;display:flex;gap:4px;border:1px solid rgba(255,255,255,.1)}
.typing-dot{width:8px;height:8px;border-radius:50%;background:#8B8B9E;animation:tb 1.4s infinite}
.typing-dot:nth-child(2){animation-delay:.2s}.typing-dot:nth-child(3){animation-delay:.4s}
@keyframes tb{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
.input-container{background:#12121F;padding:12px 16px;display:flex;gap:10px;border-top:1px solid rgba(255,255,255,.1)}
.input-container input{flex:1;padding:13px 18px;border-radius:24px;border:2px solid rgba(255,255,255,.1);background:#0A0A12;color:#fff;font-size:15px;outline:none}
.input-container input:focus{border-color:#FF007A}
.input-container input:disabled{opacity:.45}
.send-btn{width:48px;height:48px;border-radius:50%;border:none;background:linear-gradient(135deg,#FF007A,#7928CA);color:#fff;font-size:19px;cursor:pointer;box-shadow:0 4px 15px rgba(255,0,122,.4)}
.send-btn:disabled{opacity:.5}
.messages-container::-webkit-scrollbar{width:4px}
.messages-container::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);border-radius:2px}
</style>
</head>
<body>
<div class="chat-header">
  <div class="avatar-wrap" id="headerAvatar"></div>
  <div class="user-info">
    <div class="user-name" id="headerName">...</div>
    <div class="user-status"><span class="online-dot" id="onlineDot"></span><span id="headerStatus">Online</span></div>
  </div>
</div>
<div class="messages-container" id="messagesContainer"></div>
<div class="input-container">
  <input type="text" id="messageInput" placeholder="Type a message..." maxlength="500" autocomplete="off">
  <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
</div>
<script>
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); tg.setHeaderColor('#FF007A'); tg.setBackgroundColor('#0A0A12'); }

const P = new URLSearchParams(window.location.search);
const CFG = {
  name: P.get('name')||'Sofia', age: P.get('age')||'22', city: P.get('city')||'City',
  country: P.get('country')||'Country', flag: P.get('flag')||'🌍', photo: P.get('photo')||'',
  ptype: P.get('ptype')||'face', sticker: P.get('sticker')||'🌸', gender: P.get('gender')||'female'
};
document.title = 'Chat with ' + CFG.name;
document.getElementById('headerName').textContent = CFG.name + ', ' + CFG.age;

const mc = document.getElementById('messagesContainer');
const input = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const statusEl = document.getElementById('headerStatus');
const dotEl = document.getElementById('onlineDot');

let state='active', userMsgCount=0, busy=false, userSent=false, histMsgs=[];
let ghostAt = pickGhost();
const HIST_KEY = 'wc_hist_v4_' + CFG.name;

const COMEBACK = ["hey sorry! I had to go suddenly 😅","sorry naa 🙈 my mom was calling me","I'm back! did you miss me? 😜","sorry, my phone died, just charged it 😅","hey I'm back, sorry for leaving suddenly 😊"];
const GOODBYE = ["sorry I have to go now 😅 talk later!","bye for now 🙈 mom is calling","gotta go, battery low 😅 ttyl!"];
const RETURN_NOTES = ["hey you're back 😊","oh you came back, nice 😄","hey! I was just thinking about you 😊"];
const LAST_SEEN = ['last seen just now','last seen 1 min ago','last seen recently'];

function pick(a){ return a[Math.floor(Math.random()*a.length)]; }
function pickGhost(){
  const r = Math.random();
  if (r < 0.30) return 1;
  if (r < 0.60) return 2;
  if (r < 0.85) return 3 + Math.floor(Math.random()*2);
  return 5 + Math.floor(Math.random()*3);
}
function decideReturn(){ return Math.random() < 0.78; }
function returnDelay(){
  const r = Math.random();
  if (r < 0.35) return 12000 + Math.random()*18000;
  if (r < 0.75) return 30000 + Math.random()*45000;
  return 75000 + Math.random()*60000;
}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
function nowStr(){return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
function typingDelay(t){ return 2000 + Math.min(t.length*60, 5000) + Math.random()*2000; }
function setStatus(t, on){ statusEl.textContent=t; dotEl.classList.toggle('off', !on); }
function disableInput(){ input.disabled=true; sendBtn.disabled=true; }
function enableInput(){ input.disabled=false; sendBtn.disabled=false; }

function saveHist(){ try{ localStorage.setItem(HIST_KEY, JSON.stringify({messages: histMsgs.slice(-60), state: state})); }catch(e){} }
function loadHist(){ try{ return JSON.parse(localStorage.getItem(HIST_KEY)); }catch(e){ return null; } }

function avatarHTML(){
  const st = (CFG.ptype==='sticker') ? '<div class="sticker">'+CFG.sticker+'</div>' : '';
  if (!CFG.photo) return '<div class="avatar-fallback">'+CFG.name.charAt(0).toUpperCase()+'</div>'+st;
  return '<img src="'+CFG.photo+'" onerror="this.outerHTML=\'<div class=avatar-fallback>'+CFG.name.charAt(0).toUpperCase()+'</div>\'">'+st;
}
document.getElementById('headerAvatar').innerHTML = avatarHTML();
const subNote = CFG.ptype==='sticker' ? ' • 🙈 shy' : (CFG.ptype==='alt' ? ' • ✨' : '');
mc.innerHTML = '<div class="profile-card"><div class="big-avatar">'+avatarHTML()+'</div><div class="pc-name">'+esc(CFG.name)+', '+esc(String(CFG.age))+'</div><div class="pc-sub">📍 '+esc(CFG.city)+', '+esc(CFG.country)+' '+CFG.flag+subNote+'</div></div>';

function domMsg(m){
  const d=document.createElement('div');
  if(m.t==='system'){ d.className='system-msg'; d.innerHTML=esc(m.text)+(m.btn?'<br><button class="new-chat-btn" onclick="newChat()">🔄 START NEW CHAT</button>':''); }
  else{ d.className='message '+m.t; d.innerHTML='<div>'+esc(m.text)+'</div><span class="message-time">'+(m.time||'')+'</span>'; }
  mc.appendChild(d); mc.scrollTop=mc.scrollHeight;
}
function appendMsg(t,ty){ const m={t:ty,text:t,time:nowStr()}; domMsg(m); histMsgs.push(m); saveHist(); }
function addSystem(t,btn){ const m={t:'system',text:t,btn:!!btn}; domMsg(m); histMsgs.push(m); saveHist(); }
function showTyping(){ const d=document.createElement('div'); d.className='typing-indicator'; d.id='typingInd'; d.innerHTML='<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>'; mc.appendChild(d); mc.scrollTop=mc.scrollHeight; }
function hideTyping(){ const t=document.getElementById('typingInd'); if(t)t.remove(); }
function newChat(){ try{localStorage.removeItem(HIST_KEY);}catch(e){} location.reload(); }

async function apiReply(text){
  const res = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message:text, gender:CFG.gender, name:CFG.name, age:Number(CFG.age)||22, city:CFG.city, country:CFG.country, flag:CFG.flag})});
  const d = await res.json();
  return (d.ok && d.reply) ? d.reply : "haha 😊";
}

async function triggerGhost(userText){
  state='ghosting'; disableInput();
  const r = Math.random();
  try{
    if (r < 0.45){                       // reply karke gayab
      const rep = await apiReply(userText);
      showTyping(); await wait(typingDelay(rep)); hideTyping(); appendMsg(rep,'received');
    } else if (r < 0.75){                // typing dikha ke gayab
      showTyping(); await wait(3500+Math.random()*2500); hideTyping();
    } else {                             // bye bol ke gayab
      const bye = pick(GOODBYE);
      showTyping(); await wait(typingDelay(bye)); hideTyping(); appendMsg(bye,'received');
    }
  }catch(e){ hideTyping(); }

  setStatus(pick(LAST_SEEN), false);
  await wait(4000 + Math.random()*8000);
  addSystem('⚠️ ' + CFG.name + ' has ended the chat', true);
  state='ended'; saveHist();

  if (decideReturn()) scheduleReturn(returnDelay());
  else scheduleNoReturn(30000 + Math.random()*45000);
}

function scheduleReturn(delay){
  setTimeout(async ()=>{
    if (state!=='ended') return;
    addSystem('✅ ' + CFG.name + ' has joined the chat again', false);
    setStatus('Online', true);
    const line = pick(COMEBACK);
    showTyping(); await wait(typingDelay(line)); hideTyping();
    appendMsg(line,'received');
    enableInput(); state='active';
    ghostAt = userMsgCount + pickGhost();
    saveHist();
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  }, delay);
}

function scheduleNoReturn(delay){
  setTimeout(()=>{
    if (state!=='ended') return;
    setStatus('offline', false);
    addSystem('❌ ' + CFG.name + " didn't come back online. Start a new chat to meet someone new 💫", true);
    state='closed'; saveHist();
  }, delay);
}

async function sendMessage(){
  if (busy || state!=='active') return;
  const text = input.value.trim();
  if (!text) return;
  busy=true; userSent=true; sendBtn.disabled=true;
  appendMsg(text,'sent');
  input.value='';
  userMsgCount++;

  if (userMsgCount >= ghostAt){ busy=false; triggerGhost(text); return; }

  showTyping();
  try{
    const rep = await apiReply(text);
    await wait(typingDelay(rep));
    hideTyping(); appendMsg(rep,'received');
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
  }catch(e){ hideTyping(); appendMsg("sorry, network issue 😅",'received'); }
  busy=false;
  if (state==='active') sendBtn.disabled=false;
}

(function init(){
  const hist = loadHist();
  if (hist && hist.messages && hist.messages.length){
    histMsgs = hist.messages; histMsgs.forEach(domMsg);
    userMsgCount = histMsgs.filter(m=>m.t==='sent').length;
    if (hist.state==='ended'){
      state='ended'; disableInput(); setStatus(pick(LAST_SEEN), false);
      if (decideReturn()) scheduleReturn(5000+Math.random()*10000);
      else scheduleNoReturn(15000+Math.random()*20000);
    } else if (hist.state==='closed'){
      state='closed'; disableInput(); setStatus('offline', false);
    } else {
      state='active';
      setTimeout(async ()=>{
        if (userSent && userMsgCount>0 && state==='active'){
          const line = pick(RETURN_NOTES);
          showTyping(); await wait(typingDelay(line)); hideTyping(); appendMsg(line,'received');
        }
      }, 2500+Math.random()*2500);
    }
  } else {
    if (Math.random() < 0.85){
      setTimeout(async ()=>{
        if (userSent) return;
        userSent=true;
        const first = pick(["heyy 👋","hii 😊","hey! finally someone matched me 😄","hellooo, how are you?"]);
        showTyping(); await wait(typingDelay(first)); hideTyping(); appendMsg(first,'received');
      }, 2500+Math.random()*5500);
    }
  }
})();

input.addEventListener('keydown', e=>{ if(e.key==='Enter'){ e.preventDefault(); sendMessage(); } });
setTimeout(()=>{ if(!input.disabled) input.focus(); }, 400);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
