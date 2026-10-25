// ── Incastri (Sala giochi): una griglia 10×20, dall'alto scendono pezzi di 4 blocchi (i sette classici), col telefono in verticale.
//   Si sposta, si ruota, si fa cadere subito; una fila piena esplode e si svuota.
//   Punti: 1/2/3/4 file insieme = 100/300/500/800 × il livello. Ogni 10 file si sale di livello e si cade più veloci.
//   Fine quando un pezzo nuovo non entra. Gettoni: uno ogni 400 punti, al massimo 25.
// La griglia è un array di 20 righe da 10 caselle (null, o la lettera del pezzo che l'ha riempita); lo stato è un oggetto
// semplice che le funzioni non toccano mai: ne restituiscono uno nuovo. Le prove: collaudo/giochi/incastri.mjs.

const COLONNE = 10, RIGHE = 20, TIPI = ["I", "O", "T", "S", "Z", "J", "L"];
const LATO = {I:4, O:2, T:3, S:3, Z:3, J:3, L:3};                                       // il quadrato in cui il pezzo ruota
const BASE = {I:[[1,0],[1,1],[1,2],[1,3]], O:[[0,0],[0,1],[1,0],[1,1]], T:[[0,1],[1,0],[1,1],[1,2]], S:[[0,1],[0,2],[1,0],[1,1]],
  Z:[[0,0],[0,1],[1,1],[1,2]], J:[[0,0],[1,0],[1,1],[1,2]], L:[[0,2],[1,0],[1,1],[1,2]]};   // [riga, colonna] nel quadrato
const COLORI = {I:"#00E5FF", O:"#FFD60A", T:"#C77DFF", S:"#5CFF8A", Z:"#FF4D6D", J:"#4D7CFF", L:"#FF9F1C"};
const PUNTI_FILE = [0, 100, 300, 500, 800], OGNI_LIVELLO = 10, PER_GETTONE = 400, MAX_GETTONI = 25;
const BLOCCO = 0.45, MAX_RESET = 12, PASSO = 1 / 60;       // secondi che un pezzo posato aspetta prima di fissarsi; quante volte muoverlo lo fa aspettare di nuovo
// dove può spostarsi un pezzo che ruota e non ci sta (la «spinta dal muro»): di fianco, poi un po' più giù
const SPINTE = [[0,0],[-1,0],[1,0],[-2,0],[2,0],[0,1],[-1,1],[1,1]];

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
// le quattro rotazioni (in senso orario) di ogni pezzo
const FORME = {};
for (const t of TIPI){ FORME[t] = [BASE[t]]; for (let i = 1; i < 4; i++) FORME[t].push(FORME[t][i - 1].map(([r, c]) => [c, LATO[t] - 1 - r])); }

const vuota = () => Array.from({length:RIGHE}, () => Array(COLONNE).fill(null));
const gettoni = p => Math.min(MAX_GETTONI, Math.floor(Math.max(0, Number(p) || 0) / PER_GETTONE));
const livelloDi = file => 1 + Math.floor(Math.max(0, file) / OGNI_LIVELLO);
// secondi per scendere di una riga: 0,8 al livello 1, sempre meno, mai sotto 0,07
const intervallo = livello => Math.max(0.07, 0.8 * Math.pow(0.82, Math.max(1, livello) - 1));

// il pezzo dopo, dal sacchetto dei sette: si pesca finché è vuoto, poi si rimescola. Così nessun pezzo esce più di due volte di fila.
function nuovoPezzo(caso = Math.random, sacchetto = []){
  let sac = sacchetto.slice();
  if (!sac.length){
    sac = TIPI.slice();
    for (let i = sac.length - 1; i > 0; i--){ const j = Math.min(i, Math.floor(caso() * (i + 1))); [sac[i], sac[j]] = [sac[j], sac[i]]; }
  }
  const tipo = sac.pop();
  return {tipo, sacchetto:sac};
}
// il pezzo appena entrato: in cima, al centro, con la fila più alta sulla riga 0
const entra = tipo => ({tipo, rot:0, x:Math.floor((COLONNE - LATO[tipo]) / 2), y:-Math.min(...FORME[tipo][0].map(([r]) => r))});
const celle = p => FORME[p.tipo][p.rot].map(([r, c]) => [p.y + r, p.x + c]);
const libero = (griglia, p) => celle(p).every(([r, c]) => c >= 0 && c < COLONNE && r >= 0 && r < RIGHE && !griglia[r][c]);
const appoggiato = s => !!s.pezzo && !libero(s.griglia, {...s.pezzo, y:s.pezzo.y + 1});
// dove arriverebbe il pezzo se cadesse subito (è l'ombra)
function ombra(s){ if (!s.pezzo) return null; let p = s.pezzo; while (libero(s.griglia, {...p, y:p.y + 1})) p = {...p, y:p.y + 1}; return p; }

function nuovaPartita(caso = Math.random){
  const a = nuovoPezzo(caso, []), b = nuovoPezzo(caso, a.sacchetto);
  return {griglia:vuota(), pezzo:entra(a.tipo), prossimo:b.tipo, sacchetto:b.sacchetto, punti:0, file:0, livello:1, finito:false, gocce:0, sosta:0, resetSosta:0, eventi:[]};
}
const finita = s => !!s.finito;

// il pezzo va in `p`; se era posato e lo si muove, l'attesa prima di fissarsi ricomincia (ma non all'infinito)
function conPezzo(s, p){
  const n = {...s, pezzo:p};
  if (s.sosta > 0 && s.resetSosta < MAX_RESET){ n.sosta = 0; n.resetSosta = s.resetSosta + 1; }
  return n;
}
function sposta(s, dx){
  if (s.finito || !s.pezzo) return s;
  const p = {...s.pezzo, x:s.pezzo.x + Math.sign(dx || 0)};
  return p.x !== s.pezzo.x && libero(s.griglia, p) ? conPezzo(s, p) : s;
}
// ruota in senso orario; se tocca il muro (o un blocco) prova a spingere il pezzo di lato, e se non ci sta resta com'è
function ruota(s){
  if (s.finito || !s.pezzo) return s;
  const r = {...s.pezzo, rot:(s.pezzo.rot + 1) % 4};
  for (const [dx, dy] of SPINTE){ const p = {...r, x:r.x + dx, y:r.y + dy}; if (libero(s.griglia, p)) return conPezzo(s, p); }
  return s;
}
// scende di una riga; se è posato non fa niente (a fissarlo ci pensa avanza, o fissa)
function cade(s){
  if (s.finito || !s.pezzo) return s;
  const p = {...s.pezzo, y:s.pezzo.y + 1};
  return libero(s.griglia, p) ? {...s, pezzo:p} : s;
}

// fissa il pezzo (su una copia che si può toccare), svuota le file piene, conta punti e livello, fa entrare il prossimo
function fissaDentro(s, caso){
  const g = s.griglia.map(r => r.slice());
  for (const [r, c] of celle(s.pezzo)) g[r][c] = s.pezzo.tipo;
  const piene = [];
  g.forEach((riga, r) => { if (riga.every(Boolean)) piene.push(r); });
  const n = piene.length, livelloPrima = s.livello;
  if (n){
    const punti = PUNTI_FILE[n] * livelloPrima;
    s.eventi.push({tipo:"file", n, punti, righe:piene.map(r => ({r, colori:g[r].slice()}))});
    s.punti += punti; s.file += n;
    s.livello = livelloDi(s.file);
    if (s.livello > livelloPrima) s.eventi.push({tipo:"livello", livello:s.livello});
  }
  const resto = g.filter((_, r) => !piene.includes(r));
  while (resto.length < RIGHE) resto.unshift(Array(COLONNE).fill(null));
  s.griglia = resto;
  const q = nuovoPezzo(caso, s.sacchetto), nuovo = entra(s.prossimo);
  s.prossimo = q.tipo; s.sacchetto = q.sacchetto; s.gocce = 0; s.sosta = 0; s.resetSosta = 0;
  if (libero(s.griglia, nuovo)) s.pezzo = nuovo;
  else { s.pezzo = null; s.finito = true; s.eventi.push({tipo:"fine"}); }
}
function fissa(s, caso = Math.random){
  if (s.finito || !s.pezzo) return s;
  const n = {...s, eventi:[]}; fissaDentro(n, caso); return n;
}
// cade subito dov'è l'ombra e si fissa
function cadeSubito(s, caso = Math.random){ return s.finito || !s.pezzo ? s : fissa({...s, pezzo:ombra(s)}, caso); }

// avanza di dt secondi (a passi di 1/60 s, al massimo 1/4 di secondo per volta): il pezzo scende da solo; posato, dopo un attimo si fissa
function avanza(stato, dt, caso = Math.random){
  if (stato.finito || !stato.pezzo || !(dt > 0)) return stato;
  const s = {...stato, eventi:[]};
  let resto = Math.min(dt, 0.25);
  while (resto > 1e-9 && !s.finito){
    const h = Math.min(resto, PASSO); resto -= h;
    if (appoggiato(s)){ s.gocce = 0; s.sosta += h; if (s.sosta >= BLOCCO) fissaDentro(s, caso); }
    else { s.gocce += h; if (s.gocce >= intervallo(s.livello)){ s.gocce -= intervallo(s.livello); s.pezzo = {...s.pezzo, y:s.pezzo.y + 1}; } }
  }
  return s;
}

export const logica = {COLONNE, RIGHE, TIPI, LATO, FORME, COLORI, PUNTI_FILE, OGNI_LIVELLO, PER_GETTONE, BLOCCO, MAX_RESET,
  gettoni, livelloDi, intervallo, nuovoPezzo, entra, celle, libero, appoggiato, ombra, nuovaPartita, finita, sposta, ruota, cade, fissa, cadeSubito, avanza};

// ══ il gioco nello strato: un canvas che riempie il campo
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4"), fondo:"#050d18", quadro:"#07121f", tasto:"#0b1a2a"};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:pointer";
  cv.setAttribute("aria-label", "Incastri: tocca a sinistra o a destra per spostare il pezzo, al centro per ruotarlo, scorri in giù per farlo cadere");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = nuovaPartita(), fase = "pronto", raf = 0, prima = 0, timerFine = 0, fermo = false, dpr = 1, G = null;
  let gesto = null, tenuto = null, premuto = null, particelle = [], lampi = [], scritte = {punti:-1, tempo:""};

  // i blocchi al neon si disegnano una volta con il loro bagliore, poi si copiano
  const sprite = new Map();
  function blocco(tipo, lato){
    const k = tipo + lato + "@" + dpr; if (sprite.has(k)) return sprite.get(k);
    const g = Math.ceil(lato * 0.6), c = document.createElement("canvas"); c.width = c.height = Math.ceil((lato + 2 * g) * dpr);
    const x = c.getContext("2d"); x.scale(dpr, dpr);
    x.shadowColor = COLORI[tipo]; x.shadowBlur = lato * 0.55; x.fillStyle = COLORI[tipo]; x.globalAlpha = 0.9; x.fillRect(g + 1.5, g + 1.5, lato - 3, lato - 3);
    x.shadowBlur = 0; x.globalAlpha = 1; x.fillStyle = "rgba(255,255,255,.4)"; x.fillRect(g + 3, g + 3, lato - 6, Math.max(2, lato * 0.16));
    x.fillStyle = "rgba(0,0,0,.18)"; x.fillRect(g + 3, g + lato - 3 - Math.max(2, lato * 0.12), lato - 6, Math.max(2, lato * 0.12));
    const o = {c, g}; sprite.set(k, o); return o;
  }
  const mettiBlocco = (tipo, lato, x, y) => { const {c, g} = blocco(tipo, lato); ctx.drawImage(c, x - g, y - g, lato + 2 * g, lato + 2 * g); };

  function misura(){
    const r = campo.getBoundingClientRect(), l = Math.max(240, r.width || 390), a = Math.max(360, r.height || 700), m = 10;
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(l * dpr); cv.height = Math.round(a * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); sprite.clear();
    const bh = Math.max(54, Math.min(80, Math.round(a * 0.1))), yTasti = a - bh - m, pw = Math.max(76, Math.min(110, Math.round(l * 0.24))), alto = yTasti - 2 * m;
    const cs = Math.max(10, Math.floor(Math.min((l - pw - 3 * m) / COLONNE, alto / RIGHE)));
    const bx = Math.round((l - (cs * COLONNE + m + pw)) / 2), by = m + Math.floor((alto - cs * RIGHE) / 2), px = bx + cs * COLONNE + m, bw = (l - 5 * m) / 4;
    G = {l, a, m, cs, bx, by, px, pw, pausa:{x:px + pw - 44, y:by, w:44, h:44},
      tasti:["sx", "ruota", "dx", "giu"].map((k, i) => ({k, x:m + i * (bw + m), y:yTasti, w:bw, h:bh}))};
  }
  misura();

  const ripresa = () => { prima = 0; };
  function pausa(){ if (fase !== "gioco") return; fase = "pausa"; gesto = tenuto = premuto = null; api.esito("In pausa: tocca lo schermo per riprendere."); }
  function riprendi(){ if (fase !== "pausa" && fase !== "pronto") return; fase = "gioco"; ripresa(); api.esito("Sposta, ruota, fai cadere: componi file piene."); }

  const dentro = (x, y, b) => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h;
  function applica(nuovo){ s = nuovo; racconta(s.eventi); s.eventi = []; if (s.finito && fase === "gioco") finisci(); }
  function azione(k){
    if (fase !== "gioco") return;
    if (k === "sx") applica(sposta(s, -1)); else if (k === "dx") applica(sposta(s, 1));
    else if (k === "ruota") applica(ruota(s)); else if (k === "giu") applica(cadeSubito(s));
  }

  function giu(e){
    if (fase === "fine") return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    e.preventDefault();
    if (fase !== "gioco"){ riprendi(); return; }
    if (dentro(x, y, G.pausa)){ pausa(); return; }
    const t = G.tasti.find(b => dentro(x, y, b));
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
    if (t){ premuto = {k:t.k, id:e.pointerId}; azione(t.k); if (t.k === "sx" || t.k === "dx") tenuto = {k:t.k, id:e.pointerId, t:0, n:0}; return; }
    gesto = {id:e.pointerId, x0:x, y0:y, xRif:x, mosso:false, lasciato:false};
  }
  function sposta_(e){
    if (!gesto || e.pointerId !== gesto.id || fase !== "gioco") return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, dx = x - gesto.x0, dy = y - gesto.y0;
    e.preventDefault();
    if (gesto.lasciato) return;
    if (dy > G.cs * 2.5 && dy > Math.abs(dx) * 1.3){ gesto.lasciato = gesto.mosso = true; azione("giu"); return; }
    while (x - gesto.xRif >= G.cs){ gesto.xRif += G.cs; gesto.mosso = true; azione("dx"); }
    while (gesto.xRif - x >= G.cs){ gesto.xRif -= G.cs; gesto.mosso = true; azione("sx"); }
  }
  function su(e){
    if (tenuto && e.pointerId === tenuto.id) tenuto = null;
    if (premuto && e.pointerId === premuto.id) premuto = null;
    if (gesto && e.pointerId === gesto.id){
      const g = gesto; gesto = null;
      if (e.type === "pointerup" && !g.mosso && fase === "gioco"){
        const r = cv.getBoundingClientRect(), x = e.clientX - r.left;
        azione(x < G.l / 3 ? "sx" : x > G.l * 2 / 3 ? "dx" : "ruota");
      }
    }
  }
  function tasto(e){
    if (e.type !== "keydown") return;
    const k = e.key;
    if (k === "ArrowLeft") azione("sx"); else if (k === "ArrowRight") azione("dx");
    else if (k === "ArrowUp" || k === "x" || k === "X") azione("ruota");
    else if (k === "ArrowDown" || k === " ") azione("giu");
    else if (k === "p" || k === "P"){ if (fase === "gioco") pausa(); else if (fase !== "fine") riprendi(); }
    else return;
    e.preventDefault();
  }
  const visibile = () => { if (document.hidden) pausa(); };
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => misura()) : null;
  if (ro) ro.observe(campo); else window.addEventListener("resize", misura);
  cv.addEventListener("pointerdown", giu); cv.addEventListener("pointermove", sposta_);
  cv.addEventListener("pointerup", su); cv.addEventListener("pointercancel", su);
  window.addEventListener("keydown", tasto);
  document.addEventListener("visibilitychange", visibile);

  function racconta(eventi){
    for (const e of eventi){
      if (e.tipo === "file"){
        for (const {r, colori} of e.righe){
          lampi.push({r, vita:0.3});
          for (let c = 0; c < COLONNE; c++) for (let i = 0; i < 3; i++){
            const ang = Math.random() * 6.28, v = 50 + Math.random() * 190;
            particelle.push({x:G.bx + (c + 0.5) * G.cs, y:G.by + (r + 0.5) * G.cs, vx:Math.cos(ang) * v, vy:Math.sin(ang) * v - 40, vita:0.5 + Math.random() * 0.4, colore:i ? COLORI[colori[c]] : "#ffffff"});
          }
        }
        api.esito(`${e.n === 1 ? "Una fila" : e.n + " file"}: +${e.punti}!`);
      } else if (e.tipo === "livello") api.esito(`Livello ${e.livello}: si cade più veloci!`);
      else if (e.tipo === "fine") api.esito(`Pila troppo alta: ${s.punti} punti.`);
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `Livello ${s.livello} · ${s.file} ${s.file === 1 ? "fila" : "file"}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }
  function finisci(){
    fase = "fine"; gesto = tenuto = premuto = null; scriviBarra();
    timerFine = setTimeout(() => { if (!fermo) api.fine(s.punti); }, 1300);
  }

  function disegnaTasto(b, glifo){
    const giu_ = premuto && premuto.k === b.k;
    ctx.fillStyle = giu_ ? "#173a52" : C.tasto; ctx.fillRect(b.x, b.y, b.w, b.h);
    ctx.strokeStyle = giu_ ? C.oro : C.accento; ctx.lineWidth = 2; ctx.strokeRect(b.x + 1, b.y + 1, b.w - 2, b.h - 2);
    const cx = b.x + b.w / 2, cy = b.y + b.h / 2, u = Math.min(b.h, b.w) * 0.22;
    ctx.fillStyle = ctx.strokeStyle = giu_ ? C.oro : "#e6f6ff"; ctx.lineWidth = 4; ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.beginPath();
    if (glifo === "sx" || glifo === "dx"){ const d = glifo === "sx" ? -1 : 1;
      ctx.moveTo(cx - d * u * 1.1, cy); ctx.lineTo(cx + d * u * 1.1, cy); ctx.moveTo(cx + d * u * 0.1, cy - u); ctx.lineTo(cx + d * u * 1.1, cy); ctx.lineTo(cx + d * u * 0.1, cy + u); ctx.stroke(); }
    else if (glifo === "ruota"){ ctx.arc(cx, cy, u * 1.05, -2.6, 1.5); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx + u * 0.1, cy + u * 1.05 - u * 0.7); ctx.lineTo(cx - u * 0.35, cy + u * 1.05); ctx.lineTo(cx + u * 0.1, cy + u * 1.05 + u * 0.7); ctx.stroke(); }
    else { ctx.moveTo(cx, cy - u * 1.1); ctx.lineTo(cx, cy + u * 0.7); ctx.moveTo(cx - u, cy - u * 0.1); ctx.lineTo(cx, cy + u * 0.8); ctx.lineTo(cx + u, cy - u * 0.1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - u * 1.1, cy + u * 1.25); ctx.lineTo(cx + u * 1.1, cy + u * 1.25); ctx.stroke(); }
    ctx.lineCap = "butt";
  }

  function disegna(dt){
    const {l, a, cs, bx, by, px, pw} = G;
    ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, l, a);
    // il quadro: fondo, griglia leggera, bordo
    ctx.fillStyle = C.quadro; ctx.fillRect(bx, by, cs * COLONNE, cs * RIGHE);
    ctx.strokeStyle = "rgba(0,180,216,.12)"; ctx.lineWidth = 1; ctx.beginPath();
    for (let c = 1; c < COLONNE; c++){ ctx.moveTo(bx + c * cs + 0.5, by); ctx.lineTo(bx + c * cs + 0.5, by + cs * RIGHE); }
    for (let r = 1; r < RIGHE; r++){ ctx.moveTo(bx, by + r * cs + 0.5); ctx.lineTo(bx + cs * COLONNE, by + r * cs + 0.5); }
    ctx.stroke();
    ctx.strokeStyle = C.accento; ctx.lineWidth = 2; ctx.strokeRect(bx - 1, by - 1, cs * COLONNE + 2, cs * RIGHE + 2);
    // i blocchi caduti
    for (let r = 0; r < RIGHE; r++) for (let c = 0; c < COLONNE; c++) if (s.griglia[r][c]) mettiBlocco(s.griglia[r][c], cs, bx + c * cs, by + r * cs);
    if (s.pezzo){
      const o = ombra(s);   // l'ombra, dove cadrà
      ctx.lineWidth = 2;
      for (const [r, c] of celle(o)){ ctx.globalAlpha = 0.14; ctx.fillStyle = COLORI[s.pezzo.tipo]; ctx.fillRect(bx + c * cs, by + r * cs, cs, cs);
        ctx.globalAlpha = 0.6; ctx.strokeStyle = COLORI[s.pezzo.tipo]; ctx.strokeRect(bx + c * cs + 1.5, by + r * cs + 1.5, cs - 3, cs - 3); }
      ctx.globalAlpha = 1;
      for (const [r, c] of celle(s.pezzo)) mettiBlocco(s.pezzo.tipo, cs, bx + c * cs, by + r * cs);
    }
    // le file piene: un lampo bianco, poi le scintille
    for (const f of lampi){ f.vita -= dt; ctx.globalAlpha = Math.max(0, f.vita / 0.3) * 0.85; ctx.fillStyle = "#ffffff"; ctx.fillRect(bx, by + f.r * cs, cs * COLONNE, cs); }
    lampi = lampi.filter(f => f.vita > 0); ctx.globalAlpha = 1;
    for (const p of particelle){ p.vy += 260 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, Math.min(1, p.vita / 0.5)); ctx.fillStyle = p.colore; ctx.fillRect(p.x - 2, p.y - 2, 4, 4); }
    particelle = particelle.filter(p => p.vita > 0); ctx.globalAlpha = 1;
    // il fianco: pausa, il pezzo che arriva, livello e file
    if (fase === "gioco"){ const b = G.pausa; ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(b.x, b.y, b.w, b.h); ctx.fillStyle = C.tenue; ctx.fillRect(b.x + 14, b.y + 12, 6, 20); ctx.fillRect(b.x + 24, b.y + 12, 6, 20); }
    ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillStyle = C.tenue; ctx.font = `500 12px ${MONO}`;
    const yp = by + 56; ctx.fillText("PROSSIMO", px, yp);
    ctx.strokeStyle = C.accento; ctx.lineWidth = 1; ctx.strokeRect(px + 0.5, yp + 20.5, pw - 1, pw * 0.78);
    const ps = Math.max(8, Math.min(20, Math.floor((pw - 12) / 4))), fo = FORME[s.prossimo][0], rr = fo.map(([r]) => r), cc = fo.map(([, c]) => c);
    const w = (Math.max(...cc) - Math.min(...cc) + 1) * ps, h = (Math.max(...rr) - Math.min(...rr) + 1) * ps;
    for (const [r, c] of fo) mettiBlocco(s.prossimo, ps, px + (pw - w) / 2 + (c - Math.min(...cc)) * ps, yp + 20 + (pw * 0.78 - h) / 2 + (r - Math.min(...rr)) * ps);
    const yl = yp + 20 + pw * 0.78 + 18;
    ctx.fillStyle = C.tenue; ctx.fillText("LIVELLO", px, yl); ctx.fillText("FILE", px, yl + 56);
    ctx.fillStyle = C.oro; ctx.font = `800 26px ${TITOLI}`; ctx.fillText(String(s.livello), px, yl + 16); ctx.fillText(String(s.file), px, yl + 72);
    // i quattro tasti
    G.tasti.forEach(b => disegnaTasto(b, b.k));
    // i cartelli: si parte, pausa
    if (fase === "pronto" || fase === "pausa"){
      const [titolo, riga] = fase === "pronto" ? ["Incastri", "Tocca per partire"] : ["Pausa", "Tocca per riprendere"];
      ctx.fillStyle = "rgba(5,13,24,.82)"; ctx.fillRect(0, a / 2 - 80, l, 160);
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 30px ${TITOLI}`; ctx.fillText(titolo, l / 2, a / 2 - 26);
      ctx.fillStyle = C.tenue; ctx.font = `500 17px ${MONO}`; ctx.fillText(riga, l / 2, a / 2 + 16);
      if (fase === "pronto"){ ctx.font = `400 13px ${MONO}`; ctx.fillText("Tocca ai lati per spostare, al centro per ruotare", l / 2, a / 2 + 46); }
    }
  }

  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (fase === "gioco" && dt > 0){
      if (tenuto){ tenuto.t += dt; while (tenuto.t >= 0.28 + tenuto.n * 0.07){ tenuto.n++; azione(tenuto.k); } }   // tenendo premuto ← o → il pezzo scivola
      if (fase === "gioco") applica(avanza(s, dt));
      scriviBarra();
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
      cv.removeEventListener("pointerdown", giu); cv.removeEventListener("pointermove", sposta_);
      cv.removeEventListener("pointerup", su); cv.removeEventListener("pointercancel", su);
      window.removeEventListener("keydown", tasto);
      document.removeEventListener("visibilitychange", visibile);
    },
    get punti(){ return s.punti; },
  };
}

export const gioco = {
  id:"incastri", nome:"Incastri", cabinato:{schermo:"I T L", colore:"#9D4EDD"},
  regole:"Dall'alto scendono pezzi fatti di 4 blocchi: componi file piene e spariranno. Tocca a sinistra o a destra per spostare il pezzo, al centro per ruotarlo, scorri in giù per farlo cadere subito (o usa i quattro tasti sotto). L'ombra ti mostra dove cadrà. Una fila vale 100 punti, due insieme 300, tre 500, quattro 800 — per il livello. Ogni 10 file sali di livello e si cade più veloci. Finisce quando un pezzo nuovo non entra. Un gettone ogni 400 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
