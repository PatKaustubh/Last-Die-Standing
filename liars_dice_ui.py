DICE_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Last Die Standing</title>
<style>
:root{--bg:#0e1a14;--card:#1b3427;--ink:#f3ead7;--mut:#9db3a3;--gold:#e9b949;--red:#e4572e;--line:#2c4d3b}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.45 system-ui,Segoe UI,sans-serif;background:radial-gradient(circle at 50% -10%,#23452f,var(--bg) 60%)}
main{max-width:680px;margin:0 auto;padding:16px 16px 48px}
h1{font-size:clamp(2.1rem,9vw,3.4rem);line-height:1;margin:.3em 0 .1em;letter-spacing:-.03em}
h1 em{color:var(--gold);font-style:normal}
.tag{color:var(--mut);margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin:12px 0}
input,button{font:inherit;border-radius:12px;padding:12px 14px;border:1px solid var(--line)}
input{width:100%;background:#10211a;color:var(--ink);margin-bottom:10px}
button{background:var(--gold);color:#241a02;font-weight:700;border:0;cursor:pointer}
button.alt{background:#27493a;color:var(--ink)}button.bad{background:var(--red);color:#fff}
button:disabled{opacity:.4;cursor:not-allowed}
.row{display:flex;gap:10px}.row>*{flex:1}
.rules{counter-reset:r;padding:0;list-style:none;margin:0}
.rules li{counter-increment:r;padding-left:34px;position:relative;margin:8px 0}
.rules li:before{content:counter(r);position:absolute;left:0;top:0;width:24px;height:24px;border-radius:50%;background:var(--gold);color:#241a02;font-weight:800;text-align:center;line-height:24px}
.code{font-size:3rem;font-weight:900;letter-spacing:.2em;color:var(--gold);text-align:center}
.pl{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-radius:12px;margin:6px 0;background:#10211a;border:2px solid transparent}
.pl.turn{border-color:var(--gold)}.pl.out{opacity:.35;text-decoration:line-through}.pl .away{color:var(--mut);font-size:.8rem}
.pips{letter-spacing:2px;color:var(--gold)}
.dice{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.die{font-size:3.4rem;line-height:1;background:#f3ead7;color:#111;border-radius:12px;padding:0 6px}
.die.hit{background:var(--gold)}.small .die{font-size:2rem;padding:0 3px}
.bid{font-size:1.4rem;text-align:center;margin:6px 0}
.faces{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin:10px 0}
.faces button{font-size:1.8rem;padding:6px;background:#27493a;color:var(--ink)}.faces button.on{background:var(--gold);color:#111}
.stepper{display:flex;align-items:center;gap:10px;justify-content:center;font-size:1.6rem}.stepper button{width:48px}
.log{color:var(--mut);font-size:.92rem;margin:0;padding-left:18px}
#toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:var(--red);color:#fff;padding:10px 16px;border-radius:12px;display:none;max-width:90%}
.hide{display:none}
</style></head><body><main>
<h1>Last Die <em>Standing</em></h1>
<p class="tag" style="font-size:1.1rem;color:var(--ink)">Everyone hides secret dice. Bid on what is on the <b>whole table</b>. <b style="color:var(--gold)">Bluff convincingly, or catch someone lying.</b></p>
<div id="app"></div>
</main><div id="toast"></div>
<script>
const FACE=["","\u2680","\u2681","\u2682","\u2683","\u2684","\u2685"];
const $=s=>document.querySelector(s), app=$("#app");
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const S={ws:null,g:null,q:1,f:2,timer:null};
const cid=()=>localStorage.lsdCid||(localStorage.lsdCid=Math.random().toString(36).slice(2)+Date.now());
const sess=()=>{try{return JSON.parse(sessionStorage.lsdSess||"null")}catch{return null}};
function toast(m){const t=$("#toast");t.textContent=m;t.style.display="block";clearTimeout(S.timer);S.timer=setTimeout(()=>t.style.display="none",3200)}
function send(o){if(S.ws&&S.ws.readyState===1)S.ws.send(JSON.stringify(o));else{toast("Reconnecting...");connect()}}
function connect(){
  if(S.ws&&S.ws.readyState<2)return;
  const ws=S.ws=new WebSocket((location.protocol==="https:"?"wss":"ws")+"://"+location.host+"/ws/dice");
  ws.onopen=()=>{const s=sess();if(s)send({action:"reconnect",...s})};
  ws.onmessage=e=>{const m=JSON.parse(e.data);
    if(m.type==="session")sessionStorage.lsdSess=JSON.stringify({room_code:m.room_code,player_id:m.player_id,secret:m.secret,name:m.name});
    else if(m.type==="state"){S.g=m;render()}
    else if(m.type==="error"){if(m.code==="INVALID_SESSION"||m.code==="NO_ROOM")sessionStorage.removeItem("lsdSess");toast(m.message);render()}};
  ws.onclose=()=>setTimeout(connect,1200);
}
const dice=(arr,hit)=>arr.map(d=>`<span class="die${hit&&(d===hit||(hit!==1&&d===1))?" hit":""}">${FACE[d]}</span>`).join("");
function minRaise(g){if(!g.bid)return[1,2];const[q,f]=g.bid;return f<6?[q,f+1]:[q+1,2]}
function legal(g){const[cq,cf]=g.bid||[0,0];return S.q>=1&&S.q<=g.total&&(!g.bid||S.q>cq||(S.q===cq&&S.f>cf))}
const SL=[
 {t:"The goal",b:"Everyone starts with <b>5 secret dice</b>. Each time you lose a round you lose one die. When you have none left you are out. <b>The last player with dice wins.</b>",v:`<div class="dice">${dice([1,2,3,4,5])}</div>`},
 {t:"Everyone rolls in secret",b:"You can only see <b>your own dice</b>. Nobody else knows what you rolled. That is where the bluffing comes from.",v:`<div class="dice">${dice([3,3,5,1,6])}</div><p class="tag" style="text-align:center">Only you see these.</p>`},
 {t:"Make a bid",b:"On your turn, guess how many dice of one face are on the <b>whole table</b>, everyone's dice added together. You might say <b>\u201cfive 3s\u201d</b>. Each new bid must be higher: more dice, or the same number of a bigger face. <b>1s are wild</b> and count as any face.",v:`<div class="bid">Ann bids <b>5 \u00d7 ${FACE[3]}</b></div>`},
 {t:"Or call LIAR",b:"If you think the last bid is too high, call <b>LIAR</b>. Everyone's dice are revealed. If the bid was true, the <b>caller</b> loses a die. If it was a bluff, the <b>bidder</b> loses a die. Then a new round starts.",v:`<div class="small"><div class="dice">${dice([3,3,5,1,6],3)}</div><div class="dice">${dice([2,3,4,4,6],3)}</div><div class="dice">${dice([1,5,5,6,2],3)}</div></div><p class="tag" style="text-align:center">Gold dice count: five in total, so Ann\u2019s bid was true.</p>`},
 {t:"Power cards",b:"Each player gets one <b>single-use power card</b> when the game starts: <b>Peek</b> at one opponent's die, <b>Shield</b> yourself from one lost die, <b>Double Down</b> a LIAR call so the loser drops 2 dice, or <b>Reroll</b> your own dice. Save it for the right moment.",v:`<div class="bid">\ud83d\udd0d \ud83d\udee1\ufe0f \u26a1 \ud83c\udfb2</div>`}
];
function howto(){
  const i=S.slide||0,x=SL[i];
  return `<div class="card"><div class="tag" style="margin:0">HOW TO PLAY \u00b7 ${i+1} OF ${SL.length}</div><h2 style="margin:.2em 0">${x.t}</h2><p>${x.b}</p>${x.v}
  <div class="row" style="margin-top:12px"><button class="alt" data-sl="-1" ${i?"":"disabled"}>Back</button><button data-sl="1" ${i<SL.length-1?"":"disabled"}>${i<SL.length-2?"Next":i===SL.length-2?"Last step":"Next"}</button></div></div>`;
}
function bindGuide(){document.querySelectorAll("[data-sl]").forEach(b=>b.onclick=()=>{S.slide=Math.max(0,Math.min(SL.length-1,(S.slide||0)+ +b.dataset.sl));S.g?render():lobby()})}
function lobby(){
  const keep={n:$("#nm")?.value,c:$("#cd")?.value};
  const room=new URLSearchParams(location.search).get("room")||"";
  app.innerHTML=howto()+`<div class="card"><b>Ready? Join the table</b><input id="nm" maxlength="16" placeholder="Your name" value="${esc(keep.n??sess()?.name??"")}" style="margin-top:10px">
  <div class="row"><button id="mk">Create table</button></div>
  <p class="tag" style="text-align:center">or join friends with their code</p>
  <div class="row"><input id="cd" maxlength="4" placeholder="Code" value="${esc(keep.c??room)}" style="text-transform:uppercase"><button class="alt" id="jn">Join</button></div></div>`;
  $("#mk").onclick=()=>send({action:"create_room",name:$("#nm").value,client_id:cid()});
  $("#jn").onclick=()=>send({action:"join_room",name:$("#nm").value,room_code:$("#cd").value,client_id:cid()});
  bindGuide();
}
const PW={peek:["\ud83d\udd0d Peek","On your turn, see one random die held by an opponent you choose."],shield:["\ud83d\udee1\ufe0f Shield","Arm it any time: you cannot lose a die this round. It is wasted if you are not challenged."],double:["\u26a1 Double Down","Use it when you call LIAR: the loser drops 2 dice."],reroll:["\ud83c\udfb2 Reroll","On your turn, re-roll all of your dice."]};
function powerPanel(g,myTurn){
  if(!g.power)return"";const[n,d]=PW[g.power];
  let h=`<div class="card"><b>${n}</b> ${g.power_used?'<span class="tag">(used)</span>':""}<p class="tag" style="margin:4px 0 8px">${d}</p>`;
  if(!g.power_used){
    if(g.power==="peek"&&myTurn)h+=`<div class="row">${g.players.filter(p=>p.id!==g.you&&p.count).map(p=>`<button class="alt" data-peek="${esc(p.id)}">Peek ${esc(p.name)}</button>`).join("")}</div>`;
    else if(g.power==="reroll"&&myTurn)h+=`<button class="alt" id="pw">Use Reroll</button>`;
    else if(g.power==="shield")h+=`<button class="alt" id="pw">Arm Shield</button>`;
  }
  if(g.note)h+=`<p style="margin:8px 0 0"><b style="color:var(--gold)">${esc(g.note)}</b></p>`;
  return h+`</div>`;
}
function render(){
  const g=S.g;if(!g||!sess()){S.g=null;return lobby()}
  const me=g.players.find(p=>p.id===g.you),myTurn=g.turn===g.you&&g.phase==="PLAY";
  let h=`<div class="card"><div class="tag" style="text-align:center;margin:0">TABLE CODE</div><div class="code">${esc(g.code)}</div>
  <button class="alt" style="width:100%" id="cp">Copy invite link</button></div>`;
  h+=`<div class="card">`+g.players.map(p=>`<div class="pl${g.turn===p.id&&g.phase==="PLAY"?" turn":""}${p.count?"":" out"}"><span>${esc(p.name)}${p.id===g.you?" (you)":""}${p.id===g.host?" \u2605":""}${p.bot?" \ud83e\udd16":""} <span class="away">${p.away?"away":""}</span></span><span class="pips">${g.phase==="LOBBY"?"":"\u25CF".repeat(p.count)}</span></div>`).join("")+`</div>`;
  if(g.phase==="LOBBY"){
    h+=`<div class="card"><b>Waiting for players</b><p class="tag" style="margin:6px 0 0">Share the code or invite link. You need 2 to 6 players. Read how the game works while you wait, then the host starts.</p></div>`+howto();
    h+=`<div class="card">`+(g.host===g.you?(g.players.length<6?`<button class="alt" style="width:100%;margin-bottom:8px" id="ab">Add a bot opponent</button>`:"")+`<button style="width:100%" id="st">Start game</button>`:`<p class="tag" style="text-align:center;margin:0">Waiting for the host to start...</p>`)+`<button class="alt" style="width:100%;margin-top:8px" id="lv">Leave table</button></div>`;
  }
  if(g.phase==="PLAY"){
    const bid=g.bid?`<b>${esc(g.bidder)}</b> bid <b>${g.bid[0]} \u00d7 ${FACE[g.bid[1]]}</b>`:"No bid yet. Open the bidding.";
    h+=`<div class="card"><div class="tag" style="text-align:center;margin:0 0 6px">YOUR DICE \u00b7 ROUND ${g.round} \u00b7 ${g.total} DICE IN PLAY</div><div class="dice">${dice(g.dice)}</div></div>`;
    h+=powerPanel(g,myTurn);
    h+=`<div class="card"><div class="bid">${bid}</div>`;
    if(myTurn){
      h+=`<div class="stepper"><button class="alt" id="qm">\u2212</button><b id="qv">${S.q}</b><button class="alt" id="qp">+</button></div>
      <div class="faces">${[1,2,3,4,5,6].map(f=>`<button data-f="${f}" class="${S.f===f?"on":""}">${FACE[f]}</button>`).join("")}</div>
      <div class="row"><button id="bd" ${legal(g)?"":"disabled"}>Bid ${S.q} \u00d7 ${FACE[S.f]}</button><button class="bad" id="lr" ${g.bid?"":"disabled"}>LIAR!</button></div>${g.power==="double"&&!g.power_used&&g.bid?`<button class="bad" style="width:100%;margin-top:8px" id="lr2">\u26a1 LIAR \u00d72 (Double Down)</button>`:""}`;
    }else h+=`<p class="tag" style="text-align:center;margin:0">Waiting for ${esc(g.players.find(p=>p.id===g.turn)?.name||"")}...</p>`;
    h+=`</div>`;
  }
  if(g.reveal){
    const r=g.reveal,[bq,bf]=r.bid;
    h+=`<div class="card"><b>${esc(r.caller)}</b> called LIAR on <b>${esc(r.bidder)}</b>'s ${bq} \u00d7 ${FACE[bf]}. There were <b>${r.total}</b>.
    <p><b style="color:var(--gold)">${esc(r.loser)}</b> ${r.shielded?"was saved by a Shield!":"loses "+(r.lost>1?r.lost+" dice":"a die")+(r.out?" and is out!":".")}</p>`+
    Object.entries(r.dice).map(([n,d])=>`<div class="small"><div class="tag" style="margin:6px 0 2px">${esc(n)}</div><div class="dice" style="justify-content:flex-start">${dice(d,bf)}</div></div>`).join("")+
    (g.phase==="REVEAL"?`<p class="tag">Next round starts in a few seconds...</p>`:"")+`</div>`;
  }
  if(g.phase==="END"){
    h+=`<div class="card" style="text-align:center"><div style="font-size:2.2rem">\ud83c\udfc6</div><h2 style="margin:.2em 0">${esc(g.winner)} wins!</h2>`+(g.host===g.you?`<button style="width:100%" id="rm">Play again</button>`:`<p class="tag">Waiting for the host to start a rematch...</p>`)+`</div>`;
  }
  h+=`<div class="card"><ul class="log">${g.log.slice().reverse().map(l=>`<li>${esc(l)}</li>`).join("")}</ul></div>`;
  app.innerHTML=h;bindGuide();
  const on=(id,fn)=>{const el=$(id);if(el)el.onclick=fn};
  on("#cp",async()=>{try{await navigator.clipboard.writeText(location.origin+"/?room="+g.code);toast("Invite link copied.")}catch{toast("Share code "+g.code)}});
  on("#st",()=>send({action:"start"}));on("#rm",()=>send({action:"rematch"}));
  on("#lv",()=>{send({action:"leave"});sessionStorage.removeItem("lsdSess");S.g=null;lobby()});
  on("#qm",()=>{S.q=Math.max(1,S.q-1);render()});on("#qp",()=>{S.q=Math.min(g.total,S.q+1);render()});
  document.querySelectorAll(".faces button").forEach(b=>b.onclick=()=>{S.f=+b.dataset.f;render()});
  on("#bd",()=>send({action:"bid",qty:S.q,face:S.f}));on("#lr",()=>send({action:"liar"}));on("#lr2",()=>send({action:"liar",double:true}));
  on("#ab",()=>send({action:"add_bot"}));on("#pw",()=>send({action:"power"}));
  document.querySelectorAll("[data-peek]").forEach(b=>b.onclick=()=>send({action:"power",target:b.dataset.peek}));
  if(myTurn){const k=`${g.round}-${g.bid}`;if(S.setFor!==k){S.setFor=k;[S.q,S.f]=minRaise(g);render()}}
}
lobby();connect();
</script></body></html>
"""
