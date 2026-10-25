// ── La fionda (Sala giochi): a sinistra una fionda, a destra i fortini di legno, pietra e ghiaccio con dentro i mostriciattoli verdi.
// Si tira indietro col dito e si lascia: il sasso vola con la gravità. 3-5 lanci per livello, 8 livelli fatti a mano.
// Sassi speciali: «tre» (toccando lo schermo in volo si divide in tre), «veloce» (toccando in volo accelera), «pesante» (sfonda la pietra).
//
// LA FISICA (scritta qui, senza librerie): corpi RETTANGOLARI SENZA ROTAZIONI — cadono, si appoggiano, si spingono, crollano.
// Passi fissi di 1/120 s; ogni passo: gravità → urti fra coppie (si separano, si scambiano la spinta, un po' di attrito) → terra.
// Un corpo fermo per mezzo secondo «si addormenta» (non si muove più, niente tremolio) e si sveglia se lo colpiscono forte
// o se sparisce un blocco (tutti si svegliano e ricontrollano gli appoggi). Il sasso è un cerchio a parte.
// DANNO: a ogni urto più forte di SOGLIA la «forza» è velocità d'urto × massa ridotta; toglie vita a chi si urta.
// Ghiaccio 400, legno 1300, pietra 9000 di vita; mostriciattolo 500 (cadere da un'altezza vera o un colpo forte lo elimina).
// Punti: mostriciattolo 500, blocco rotto 50, lancio avanzato 1000. Gettoni: punti/1000, al massimo 25.
// Lo stato si MUTA e si restituisce (è fatto di soli numeri, stringhe e liste). Le prove: collaudo/giochi/fionda.mjs.

const W = 390, H = 640, TERRA = 560, G = 900, SOTTO = 1 / 120;
const ANCORA = {x:70, y:440};                       // dove sta la forcella della fionda
const MAXT = 100, MINT = 14, K = 4.7;               // tensione massima (px), minima per lanciare, velocità = tensione × K (max 470 px/s)
const SOGLIA = 40, SVEGLIA = 60, QUIETE = 0.5, TERRA_DANNO_BLOCCO = 0.15, FORZA_MAX_VOLO = 12;
const PUNTI = {mostro:500, blocco:50, avanzato:1000}, PER_GETTONE = 1000;
const MAT = {
  ghiaccio:{dens:0.7, hp:400}, legno:{dens:1, hp:1300}, pietra:{dens:2.2, hp:9000}, mostro:{dens:0.6, hp:500},
};
const SASSI = {
  normale:{r:10, massa:10}, tre:{r:10, massa:8}, veloce:{r:9, massa:8}, pesante:{r:14, massa:34, sfonda:3}, pezzo:{r:7, massa:5},
};

// ══ i livelli: pezzi con la base a b px sopra la terra. casa = due pilastri + un tetto, col mostriciattolo dentro (o no)
const blocco = (m, x, b, w, h) => ({m, x, b, w, h});
const mostro = (x, b) => blocco("mostro", x, b, 26, 26);
const casa = (pilastri, tetto, c, b, dentro = true) => [
  blocco(pilastri, c - 24, b, 16, 48), blocco(pilastri, c + 24, b, 16, 48), blocco(tetto, c, b + 48, 64, 16), ...(dentro ? [mostro(c, b)] : [])];
const cubo = (m, x, b) => blocco(m, x, b, 32, 32);
const LIVELLI = [
  {nome:"Il capanno",     lanci:["normale","normale","normale","normale"],
   oggetti:[...casa("legno", "legno", 300, 0), mostro(300, 64)]},
  {nome:"Ghiaccio sottile", lanci:["normale","normale","normale","normale"],
   oggetti:[...casa("ghiaccio", "legno", 270, 0), mostro(270, 64), mostro(350, 0)]},
  {nome:"Due torri",      lanci:["normale","normale","normale","normale"],
   oggetti:[...casa("legno", "legno", 255, 0, false), mostro(255, 64), ...casa("ghiaccio", "legno", 335, 0), mostro(335, 64)]},
  {nome:"Il muro di pietra", lanci:["tre","normale","tre","normale"],
   oggetti:[cubo("pietra", 205, 0), cubo("pietra", 205, 32), ...casa("legno", "legno", 300, 0), mostro(300, 64), mostro(362, 0)]},
  {nome:"Lontano lontano", lanci:["veloce","normale","veloce","normale","normale"],
   oggetti:[...casa("ghiaccio", "legno", 320, 0), ...casa("ghiaccio", "ghiaccio", 320, 64), mostro(320, 128)]},
  {nome:"Fortini di pietra", lanci:["pesante","normale","pesante","normale"],
   oggetti:[...casa("pietra", "pietra", 260, 0), mostro(260, 64), ...casa("legno", "pietra", 340, 0), mostro(340, 64)]},
  {nome:"Le due torri alte", lanci:["tre","pesante","veloce","normale","normale"],
   oggetti:[...casa("pietra", "legno", 230, 0, false), ...casa("legno", "ghiaccio", 230, 64), mostro(230, 128),
     ...casa("ghiaccio", "legno", 320, 0), ...casa("legno", "legno", 320, 64), mostro(320, 128)]},
  {nome:"La cittadella",  lanci:["pesante","tre","veloce","tre","pesante"],
   oggetti:[...casa("pietra", "pietra", 230, 0), ...casa("legno", "legno", 230, 64), ...casa("ghiaccio", "ghiaccio", 230, 128), mostro(230, 192),
     ...casa("legno", "pietra", 330, 0), ...casa("ghiaccio", "legno", 330, 64), mostro(330, 128)]},
];

// ══ la logica: solo funzioni, niente DOM (si prova in node)
const gettoni = p => Math.min(25, Math.max(0, Math.floor(p / PER_GETTONE)));
const sveglia = c => { c.dormi = false; c.quiete = 0; };
const svegliaTutti = s => { for (const c of s.corpi) sveglia(c); };
const conta = s => { s.mostri = s.corpi.filter(c => c.m === "mostro").length; };

function nuovaScena(corpi = [], lanci = ["normale"]){
  const s = {livello:0, lanci:lanci.slice(), corpi:[], sassi:[], punti:0, fase:"mira", t:0, tFase:0, tZero:0, eventi:[], mostri:0, immune:false, prossimoId:1, bonus:0};
  for (const c of corpi) aggiungi(s, c.m, c.x, c.y, c.w, c.h);
  conta(s); return s;
}
function aggiungi(s, m, x, y, w, h){
  const c = {id:s.prossimoId++, m, x, y, w, h, vx:0, vy:0, hp:MAT[m].hp, hp0:MAT[m].hp, massa:w * h * MAT[m].dens / 100, dormi:false, quiete:0, suolo:false};
  s.corpi.push(c); return c;
}
function nuovoLivello(indice, punti = 0){
  const L = LIVELLI[indice];
  if (!L) return {livello:indice, lanci:[], corpi:[], sassi:[], punti, fase:"finito", t:0, tFase:0, tZero:0, eventi:[], mostri:0, immune:false, prossimoId:1, bonus:0};
  const s = nuovaScena([], L.lanci); s.livello = indice; s.punti = punti;
  for (const o of L.oggetti) aggiungi(s, o.m, o.x, TERRA - o.b - o.h / 2, o.w, o.h);
  conta(s); assesta(s); return s;
}
const nuovaPartita = () => nuovoLivello(0, 0);
const prossimoLivello = s => nuovoLivello(s.livello + 1, s.punti);
// all'inizio i pezzi si «assestano» senza farsi male, poi tutto dorme
function assesta(s){
  s.immune = true;
  for (let i = 0; i < 360; i++) passo(s, SOTTO);
  for (const c of s.corpi){ c.vx = c.vy = 0; c.dormi = true; c.hp = c.hp0; }
  s.immune = false; s.eventi = []; s.sassi = []; return s;
}

const sassoDa = (tipo, x, y, vx, vy) => ({tipo, x, y, vx, vy, r:SASSI[tipo].r, massa:SASSI[tipo].massa, t:0, lento:0, usato:false});
// il tiro è lo spostamento del dito dal punto dove ha toccato: indietro e in basso = sasso in avanti e in alto
function velocitaTiro(tiro){
  const T = Math.hypot(tiro.dx, tiro.dy); if (!(T >= MINT)) return null;
  const t = Math.min(T, MAXT);
  return {vx:-tiro.dx / T * t * K, vy:-tiro.dy / T * t * K, tensione:t};
}
function lancia(s, tiro){
  if (s.fase !== "mira" || !s.lanci.length) return s;
  const v = velocitaTiro(tiro); if (!v) return s;
  const tipo = s.lanci.shift();
  s.sassi.push(sassoDa(tipo, ANCORA.x, ANCORA.y, v.vx, v.vy)); s.fase = "volo"; s.tFase = 0; s.tZero = 0;
  return s;
}
// i punti a cui è il sasso a distanza t secondi dal lancio (per i puntini della mira)
function traiettoria(tiro, n = 12, passo = 0.06){
  const v = velocitaTiro(tiro); if (!v) return [];
  return Array.from({length:n}, (_, i) => { const t = (i + 1) * passo; return {x:ANCORA.x + v.vx * t, y:ANCORA.y + v.vy * t + G * t * t / 2}; });
}
// il tocco in volo: «tre» si divide, «veloce» accelera, una volta sola per sasso
function tocca(s){
  if (s.fase !== "volo") return s;
  const p = s.sassi.find(q => !q.usato && (q.tipo === "tre" || q.tipo === "veloce")); if (!p) return s;
  p.usato = true;
  if (p.tipo === "veloce"){ const v = Math.hypot(p.vx, p.vy) || 1, nuova = Math.min(900, v * 1.7); p.vx *= nuova / v; p.vy *= nuova / v; s.eventi.push({tipo:"scatto", x:p.x, y:p.y}); }
  else {
    const sp = Math.hypot(p.vx, p.vy), base = Math.atan2(p.vy, p.vx);
    s.sassi = s.sassi.filter(q => q !== p);
    for (const a of [-0.22, 0, 0.22]) s.sassi.push(sassoDa("pezzo", p.x, p.y, Math.cos(base + a) * sp, Math.sin(base + a) * sp));
    s.eventi.push({tipo:"divide", x:p.x, y:p.y});
  }
  return s;
}
const ferma = s => s.sassi.length === 0 && s.corpi.every(c => c.dormi);
// toglie un corpo (senza punti) e sveglia tutti: i pezzi sopra ricontrollano di avere ancora un appoggio
function togli(s, id){ s.corpi = s.corpi.filter(c => c.id !== id); svegliaTutti(s); conta(s); return s; }

const colpisci = (s, c, f) => { if (!s.immune) c.hp -= f; };

// due rettangoli: si separano lungo l'asse dove si compenetrano meno; chi dorme è come fermo (a meno di un urto forte)
function urto(s, a, b){
  const ox = (a.w + b.w) / 2 - Math.abs(a.x - b.x), oy = (a.h + b.h) / 2 - Math.abs(a.y - b.y);
  if (ox <= 0 || oy <= 0) return;
  let nx = 0, ny = 0, pen;
  if (ox < oy){ nx = b.x >= a.x ? 1 : -1; pen = ox; } else { ny = b.y >= a.y ? 1 : -1; pen = oy; }
  const vrel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny;
  if ((a.dormi || b.dormi) && vrel < -SVEGLIA){ sveglia(a); sveglia(b); }
  const ia = a.dormi ? 0 : 1 / a.massa, ib = b.dormi ? 0 : 1 / b.massa, tot = ia + ib;
  if (ny > 0) a.suolo = true; else if (ny < 0) b.suolo = true;
  if (!tot) return;
  const corr = Math.max(0, pen - 0.02);
  a.x -= nx * corr * ia / tot; a.y -= ny * corr * ia / tot; b.x += nx * corr * ib / tot; b.y += ny * corr * ib / tot;
  if (vrel < 0){
    const vn = -vrel;
    if (vn > SOGLIA){ const f = vn / tot; colpisci(s, a, f); colpisci(s, b, f); }
    const j = -(1 + (vn > 150 ? 0.1 : 0)) * vrel / tot;
    a.vx -= j * ia * nx; a.vy -= j * ia * ny; b.vx += j * ib * nx; b.vy += j * ib * ny;
    if (ny){ const vt = b.vx - a.vx, jt = Math.max(-0.5 * j, Math.min(0.5 * j, -vt / tot)); a.vx -= jt * ia; b.vx += jt * ib; }
  }
}

function passoSasso(s, p, dt){
  p.t += dt; p.vy += G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
  if (p.y + p.r > TERRA){ p.y = TERRA - p.r; if (p.vy > 0){ p.vy = -p.vy * 0.3; if (Math.abs(p.vy) < 30) p.vy = 0; p.vx *= 0.85; } p.vx *= 1 - 1.5 * dt; }
  for (const c of s.corpi){
    const qx = Math.max(c.x - c.w / 2, Math.min(c.x + c.w / 2, p.x)), qy = Math.max(c.y - c.h / 2, Math.min(c.y + c.h / 2, p.y));
    let ex = p.x - qx, ey = p.y - qy, d = Math.hypot(ex, ey);
    if (d >= p.r) continue;
    if (d === 0){ const dx = p.x - c.x, dy = p.y - c.y; if (Math.abs(dx) / c.w > Math.abs(dy) / c.h){ ex = Math.sign(dx) || 1; ey = 0; } else { ex = 0; ey = Math.sign(dy) || -1; } d = 1; }
    const nx = ex / d, ny = ey / d;
    p.x += nx * (p.r - d); p.y += ny * (p.r - d);
    const vrel = (p.vx - c.vx) * nx + (p.vy - c.vy) * ny;
    if (vrel >= 0) continue;
    const vn = -vrel;
    if (c.dormi && vn > 30) sveglia(c);
    if (vn > SOGLIA){
      const mr = p.massa * c.massa / (p.massa + c.massa), sf = SASSI[p.tipo].sfonda && c.m === "pietra" ? SASSI[p.tipo].sfonda : 1;
      colpisci(s, c, vn * mr * sf);
      if (c.hp <= 0){ p.vx *= 0.85; p.vy *= 0.85; continue; }   // il blocco si rompe e il sasso passa, un po' frenato
    }
    const ic = c.dormi ? 0 : 1 / c.massa, j = -1.25 * vrel / (1 / p.massa + ic);
    p.vx += j / p.massa * nx; p.vy += j / p.massa * ny; c.vx -= j * ic * nx; c.vy -= j * ic * ny;
  }
  const v = Math.hypot(p.vx, p.vy);
  p.lento = v < 20 ? p.lento + dt : 0;
}

function passo(s, dt){
  for (const c of s.corpi){ c.suolo = false; if (!c.dormi){ c.vy += G * dt; c.x += c.vx * dt; c.y += c.vy * dt; } }
  for (const p of s.sassi) passoSasso(s, p, dt);
  for (let it = 0; it < 3; it++){
    for (let i = 0; i < s.corpi.length; i++) for (let j = i + 1; j < s.corpi.length; j++){
      const a = s.corpi[i], b = s.corpi[j]; if (a.dormi && b.dormi) continue; urto(s, a, b); }
    for (const c of s.corpi){
      const pen = c.y + c.h / 2 - TERRA; if (pen <= 0) continue;
      c.y -= pen; if (c.dormi) continue;
      if (c.vy > 0){ const vn = c.vy; if (vn > SOGLIA) colpisci(s, c, vn * c.massa * (c.m === "mostro" ? 1 : TERRA_DANNO_BLOCCO)); c.vy = vn > 150 ? -vn * 0.1 : 0; }
      c.suolo = true;
    }
  }
  for (const c of s.corpi){
    if (c.dormi) continue;
    if (c.suolo) c.vx *= Math.max(0, 1 - 6 * dt);
    if (c.suolo && Math.abs(c.vx) < 14 && Math.abs(c.vy) < 14){ c.quiete += dt; if (c.quiete > QUIETE){ c.dormi = true; c.vx = c.vy = 0; } } else c.quiete = 0;
  }
  s.sassi = s.sassi.filter(p => p.lento < 0.6 && p.t < 8 && p.x < W + 80 && p.x > -80 && p.y < H + 200);
  // chi ha finito la vita sparisce (punti); chi esce dal mondo sparisce (un mostriciattolo caduto di là conta)
  let tolto = false;
  s.corpi = s.corpi.filter(c => {
    const fuori = c.x > W + 60 || c.x < -60 || c.y > H + 120;
    if (c.hp > 0 && !fuori) return true;
    tolto = true;
    if (c.m === "mostro"){ s.punti += PUNTI.mostro; s.eventi.push({tipo:"mostro", x:c.x, y:c.y}); }
    else if (!fuori){ s.punti += PUNTI.blocco; s.eventi.push({tipo:"rotto", m:c.m, x:c.x, y:c.y, w:c.w, h:c.h}); }
    return false;
  });
  if (tolto){ svegliaTutti(s); conta(s); }
}

// muove il mondo di dt secondi e decide che cosa succede dopo: livello passato, altro lancio, sassi finiti
function avanza(s, dt){
  s.eventi = [];
  if (!(dt > 0) || s.fase === "finito") return s;
  if (s.fase === "mira" || s.fase === "vinto" || s.fase === "perso"){ if (ferma(s)) return s; }
  const n = Math.max(1, Math.ceil(Math.min(dt, 0.1) / SOTTO)), h = Math.min(dt, 0.1) / n;
  for (let i = 0; i < n; i++) passo(s, h);
  s.t += dt;
  if (s.fase === "volo"){
    s.tFase += dt; if (s.mostri === 0) s.tZero += dt;
    if (s.tFase > FORZA_MAX_VOLO){ s.sassi = []; for (const c of s.corpi){ c.dormi = true; c.vx = c.vy = 0; } }   // rete di sicurezza: niente attese infinite
    if (s.mostri === 0 && (ferma(s) || s.tZero > 2)){
      s.bonus = s.lanci.length * PUNTI.avanzato; s.punti += s.bonus; s.fase = "vinto"; s.eventi.push({tipo:"vinto", bonus:s.bonus});
    } else if (s.mostri > 0 && ferma(s)){
      if (s.lanci.length){ s.fase = "mira"; } else { s.fase = "perso"; s.eventi.push({tipo:"perso"}); }
    }
  }
  return s;
}

export const logica = {W, H, TERRA, G, ANCORA, MAXT, MINT, K, PUNTI, PER_GETTONE, MAT, SASSI, livelli:LIVELLI,
  gettoni, nuovaScena, nuovoLivello, nuovaPartita, prossimoLivello, velocitaTiro, lancia, traiettoria, tocca, avanza, ferma, togli, sassoDa};

// ══ il gioco nello strato: un canvas che riempie il campo; il mondo (390×640) si scala per stare nello schermo
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';
const COLORE_SASSO = {normale:"#9aa5b1", tre:"#FFD60A", veloce:"#00B4D8", pesante:"#4a5260", pezzo:"#FFD60A"};
const COLORE_MAT = {ghiaccio:["#a8e6ff", "#e8f9ff"], legno:["#a9692f", "#d39a5a"], pietra:["#6f7a88", "#aab4c0"]};
const SUGGERIMENTO = {tre:"Tocca in volo: si divide in tre!", veloce:"Tocca in volo: accelera!", pesante:"Sasso pesante: sfonda la pietra.", normale:"Trascina all'indietro e lascia."};

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4")};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:pointer";
  cv.setAttribute("aria-label", "La fionda: trascina all'indietro e lascia per lanciare il sasso");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = nuovaPartita(), vista = "pronto", raf = 0, prima = 0, fermo = false, dpr = 1, l = W, a = H, k = 1, ox = 0, oy = 0;
  let tira = null, banner = null, particelle = [], scritte = {punti:-1, tempo:""}, concluso = false;

  function misura(){
    const r = campo.getBoundingClientRect(); l = Math.max(240, r.width || 390); a = Math.max(360, r.height || 700);
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(l * dpr); cv.height = Math.round(a * dpr);
    k = Math.min(l / W, a / H); ox = (l - W * k) / 2; oy = a - H * k;
  }
  misura();
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => misura()) : null;
  if (ro) ro.observe(campo); else window.addEventListener("resize", misura);

  const sulBottonePausa = (x, y) => x > l - 60 && y < 60;
  function pausa(){ if (vista !== "gioco") return; vista = "pausa"; tira = null; api.esito("In pausa: tocca lo schermo per riprendere."); }
  function riprendi(){ if (vista !== "pausa" && vista !== "pronto") return; vista = "gioco"; prima = 0; messaggio(); }
  function messaggio(){
    if (s.fase === "mira") api.esito(`Sasso ${LIVELLI[s.livello].lanci.length - s.lanci.length + 1} di ${LIVELLI[s.livello].lanci.length}: ${SUGGERIMENTO[s.lanci[0]]}`);
  }
  function giu(e){
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (vista === "pronto" || vista === "pausa"){ riprendi(); e.preventDefault(); return; }
    if (vista !== "gioco" || banner) return;
    if (sulBottonePausa(x, y)){ pausa(); return; }
    if (s.fase === "mira"){ tira = {id:e.pointerId, x0:e.clientX, y0:e.clientY, dx:0, dy:0}; try { cv.setPointerCapture(e.pointerId); } catch (_) {} }
    else if (s.fase === "volo"){ tocca(s); racconta(s.eventi); }
    e.preventDefault();
  }
  function sposta(e){ if (!tira || e.pointerId !== tira.id) return; tira.dx = (e.clientX - tira.x0) / k; tira.dy = (e.clientY - tira.y0) / k; e.preventDefault(); }
  function su(e){
    if (!tira || e.pointerId !== tira.id) return;
    const t = tira; tira = null;
    if (vista === "gioco" && s.fase === "mira" && velocitaTiro(t)){ lancia(s, t); api.esito("Via!" + (s.sassi[0] && (s.sassi[0].tipo === "tre" || s.sassi[0].tipo === "veloce") ? " " + SUGGERIMENTO[s.sassi[0].tipo] : "")); }
  }
  const visibile = () => { if (document.hidden) pausa(); };
  cv.addEventListener("pointerdown", giu); cv.addEventListener("pointermove", sposta);
  cv.addEventListener("pointerup", su); cv.addEventListener("pointercancel", su);
  document.addEventListener("visibilitychange", visibile);

  function scintille(x, y, n, colore){
    for (let i = 0; i < n; i++){ const ang = Math.random() * 6.28, v = 40 + Math.random() * 180; particelle.push({x, y, vx:Math.cos(ang) * v, vy:Math.sin(ang) * v - 60, vita:0.7, colore}); }
  }
  function racconta(eventi){
    for (const e of eventi){
      if (e.tipo === "mostro"){ scintille(e.x, e.y, 16, "#7bd63a"); api.esito("Mostriciattolo giù! +500"); }
      else if (e.tipo === "rotto") scintille(e.x, e.y, 6, COLORE_MAT[e.m][1]);
      else if (e.tipo === "divide" || e.tipo === "scatto") scintille(e.x, e.y, 8, C.oro);
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `Livello ${s.livello + 1}/${LIVELLI.length} · ${s.mostri} ${s.mostri === 1 ? "mostro" : "mostri"}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }
  function metti(titolo, riga, secondi, dopo){ banner = {titolo, riga, resta:secondi, dopo}; }
  function fine(){ if (concluso) return; concluso = true; vista = "fine"; api.fine(s.punti); }
  function controlla(){
    if (banner || concluso) return;
    if (s.fase === "vinto"){
      const ultimo = s.livello + 1 >= LIVELLI.length;
      metti(ultimo ? "Tutti i fortini sono caduti!" : "Livello superato!", s.bonus ? `+${s.bonus} per ${s.bonus / PUNTI.avanzato} ${s.bonus / PUNTI.avanzato === 1 ? "sasso avanzato" : "sassi avanzati"}` : "Nessun sasso avanzato", 2.2,
        () => { if (ultimo) fine(); else { s = prossimoLivello(s); messaggio(); } });
    } else if (s.fase === "perso") metti("Sassi finiti", `Restano ${s.mostri} mostriciattoli`, 1.8, fine);
  }

  // ── il disegno, in coordinate del mondo
  function rettangolo(c){
    const x = c.x - c.w / 2, y = c.y - c.h / 2;
    if (c.m === "mostro"){
      ctx.fillStyle = "#4fb72f"; ctx.beginPath(); ctx.arc(c.x, c.y + 1, 13, 0, 6.29); ctx.fill();
      ctx.fillStyle = "#7bd63a"; ctx.beginPath(); ctx.arc(c.x - 3, c.y - 3, 7, 0, 6.29); ctx.fill();
      ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(c.x - 5, c.y - 2, 4, 0, 6.29); ctx.arc(c.x + 5, c.y - 2, 4, 0, 6.29); ctx.fill();
      ctx.fillStyle = "#12202e"; ctx.beginPath(); ctx.arc(c.x - 4, c.y - 1, 1.8, 0, 6.29); ctx.arc(c.x + 6, c.y - 1, 1.8, 0, 6.29); ctx.fill();
      ctx.strokeStyle = "#12202e"; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(c.x, c.y + 6, 4, 0.2, 2.9); ctx.stroke();
      return;
    }
    const [scuro, chiaro] = COLORE_MAT[c.m];
    ctx.fillStyle = scuro; ctx.globalAlpha = c.m === "ghiaccio" ? 0.82 : 1; ctx.fillRect(x, y, c.w, c.h); ctx.globalAlpha = 1;
    ctx.fillStyle = chiaro; ctx.globalAlpha = 0.35; ctx.fillRect(x, y, c.w, 3); ctx.fillRect(x, y, 3, c.h); ctx.globalAlpha = 1;
    ctx.strokeStyle = "rgba(5,13,24,.7)"; ctx.lineWidth = 1.5; ctx.strokeRect(x + 0.75, y + 0.75, c.w - 1.5, c.h - 1.5);
    if (c.m === "legno"){ ctx.strokeStyle = "rgba(60,30,10,.35)"; ctx.lineWidth = 1; ctx.beginPath();
      if (c.w >= c.h){ for (let i = 5; i < c.h - 2; i += 5){ ctx.moveTo(x + 3, y + i); ctx.lineTo(x + c.w - 3, y + i); } }
      else { for (let i = 5; i < c.w - 2; i += 5){ ctx.moveTo(x + i, y + 3); ctx.lineTo(x + i, y + c.h - 3); } }
      ctx.stroke(); }
    const r = c.hp / c.hp0;
    if (r < 0.7){ ctx.strokeStyle = "rgba(5,13,24,.8)"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x + c.w * 0.2, y); ctx.lineTo(x + c.w * 0.5, y + c.h * 0.5); ctx.lineTo(x + c.w * 0.4, y + c.h); if (r < 0.35){ ctx.moveTo(x + c.w, y + c.h * 0.3); ctx.lineTo(x + c.w * 0.5, y + c.h * 0.5); } ctx.stroke(); }
  }
  function sasso(p){
    ctx.fillStyle = COLORE_SASSO[p.tipo]; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.29); ctx.fill();
    ctx.strokeStyle = "rgba(5,13,24,.8)"; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,.35)"; ctx.beginPath(); ctx.arc(p.x - p.r * 0.3, p.y - p.r * 0.3, p.r * 0.35, 0, 6.29); ctx.fill();
  }
  function fionda(pouch){
    const A = ANCORA, sx = A.x - 9, dx = A.x + 9;
    ctx.strokeStyle = "#7a4a1f"; ctx.lineWidth = 9; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(A.x, TERRA); ctx.lineTo(A.x, A.y + 26); ctx.lineTo(sx - 4, A.y - 4); ctx.moveTo(A.x, A.y + 26); ctx.lineTo(dx + 4, A.y - 4); ctx.stroke();
    ctx.strokeStyle = C.oro; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(sx - 4, A.y - 4); ctx.lineTo(pouch.x, pouch.y); ctx.stroke();
    return () => { ctx.strokeStyle = C.oro; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(dx + 4, A.y - 4); ctx.lineTo(pouch.x, pouch.y); ctx.stroke(); ctx.lineCap = "butt"; };
  }

  function disegna(dt){
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const cielo = ctx.createLinearGradient(0, 0, 0, a); cielo.addColorStop(0, "#050d18"); cielo.addColorStop(1, "#0d2c45");
    ctx.fillStyle = cielo; ctx.fillRect(0, 0, l, a);
    ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * ox, dpr * oy);
    // terra
    ctx.fillStyle = "#13283b"; ctx.fillRect(-ox / k - 2, TERRA, l / k + 4, H - TERRA + a / k);
    ctx.fillStyle = C.oro; ctx.fillRect(-ox / k - 2, TERRA, l / k + 4, 3);
    // la fionda, con la mira
    let pouch = {x:ANCORA.x, y:ANCORA.y};
    const v = tira && vista === "gioco" ? velocitaTiro(tira) : null;
    if (tira && v){ const T = Math.hypot(tira.dx, tira.dy), c = Math.min(T, MAXT) / T; pouch = {x:ANCORA.x + tira.dx * c, y:ANCORA.y + tira.dy * c}; }
    const davanti = fionda(pouch);
    if (s.fase === "mira" && s.lanci.length){ sasso({tipo:s.lanci[0], x:pouch.x, y:pouch.y, r:SASSI[s.lanci[0]].r}); }
    davanti();
    if (v){ ctx.fillStyle = C.oro; traiettoria(tira).forEach((p, i, tutti) => { ctx.globalAlpha = 1 - i / tutti.length * 0.8; ctx.beginPath(); ctx.arc(p.x, p.y, 3.2, 0, 6.29); ctx.fill(); }); ctx.globalAlpha = 1; }
    for (const c of s.corpi) rettangolo(c);
    for (const p of s.sassi) sasso(p);
    for (const p of particelle){ p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 600 * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, p.vita / 0.7); ctx.fillStyle = p.colore; ctx.fillRect(p.x - 2, p.y - 2, 4, 4); }
    particelle = particelle.filter(p => p.vita > 0 && p.y < TERRA + 20); ctx.globalAlpha = 1;
    // interfaccia, in pixel dello schermo
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    s.lanci.forEach((t, i) => { ctx.fillStyle = COLORE_SASSO[t]; ctx.globalAlpha = i === 0 ? 1 : 0.6; ctx.beginPath(); ctx.arc(22 + i * 26, 26, i === 0 ? 10 : 8, 0, 6.29); ctx.fill(); });
    ctx.globalAlpha = 1;
    if (vista === "gioco"){ ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(l - 54, 10, 44, 44); ctx.fillStyle = C.tenue; ctx.fillRect(l - 40, 22, 6, 20); ctx.fillRect(l - 30, 22, 6, 20); }
    const cartello = vista === "pronto" ? ["La fionda", "Tocca per iniziare", "Trascina all'indietro e lascia"]
      : vista === "pausa" ? ["Pausa", "Tocca per riprendere", ""] : banner ? [banner.titolo, banner.riga, ""] : null;
    if (cartello){
      ctx.fillStyle = "rgba(5,13,24,.78)"; ctx.fillRect(0, a / 2 - 80, l, 160); ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 26px ${TITOLI}`; ctx.fillText(cartello[0], l / 2, a / 2 - 26, l - 24);
      ctx.fillStyle = C.tenue; ctx.font = `500 16px ${MONO}`; ctx.fillText(cartello[1], l / 2, a / 2 + 16, l - 24);
      if (cartello[2]){ ctx.font = `400 13px ${MONO}`; ctx.fillText(cartello[2], l / 2, a / 2 + 46, l - 24); }
    }
  }

  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (vista === "gioco" && dt > 0){
      if (banner){ banner.resta -= dt; if (banner.resta <= 0){ const d = banner.dopo; banner = null; d(); } }
      else { const fase = s.fase; avanza(s, dt); racconta(s.eventi); if (fase === "volo" && s.fase === "mira") messaggio(); controlla(); }
      scriviBarra();
    }
    disegna(dt);
    raf = requestAnimationFrame(fotogramma);
  }
  api.punti(0); scriviBarra(); api.esito("Tocca lo schermo per iniziare.");
  raf = requestAnimationFrame(fotogramma);

  return {
    ferma(){
      fermo = true; cancelAnimationFrame(raf);
      if (ro) ro.disconnect(); else window.removeEventListener("resize", misura);
      cv.removeEventListener("pointerdown", giu); cv.removeEventListener("pointermove", sposta);
      cv.removeEventListener("pointerup", su); cv.removeEventListener("pointercancel", su);
      document.removeEventListener("visibilitychange", visibile);
    },
    get punti(){ return s.punti; },
  };
}

export const gioco = {
  id:"fionda", nome:"La fionda", cabinato:{schermo:"SASSI", colore:"#FFD60A"},
  regole:"Trascina il dito all'indietro e lascia: il sasso parte, e più tiri più va lontano (guida i puntini). Fai cadere i mostriciattoli verdi dai fortini: il ghiaccio si rompe con poco, il legno con un colpo forte, la pietra quasi mai. Hai 3-5 sassi per livello, 8 livelli. Più avanti: il sasso che si divide in tre (toccalo in volo), quello che accelera (toccalo in volo) e quello pesante che sfonda la pietra. Mostriciattolo 500 punti, blocco rotto 50, ogni sasso avanzato 1000. Un gettone ogni 1000 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
