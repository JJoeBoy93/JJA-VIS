// ── Assalto dallo spazio (Sala giochi): sparatutto a scorrimento, col telefono in verticale.
//   La navicella in basso spara da sola in su; si muove trascinando il dito (o con le frecce).
//   Scendono ondate di nemici: 👾 lento (10 punti), 🛸 a zig-zag (20), 👽 che spara (30). Ogni 4 ondate un capo 🐙 (200).
//   3 vite; dopo un colpo si è intoccabili per 1,5 s. Un bonus raro 🛡️ dà lo scudo per 5 s.
//   La difficoltà cresce con le ondate (più nemici, più fitti, più veloci) e col tempo (tutto un po' più svelto).
// Gettoni: un gettone ogni 40 punti, al massimo 25.
// Il mondo è in pixel CSS del campo (x verso destra, y verso il basso); lo stato è un oggetto semplice che `avanza` non
// tocca mai: ne restituisce uno nuovo. Le prove: collaudo/giochi/spazio.mjs.

const PUNTI = {lento:10, zigzag:20, sparo:30, capo:200};
const R = {nave:18, lento:16, zigzag:15, sparo:17, capo:46, colpo:4, spari:5, bonus:14};   // i raggi, per le collisioni
const VEL = {lento:70, zigzag:85, sparo:60};                                                 // pixel al secondo, all'ondata 1
const VITE = 3, SCUDO = 5, INVULN = 1.5, CADENZA = 0.2, OGNI_CAPO = 4, PAUSA_ONDATA = 1.6, PROB_BONUS = 0.05;
const VEL_COLPO = 620, VEL_SPARI = 240, VEL_BONUS = 110, AMPIEZZA = 50, PASSO = 1 / 60, DAL_FONDO = 80, PER_GETTONE = 40;

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const limita = (v, a, b) => Math.max(a, Math.min(b, v));
// l'ondata n (da 1): i nemici in ordine d'arrivo, il ritmo d'arrivo in secondi, la velocità; ogni 4 un capo con la sua vita
function prossimaOndata(n){
  n = Math.max(1, Math.floor(Number(n) || 1));
  const velocita = Math.min(2.2, 1 + 0.1 * (n - 1));
  if (n % OGNI_CAPO === 0) return {n, capo:true, vita:30 + 15 * (n / OGNI_CAPO - 1), velocita, nemici:[], ritmo:0};
  const nemici = Array.from({length:Math.min(24, 5 + 2 * n)}, (_, i) => (n >= 3 && i % 3 === 2 ? "sparo" : n >= 2 && i % 2 === 1 ? "zigzag" : "lento"));
  return {n, capo:false, vita:0, velocita, nemici, ritmo:Math.max(0.3, 1 - 0.06 * (n - 1))};
}
// col passare dei secondi tutto va un po' più svelto: +60% dopo 5 minuti
const spinta = t => 1 + Math.min(0.6, Math.max(0, t) / 300);
const velocita = s => prossimaOndata(s.ondata).velocita * spinta(s.t);
const gettoni = p => Math.min(25, Math.floor(Math.max(0, Number(p) || 0) / PER_GETTONE));

function nuovaPartita(l = 390, a = 700){
  const o = prossimaOndata(1);
  return {l, a, t:0, punti:0, vite:VITE, finito:false, ondata:1, coda:o.nemici.slice(), capoDaFare:o.capo, attesa:PAUSA_ONDATA,
    nave:{x:l / 2, y:a - DAL_FONDO}, ricarica:0, colpi:[], nemici:[], spari:[], bonus:[], capo:null, scudoFino:0, invulnFino:0, eventi:[]};
}
const copia = s => ({...s, nave:{...s.nave}, coda:s.coda.slice(), colpi:s.colpi.map(o => ({...o})), nemici:s.nemici.map(o => ({...o})),
  spari:s.spari.map(o => ({...o})), bonus:s.bonus.map(o => ({...o})), capo:s.capo && {...s.capo}, eventi:[]});
const tocca = (p, rp, q, rq) => { const dx = p.x - q.x, dy = p.y - q.y, r = rp + rq; return dx * dx + dy * dy <= r * r; };
const scudo = s => s.t < s.scudoFino;
const intoccabile = s => scudo(s) || s.t < s.invulnFino;

// la navicella va a x (dentro lo schermo)
const muovi = (s, x) => (Number.isFinite(x) ? {...s, nave:{...s.nave, x:limita(x, R.nave, s.l - R.nave)}} : s);
// il campo ha cambiato misura: la navicella resta in basso e dentro
const ridimensiona = (s, l, a) => { const n = {...s, l, a, nave:{...s.nave, y:a - DAL_FONDO}}; return muovi(n, n.nave.x); };

// un colpo alla navicella: con lo scudo o appena colpiti non succede niente; se no una vita in meno, e a zero la partita è finita
function ferisci(s){
  if (s.finito || intoccabile(s)) return false;
  s.vite = Math.max(0, s.vite - 1); s.invulnFino = s.t + INVULN; s.eventi.push({tipo:"ahi", x:s.nave.x, y:s.nave.y});
  if (s.vite === 0){ s.finito = true; s.eventi.push({tipo:"fine"}); }
  return true;
}
function colpito(stato){ const s = copia(stato); ferisci(s); return s; }

function passo(s, h, caso){
  s.t += h;
  const v = velocita(s), onda = prossimaOndata(s.ondata);
  // la navicella spara da sola
  s.ricarica -= h;
  if (s.ricarica <= 0){ s.colpi.push({x:s.nave.x, y:s.nave.y - R.nave}); s.ricarica += CADENZA; }
  for (const c of s.colpi) c.y -= VEL_COLPO * h;
  // gli arrivi: un nemico ogni «ritmo» secondi, o il capo
  s.attesa -= h;
  if (s.attesa <= 0){
    if (s.capoDaFare){ s.capoDaFare = false; s.capo = {x:s.l / 2, y:-R.capo, vita:onda.vita, max:onda.vita, dir:1, ricarica:2}; s.eventi.push({tipo:"capo"}); }
    else if (s.coda.length){
      const tipo = s.coda.shift(), m = R[tipo] + 8 + (tipo === "zigzag" ? AMPIEZZA : 0);
      const x = s.l > 2 * m ? m + caso() * (s.l - 2 * m) : s.l / 2;
      s.nemici.push({tipo, x, x0:x, y:-R[tipo], fase:caso() * 6.28, ricarica:1 + caso() * 1.5});
      s.attesa = onda.ritmo;
    }
  }
  for (const n of s.nemici){
    n.y += VEL[n.tipo] * v * h;
    if (n.tipo === "zigzag"){ n.fase += 3 * h; n.x = n.x0 + Math.sin(n.fase) * AMPIEZZA; }
    if (n.tipo === "sparo" && n.y > 0 && n.y < s.nave.y - 120){
      n.ricarica -= h;
      if (n.ricarica <= 0){ s.spari.push({x:n.x, y:n.y + R.sparo, vx:0, vy:VEL_SPARI * v}); n.ricarica = Math.max(0.8, 2.2 / v) + caso(); }
    }
  }
  if (s.capo){
    const c = s.capo;
    if (c.y < 110) c.y = Math.min(110, c.y + 60 * h);
    else {
      c.x += c.dir * 70 * v * h;
      if (c.x > s.l - R.capo){ c.x = s.l - R.capo; c.dir = -1; }
      if (c.x < R.capo){ c.x = R.capo; c.dir = 1; }
      c.ricarica -= h;
      if (c.ricarica <= 0){ for (const vx of [-90, 0, 90]) s.spari.push({x:c.x, y:c.y + R.capo * 0.6, vx, vy:VEL_SPARI * v}); c.ricarica = Math.max(0.7, 1.6 / v); }
    }
  }
  for (const p of s.spari){ p.x += p.vx * h; p.y += p.vy * h; }
  for (const b of s.bonus) b.y += VEL_BONUS * h;
  // i colpi della navicella
  for (const c of s.colpi){
    for (const n of s.nemici) if (!n.via && tocca(c, R.colpo, n, R[n.tipo])){
      c.via = n.via = true; s.punti += PUNTI[n.tipo]; s.eventi.push({tipo:"boom", x:n.x, y:n.y, chi:n.tipo});
      if (caso() < PROB_BONUS) s.bonus.push({x:n.x, y:n.y});
      break;
    }
    if (!c.via && s.capo && tocca(c, R.colpo, s.capo, R.capo)){
      c.via = true; s.capo.vita--; s.eventi.push({tipo:"tac", x:c.x, y:c.y});
      if (s.capo.vita <= 0){ s.punti += PUNTI.capo; s.eventi.push({tipo:"boom", x:s.capo.x, y:s.capo.y, chi:"capo"}); s.bonus.push({x:s.capo.x, y:s.capo.y}); s.capo = null; }
    }
  }
  // quello che tocca la navicella
  const nave = s.nave;
  for (const p of s.spari) if (tocca(p, R.spari, nave, R.nave * 0.8)){ p.via = true; ferisci(s); }
  for (const n of s.nemici) if (!n.via && tocca(n, R[n.tipo], nave, R.nave * 0.8)){ n.via = true; s.eventi.push({tipo:"boom", x:n.x, y:n.y, chi:n.tipo}); ferisci(s); }
  if (s.capo && tocca(s.capo, R.capo * 0.8, nave, R.nave * 0.8)) ferisci(s);
  for (const b of s.bonus) if (tocca(b, R.bonus, nave, R.nave)){ b.via = true; s.scudoFino = s.t + SCUDO; s.eventi.push({tipo:"scudo"}); }
  // via quello che è finito o uscito dallo schermo
  s.colpi = s.colpi.filter(c => !c.via && c.y > -20);
  s.nemici = s.nemici.filter(n => !n.via && n.y < s.a + 30);
  s.spari = s.spari.filter(p => !p.via && p.y < s.a + 20 && p.x > -20 && p.x < s.l + 20);
  s.bonus = s.bonus.filter(b => !b.via && b.y < s.a + 20);
  // ondata finita: la prossima
  if (!s.capo && !s.capoDaFare && !s.coda.length && !s.nemici.length){
    const o = prossimaOndata(++s.ondata); s.coda = o.nemici.slice(); s.capoDaFare = o.capo; s.attesa = PAUSA_ONDATA;
    s.eventi.push({tipo:"ondata", n:s.ondata});
  }
}
// avanza di dt secondi (a passi di 1/60 s, al massimo 1/4 di secondo per volta); caso() fa gli arrivi e i bonus
function avanza(stato, dt, caso = Math.random){
  if (stato.finito || !(dt > 0)) return stato;
  const s = copia(stato);
  let resto = Math.min(dt, 0.25);
  while (resto > 1e-9 && !s.finito){ const h = Math.min(resto, PASSO); passo(s, h, caso); resto -= h; }
  return s;
}

export const logica = {PUNTI, R, VEL, VITE, SCUDO, INVULN, CADENZA, OGNI_CAPO, PAUSA_ONDATA, PER_GETTONE,
  prossimaOndata, spinta, velocita, gettoni, nuovaPartita, muovi, ridimensiona, colpito, avanza, tocca, scudo, intoccabile};

// ══ il gioco nello strato: un canvas che riempie il campo
const FIGURA = {lento:"👾", zigzag:"🛸", sparo:"👽", capo:"🐙", bonus:"🛡️"};
const EMOJI = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",system-ui,sans-serif';
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4"), fondo:"#050d18", nemico:"#ff4d6d"};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:pointer";
  cv.setAttribute("aria-label", "Assalto dallo spazio: trascina il dito per muovere la navicella");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = null, fase = "pronto", raf = 0, prima = 0, timerFine = 0, fermo = false, dpr = 1;
  let trascina = null, tasti = {sx:false, dx:false}, particelle = [], scritte = {punti:-1, tempo:""};
  const stelle = Array.from({length:80}, () => ({x:Math.random(), y:Math.random(), v:0.2 + Math.random() * 0.8}));

  // le emoji si disegnano una volta in un canvas piccolo, poi si copiano
  const sprite = new Map();
  function figura(e, lato){
    const k = e + lato + "@" + dpr; if (sprite.has(k)) return sprite.get(k);
    const c = document.createElement("canvas"); c.width = c.height = Math.ceil(lato * 1.3 * dpr);
    const x = c.getContext("2d"); x.scale(dpr, dpr); x.font = `${lato}px ${EMOJI}`; x.textAlign = "center"; x.textBaseline = "middle";
    x.fillText(e, lato * 0.65, lato * 0.7); sprite.set(k, c); return c;
  }
  const metti = (e, lato, x, y) => { const c = figura(e, lato), w = c.width / dpr; ctx.drawImage(c, x - w / 2, y - w / 2, w, w); };

  function misura(){
    const r = campo.getBoundingClientRect(), l = Math.max(240, r.width || 390), a = Math.max(360, r.height || 700);
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(l * dpr); cv.height = Math.round(a * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    s = s ? ridimensiona(s, l, a) : nuovaPartita(l, a);
  }
  misura();

  const ripresa = () => { prima = 0; };
  function pausa(){ if (fase !== "gioco") return; fase = "pausa"; trascina = null; api.esito("In pausa: tocca lo schermo per riprendere."); }
  function riprendi(){ if (fase !== "pausa" && fase !== "pronto") return; fase = "gioco"; ripresa(); api.esito("Trascina il dito per muoverti: la navicella spara da sola."); }
  const sulBottonePausa = (x, y) => x > s.l - 64 && y < 64;

  function giu(e){
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (fase === "fine") return;
    if (fase !== "gioco"){ riprendi(); }
    else if (sulBottonePausa(x, y)){ pausa(); return; }
    trascina = {id:e.pointerId, x0:e.clientX, nave0:s.nave.x};
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  }
  function sposta(e){
    if (!trascina || e.pointerId !== trascina.id || fase !== "gioco") return;
    s = muovi(s, trascina.nave0 + (e.clientX - trascina.x0) * 1.3); e.preventDefault();
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
      if (e.tipo === "boom"){ const tanti = e.chi === "capo" ? 40 : 14;
        for (let i = 0; i < tanti; i++){ const ang = Math.random() * 6.28, v = 40 + Math.random() * (e.chi === "capo" ? 260 : 160);
          particelle.push({x:e.x, y:e.y, vx:Math.cos(ang) * v, vy:Math.sin(ang) * v, vita:0.6, colore:i % 2 ? C.oro : C.accento}); } }
      else if (e.tipo === "tac") particelle.push({x:e.x, y:e.y, vx:0, vy:-40, vita:0.2, colore:C.oro});
      else if (e.tipo === "ahi") api.esito(s.vite ? `Colpito! Ti restano ${s.vite} ${s.vite === 1 ? "vita" : "vite"}.` : "Colpito!");
      else if (e.tipo === "scudo") api.esito("🛡️ Scudo per 5 secondi!");
      else if (e.tipo === "capo") api.esito("Arriva il capo: tieni duro!");
      else if (e.tipo === "ondata") api.esito(prossimaOndata(e.n).capo ? `Ondata ${e.n}: qualcosa di grosso si avvicina…` : `Ondata ${e.n}!`);
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `Ondata ${s.ondata} · ${"❤️".repeat(s.vite)}${"🖤".repeat(Math.max(0, VITE - s.vite))}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }

  function disegna(dt){
    const {l, a} = s;
    ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, l, a);
    ctx.fillStyle = C.tenue;
    for (const st of stelle){ st.y += st.v * dt * (fase === "gioco" ? 0.12 : 0.02); if (st.y > 1) { st.y -= 1; st.x = Math.random(); }
      ctx.globalAlpha = 0.25 + st.v * 0.6; ctx.fillRect(st.x * l, st.y * a, st.v * 2, st.v * 2); }
    ctx.globalAlpha = 1;
    // colpi
    ctx.fillStyle = C.oro; ctx.shadowColor = C.oro; ctx.shadowBlur = 8;
    for (const c of s.colpi) ctx.fillRect(c.x - 1.5, c.y - 6, 3, 12);
    ctx.fillStyle = C.nemico; ctx.shadowColor = C.nemico;
    for (const p of s.spari){ ctx.beginPath(); ctx.arc(p.x, p.y, R.spari, 0, 6.29); ctx.fill(); }
    ctx.shadowBlur = 0;
    // nemici, capo, bonus
    for (const n of s.nemici) metti(FIGURA[n.tipo], R[n.tipo] * 2.2, n.x, n.y);
    if (s.capo) metti(FIGURA.capo, R.capo * 2.2, s.capo.x, s.capo.y);
    for (const b of s.bonus){ ctx.strokeStyle = C.oro; ctx.globalAlpha = 0.5 + 0.5 * Math.sin(s.t * 8); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(b.x, b.y, R.bonus + 4, 0, 6.29); ctx.stroke(); ctx.globalAlpha = 1; metti(FIGURA.bonus, R.bonus * 2, b.x, b.y); }
    // la navicella (lampeggia quando è intoccabile dopo un colpo)
    const nv = s.nave, lampo = s.t < s.invulnFino && Math.floor(s.t * 12) % 2;
    if (!lampo || fase !== "gioco"){
      ctx.fillStyle = C.oro; ctx.beginPath(); ctx.moveTo(nv.x - 6, nv.y + 14); ctx.lineTo(nv.x, nv.y + 22 + Math.random() * 10); ctx.lineTo(nv.x + 6, nv.y + 14); ctx.fill();
      ctx.fillStyle = C.accento; ctx.shadowColor = C.accento; ctx.shadowBlur = 14; ctx.beginPath();
      ctx.moveTo(nv.x, nv.y - 22); ctx.lineTo(nv.x + 9, nv.y + 2); ctx.lineTo(nv.x + 20, nv.y + 14); ctx.lineTo(nv.x + 7, nv.y + 12);
      ctx.lineTo(nv.x - 7, nv.y + 12); ctx.lineTo(nv.x - 20, nv.y + 14); ctx.lineTo(nv.x - 9, nv.y + 2); ctx.closePath(); ctx.fill();
      ctx.shadowBlur = 0; ctx.fillStyle = "#e6f6ff"; ctx.beginPath(); ctx.arc(nv.x, nv.y - 4, 4, 0, 6.29); ctx.fill();
    }
    if (scudo(s)){ const resto = s.scudoFino - s.t; ctx.strokeStyle = C.oro; ctx.lineWidth = 3;
      ctx.globalAlpha = resto < 1.2 ? 0.3 + 0.7 * (Math.floor(s.t * 10) % 2) : 0.8; ctx.beginPath(); ctx.arc(nv.x, nv.y, R.nave + 14, 0, 6.29); ctx.stroke();
      ctx.globalAlpha = 1; ctx.fillStyle = C.oro; ctx.font = `700 15px ${MONO}`; ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText(`🛡️ ${Math.ceil(resto)} s`, 12, 14); }
    // scintille
    for (const p of particelle){ p.x += p.vx * dt; p.y += p.vy * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, p.vita / 0.6); ctx.fillStyle = p.colore; ctx.fillRect(p.x - 2, p.y - 2, 4, 4); }
    particelle = particelle.filter(p => p.vita > 0); ctx.globalAlpha = 1;
    // la vita del capo
    if (s.capo){ const w = l - 96, x = 16, y = 18; ctx.fillStyle = "#13283b"; ctx.fillRect(x, y, w, 12);
      ctx.fillStyle = C.oro; ctx.fillRect(x, y, w * s.capo.vita / s.capo.max, 12); ctx.strokeStyle = C.tenue; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, w - 1, 11);
      ctx.fillStyle = C.oro; ctx.font = `800 13px ${TITOLI}`; ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText("CAPO", x, y + 16); }
    // il bottone della pausa
    if (fase === "gioco"){ ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(l - 54, 10, 44, 44); ctx.fillStyle = C.tenue; ctx.fillRect(l - 40, 22, 6, 20); ctx.fillRect(l - 30, 22, 6, 20); }
    // i cartelli: si parte, pausa, fine
    if (fase !== "gioco"){
      const [titolo, riga] = fase === "pronto" ? ["Assalto dallo spazio", "Tocca per partire"] : fase === "pausa" ? ["Pausa", "Tocca per riprendere"] : ["Partita finita", `${s.punti} punti · ondata ${s.ondata}`];
      ctx.fillStyle = "rgba(5,13,24,.78)"; ctx.fillRect(0, a / 2 - 80, l, 160);
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 28px ${TITOLI}`; ctx.fillText(titolo, l / 2, a / 2 - 26);
      ctx.fillStyle = C.tenue; ctx.font = `500 17px ${MONO}`; ctx.fillText(riga, l / 2, a / 2 + 16);
      if (fase === "pronto"){ ctx.font = `400 13px ${MONO}`; ctx.fillText("Trascina il dito per muoverti", l / 2, a / 2 + 46); }
    }
  }

  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (fase === "gioco" && dt > 0){
      if (tasti.sx !== tasti.dx) s = muovi(s, s.nave.x + (tasti.dx ? 360 : -360) * dt);
      s = avanza(s, dt); racconta(s.eventi); scriviBarra();
      if (s.finito){ fase = "fine"; trascina = null; api.esito(`Navicella distrutta all'ondata ${s.ondata}.`);
        timerFine = setTimeout(() => { if (!fermo) api.fine(s.punti); }, 1600); }
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
  id:"spazio", nome:"Assalto dallo spazio", cabinato:{schermo:"🚀 👾", colore:"#00B4D8"},
  regole:"La tua navicella spara da sola: trascina il dito per spostarla a destra e a sinistra. Abbatti le ondate di nemici: 👾 lento 10 punti, 🛸 a zig-zag 20, 👽 che spara 30. Ogni 4 ondate arriva un capo 🐙 da 200 punti. Hai 3 vite; il bonus raro 🛡️ ti dà lo scudo per 5 secondi. Più vai avanti, più si fa dura. Un gettone ogni 40 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
