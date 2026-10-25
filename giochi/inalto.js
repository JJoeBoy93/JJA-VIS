// ── In alto! (Sala giochi): un personaggino salta da solo di piattaforma in piattaforma, sempre più su.
//   Si guida trascinando il dito a destra e a sinistra; uscendo da un lato si rientra dall'altro.
//   La visuale sale con lui: se cade sotto il bordo dello schermo la partita è finita.
//   Piattaforme fisse, che si muovono, che si sbriciolano dopo un salto; molle che lanciano altissimo.
//   Più in alto: mostri volanti (da evitare, o da schiacciare saltandoci sopra) e, raro, un razzo che porta su veloce.
//   Più si sale, più le piattaforme sono rade. Lo sfondo cambia con l'altezza: prato, nuvole, cielo notturno, spazio.
// Punti = metri saliti. Gettoni: uno ogni 100 punti, al massimo 25.
// Il mondo è in pixel CSS: x verso destra, y verso l'ALTO (la visuale parte da cam, il bordo basso dello schermo). Lo stato è un
// oggetto semplice che `avanza` non tocca mai: ne restituisce uno nuovo. Le prove: collaudo/giochi/inalto.mjs.

const G = 1500, V_SALTO = 620, V_MOLLA = 1120, V_RAZZO = 1500, T_RAZZO = 1.6;      // pixel e secondi
const H_SALTO = V_SALTO * V_SALTO / (2 * G), H_MOLLA = V_MOLLA * V_MOLLA / (2 * G);   // quanto sale un salto, una molla
const GAP_MIN = 42, GAP_MAX = Math.floor(H_SALTO * 0.85);   // la distanza fra due piattaforme sta sempre sotto il salto
const SALITA = 15000;        // a quest'altezza (px) la difficoltà è al massimo
const BASE_Y = 60, PX_METRO = 10, RP = 16, R_MOSTRO = 20, MARGINE = 40, OLTRE = 320, PASSO = 1 / 60;
const DA_FRAGILI = 400, DA_MOBILI = 800, DA_MOLLE = 300, DA_MOSTRI = 2000, DA_RAZZI = 4000;   // altezze (px) da cui compaiono
const PER_GETTONE = 100, MASSIMO = 25;

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const lim = (v, a, b) => Math.max(a, Math.min(b, v));
const mescola = (a, b, t) => a + (b - a) * t;
const difficolta = alt => lim(alt / SALITA, 0, 1);
const giro = (v, l) => ((v % l) + l) % l;
const distX = (a, b, l) => { const d = Math.abs(a - b); return Math.min(d, l - d); };     // la distanza, rientrando dall'altro lato
const gettoni = p => Math.min(MASSIMO, Math.floor(Math.max(0, Number(p) || 0) / PER_GETTONE));

const copia = s => ({...s, piatt:s.piatt.map(p => ({...p})), mostri:s.mostri.map(m => ({...m})), razzi:s.razzi.map(r => ({...r})), eventi:[]});

// il cielo a quella quota in metri: nome, colori (alto e basso dello schermo), quante stelle
const TAPPE = [   // [da quanti metri, nome, cima, fondo, stelle]
  [0,   "prato",   "#0d4f6e", "#2a9d8f", 0],
  [150, "nuvole",  "#1d5f93", "#7cc4e8", 0],
  [400, "notte",   "#070d28", "#1c2c63", 0.6],
  [800, "spazio",  "#010208", "#0a0620", 1],
];
const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const hex = c => "#" + c.map(v => Math.round(v).toString(16).padStart(2, "0")).join("");
const tinte = (a, b, t) => hex(rgb(a).map((v, i) => mescola(v, rgb(b)[i], t)));
function sfondo(metri){
  const m = Math.max(0, Number(metri) || 0);
  let i = 0; while (i + 1 < TAPPE.length && m >= TAPPE[i + 1][0]) i++;
  const t = TAPPE[i], prossima = TAPPE[i + 1];
  // negli ultimi 60 m prima di un cambio il cielo sfuma verso il successivo
  const k = prossima ? lim((m - (prossima[0] - 60)) / 60, 0, 1) : 0;
  return prossima && k > 0
    ? {nome:t[1], cima:tinte(t[2], prossima[2], k), fondo:tinte(t[3], prossima[3], k), stelle:mescola(t[4], prossima[4], k)}
    : {nome:t[1], cima:t[2], fondo:t[3], stelle:t[4]};
}

// aggiunge piattaforme (e ogni tanto una molla, un mostro, un razzo) fino sopra lo schermo, toglie quelle rimaste sotto
function riempi(s, caso){
  const tetto = s.cam + s.a + OLTRE;
  while (s.alto < tetto){
    const alt = s.alto - BASE_Y, d = difficolta(alt);
    const gap = lim(mescola(GAP_MIN, GAP_MAX, d) * (0.7 + 0.3 * caso()), 30, GAP_MAX);
    const y = s.alto + gap, w = Math.round(mescola(74, 50, d));
    const r = caso(), pF = alt > DA_FRAGILI ? 0.06 + 0.2 * d : 0, pM = alt > DA_MOBILI ? 0.08 + 0.22 * d : 0;
    const tipo = r < pF && s.ultimo !== "fragile" ? "fragile" : r < pF + pM ? "mobile" : "fissa";
    const p = {x:w / 2 + caso() * (s.l - w), y, w, tipo, rotta:false};
    if (tipo === "mobile"){
      p.amp = Math.min(70, (s.l - w) / 2); p.x0 = lim(p.x, w / 2 + p.amp, s.l - w / 2 - p.amp); p.x = p.x0;
      p.vel = 0.8 + 1.4 * caso(); p.fase = caso() * 6.28;
    }
    if (tipo === "fissa" && alt > DA_MOLLE && caso() < 0.07) p.molla = {dx:(caso() - 0.5) * w * 0.5};
    if (tipo === "fissa" && alt > DA_RAZZI && caso() < 0.025) s.razzi.push({x:p.x, y:y + 14, preso:false});
    else if (alt > DA_MOSTRI && caso() < 0.08 + 0.25 * d){
      const amp = Math.min(60, s.l / 4), x0 = lim(caso() * s.l, R_MOSTRO + amp, s.l - R_MOSTRO - amp);
      s.mostri.push({x:x0, x0, amp, y:(s.alto + y) / 2, vel:1 + 1.5 * caso(), fase:caso() * 6.28, vivo:true});
    }
    s.piatt.push(p); s.alto = y; s.ultimo = tipo;
  }
  const sotto = s.cam - 200;
  s.piatt = s.piatt.filter(p => p.y > sotto); s.mostri = s.mostri.filter(m => m.y > sotto); s.razzi = s.razzi.filter(r => r.y > sotto);
  return s;
}
function generaPiattaforme(stato, caso = Math.random){ return riempi(copia(stato), caso); }

// una partita nuova su uno schermo largo l e alto a: si parte da una base larga quanto lo schermo
function nuovaPartita(l, a, caso = Math.random){
  const s = {l, a, t:0, x:l / 2, y:BASE_Y, vy:V_SALTO, dir:1, cam:0, alto:BASE_Y, ultimo:"fissa", razzo:0, massimo:BASE_Y, punti:0,
    finito:false, causa:null, piatt:[{x:l / 2, y:BASE_Y, w:l, tipo:"fissa", rotta:false}], mostri:[], razzi:[], eventi:[]};
  return riempi(s, caso);
}
const metriDi = s => Math.max(0, Math.floor((s.massimo - BASE_Y) / PX_METRO));
const finita = s => !!s.finito || s.y < s.cam - MARGINE;

function passo(s, h, x, caso){
  s.t += h;
  for (const p of s.piatt){
    if (p.tipo === "mobile" && !p.rotta) p.x = p.x0 + Math.sin(s.t * p.vel + p.fase) * p.amp;
    if (p.rotta){ p.cade = (p.cade || 0) + G * 0.6 * h; p.y -= p.cade * h; }
  }
  for (const m of s.mostri) if (m.vivo) m.x = m.x0 + Math.sin(s.t * m.vel + m.fase) * m.amp;
  // di lato: il dito dice dove vuole la figura; uscendo da una parte si rientra dall'altra
  if (Number.isFinite(x)){ if (Math.abs(x - s.x) > 0.5) s.dir = x > s.x ? 1 : -1; s.x = giro(x, s.l); }
  const y0 = s.y, conRazzo = s.razzo > 0;
  if (conRazzo){ s.razzo -= h; s.vy = V_RAZZO; } else s.vy -= G * h;
  s.y += s.vy * h;
  // si rimbalza solo scendendo, e solo sopra una piattaforma intera; mai da sotto
  if (!conRazzo && s.vy < 0){
    let top = null;
    for (const p of s.piatt) if (!p.rotta && y0 >= p.y && s.y <= p.y && distX(s.x, p.x, s.l) <= p.w / 2 + RP * 0.6 && (!top || p.y > top.y)) top = p;
    if (top){
      s.y = top.y;
      if (top.molla && distX(s.x, top.x + top.molla.dx, s.l) <= 16){ s.vy = V_MOLLA; s.eventi.push({tipo:"molla", x:s.x, y:s.y}); }
      else { s.vy = V_SALTO; s.eventi.push({tipo:"salto", x:s.x, y:s.y}); }
      if (top.tipo === "fragile"){ top.rotta = true; top.cade = 0; s.eventi.push({tipo:"rompe", x:top.x, y:top.y}); }
    }
  }
  for (const r of s.razzi) if (!r.preso && distX(s.x, r.x, s.l) < 28 && Math.abs(s.y + RP - r.y) < 34){
    r.preso = true; s.razzo = T_RAZZO; s.eventi.push({tipo:"razzo", x:r.x, y:r.y});
  }
  for (const m of s.mostri){
    if (!m.vivo || s.razzo > 0) continue;
    if (distX(s.x, m.x, s.l) < R_MOSTRO + RP * 0.7 && s.y < m.y + R_MOSTRO && s.y + 2 * RP > m.y - R_MOSTRO){
      if (s.vy < 0 && y0 >= m.y){ m.vivo = false; s.vy = V_SALTO * 1.05; s.eventi.push({tipo:"schiaccia", x:m.x, y:m.y}); }
      else { s.finito = true; s.causa = "mostro"; s.eventi.push({tipo:"morte", causa:"mostro"}); return; }
    }
  }
  s.cam = Math.max(s.cam, s.y - s.a * 0.4); s.massimo = Math.max(s.massimo, s.y); s.punti = metriDi(s);
  if (s.y < s.cam - MARGINE){ s.finito = true; s.causa = "caduto"; s.eventi.push({tipo:"morte", causa:"caduto"}); }
}
// avanza di dt secondi (a passi di 1/60 s, al massimo 1/10 di secondo per volta); x è dove il dito vuole la figura (px, anche fuori
// dallo schermo: rientra dall'altra parte), o niente; caso() fa le piattaforme nuove
function avanza(stato, dt, x, caso = Math.random){
  if (finita(stato) || !(dt > 0)) return stato;
  const s = copia(stato);
  let resto = Math.min(dt, 0.1);
  while (resto > 1e-9 && !s.finito){ const h = Math.min(resto, PASSO); passo(s, h, x, caso); resto -= h; }
  return riempi(s, caso);
}

export const logica = {G, V_SALTO, V_MOLLA, V_RAZZO, T_RAZZO, H_SALTO, H_MOLLA, GAP_MIN, GAP_MAX, SALITA, BASE_Y, PX_METRO, RP, R_MOSTRO,
  DA_FRAGILI, DA_MOBILI, DA_MOLLE, DA_MOSTRI, DA_RAZZI, PER_GETTONE, MASSIMO,
  gettoni, sfondo, difficolta, nuovaPartita, generaPiattaforme, avanza, finita, metriDi};

// ══ il gioco nello strato: un canvas che riempie il campo
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4"), mostro:"#ff4d6d", fragile:"#b9835a"};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:pointer";
  cv.setAttribute("aria-label", "In alto!: trascina il dito a destra e a sinistra per guidare il salto");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = null, fase = "pronto", raf = 0, prima = 0, timerFine = 0, fermo = false, dpr = 1, trascina = null, pendente = 0;
  const tasti = {sx:false, dx:false}, scritte = {punti:-1, tempo:""}, scintille = [];
  const nuvole = Array.from({length:7}, () => ({x:Math.random(), y:Math.random(), r:26 + Math.random() * 30}));
  const stelle = Array.from({length:90}, () => ({x:Math.random(), y:Math.random(), v:0.3 + Math.random() * 0.7}));

  function misura(){
    const r = campo.getBoundingClientRect(), l = Math.max(240, r.width || 390), a = Math.max(360, r.height || 700);
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(l * dpr); cv.height = Math.round(a * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    s = s && fase !== "pronto" ? {...s, l, a} : nuovaPartita(l, a);
  }
  misura();

  const ripresa = () => { prima = 0; };
  function pausa(){ if (fase !== "gioco") return; fase = "pausa"; trascina = null; api.esito("In pausa: tocca lo schermo per riprendere."); }
  function riprendi(){ if (fase !== "pausa" && fase !== "pronto") return; fase = "gioco"; ripresa(); api.esito("Trascina il dito a destra e a sinistra: salti da solo."); }
  const sulBottonePausa = (x, y) => x > s.l - 64 && y < 64;

  function giu(e){
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (fase === "fine") return;
    if (fase !== "gioco") riprendi();
    else if (sulBottonePausa(x, y)){ pausa(); return; }
    trascina = {id:e.pointerId, ultimo:e.clientX};
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  }
  function sposta(e){
    if (!trascina || e.pointerId !== trascina.id || fase !== "gioco") return;
    pendente += (e.clientX - trascina.ultimo) * 1.5; trascina.ultimo = e.clientX; e.preventDefault();
  }
  function su(e){ if (trascina && e.pointerId === trascina.id) trascina = null; }
  function tasto(e){
    const premuto = e.type === "keydown";
    if (e.key === "ArrowLeft"){ tasti.sx = premuto; e.preventDefault(); }
    else if (e.key === "ArrowRight"){ tasti.dx = premuto; e.preventDefault(); }
    else if (premuto && (e.key === " " || e.key === "p" || e.key === "P")){ if (fase === "gioco") pausa(); else if (fase !== "fine") riprendi(); e.preventDefault(); }
  }
  const visibile = () => { if (document.hidden) pausa(); };
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => misura()) : null;
  if (ro) ro.observe(campo); else window.addEventListener("resize", misura);
  cv.addEventListener("pointerdown", giu); cv.addEventListener("pointermove", sposta);
  cv.addEventListener("pointerup", su); cv.addEventListener("pointercancel", su);
  window.addEventListener("keydown", tasto); window.addEventListener("keyup", tasto);
  document.addEventListener("visibilitychange", visibile);

  function racconta(eventi){
    for (const e of eventi){
      if (e.tipo === "molla"){ api.esito("Boing! Una molla!"); for (let i = 0; i < 10; i++) scintille.push({x:e.x, y:e.y, vx:(Math.random() - 0.5) * 220, vy:-60 - Math.random() * 120, vita:0.5, colore:C.oro}); }
      else if (e.tipo === "rompe") for (let i = 0; i < 8; i++) scintille.push({x:e.x + (Math.random() - 0.5) * 40, y:e.y, vx:(Math.random() - 0.5) * 120, vy:-40 - Math.random() * 80, vita:0.6, colore:C.fragile});
      else if (e.tipo === "schiaccia"){ api.esito("Mostro schiacciato!"); for (let i = 0; i < 12; i++) scintille.push({x:e.x, y:e.y, vx:(Math.random() - 0.5) * 260, vy:(Math.random() - 0.5) * 260, vita:0.6, colore:C.mostro}); }
      else if (e.tipo === "razzo") api.esito("Un razzo! Si vola!");
      else if (e.tipo === "morte") api.esito(e.causa === "mostro" ? "Un mostro ti ha preso!" : "Sei caduto!");
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `${s.punti} m · ${sfondo(s.punti).nome}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }

  const sy = y => s.a - (y - s.cam);            // dal mondo (y in su) allo schermo (y in giù)
  function pillola(x, y, w, h, r){
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
  }
  function personaggio(x, y){
    const dir = s.dir || 1, vola = s.razzo > 0;
    if (vola){ ctx.fillStyle = C.oro; ctx.beginPath(); ctx.moveTo(x - 8, y - 2); ctx.lineTo(x, y + 26 + Math.random() * 14); ctx.lineTo(x + 8, y - 2); ctx.fill();
      ctx.fillStyle = "#ff6b35"; ctx.beginPath(); ctx.moveTo(x - 4, y - 2); ctx.lineTo(x, y + 14 + Math.random() * 8); ctx.lineTo(x + 4, y - 2); ctx.fill(); }
    const squash = s.vy > 0 ? 1.08 : 0.94;
    ctx.save(); ctx.translate(x, y - RP); ctx.scale(1 / squash, squash);
    ctx.fillStyle = C.oro; ctx.shadowColor = C.oro; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(0, 0, RP, 0, 6.29); ctx.fill(); ctx.shadowBlur = 0;
    ctx.fillStyle = "#050d18"; ctx.beginPath(); ctx.arc(-5 + dir * 3, -4, 3.2, 0, 6.29); ctx.arc(6 + dir * 3, -4, 3.2, 0, 6.29); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(-4 + dir * 4, -5, 1.1, 0, 6.29); ctx.arc(7 + dir * 4, -5, 1.1, 0, 6.29); ctx.fill();
    ctx.strokeStyle = "#050d18"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(dir * 2, 3, 5, 0.15 * 3.14, 0.85 * 3.14); ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = C.accento; ctx.lineWidth = 3; ctx.lineCap = "round"; ctx.beginPath();
    ctx.moveTo(x - 6, y - 2); ctx.lineTo(x - 7, y + 3); ctx.moveTo(x + 6, y - 2); ctx.lineTo(x + 7, y + 3); ctx.stroke();
  }
  function mostro(m){
    const x = m.x, y = sy(m.y), ali = Math.sin(s.t * 14) * 8;
    ctx.fillStyle = "rgba(255,77,109,.55)"; ctx.beginPath(); ctx.ellipse(x - 22, y - 4, 14, 7 + ali * 0.4, -0.4, 0, 6.29); ctx.ellipse(x + 22, y - 4, 14, 7 + ali * 0.4, 0.4, 0, 6.29); ctx.fill();
    ctx.fillStyle = C.mostro; ctx.shadowColor = C.mostro; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(x, y, R_MOSTRO, 0, 6.29); ctx.fill(); ctx.shadowBlur = 0;
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x - 7, y - 4, 6, 0, 6.29); ctx.arc(x + 7, y - 4, 6, 0, 6.29); ctx.fill();
    ctx.fillStyle = "#050d18"; ctx.beginPath(); ctx.arc(x - 6, y - 3, 2.6, 0, 6.29); ctx.arc(x + 8, y - 3, 2.6, 0, 6.29); ctx.fill();
    ctx.strokeStyle = "#050d18"; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(x - 10, y - 12); ctx.lineTo(x - 3, y - 9); ctx.moveTo(x + 10, y - 12); ctx.lineTo(x + 3, y - 9); ctx.stroke();
  }
  function razzoFermo(r){
    const x = r.x, y = sy(r.y);
    ctx.fillStyle = "#e6f6ff"; ctx.beginPath(); ctx.moveTo(x, y - 18); ctx.quadraticCurveTo(x + 10, y - 4, x + 8, y + 10); ctx.lineTo(x - 8, y + 10); ctx.quadraticCurveTo(x - 10, y - 4, x, y - 18); ctx.fill();
    ctx.fillStyle = C.mostro; ctx.beginPath(); ctx.moveTo(x - 8, y + 4); ctx.lineTo(x - 15, y + 14); ctx.lineTo(x - 6, y + 10); ctx.moveTo(x + 8, y + 4); ctx.lineTo(x + 15, y + 14); ctx.lineTo(x + 6, y + 10); ctx.fill();
    ctx.fillStyle = C.accento; ctx.beginPath(); ctx.arc(x, y - 3, 4, 0, 6.29); ctx.fill();
  }
  function piattaforma(p){
    const x = p.x - p.w / 2, y = sy(p.y), colore = p.tipo === "mobile" ? C.oro : p.tipo === "fragile" ? C.fragile : C.accento;
    ctx.fillStyle = colore; pillola(x, y, p.w, 12, 6); ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,.28)"; pillola(x + 4, y + 2, p.w - 8, 3, 1.5); ctx.fill();
    if (p.tipo === "fragile"){ ctx.strokeStyle = "#050d18"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(p.x - 8, y); ctx.lineTo(p.x - 3, y + 7); ctx.lineTo(p.x - 9, y + 12); ctx.moveTo(p.x + 10, y); ctx.lineTo(p.x + 5, y + 6); ctx.lineTo(p.x + 11, y + 12); ctx.stroke(); }
    if (p.molla){ const mx = p.x + p.molla.dx; ctx.strokeStyle = "#e6f6ff"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(mx - 8, y);
      for (let i = 0; i < 4; i++){ ctx.lineTo(mx + (i % 2 ? -8 : 8), y - 4 - i * 4); } ctx.stroke();
      ctx.fillStyle = C.mostro; pillola(mx - 11, y - 24, 22, 7, 3); ctx.fill(); }
  }

  function disegna(dt){
    const {l, a} = s, cielo = sfondo(s.punti);
    const gr = ctx.createLinearGradient(0, 0, 0, a); gr.addColorStop(0, cielo.cima); gr.addColorStop(1, cielo.fondo);
    ctx.fillStyle = gr; ctx.fillRect(0, 0, l, a);
    if (cielo.stelle > 0){ ctx.fillStyle = "#e6f6ff";
      for (const st of stelle){ ctx.globalAlpha = cielo.stelle * (0.3 + st.v * 0.7); const py = giro(st.y * a + s.cam * 0.08 * st.v, a); ctx.fillRect(st.x * l, py, st.v * 2.2, st.v * 2.2); } ctx.globalAlpha = 1; }
    if (cielo.nome === "nuvole" || cielo.nome === "prato"){ ctx.fillStyle = "rgba(255,255,255,.16)";
      for (const n of nuvole){ const py = giro(n.y * (a + 120) + s.cam * 0.3, a + 120) - 60, px = n.x * l;
        ctx.beginPath(); ctx.arc(px, py, n.r, 0, 6.29); ctx.arc(px + n.r * 0.9, py + 6, n.r * 0.7, 0, 6.29); ctx.arc(px - n.r * 0.9, py + 8, n.r * 0.6, 0, 6.29); ctx.fill(); } }
    // il prato in fondo, finché si vede
    const terra = sy(BASE_Y);
    if (terra < a + 40){ ctx.fillStyle = "#14532d"; ctx.fillRect(0, terra, l, a - terra + 40);
      ctx.fillStyle = "#1f7a45"; ctx.beginPath(); ctx.ellipse(l * 0.25, terra + 18, l * 0.5, 34, 0, Math.PI, 0); ctx.ellipse(l * 0.85, terra + 18, l * 0.45, 26, 0, Math.PI, 0); ctx.fill(); }
    for (const p of s.piatt) if (p.y > s.cam - 40 && p.y < s.cam + a + 40 && !(p.y === BASE_Y && p.w === l)) piattaforma(p);
    for (const r of s.razzi) if (!r.preso) razzoFermo(r);
    for (const m of s.mostri) if (m.vivo) mostro(m);
    const py = sy(s.y);
    if (!(s.causa === "caduto" && py > a + 40)){ personaggio(s.x, py); if (s.x < RP + 2) personaggio(s.x + l, py); else if (s.x > l - RP - 2) personaggio(s.x - l, py); }
    for (const p of scintille){ p.x += p.vx * dt; p.y -= p.vy * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, p.vita / 0.6); ctx.fillStyle = p.colore; ctx.fillRect(p.x - 2, sy(p.y) - 2, 4, 4); }
    for (let i = scintille.length - 1; i >= 0; i--) if (scintille[i].vita <= 0) scintille.splice(i, 1);
    ctx.globalAlpha = 1;
    if (fase === "gioco"){ ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(l - 54, 10, 44, 44); ctx.fillStyle = C.tenue; ctx.fillRect(l - 40, 22, 6, 20); ctx.fillRect(l - 30, 22, 6, 20); }
    if (fase === "pronto" || fase === "pausa"){
      const [titolo, riga] = fase === "pronto" ? ["In alto!", "Tocca per partire"] : ["Pausa", "Tocca per riprendere"];
      ctx.fillStyle = "rgba(5,13,24,.78)"; ctx.fillRect(0, a / 2 - 80, l, 160);
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 30px ${TITOLI}`; ctx.fillText(titolo, l / 2, a / 2 - 26);
      ctx.fillStyle = C.tenue; ctx.font = `500 17px ${MONO}`; ctx.fillText(riga, l / 2, a / 2 + 16);
      if (fase === "pronto"){ ctx.font = `400 13px ${MONO}`; ctx.fillText("Trascina il dito a destra e a sinistra", l / 2, a / 2 + 46); }
    }
  }

  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (fase === "gioco" && dt > 0){
      let x = s.x + pendente; pendente = 0;
      if (tasti.sx !== tasti.dx) x += (tasti.dx ? 420 : -420) * dt;
      s = avanza(s, dt, x); racconta(s.eventi); scriviBarra();
      if (s.finito){ fase = "fine"; trascina = null; timerFine = setTimeout(() => { if (!fermo) api.fine(s.punti); }, 1200); }
    }
    disegna(dt);
    raf = requestAnimationFrame(fotogramma);
  }
  api.punti(0); scriviBarra(); api.esito("Tocca lo schermo per partire.");
  raf = requestAnimationFrame(fotogramma);

  return {
    ferma(){
      fermo = true; cancelAnimationFrame(raf); clearTimeout(timerFine);
      if (ro) ro.disconnect(); else window.removeEventListener("resize", misura);
      cv.removeEventListener("pointerdown", giu); cv.removeEventListener("pointermove", sposta);
      cv.removeEventListener("pointerup", su); cv.removeEventListener("pointercancel", su);
      window.removeEventListener("keydown", tasto); window.removeEventListener("keyup", tasto);
      document.removeEventListener("visibilitychange", visibile);
    },
    get punti(){ return s.punti; },
  };
}

export const gioco = {
  id:"inalto", nome:"In alto!", cabinato:{schermo:"IN ALTO", colore:"#48CAE4"},
  regole:"Il tuo personaggino salta da solo di piattaforma in piattaforma: trascina il dito a destra e a sinistra per guidarlo (uscendo da un lato rientri dall'altro). Rimbalzi solo cadendo su una piattaforma, mai da sotto. Alcune si muovono, altre si sbriciolano dopo un salto; le molle ti lanciano altissimo. Più in alto incontri mostri volanti: evitali, o schiacciali saltandoci sopra. Se vedi un razzo, prendilo! Più sali, più le piattaforme sono rade, e lo sfondo cambia con l'altezza. Se cadi sotto il bordo dello schermo è finita. Un punto per ogni metro; un gettone ogni 100 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
