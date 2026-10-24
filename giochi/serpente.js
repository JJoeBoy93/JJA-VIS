// ── Il Serpentone (Sala giochi): il serpente mangia i gettoni di JJA-VIS e si allunga, su una griglia 15×21.
// Muore se tocca il bordo o sé stesso. Non si gira di 180° in un colpo (il comando contrario si ignora).
// Velocità: 7 passi al secondo, +1 ogni 5 punti, fino a 14. Ogni 4 gettoni mangiati spunta un gettone d'oro:
// vale 3 e sparisce dopo 5 s. Punti = gettoni mangiati (l'oro vale 3); gettoni vinti = punti, al massimo 25.
// Le celle sono {x, y}: x da 0 (sinistra) a 14, y da 0 (in alto) a 20. Il corpo va dal collo alla coda, senza la testa.
// Le prove: collaudo/giochi/serpente.mjs.

const LARGHEZZA = 15, ALTEZZA = 21;
const VEL_MIN = 7, VEL_MAX = 14, OGNI_VEL = 5;     // passi al secondo, e ogni quanti punti si accelera
const VALORE = 1, VALORE_ORO = 3, OGNI_ORO = 4, DURATA_ORO = 5000;
const DIREZIONI = {su:[0,-1], giu:[0,1], sinistra:[-1,0], destra:[1,0]};
const OPPOSTA = {su:"giu", giu:"su", sinistra:"destra", destra:"sinistra"};

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const uguale = (a, b) => !!a && !!b && a.x === b.x && a.y === b.y;
const fuori = (s, c) => c.x < 0 || c.y < 0 || c.x >= s.larghezza || c.y >= s.altezza;
const occupata = (s, c) => uguale(s.testa, c) || s.corpo.some(p => uguale(p, c)) || uguale(s.cibo, c) || uguale(s.oro, c);
const velocita = punti => Math.min(VEL_MAX, VEL_MIN + Math.floor(Math.max(0, punti) / OGNI_VEL));
const contraria = (a, b) => OPPOSTA[a] === b;
// una cella libera a caso (mai sul serpente, né su un altro gettone); null se la griglia è piena
function nuovoCibo(s, caso = Math.random){
  const libere = [];
  for (let y = 0; y < s.altezza; y++) for (let x = 0; x < s.larghezza; x++) if (!occupata(s, {x, y})) libere.push({x, y});
  return libere.length ? libere[Math.min(libere.length - 1, Math.floor(caso() * libere.length))] : null;
}
// la partita appena cominciata: testa a metà, lungo 3, va su
function inizio(caso = Math.random){
  const x = Math.floor(LARGHEZZA / 2), y = Math.floor(ALTEZZA / 2) + 2;
  const s = {larghezza:LARGHEZZA, altezza:ALTEZZA, testa:{x, y}, corpo:[{x, y:y + 1}, {x, y:y + 2}], direzione:"su",
    cibo:null, oro:null, vivo:true, morte:null, punti:0, mangiati:0, passi:0};
  return {...s, cibo:nuovoCibo(s, caso)};
}
// un passo nella direzione chiesta (o in quella di prima, se è contraria o non valida); caso serve solo se mangia
function passo(s, direzione, caso = Math.random){
  if (!s.vivo) return s;
  const d = DIREZIONI[direzione] && !contraria(s.direzione, direzione) ? direzione : s.direzione;
  const [dx, dy] = DIREZIONI[d], t = {x:s.testa.x + dx, y:s.testa.y + dy};
  const base = {...s, direzione:d, passi:s.passi + 1};
  if (fuori(s, t)) return {...base, vivo:false, morte:"bordo"};
  const mangia = uguale(t, s.cibo), mangiaOro = uguale(t, s.oro);
  const tutto = [s.testa, ...s.corpo], corpo = mangia || mangiaOro ? tutto : tutto.slice(0, -1);   // se non cresce, la coda si sposta
  if (corpo.some(p => uguale(p, t))) return {...base, vivo:false, morte:"sé stesso"};
  let n = {...base, testa:t, corpo};
  if (mangiaOro) n = {...n, punti:n.punti + VALORE_ORO, oro:null};
  if (mangia){
    n = {...n, punti:n.punti + VALORE, mangiati:n.mangiati + 1, cibo:null};
    n = {...n, cibo:nuovoCibo(n, caso)};
    if (n.mangiati % OGNI_ORO === 0 && !n.oro){ const c = nuovoCibo(n, caso); if (c) n = {...n, oro:{...c, resta:DURATA_ORO}}; }
  }
  return n;
}
// il tempo che passa (ms): il gettone d'oro si consuma e, finito il suo tempo, sparisce
function invecchia(s, ms){
  if (!s.oro) return s;
  const resta = s.oro.resta - Math.max(0, ms);
  return {...s, oro:resta > 0 ? {...s.oro, resta} : null};
}
// finita: morto, o la griglia è piena e non c'è più dove mettere un gettone
const finita = s => !s.vivo || !s.cibo;
const lunghezza = s => 1 + s.corpo.length;

export const logica = {LARGHEZZA, ALTEZZA, VEL_MIN, VEL_MAX, OGNI_VEL, VALORE, VALORE_ORO, OGNI_ORO, DURATA_ORO, DIREZIONI, OPPOSTA,
  uguale, velocita, contraria, nuovoCibo, inizio, passo, invecchia, finita, lunghezza};

// ══ il gioco nello strato
const STILE = `
.serpente{position:absolute;inset:0;touch-action:none;user-select:none;-webkit-user-select:none}
.serpente canvas{position:absolute;inset:0;display:block;touch-action:none}
.serpente .serpente-frecce{position:absolute;left:50%;bottom:10px;transform:translateX(-50%);display:grid;grid-template-columns:repeat(3,1fr);grid-template-areas:". su ." "sinistra giu destra";gap:8px;width:min(92vw,330px)}
.serpente .serpente-frecce button{min-height:66px;background:#0b1a2a;color:var(--accento);border:2px solid var(--accento);font:800 40px/1 var(--f-titoli);cursor:pointer;padding:0;touch-action:none;border-radius:14px}
.serpente .serpente-frecce button:active{background:color-mix(in srgb,var(--accento) 30%,#0b1a2a);color:#e6f6ff}`;
const FRECCE = [["su","▲","Su"],["sinistra","◀","Sinistra"],["giu","▼","Giù"],["destra","▶","Destra"]];
const CHIAVI = {ArrowUp:"su", ArrowDown:"giu", ArrowLeft:"sinistra", ArrowRight:"destra"};
const SCORRI = 24, ATTESA_FINE = 1400;

function avvia(campo, api){
  if (!document.getElementById("stile-serpente")){ const s = document.createElement("style"); s.id = "stile-serpente"; s.textContent = STILE; document.head.appendChild(s); }
  const css = getComputedStyle(document.documentElement), colore = (v, d) => css.getPropertyValue(v).trim() || d;
  const C = {oro:colore("--oro", "#FFD60A"), accento:colore("--accento", "#00B4D8"), tenue:colore("--tenue", "#48CAE4"), testo:colore("--testo", "#CAF0F8")};
  const box = document.createElement("div"); box.className = "serpente"; campo.textContent = ""; campo.appendChild(box);
  const tela = document.createElement("canvas"); tela.setAttribute("aria-label", "Il campo del Serpentone"); box.appendChild(tela);
  const pad = document.createElement("div"); pad.className = "serpente-frecce"; box.appendChild(pad);
  const ctx = tela.getContext("2d");

  const st = {s:inizio(), coda:[], partito:false, pausa:false, fermo:false, acc:0, ultimo:null, raf:0, timer:null, w:0, h:0, dpr:1, morto:0};
  const via = [];   // gli ascoltatori da togliere in ferma()
  const ascolta = (bersaglio, tipo, fa, opz) => { bersaglio.addEventListener(tipo, fa, opz); via.push(() => bersaglio.removeEventListener(tipo, fa, opz)); };

  function scriviTempo(){ api.tempo(`${velocita(st.s.punti)} passi/s · lungo ${lunghezza(st.s)}`); }
  // un comando: in coda (al massimo due, per le svolte veloci), mai uguale o contrario all'ultimo
  function comanda(d){
    if (st.fermo || finita(st.s) || !DIREZIONI[d]) return;
    if (!st.partito || st.pausa){ st.partito = true; st.pausa = false; st.ultimo = null; api.esito("Mangia i gettoni, non toccare il bordo né te stesso."); }
    const prima = st.coda.length ? st.coda[st.coda.length - 1] : st.s.direzione;
    if (d === prima || contraria(prima, d) || st.coda.length >= 2) return;
    st.coda.push(d);
  }
  FRECCE.forEach(([d, segno, nome]) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = segno; b.style.gridArea = d; b.dataset.direzione = d; b.setAttribute("aria-label", nome);
    ascolta(b, "pointerdown", e => { e.preventDefault(); comanda(d); });
    ascolta(b, "click", e => { if (e.detail === 0) comanda(d); });   // da tastiera (Invio/spazio sul bottone)
    pad.appendChild(b);
  });
  // lo scorrimento del dito: appena supera SCORRI px si decide la direzione, e si riparte da lì (si può svoltare senza staccare)
  let dito = null;
  ascolta(tela, "pointerdown", e => { e.preventDefault(); dito = {x:e.clientX, y:e.clientY, id:e.pointerId}; try { tela.setPointerCapture(e.pointerId); } catch (_) {}
    if (st.pausa) comanda(st.coda[st.coda.length - 1] || st.s.direzione); });
  ascolta(tela, "pointermove", e => { if (!dito || e.pointerId !== dito.id) return;
    const dx = e.clientX - dito.x, dy = e.clientY - dito.y; if (Math.max(Math.abs(dx), Math.abs(dy)) < SCORRI) return;
    comanda(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "destra" : "sinistra") : (dy > 0 ? "giu" : "su")); dito = {...dito, x:e.clientX, y:e.clientY}; });
  const lascia = () => { dito = null; };
  ascolta(tela, "pointerup", lascia); ascolta(tela, "pointercancel", lascia);
  ascolta(document, "keydown", e => { const d = CHIAVI[e.key]; if (d){ e.preventDefault(); comanda(d); } });
  ascolta(document, "visibilitychange", () => { if (document.hidden && st.partito && !finita(st.s)){ st.pausa = true; st.coda = []; api.esito("In pausa: tocca o scorri per riprendere."); } st.ultimo = null; });

  function misura(){
    const r = campo.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    if (r.width === st.w && r.height === st.h && dpr === st.dpr) return;
    st.w = r.width; st.h = r.height; st.dpr = dpr;
    tela.width = Math.max(1, Math.round(r.width * dpr)); tela.height = Math.max(1, Math.round(r.height * dpr));
    tela.style.width = r.width + "px"; tela.style.height = r.height + "px";
  }
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(misura) : null; if (ro) ro.observe(campo);
  ascolta(window, "resize", misura);

  function giro(ora){
    if (st.fermo) return;
    st.raf = requestAnimationFrame(giro);
    const dt = st.ultimo == null ? 0 : Math.min(250, ora - st.ultimo); st.ultimo = ora;
    if (st.partito && !st.pausa && !finita(st.s)){
      st.s = invecchia(st.s, dt); st.acc += dt;
      const ogni = 1000 / velocita(st.s.punti);
      while (st.acc >= ogni && !finita(st.s)){ st.acc -= ogni; avanza(st.coda.shift() || st.s.direzione); }
    }
    disegna(ora);
  }
  function avanza(d){
    const prima = st.s; st.s = passo(st.s, d);
    if (st.s.punti !== prima.punti){ api.punti(st.s.punti); scriviTempo();
      if (velocita(st.s.punti) > velocita(prima.punti)) api.esito(`Più veloce! ${velocita(st.s.punti)} passi al secondo.`);
      else if (st.s.punti - prima.punti >= VALORE_ORO) api.esito(`Gettone d'oro: +${VALORE_ORO}!`); }
    if (st.s.oro && !prima.oro) api.esito("Un gettone d'oro! Vale 3, ma sparisce in 5 secondi.");
    if (finita(st.s)){
      st.morto = performance.now(); st.coda = [];
      api.esito(!st.s.vivo ? (st.s.morte === "bordo" ? `Hai toccato il bordo! ${st.s.punti} punti.` : `Ti sei morso la coda! ${st.s.punti} punti.`) : `Griglia piena: incredibile! ${st.s.punti} punti.`);
      clearTimeout(st.timer); st.timer = setTimeout(() => { if (!st.fermo) api.fine(st.s.punti); }, ATTESA_FINE);
    }
  }

  // ── il disegno: tutto in codice, forme e testo
  function disegna(ora){
    misura();
    const {w, h, dpr} = st, s = st.s; if (!w || !h) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#07131f"; ctx.fillRect(0, 0, w, h);
    const sotto = pad.offsetHeight + 20, area = Math.max(60, h - sotto);
    const cella = Math.max(4, Math.floor(Math.min((w - 16) / s.larghezza, (area - 12) / s.altezza)));
    const W = cella * s.larghezza, H = cella * s.altezza, ox = Math.round((w - W) / 2), oy = Math.max(6, Math.round((area - H) / 2));
    const X = x => ox + x * cella, Y = y => oy + y * cella;
    // la scacchiera
    ctx.fillStyle = "#0b1a2a"; ctx.fillRect(ox, oy, W, H);
    ctx.fillStyle = "rgba(255,255,255,0.025)";
    for (let y = 0; y < s.altezza; y++) for (let x = (y % 2); x < s.larghezza; x += 2) ctx.fillRect(X(x), Y(y), cella, cella);
    ctx.save(); ctx.strokeStyle = C.tenue; ctx.globalAlpha = 0.55; ctx.lineWidth = 2; ctx.strokeRect(ox - 1, oy - 1, W + 2, H + 2); ctx.restore();
    // i gettoni
    if (s.cibo) moneta(X(s.cibo.x) + cella / 2, Y(s.cibo.y) + cella / 2, cella * (0.36 + 0.03 * Math.sin(ora / 180)), "J", false);
    if (s.oro){
      const cx = X(s.oro.x) + cella / 2, cy = Y(s.oro.y) + cella / 2, f = s.oro.resta / DURATA_ORO;
      if (s.oro.resta > 1500 || Math.floor(ora / 120) % 2){
        ctx.save(); ctx.shadowColor = C.oro; ctx.shadowBlur = cella * 0.8; moneta(cx, cy, cella * (0.46 + 0.04 * Math.sin(ora / 90)), "3", true); ctx.restore(); }
      ctx.save(); ctx.strokeStyle = C.accento; ctx.lineWidth = Math.max(2, cella * 0.09); ctx.beginPath();
      ctx.arc(cx, cy, cella * 0.62, -Math.PI / 2, -Math.PI / 2 + f * Math.PI * 2); ctx.stroke(); ctx.restore();
    }
    // il serpente, dalla coda alla testa
    const pezzi = [s.testa, ...s.corpo], n = pezzi.length, morto = !s.vivo;
    for (let i = n - 1; i >= 1; i--){
      const p = pezzi[i], m = cella * (0.1 + 0.08 * i / n);
      ctx.save(); ctx.globalAlpha = 1 - 0.5 * i / n; ctx.fillStyle = morto ? "#7a2a3a" : C.accento;
      tondo(X(p.x) + m, Y(p.y) + m, cella - 2 * m, cella - 2 * m, cella * 0.25); ctx.restore();
    }
    const t = s.testa, lampo = morto && Math.floor((performance.now() - st.morto) / 140) % 2;
    ctx.save(); ctx.shadowColor = morto ? "#ff4d6d" : C.accento; ctx.shadowBlur = cella * 0.5; ctx.fillStyle = morto ? (lampo ? "#ff4d6d" : "#ffd0d8") : C.testo;
    tondo(X(t.x) + 1, Y(t.y) + 1, cella - 2, cella - 2, cella * 0.32); ctx.restore();
    // gli occhi guardano dove va
    const [dx, dy] = DIREZIONI[s.direzione], cx = X(t.x) + cella / 2 + dx * cella * 0.14, cy = Y(t.y) + cella / 2 + dy * cella * 0.14;
    ctx.fillStyle = "#07131f";
    for (const k of [-1, 1]){ ctx.beginPath(); ctx.arc(cx + dy * k * cella * 0.2, cy + dx * k * cella * 0.2, Math.max(1.5, cella * 0.1), 0, Math.PI * 2); ctx.fill(); }
    // i cartelli: prima della partenza, in pausa
    if (!st.partito || st.pausa) cartello(ox + W / 2, oy + H * 0.3, st.pausa ? "⏸ In pausa" : "🐍 Serpentone", st.pausa ? "Tocca o scorri per riprendere" : "Scorri col dito o usa le frecce", Math.min(W - 20, 320));
  }
  function tondo(x, y, w, h, r){ ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); ctx.fill(); }
  function moneta(cx, cy, r, segno, oro){
    ctx.fillStyle = oro ? C.oro : "#c9a400"; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = oro ? "#fff3a6" : C.oro; ctx.beginPath(); ctx.arc(cx, cy, r * 0.74, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#3a2c00"; ctx.font = `800 ${Math.round(r * 1.05)}px system-ui, sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(segno, cx, cy + r * 0.05);
  }
  function cartello(cx, cy, titolo, riga, larga){
    ctx.save(); ctx.fillStyle = "rgba(7,19,31,0.86)"; ctx.strokeStyle = C.oro; ctx.lineWidth = 2;
    ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(cx - larga / 2, cy - 52, larga, 104, 16); else ctx.rect(cx - larga / 2, cy - 52, larga, 104); ctx.fill(); ctx.stroke();
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillStyle = C.oro; ctx.font = "800 26px system-ui, sans-serif"; ctx.fillText(titolo, cx, cy - 16);
    ctx.fillStyle = C.tenue; ctx.font = "500 15px system-ui, sans-serif"; ctx.fillText(riga, cx, cy + 22); ctx.restore();
  }

  api.punti(0); scriviTempo(); api.esito("Scorri col dito o usa le frecce per partire.");
  misura(); st.raf = requestAnimationFrame(giro);
  return { ferma(){ st.fermo = true; cancelAnimationFrame(st.raf); clearTimeout(st.timer); via.forEach(f => f()); via.length = 0; if (ro) ro.disconnect(); },
    get punti(){ return st.s.punti; } };
}

export const gioco = {
  id:"serpente", nome:"Serpentone", cabinato:{schermo:"🐍 ●", colore:"#00B4D8"},
  regole:"Guida il serpente sulla griglia: scorri il dito nella direzione, o usa le quattro frecce. Mangia i gettoni di JJA-VIS e ti allunghi; se tocchi il bordo o te stesso, è finita. Non puoi tornare indietro di colpo. Ogni 5 punti va più veloce. Ogni tanto spunta un gettone d'oro: vale 3, ma sparisce dopo 5 secondi. Un gettone per punto, fino a 25 a partita.",
  massimo:25, gettoni:p => p, avvia,
};
