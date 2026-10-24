// ── Il Tris (Sala giochi): 3×3 contro JJA-VIS, tre round, tre livelli.
//   Facile     mosse a caso
//   Medio      vince se può, blocca se deve, se no a caso
//   Difficile  minimax: non perde mai (si può solo pareggiare)
// Punti: vittoria 3, pareggio 1, per il moltiplicatore del livello (JJ, 25/10: Facile ×1, Medio ×3, Difficile ×10 —
// al Difficile si può solo pareggiare: 3 pareggi = 30). Gettoni: 1 per punto, al massimo 30.
// Come nel tris di carta comincia sempre la X: al 1° e al 3° round sei tu la X, al 2° comincia JJA-VIS.
// La griglia è un array di 9 caselle ("X", "O" o null), riga per riga. Le prove: collaudo/giochi/tris.mjs.

const RIGHE = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
const PUNTI = {vittoria:3, pareggio:1, sconfitta:0};
const PER_LIVELLO = {facile:1, medio:3, difficile:10};
const ROUND = 3, ATTESA = 400, PAUSA = 1600;

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const vuota = () => Array(9).fill(null);
const libere = g => g.reduce((a, c, i) => (c ? a : (a.push(i), a)), []);
const rigaVincente = g => RIGHE.find(([a,b,c]) => g[a] && g[a] === g[b] && g[a] === g[c]) || null;
// "X" o "O" se ha fatto tris, "pari" se la griglia è piena, null se si gioca ancora
const vincitore = g => { const r = rigaVincente(g); return r ? g[r[0]] : libere(g).length ? null : "pari"; };
const chiMuove = g => (g.filter(c => c === "X").length > g.filter(c => c === "O").length ? "O" : "X");
const altro = s => (s === "X" ? "O" : "X");
const metti = (g, i, s) => { const n = g.slice(); n[i] = s; return n; };
// la casella che fa tris per s, se c'è
const chiude = (g, s) => { for (const i of libere(g)) if (rigaVincente(metti(g, i, s))) return i; return null; };
const aCaso = (g, caso) => { const l = libere(g); return l.length ? l[Math.min(l.length - 1, Math.floor(caso() * l.length))] : null; };

function mossaFacile(g, caso = Math.random){ return aCaso(g, caso); }
function mossaMedia(g, caso = Math.random){
  const io = chiMuove(g), vince = chiude(g, io); if (vince !== null) return vince;
  const blocca = chiude(g, altro(io)); if (blocca !== null) return blocca;
  return aCaso(g, caso);
}
// negamax: quanto vale la griglia per chi deve muovere. Perdere più tardi vale più che perdere subito, vincere prima più che dopo.
const MEMO = new Map();
function valore(g){
  const k = g.map(c => c || "-").join(""); if (MEMO.has(k)) return MEMO.get(k);
  const v = vincitore(g); let m;
  if (v === "pari") m = 0;
  else if (v) m = -(1 + libere(g).length);   // ha appena vinto l'altro
  else { const s = chiMuove(g); m = -Infinity; for (const i of libere(g)) m = Math.max(m, -valore(metti(g, i, s))); }
  MEMO.set(k, m); return m;
}
function mossaPerfetta(g){
  if (vincitore(g)) return null;
  const s = chiMuove(g); let meglio = null, m = -Infinity;
  for (const i of libere(g)){ const v = -valore(metti(g, i, s)); if (v > m){ m = v; meglio = i; } }
  return meglio;
}
const LIVELLI = {facile:mossaFacile, medio:mossaMedia, difficile:g => mossaPerfetta(g)};
const mossaPer = (livello, g, caso = Math.random) => (LIVELLI[livello] || mossaFacile)(g, caso);
// i punti di un round finito, per chi gioca col segno tu
const puntiRound = (g, tu, livello = "facile") => { const v = vincitore(g); return (PER_LIVELLO[livello] || 1) * (v === tu ? PUNTI.vittoria : v === "pari" ? PUNTI.pareggio : PUNTI.sconfitta); };

export const logica = {RIGHE, PUNTI, PER_LIVELLO, ROUND, vuota, libere, rigaVincente, vincitore, chiMuove, altro, metti, mossaFacile, mossaMedia, mossaPerfetta, mossaPer, puntiRound};

// ══ il gioco nello strato
const STILE = `
.tris{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:16px;box-sizing:border-box;overflow:auto}
.tris h3{margin:0;font:800 22px/1.2 var(--f-titoli);color:var(--oro)}
.tris .tris-livelli{display:flex;flex-direction:column;gap:12px;width:min(92vw,380px)}
.tris .tris-livelli button{display:flex;flex-direction:column;align-items:flex-start;gap:4px;min-height:72px;padding:14px 18px;background:#0b1a2a;color:#e6f6ff;border:1px solid var(--accento);cursor:pointer;text-align:left}
.tris .tris-livelli b{font:800 20px/1.1 var(--f-titoli)}
.tris .tris-livelli span{font:400 13px/1.35 var(--f-mono);color:var(--tenue)}
.tris .tris-griglia{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;width:min(92vw,52vh,380px);aspect-ratio:1}
.tris .tris-cella{min-width:80px;min-height:80px;background:#0b1a2a;border:2px solid #1f3a52;color:#e6f6ff;font:800 clamp(44px,14vw,72px)/1 var(--f-titoli);cursor:pointer;padding:0;touch-action:manipulation}
.tris .tris-cella[data-segno="X"]{color:var(--accento)}
.tris .tris-cella[data-segno="O"]{color:var(--oro)}
.tris .tris-cella.vince{background:color-mix(in srgb,var(--oro) 28%,#0b1a2a);border-color:var(--oro);box-shadow:0 0 18px var(--oro)}
.tris .tris-cella:disabled{cursor:default}
.tris .tris-riga{font:500 14px/1.4 var(--f-mono);color:var(--tenue);text-align:center;margin:0}`;

function avvia(campo, api){
  if (!document.getElementById("stile-tris")){ const s = document.createElement("style"); s.id = "stile-tris"; s.textContent = STILE; document.head.appendChild(s); }
  const st = {livello:null, round:0, punti:0, griglia:vuota(), tu:"X", fermo:false, attesa:false, timer:null};
  const box = document.createElement("div"); box.className = "tris"; campo.textContent = ""; campo.appendChild(box);
  const dopo = (ms, fa) => { clearTimeout(st.timer); st.timer = setTimeout(() => { if (!st.fermo) fa(); }, ms); };
  const nodo = (tag, cls, testo) => { const e = document.createElement(tag); if (cls) e.className = cls; if (testo != null) e.textContent = testo; return e; };

  function scegli(){
    box.textContent = ""; api.tempo("3 round"); api.esito("Scegli il livello: si gioca contro JJA-VIS.");
    box.appendChild(nodo("h3", null, "Scegli il livello"));
    const L = nodo("div", "tris-livelli");
    [["facile","Facile","JJA-VIS gioca a caso."],["medio","Medio","Vince se può, ti blocca se deve."],["difficile","Difficile","Non perde mai: il meglio che puoi fare è pareggiare."]].forEach(([k, n, d]) => {
      const b = nodo("button"); b.type = "button"; b.dataset.livello = k; b.append(nodo("b", null, n), nodo("span", null, d));
      b.addEventListener("click", () => { st.livello = k; nuovoRound(); }); L.appendChild(b); });
    box.appendChild(L);
  }
  let celle = [], riga = null;
  function disegna(){
    const r = rigaVincente(st.griglia) || [];
    celle.forEach((c, i) => { const s = st.griglia[i]; c.textContent = s || ""; if (s) c.dataset.segno = s; else delete c.dataset.segno;
      c.classList.toggle("vince", r.includes(i)); c.disabled = !!s || st.attesa || !!vincitore(st.griglia);
      c.setAttribute("aria-label", `Casella ${i + 1}${s ? ": " + s : ", libera"}`); });
  }
  function nuovoRound(){
    st.round++; st.griglia = vuota(); st.tu = st.round % 2 ? "X" : "O"; st.attesa = false;
    box.textContent = ""; api.tempo(`Round ${st.round}/${ROUND}`);
    const G = nodo("div", "tris-griglia"); celle = [];
    for (let i = 0; i < 9; i++){ const c = nodo("button", "tris-cella"); c.type = "button"; c.dataset.cella = i; c.addEventListener("click", () => tocca(i)); G.appendChild(c); celle.push(c); }
    riga = nodo("p", "tris-riga", `Tu sei ${st.tu} · JJA-VIS è ${altro(st.tu)} · livello ${st.livello}`);
    box.append(G, riga);
    if (st.tu === "X"){ api.esito("Tocca a te: comincia la X."); disegna(); } else { api.esito("Comincia JJA-VIS…"); muoveJJAVIS(); }
  }
  function tocca(i){
    if (st.fermo || st.attesa || st.griglia[i] || vincitore(st.griglia)) return;
    st.griglia = metti(st.griglia, i, st.tu); disegna();
    if (!finito()) { api.esito("JJA-VIS ci pensa…"); muoveJJAVIS(); }
  }
  function muoveJJAVIS(){
    st.attesa = true; disegna();
    dopo(ATTESA, () => { const m = mossaPer(st.livello, st.griglia); if (m !== null) st.griglia = metti(st.griglia, m, altro(st.tu));
      st.attesa = false; disegna(); if (!finito()) api.esito("Tocca a te."); });
  }
  function finito(){
    const v = vincitore(st.griglia); if (!v) return false;
    const p = puntiRound(st.griglia, st.tu, st.livello); st.punti += p; api.punti(st.punti); disegna();
    api.esito(v === st.tu ? `Tris! Round vinto: +${p}.` : v === "pari" ? `Pareggio: +${p}.` : "Tris di JJA-VIS: questo round è suo.");
    dopo(PAUSA, () => { if (st.round < ROUND) nuovoRound(); else api.fine(st.punti); });
    return true;
  }
  api.punti(0); scegli();
  return { ferma(){ st.fermo = true; clearTimeout(st.timer); }, get punti(){ return st.punti; } };
}

export const gioco = {
  id:"tris", nome:"Tris", cabinato:{schermo:"X O", colore:"#FFD60A"},
  regole:"Tre in fila contro JJA-VIS, su una griglia 3×3. Scegli il livello: Facile (gioca a caso), Medio (vince se può, ti blocca se deve), Difficile (non perde mai). Tre round: la vittoria vale 3 punti, il pareggio 1 — al Medio ×3, al Difficile ×10 (lì al massimo si pareggia). Un gettone per punto, fino a 30 a partita.",
  massimo:30, gettoni:p => p, avvia,
};
