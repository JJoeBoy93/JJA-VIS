// ── Rompimattoni (Sala giochi): racchetta in basso, pallina che rimbalza, mattoni in alto. Col telefono in verticale.
//   Si trascina il dito per muovere la racchetta. L'angolo del rimbalzo dipende da dove la pallina tocca la racchetta
//   (al centro va dritta, al bordo va obliqua). Mattoni da 1, 2 o 3 colpi (10 / 20 / 30 punti), e alcuni di ferro che non si rompono.
//   Dai mattoni rotti cadono bonus da prendere con la racchetta: L larga, 3 tre palline, S pallina lenta, F racchetta che spara.
//   3 vite (la pallina che cade sotto ne toglie una). Livello finito: +500. Otto forme di livello, poi si ripetono più dure;
//   la pallina accelera piano col tempo. Gettoni: uno ogni 200 punti, al massimo 25.
// Il mondo è fisso, 360×640, in pixel logici: il canvas lo scala per stare nel campo (x verso destra, y verso il basso).
// Lo stato è un oggetto semplice che `avanza` non tocca mai: ne restituisce uno nuovo. Le prove: collaudo/giochi/mattoni.mjs.

const W = 360, H = 640, COLS = 8, MARGINE = 12, BW = 42, BH = 20, TOP = 48;      // il campo e la griglia dei mattoni
const PY = H - 72, PH = 12, BASE = 72, LARGA = 120, R = 7;                      // racchetta (y della sua cima) e pallina
const PUNTI = {1:10, 2:20, 3:30}, BONUS_LIVELLO = 500, VITE = 3, PER_GETTONE = 200;
const PROB_BONUS = 0.22, TIPI = ["larga", "tre", "lenta", "spara"];
const DURATA = {larga:10, lenta:8, spara:8}, LENTA = 0.6, VEL_BONUS = 130, VEL_LASER = 700, CADENZA = 0.35;
const ATTESA = 1.2, MAX_ANGOLO = 1.08, PASSO = 1 / 60;

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const limita = (v, a, b) => Math.max(a, Math.min(b, v));

// le forme dei livelli: '.' vuoto, '1' '2' '3' i colpi che servono, 'x' ferro (non si rompe)
const FORME = [
  {nome:"Il muro",       righe:["11111111", "11111111", "22222222", "11111111"]},
  {nome:"La piramide",   righe:["...11...", "..1221..", ".122221.", "12222221"]},
  {nome:"La scacchiera", righe:["1.1.1.1.", ".2.2.2.2", "1.1.1.1.", ".2.2.2.2", "x.x.x.x."]},
  {nome:"Il diamante",   righe:["...22...", "..2332..", ".123321.", "..2332..", "...22..."]},
  {nome:"Il cuore",      righe:[".11..11.", "12211221", "12333321", ".123321.", "..1331..", "...11..."]},
  {nome:"La cornice",    righe:["xxxxxxxx", "x111111x", "x122221x", "x123321x", "x122221x", "x......x"]},
  {nome:"La V",          righe:["1......1", ".2....2.", "..3..3..", "...22...", "..x..x.."]},
  {nome:"La scala",      righe:["11......", ".22.....", "..33....", "...33...", "....22..", ".....11."]},
];
// il livello n (da 1): la forma, i mattoni con la loro posizione, la velocità di base; dal secondo giro i mattoni sono più duri
function livello(n){
  n = Math.max(1, Math.floor(Number(n) || 1));
  const f = FORME[(n - 1) % FORME.length], giro = Math.floor((n - 1) / FORME.length), mattoni = [];
  f.righe.forEach((riga, r) => [...riga].forEach((ch, c) => {
    if (ch === ".") return;
    const fisso = ch === "x"; let max = fisso ? 0 : Number(ch);
    if (!fisso && giro && max < 3 && (c + 2 * r + giro) % 3 === 0) max++;
    mattoni.push({c, r, x:MARGINE + c * BW, y:TOP + r * BH, max, colpi:max, fisso});
  }));
  return {n, nome:f.nome, forma:(n - 1) % FORME.length, giro, righe:f.righe, mattoni, velocita:velocitaBase(n)};
}
const velocitaBase = n => Math.min(520, 300 + 25 * (Math.max(1, n) - 1));
// col passare dei secondi la pallina va un po' più svelta: +50% dopo 4 minuti
const spinta = t => 1 + Math.min(0.5, Math.max(0, t) / 240);
const velocita = s => velocitaBase(s.livello) * spinta(s.t) * (s.t < s.lentaFino ? LENTA : 1);
const gettoni = p => Math.min(25, Math.floor(Math.max(0, Number(p) || 0) / PER_GETTONE));

// dove va la pallina dopo aver toccato la racchetta in x: al centro dritta in su, al bordo obliqua (fino a ~62° dalla verticale)
function rimbalzoRacchetta(x, racchetta){
  const t = limita((x - racchetta.x) / (racchetta.w / 2), -1, 1), a = t * MAX_ANGOLO;
  return {dx:Math.sin(a), dy:-Math.cos(a)};
}

function nuovaPartita(){
  const s = {t:0, punti:0, vite:VITE, livello:1, finito:false, racchetta:{x:W / 2, w:BASE}, palle:[], attaccata:true, attesa:ATTESA,
    mattoni:livello(1).mattoni, bonus:[], colpi:[], largaFino:0, lentaFino:0, sparaFino:0, ricarica:0, eventi:[]};
  nuovaPalla(s); return s;
}
const copia = s => ({...s, racchetta:{...s.racchetta}, palle:s.palle.map(o => ({...o})), mattoni:s.mattoni.map(o => ({...o})),
  bonus:s.bonus.map(o => ({...o})), colpi:s.colpi.map(o => ({...o})), eventi:[]});

function nuovaPalla(s){ s.palle = [{x:s.racchetta.x, y:PY - R - 1, vx:0, vy:0}]; s.attaccata = true; s.attesa = ATTESA; }
function parti(s, caso){
  if (!s.attaccata) return;
  const dx = (caso() - 0.5) * 0.5, sp = velocita(s);
  s.attaccata = false; s.palle = [{x:s.racchetta.x, y:PY - R - 1, vx:dx * sp, vy:-Math.sqrt(1 - dx * dx) * sp}];
  s.eventi.push({tipo:"lancio"});
}
// la racchetta va a x (dentro lo schermo); la pallina ancora attaccata la segue
function muovi(s, x){
  if (!Number.isFinite(x)) return s;
  const nx = limita(x, s.racchetta.w / 2, W - s.racchetta.w / 2);
  return {...s, racchetta:{...s.racchetta, x:nx}, palle:s.attaccata ? s.palle.map(b => ({...b, x:nx})) : s.palle};
}
function lancia(stato, caso = Math.random){ if (stato.finito || !stato.attaccata) return stato; const s = copia(stato); parti(s, caso); return s; }

function inclina(b){      // mai quasi orizzontale: sennò la pallina non scende più
  const sp = Math.hypot(b.vx, b.vy), minimo = 0.22 * sp;
  if (Math.abs(b.vy) < minimo){ b.vy = (b.vy < 0 ? -1 : 1) * minimo; b.vx = (b.vx < 0 ? -1 : 1) * Math.sqrt(sp * sp - minimo * minimo); }
}
// un colpo a un mattone (della pallina o di un colpo sparato): il ferro resiste, gli altri perdono un colpo e, a zero, si rompono
function dannoMattone(s, m, caso){
  if (m.fisso){ s.eventi.push({tipo:"ferro", x:m.x + BW / 2, y:m.y + BH / 2}); return; }
  m.colpi--;
  if (m.colpi > 0){ s.eventi.push({tipo:"duro", x:m.x + BW / 2, y:m.y + BH / 2, r:m.r}); return; }
  m.via = true; s.punti += PUNTI[m.max]; s.eventi.push({tipo:"rotto", x:m.x + BW / 2, y:m.y + BH / 2, r:m.r});
  if (caso() < PROB_BONUS) s.bonus.push({tipo:TIPI[Math.min(TIPI.length - 1, Math.floor(caso() * TIPI.length))], x:m.x + BW / 2, y:m.y + BH / 2});
}
// la pallina tocca un mattone? (cerchio contro rettangolo) → il più vicino
function mattoneToccato(s, b){
  let meglio = null, dm = Infinity;
  for (const m of s.mattoni){
    if (m.via) continue;
    const dx = b.x - limita(b.x, m.x, m.x + BW), dy = b.y - limita(b.y, m.y, m.y + BH), d2 = dx * dx + dy * dy;
    if (d2 < R * R && d2 < dm){ dm = d2; meglio = m; }
  }
  return meglio;
}

// la pallina avanza di h secondi a piccoli passi (al massimo 3 pixel per volta), così non attraversa niente neanche a gran velocità
function avanzaPalla(s, b, h, target, caso){
  let sp = Math.hypot(b.vx, b.vy); if (sp < 1e-9) return;
  const nuovo = sp + (target - sp) * Math.min(1, 3 * h); b.vx *= nuovo / sp; b.vy *= nuovo / sp; sp = nuovo;   // si adegua piano alla velocità giusta
  const n = Math.max(1, Math.ceil(sp * h / 3)), r = s.racchetta;
  for (let i = 0; i < n && !b.persa; i++){
    const px = b.x, py = b.y;
    b.x += b.vx * h / n; b.y += b.vy * h / n;
    if (b.x < R){ b.x = R; b.vx = Math.abs(b.vx); inclina(b); s.eventi.push({tipo:"muro"}); }
    else if (b.x > W - R){ b.x = W - R; b.vx = -Math.abs(b.vx); inclina(b); s.eventi.push({tipo:"muro"}); }
    if (b.y < R){ b.y = R; b.vy = Math.abs(b.vy); s.eventi.push({tipo:"muro"}); }
    if (b.vy > 0 && b.y + R >= PY && b.y - R <= PY + PH && py + R <= PY + 6 && Math.abs(b.x - r.x) <= r.w / 2 + R){
      const d = rimbalzoRacchetta(b.x, r), v = Math.hypot(b.vx, b.vy);
      b.vx = d.dx * v; b.vy = d.dy * v; b.y = PY - R; s.eventi.push({tipo:"racchetta"});
      continue;
    }
    const m = mattoneToccato(s, b);
    if (m){
      const ox = px + R > m.x && px - R < m.x + BW, oy = py + R > m.y && py - R < m.y + BH;
      const lato = !ox && oy, alto = ox && !oy || (ox && oy);
      if (lato || (!ox && !oy)) b.vx = b.x < m.x + BW / 2 ? -Math.abs(b.vx) : Math.abs(b.vx);
      if (alto || (!ox && !oy)) b.vy = b.y < m.y + BH / 2 ? -Math.abs(b.vy) : Math.abs(b.vy);
      b.x = px; b.y = py; inclina(b);
      dannoMattone(s, m, caso);
    }
    if (b.y - R > H) b.persa = true;
  }
}
function prendiBonus(s, tipo, caso){
  s.eventi.push({tipo:"bonus", chi:tipo});
  if (tipo === "larga"){ s.largaFino = s.t + DURATA.larga; s.racchetta.w = LARGA; }
  else if (tipo === "lenta") s.lentaFino = s.t + DURATA.lenta;
  else if (tipo === "spara"){ s.sparaFino = s.t + DURATA.spara; s.ricarica = 0; }
  else if (tipo === "tre"){
    parti(s, caso);
    const b = s.palle[0]; if (!b || s.palle.length >= 7) return;
    for (const a of [0.45, -0.45]){ const c = Math.cos(a), n = Math.sin(a); s.palle.push({x:b.x, y:b.y, vx:b.vx * c - b.vy * n, vy:b.vx * n + b.vy * c}); }
  }
}
function azzeraEffetti(s){ s.largaFino = s.lentaFino = s.sparaFino = 0; s.racchetta.w = BASE; s.bonus = []; s.colpi = []; }
function passaLivello(s){
  s.punti += BONUS_LIVELLO; s.livello++; s.mattoni = livello(s.livello).mattoni; azzeraEffetti(s); nuovaPalla(s);
  s.eventi.push({tipo:"livello", n:s.livello});
}
function perdiVita(s){
  s.vite = Math.max(0, s.vite - 1); s.eventi.push({tipo:"vita", x:s.racchetta.x, y:PY});
  if (s.vite === 0){ s.finito = true; s.eventi.push({tipo:"fine"}); } else { azzeraEffetti(s); nuovaPalla(s); }
}

function passo(s, h, caso){
  s.t += h;
  const r = s.racchetta;
  r.w = s.t < s.largaFino ? LARGA : BASE; r.x = limita(r.x, r.w / 2, W - r.w / 2);
  // la racchetta che spara: due colpi per volta, in su
  if (s.t < s.sparaFino && !s.attaccata){
    s.ricarica -= h;
    if (s.ricarica <= 0){ for (const dx of [-(r.w / 2 - 8), r.w / 2 - 8]) s.colpi.push({x:r.x + dx, y:PY}); s.ricarica = CADENZA; }
  }
  for (const c of s.colpi){
    c.y -= VEL_LASER * h;
    let m = null;
    for (const k of s.mattoni) if (!k.via && c.x >= k.x && c.x <= k.x + BW && c.y <= k.y + BH && c.y + VEL_LASER * h >= k.y && (!m || k.y > m.y)) m = k;
    if (m){ c.via = true; dannoMattone(s, m, caso); }
  }
  // le palline
  if (s.attaccata){
    for (const b of s.palle){ b.x = r.x; b.y = PY - R - 1; }
    s.attesa -= h; if (s.attesa <= 0) parti(s, caso);
  } else { const target = velocita(s); for (const b of s.palle) avanzaPalla(s, b, h, target, caso); }
  s.palle = s.palle.filter(b => !b.persa);
  // i bonus che cadono
  for (const b of s.bonus){
    b.y += VEL_BONUS * h;
    if (b.y + 12 >= PY && b.y - 12 <= PY + PH && Math.abs(b.x - r.x) <= r.w / 2 + 12){ b.via = true; prendiBonus(s, b.tipo, caso); }
    else if (b.y > H + 20) b.via = true;
  }
  s.bonus = s.bonus.filter(b => !b.via); s.colpi = s.colpi.filter(c => !c.via && c.y > -20); s.mattoni = s.mattoni.filter(m => !m.via);
  if (!s.mattoni.some(m => !m.fisso)) passaLivello(s);
  else if (!s.palle.length) perdiVita(s);
}
// avanza di dt secondi (a passi di 1/60 s, al massimo 1/4 di secondo per volta); caso() decide i bonus e il verso del lancio
function avanza(stato, dt, caso = Math.random){
  if (stato.finito || !(dt > 0)) return stato;
  const s = copia(stato);
  let resto = Math.min(dt, 0.25);
  while (resto > 1e-9 && !s.finito){ const h = Math.min(resto, PASSO); passo(s, h, caso); resto -= h; }
  return s;
}

export const logica = {W, H, COLS, BW, BH, TOP, PY, PH, BASE, LARGA, R, PUNTI, BONUS_LIVELLO, VITE, PER_GETTONE, PROB_BONUS, TIPI, DURATA, LENTA, FORME,
  livello, velocitaBase, spinta, velocita, gettoni, rimbalzoRacchetta, nuovaPartita, muovi, lancia, avanza};

// ══ il gioco nello strato: un canvas che riempie il campo
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';
const FILE = ["#ff4d6d", "#ff9f1c", "#FFD60A", "#2ec4b6", "#00B4D8", "#9d4edd"];     // un colore per ogni fila
const SIGLA = {larga:"L", tre:"3", lenta:"S", spara:"F"};
const COLORE_BONUS = {larga:"#2ec4b6", tre:"#ff9f1c", lenta:"#00B4D8", spara:"#ff4d6d"};

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4"), fondo:"#050d18", campo:"#08172a", ferro:"#8d99ae"};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:pointer";
  cv.setAttribute("aria-label", "Rompimattoni: trascina il dito per muovere la racchetta");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = nuovaPartita(), fase = "pronto", raf = 0, prima = 0, timerFine = 0, fermo = false, dpr = 1, cw = 390, ch = 700, sc = 1, ox = 0, oy = 0;
  let trascina = null, tasti = {sx:false, dx:false}, particelle = [], scritte = {punti:-1, tempo:""};

  function misura(){
    const r = campo.getBoundingClientRect(); cw = Math.max(240, r.width || 390); ch = Math.max(360, r.height || 700);
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(cw * dpr); cv.height = Math.round(ch * dpr);
    sc = Math.min(cw / W, ch / H); ox = (cw - W * sc) / 2; oy = (ch - H * sc) / 2;
  }
  misura();

  function pausa(){ if (fase !== "gioco") return; fase = "pausa"; trascina = null; api.esito("In pausa: tocca lo schermo per riprendere."); }
  function riprendi(){ if (fase !== "pausa" && fase !== "pronto") return; fase = "gioco"; prima = 0; api.esito("Trascina il dito per muovere la racchetta."); }
  const sulBottonePausa = (x, y) => x > W - 48 && y < 44;

  function giu(e){
    if (fase === "fine") return;
    const r = cv.getBoundingClientRect(), x = (e.clientX - r.left - ox) / sc, y = (e.clientY - r.top - oy) / sc;
    if (fase !== "gioco") riprendi();
    else if (sulBottonePausa(x, y)){ pausa(); return; }
    else if (s.attaccata) s = lancia(s);
    trascina = {id:e.pointerId, x0:e.clientX, rac0:s.racchetta.x};
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  }
  function sposta(e){
    if (!trascina || e.pointerId !== trascina.id || fase !== "gioco") return;
    s = muovi(s, trascina.rac0 + (e.clientX - trascina.x0) / sc * 1.3); e.preventDefault();
  }
  function su(e){ if (trascina && e.pointerId === trascina.id) trascina = null; }
  function tasto(e){
    const premuto = e.type === "keydown";
    if (e.key === "ArrowLeft"){ tasti.sx = premuto; e.preventDefault(); }
    else if (e.key === "ArrowRight"){ tasti.dx = premuto; e.preventDefault(); }
    else if (premuto && e.key === " "){ if (fase === "gioco" && s.attaccata) s = lancia(s); else if (fase === "gioco") pausa(); else if (fase !== "fine") riprendi(); e.preventDefault(); }
    else if (premuto && (e.key === "p" || e.key === "P")){ if (fase === "gioco") pausa(); else if (fase !== "fine") riprendi(); e.preventDefault(); }
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
      if (e.tipo === "rotto"){ for (let i = 0; i < 8; i++){ const ang = Math.random() * 6.28, v = 40 + Math.random() * 120;
          particelle.push({x:e.x, y:e.y, vx:Math.cos(ang) * v, vy:Math.sin(ang) * v, vita:0.5, colore:FILE[e.r % FILE.length]}); } }
      else if (e.tipo === "duro" || e.tipo === "ferro") particelle.push({x:e.x, y:e.y, vx:0, vy:-30, vita:0.2, colore:e.tipo === "ferro" ? C.ferro : C.oro});
      else if (e.tipo === "vita") api.esito(s.vite ? `Pallina persa! Ti restano ${s.vite} ${s.vite === 1 ? "vita" : "vite"}.` : "Pallina persa!");
      else if (e.tipo === "livello") api.esito(`Livello finito! +${BONUS_LIVELLO}. Ora: ${livello(e.n).nome}.`);
      else if (e.tipo === "bonus") api.esito({larga:"Racchetta larga!", tre:"Tre palline!", lenta:"Pallina lenta!", spara:"Racchetta che spara!"}[e.chi]);
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `Livello ${s.livello} · vite ${s.vite}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }

  const rett = (x, y, w, h, rr) => { ctx.beginPath(); ctx.moveTo(x + rr, y); ctx.arcTo(x + w, y, x + w, y + h, rr); ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr); ctx.arcTo(x, y, x + w, y, rr); ctx.closePath(); };

  function disegna(dt){
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, cw, ch);
    ctx.save(); ctx.translate(ox, oy); ctx.scale(sc, sc);
    ctx.fillStyle = C.campo; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "#13283b"; ctx.lineWidth = 2; ctx.strokeRect(1, 1, W - 2, H - 2);
    // i mattoni
    for (const m of s.mattoni){
      const x = m.x + 1, y = m.y + 1, w = BW - 2, h = BH - 2;
      if (m.fisso){ ctx.fillStyle = C.ferro; rett(x, y, w, h, 3); ctx.fill(); ctx.strokeStyle = "#4a5568"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x + 4, y + 4); ctx.lineTo(x + w - 4, y + h - 4); ctx.moveTo(x + w - 4, y + 4); ctx.lineTo(x + 4, y + h - 4); ctx.stroke(); continue; }
      ctx.fillStyle = FILE[m.r % FILE.length]; rett(x, y, w, h, 3); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,.28)"; ctx.fillRect(x + 2, y + 2, w - 4, 4);
      if (m.max > 1){ ctx.fillStyle = "rgba(5,13,24,.75)"; for (let i = 0; i < m.colpi; i++){ ctx.beginPath(); ctx.arc(x + w / 2 + (i - (m.colpi - 1) / 2) * 9, y + h / 2 + 2, 2.6, 0, 6.29); ctx.fill(); } }
    }
    // colpi sparati e bonus che cadono
    ctx.fillStyle = C.oro; ctx.shadowColor = C.oro; ctx.shadowBlur = 8;
    for (const c of s.colpi) ctx.fillRect(c.x - 1.5, c.y - 6, 3, 12);
    ctx.shadowBlur = 0;
    for (const b of s.bonus){ ctx.fillStyle = COLORE_BONUS[b.tipo]; rett(b.x - 14, b.y - 10, 28, 20, 8); ctx.fill();
      ctx.fillStyle = "#050d18"; ctx.font = `800 14px ${TITOLI}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(SIGLA[b.tipo], b.x, b.y + 1); }
    // la racchetta
    const r = s.racchetta, spara = s.t < s.sparaFino;
    ctx.fillStyle = C.accento; ctx.shadowColor = C.accento; ctx.shadowBlur = 12; rett(r.x - r.w / 2, PY, r.w, PH, 6); ctx.fill(); ctx.shadowBlur = 0;
    ctx.fillStyle = C.oro; ctx.fillRect(r.x - 10, PY + 3, 20, 3);
    if (spara){ ctx.fillStyle = "#ff4d6d"; ctx.fillRect(r.x - r.w / 2 + 4, PY - 6, 8, 8); ctx.fillRect(r.x + r.w / 2 - 12, PY - 6, 8, 8); }
    // le palline
    const lenta = s.t < s.lentaFino;
    for (const b of s.palle){ ctx.fillStyle = lenta ? "#9fe8ff" : C.oro; ctx.shadowColor = lenta ? C.accento : C.oro; ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.arc(b.x, b.y, R, 0, 6.29); ctx.fill(); }
    ctx.shadowBlur = 0;
    // scintille
    for (const p of particelle){ p.x += p.vx * dt; p.y += p.vy * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, p.vita / 0.5); ctx.fillStyle = p.colore; ctx.fillRect(p.x - 2, p.y - 2, 4, 4); }
    particelle = particelle.filter(p => p.vita > 0); ctx.globalAlpha = 1;
    // i bonus attivi, col tempo che resta
    ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.font = `700 13px ${MONO}`;
    let riga = 0;
    for (const [k, fino] of [["larga", s.largaFino], ["lenta", s.lentaFino], ["spara", s.sparaFino]]) if (s.t < fino){
      ctx.fillStyle = COLORE_BONUS[k]; ctx.fillText(`${SIGLA[k]} ${Math.ceil(fino - s.t)} s`, 14, 12 + riga * 16); riga++; }
    // il bottone della pausa
    if (fase === "gioco"){ ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(W - 44, 6, 36, 36); ctx.fillStyle = C.tenue; ctx.fillRect(W - 33, 15, 5, 18); ctx.fillRect(W - 24, 15, 5, 18); }
    // i cartelli: si parte, pausa
    if (fase === "pronto" || fase === "pausa"){
      ctx.fillStyle = "rgba(5,13,24,.78)"; ctx.fillRect(0, H / 2 - 70, W, 140);
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 28px ${TITOLI}`; ctx.fillText(fase === "pronto" ? "Rompimattoni" : "Pausa", W / 2, H / 2 - 20);
      ctx.fillStyle = C.tenue; ctx.font = `500 16px ${MONO}`; ctx.fillText(fase === "pronto" ? "Tocca per partire" : "Tocca per riprendere", W / 2, H / 2 + 18);
      if (fase === "pronto"){ ctx.font = `400 13px ${MONO}`; ctx.fillText("Trascina il dito per muovere la racchetta", W / 2, H / 2 + 46); }
    }
    ctx.restore();
  }

  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (fase === "gioco" && dt > 0){
      if (tasti.sx !== tasti.dx) s = muovi(s, s.racchetta.x + (tasti.dx ? 420 : -420) * dt);
      s = avanza(s, dt); racconta(s.eventi); scriviBarra();
      if (s.finito){ fase = "fine"; trascina = null; api.esito(`Pallina persa: partita finita al livello ${s.livello}.`);
        timerFine = setTimeout(() => { if (!fermo) api.fine(s.punti); }, 1000); }
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
  id:"mattoni", nome:"Rompimattoni", cabinato:{schermo:"MATTONI", colore:"#FFD60A"},
  regole:"Trascina il dito per muovere la racchetta e tieni su la pallina: rompi tutti i mattoni! Dove la pallina tocca la racchetta decide l'angolo del rimbalzo. Alcuni mattoni vogliono 2 o 3 colpi (10, 20, 30 punti), quelli di ferro non si rompono. Dai mattoni cadono bonus da prendere con la racchetta: L racchetta larga, 3 tre palline, S pallina lenta, F racchetta che spara. Hai 3 vite; ogni livello finito vale 500 punti, e la pallina accelera piano col tempo. Un gettone ogni 200 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
