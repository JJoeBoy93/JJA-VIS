// ── Il furgone in fuga (Sala giochi): il furgone di Athena Trasporti corre su una strada a 3 corsie, visto da dietro.
// Scorri a sinistra/destra (o i tasti ◀ ▶) per cambiare corsia, in su (o ⤒) per saltare una transenna bassa.
// Auto e cantieri non si saltano: lo schianto chiude la partita. La velocità cresce, le file di ostacoli si fanno più fitte
// e più spesso da due. Ogni fila lascia SEMPRE almeno una corsia libera. Punti: metri/10 + 5 per pacco. Gettoni: punti/10, al massimo 25.
// Le cose in strada stanno in stato.cose: {tipo, corsia (0 sinistra … 2 destra), y (metri davanti al furgone)}.
// Le prove: collaudo/giochi/furgone.mjs.

const CORSIE = 3, ORIZZONTE = 70, MEZZO = 1.6, DIETRO = -6, SALTO = 0.65, PASSO = 1 / 60, DT_MAX = 0.25;
const V0 = 14, VMAX = 42, ACCEL = 0.35;           // metri al secondo: 50 km/h all'inizio, 151 al massimo (dopo 80 s)
const FILA0 = 34, FILA_MIN = 20, STRINGE = 0.25;   // metri fra una fila e la prossima: da 34 giù fino a 20
const PACCO = 0.45, PUNTI_PACCO = 5;
const TIPI = ["auto", "transenna", "cantiere"];

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const velocita = t => Math.min(VMAX, V0 + ACCEL * t);
const distanza = t => Math.max(FILA_MIN, FILA0 - STRINGE * t);
const doppia = t => Math.min(0.7, 0.15 + 0.01 * t);   // probabilità che una fila chiuda due corsie
const kmh = v => Math.round(v * 3.6);
const nuovo = () => ({corsia:1, metri:0, tempo:0, velocita:V0, cose:[], pacchi:0, salto:0, prossima:5, finito:false, schianto:null, id:0});
const punti = s => Math.floor(s.metri / 10) + PUNTI_PACCO * s.pacchi;
const blocca = c => c.tipo !== "pacco";
const tipoA = r => (r < 0.45 ? "auto" : r < 0.75 ? "transenna" : "cantiere");
const pesca = (n, caso) => Math.min(n - 1, Math.floor(caso() * n));

// una fila nuova all'orizzonte: 1 o 2 ostacoli (mai 3), e a volte un pacco in una corsia libera
function generaFila(tempo, caso = Math.random){
  const corsie = [0, 1, 2];
  for (let i = CORSIE - 1; i > 0; i--){ const j = pesca(i + 1, caso); [corsie[i], corsie[j]] = [corsie[j], corsie[i]]; }
  const n = caso() < doppia(tempo) ? 2 : 1;
  const fila = corsie.slice(0, n).map(c => ({tipo:tipoA(caso()), corsia:c, y:ORIZZONTE, tinta:pesca(4, caso)}));
  if (caso() < PACCO) fila.push({tipo:"pacco", corsia:corsie[n + pesca(CORSIE - n, caso)], y:ORIZZONTE});
  return fila;
}
// le corsie che una fila lascia aperte (una transenna chiude: si passa solo saltando)
const corsieLibere = fila => [0, 1, 2].filter(c => !fila.some(o => blocca(o) && o.corsia === c));

function cambiaCorsia(s, verso){
  if (s.finito) return s;
  const c = Math.max(0, Math.min(CORSIE - 1, s.corsia + Math.sign(verso)));
  return c === s.corsia ? s : {...s, corsia:c};
}
const salta = s => (s.finito || s.salto > 0 ? s : {...s, salto:SALTO});
// l'ostacolo contro cui il furgone sbatte adesso, o null. La transenna bassa non si prende se si sta saltando.
const collisione = s => s.cose.find(c => blocca(c) && c.corsia === s.corsia && Math.abs(c.y) <= MEZZO && !(c.tipo === "transenna" && s.salto > 0)) || null;

// muove tutto di dt secondi (a passi di 1/60 s, così niente attraversa il furgone), genera le file, prende i pacchi, guarda lo schianto
function avanza(stato, dt, caso = Math.random){
  if (stato.finito || !(dt > 0)) return stato;
  const s = {...stato, cose:stato.cose.map(c => ({...c}))};
  let resto = Math.min(dt, DT_MAX);
  while (resto > 1e-9 && !s.finito){
    const h = Math.min(PASSO, resto); resto -= h;
    s.tempo += h; s.velocita = velocita(s.tempo); s.salto = Math.max(0, s.salto - h);
    const d = s.velocita * h; s.metri += d;
    for (const c of s.cose) c.y -= d;
    while (s.metri >= s.prossima){
      const oltre = s.metri - s.prossima;   // la fila nasce dove sarebbe se fosse nata al metro giusto: distanze esatte
      for (const c of generaFila(s.tempo, caso)) s.cose.push({...c, y:ORIZZONTE - oltre, id:++s.id});
      s.prossima += distanza(s.tempo);
    }
    const presi = s.cose.filter(c => c.tipo === "pacco" && c.corsia === s.corsia && Math.abs(c.y) <= MEZZO);
    if (presi.length){ s.pacchi += presi.length; s.cose = s.cose.filter(c => !presi.includes(c)); }
    const urto = collisione(s);
    if (urto){ s.finito = true; s.schianto = urto; }
    s.cose = s.cose.filter(c => c.y > DIETRO);
  }
  return s;
}

export const logica = {CORSIE, ORIZZONTE, MEZZO, SALTO, V0, VMAX, FILA_MIN, PUNTI_PACCO, TIPI,
  velocita, distanza, doppia, kmh, nuovo, punti, generaFila, corsieLibere, cambiaCorsia, salta, collisione, avanza};

// ══ il gioco nello strato
const STILE = `
.furgone{position:absolute;inset:0;user-select:none;-webkit-user-select:none}
.furgone canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none}
.furgone .furgone-comandi{position:absolute;left:0;right:0;bottom:0;display:flex;gap:10px;padding:10px 12px calc(10px + env(safe-area-inset-bottom,0px));box-sizing:border-box}
.furgone .furgone-comandi button{flex:1;min-height:76px;font:800 30px/1 var(--f-titoli);color:#e6f6ff;background:color-mix(in srgb,#0b1a2a 78%,transparent);border:2px solid var(--accento);border-radius:14px;cursor:pointer;touch-action:manipulation;padding:0}
.furgone .furgone-comandi button[data-verso="su"]{border-color:var(--oro);color:var(--oro)}
.furgone .furgone-comandi button:active{background:color-mix(in srgb,var(--accento) 35%,#0b1a2a)}`;

const TINTE = ["#E63946", "#4CC9F0", "#B5E48C", "#F4F4F4"];
const F = 8;   // la «focale» della prospettiva: a F metri davanti tutto è grande la metà

function avvia(campo, api){
  if (!document.getElementById("stile-furgone")){ const e = document.createElement("style"); e.id = "stile-furgone"; e.textContent = STILE; document.head.appendChild(e); }
  const css = getComputedStyle(document.documentElement), col = (v, d) => css.getPropertyValue(v).trim() || d;
  const ORO = col("--oro", "#FFD60A"), ACCENTO = col("--accento", "#00B4D8"), TENUE = col("--tenue", "#48CAE4");
  campo.textContent = "";
  const box = document.createElement("div"); box.className = "furgone";
  const tela = document.createElement("canvas"); tela.setAttribute("aria-label", "La strada del furgone in fuga");
  const comandi = document.createElement("div"); comandi.className = "furgone-comandi";
  const tasto = (verso, testo, nome) => { const b = document.createElement("button"); b.type = "button"; b.dataset.verso = verso; b.textContent = testo; b.setAttribute("aria-label", nome); comandi.appendChild(b); return b; };
  const tSx = tasto("sx", "◀", "Corsia a sinistra"), tSu = tasto("su", "⤒", "Salta"), tDx = tasto("dx", "▶", "Corsia a destra");
  box.append(tela, comandi); campo.appendChild(box);
  const ctx = tela.getContext("2d");

  const st = {stato:nuovo(), partito:false, pausa:false, fermo:false, raf:0, timer:null, ultimo:0, W:0, H:0, x:null, scossa:0, lampo:0, testo:"", punti:-1};
  const ascolti = [];
  const ascolta = (bersaglio, ev, fa, opz) => { bersaglio.addEventListener(ev, fa, opz); ascolti.push([bersaglio, ev, fa, opz]); };

  function misura(){
    const r = campo.getBoundingClientRect(), dpr = Math.min(3, window.devicePixelRatio || 1);
    st.W = Math.max(1, r.width); st.H = Math.max(1, r.height);
    tela.width = Math.round(st.W * dpr); tela.height = Math.round(st.H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // ── comandi
  function comando(verso){
    if (st.fermo || st.stato.finito) return;
    if (!st.partito || st.pausa){ riprendi(); return; }
    st.stato = verso === "su" ? salta(st.stato) : cambiaCorsia(st.stato, verso === "sx" ? -1 : 1);
  }
  function riprendi(){
    if (st.stato.finito) return;
    st.partito = true; st.pausa = false; st.ultimo = 0;
    api.esito("Scorri ◀ ▶ per cambiare corsia, in su per saltare le transenne. Prendi i pacchi 📦!");
  }
  [[tSx, "sx"], [tSu, "su"], [tDx, "dx"]].forEach(([b, v]) => ascolta(b, "pointerdown", e => { e.preventDefault(); comando(v); }));
  let tocco = null;
  ascolta(tela, "pointerdown", e => { tocco = {x:e.clientX, y:e.clientY}; });
  ascolta(tela, "pointerup", e => {
    if (!tocco) return; const dx = e.clientX - tocco.x, dy = e.clientY - tocco.y; tocco = null;
    if (!st.partito || st.pausa) return riprendi();
    if (Math.abs(dx) > 28 && Math.abs(dx) > Math.abs(dy)) comando(dx < 0 ? "sx" : "dx");
    else if (dy < -28) comando("su");
    else { const r = tela.getBoundingClientRect(), q = (e.clientX - r.left) / r.width; comando(q < 0.35 ? "sx" : q > 0.65 ? "dx" : "su"); }
  });
  ascolta(tela, "pointercancel", () => { tocco = null; });
  ascolta(window, "keydown", e => {
    const v = {ArrowLeft:"sx", a:"sx", ArrowRight:"dx", d:"dx", ArrowUp:"su", w:"su", " ":"su"}[e.key];
    if (v){ e.preventDefault(); comando(v); }
  });
  ascolta(document, "visibilitychange", () => { if (document.hidden && st.partito && !st.stato.finito){ st.pausa = true; api.esito("In pausa: tocca per ripartire."); } });
  ascolta(window, "resize", misura);
  const osserva = typeof ResizeObserver === "function" ? new ResizeObserver(misura) : null;   // il campo cambia anche senza resize (la riga d'esito)
  if (osserva) osserva.observe(campo);

  // ── la prospettiva: y metri davanti → riga sullo schermo e scala
  const fondoStrada = () => st.H - 118, cielo = () => st.H * 0.24, mezzaStrada = () => Math.min(st.W * 0.47, 220);
  const proietta = y => { const s = F / (F + Math.max(y, -F * 0.6)); return {s, sy:cielo() + (fondoStrada() - cielo()) * s}; };
  const xCorsia = (c, s) => st.W / 2 + (c - 1) * (2 * mezzaStrada() / 3) * s;

  function disegnaFondo(){
    const {W, H} = st, hy = cielo();
    const g = ctx.createLinearGradient(0, 0, 0, hy); g.addColorStop(0, "#020B18"); g.addColorStop(1, "#0b2238");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, hy);
    ctx.fillStyle = "#06101c"; ctx.fillRect(0, hy, W, H - hy);
    // la città all'orizzonte: palazzi con le finestre accese
    for (let i = 0, x = -10; x < W; i++){
      const w = 26 + (i * 37) % 30, h = 18 + (i * 53) % 46;
      ctx.fillStyle = "#081a2c"; ctx.fillRect(x, hy - h, w, h);
      ctx.fillStyle = ORO; ctx.globalAlpha = 0.55;
      for (let fy = hy - h + 5; fy < hy - 5; fy += 8) for (let fx = x + 4; fx < x + w - 4; fx += 7) if (((fx * 7 + fy * 3 + i) | 0) % 5 === 0) ctx.fillRect(fx, fy, 2, 3);
      ctx.globalAlpha = 1; x += w + 4;
    }
    // la strada
    const a = proietta(-F * 0.6), b = proietta(4000), m = mezzaStrada();
    ctx.fillStyle = "#14202c";
    ctx.beginPath(); ctx.moveTo(W / 2 - m * a.s, a.sy); ctx.lineTo(W / 2 + m * a.s, a.sy); ctx.lineTo(W / 2 + m * b.s, b.sy); ctx.lineTo(W / 2 - m * b.s, b.sy); ctx.fill();
    // bordi e strisce (si muovono coi metri)
    ctx.strokeStyle = ACCENTO; ctx.lineWidth = 3; ctx.globalAlpha = 0.8;
    for (const lato of [-1, 1]){ ctx.beginPath(); ctx.moveTo(W / 2 + lato * m * a.s, a.sy); ctx.lineTo(W / 2 + lato * m * b.s, b.sy); ctx.stroke(); }
    ctx.globalAlpha = 1; ctx.fillStyle = TENUE;
    const passo = 8, scarto = st.stato.metri % passo;
    for (let y = -scarto - passo; y < ORIZZONTE + 20; y += passo){
      const p = proietta(y), q = proietta(y + passo / 2); if (p.sy - q.sy < 0.5) continue;
      for (const lato of [-1, 1]){
        const xp = W / 2 + lato * (m / 3) * p.s, xq = W / 2 + lato * (m / 3) * q.s, wp = 3 * p.s, wq = 3 * q.s;
        ctx.globalAlpha = Math.min(0.9, p.s * 1.4);
        ctx.beginPath(); ctx.moveTo(xp - wp, p.sy); ctx.lineTo(xp + wp, p.sy); ctx.lineTo(xq + wq, q.sy); ctx.lineTo(xq - wq, q.sy); ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  }

  const rett = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(x, y, w, h); };
  function disegnaCosa(c){
    const {s, sy} = proietta(c.y), x = xCorsia(c.corsia, s), u = (2 * mezzaStrada() / 3) * s * 0.78;
    if (u < 2) return;
    ctx.globalAlpha = Math.min(1, (ORIZZONTE + 5 - c.y) / 12);
    if (c.tipo === "auto"){
      const w = u, h = u * 0.62;
      rett(x - w / 2, sy - h, w, h, TINTE[c.tinta || 0]);
      rett(x - w * 0.38, sy - h * 0.92, w * 0.76, h * 0.34, "#0d1b29");             // lunotto
      rett(x - w * 0.46, sy - h * 0.45, w * 0.16, h * 0.14, "#ff2d3d");             // fanali
      rett(x + w * 0.30, sy - h * 0.45, w * 0.16, h * 0.14, "#ff2d3d");
      rett(x - w * 0.18, sy - h * 0.3, w * 0.36, h * 0.12, "#e6f6ff");              // targa
      rett(x - w * 0.5, sy - h * 0.08, w, h * 0.08, "#0a0f14");
    } else if (c.tipo === "transenna"){
      const w = u, h = u * 0.2, alto = u * 0.18;
      rett(x - w * 0.42, sy - alto - h, w * 0.06, alto + h, "#c9d6e0"); rett(x + w * 0.36, sy - alto - h, w * 0.06, alto + h, "#c9d6e0");
      ctx.save(); ctx.beginPath(); ctx.rect(x - w / 2, sy - alto - h, w, h); ctx.clip();
      rett(x - w / 2, sy - alto - h, w, h, "#f4f4f4"); ctx.fillStyle = "#E63946";
      for (let i = -1; i < 8; i++){ const x0 = x - w / 2 + i * w / 6; ctx.beginPath(); ctx.moveTo(x0, sy - alto); ctx.lineTo(x0 + w / 12, sy - alto); ctx.lineTo(x0 + w / 12 + h, sy - alto - h); ctx.lineTo(x0 + h, sy - alto - h); ctx.fill(); }
      ctx.restore();
    } else if (c.tipo === "cantiere"){
      const w = u, h = u * 0.55;
      rett(x - w / 2, sy - h, w, h, "#FF8C1A");
      ctx.save(); ctx.beginPath(); ctx.rect(x - w / 2, sy - h, w, h); ctx.clip(); ctx.fillStyle = "#1a1a1a";
      for (let i = -2; i < 8; i++){ const x0 = x - w / 2 + i * w / 5; ctx.beginPath(); ctx.moveTo(x0, sy); ctx.lineTo(x0 + w / 10, sy); ctx.lineTo(x0 + w / 10 + h, sy - h); ctx.lineTo(x0 + h, sy - h); ctx.fill(); }
      ctx.restore();
      ctx.font = `${Math.round(u * 0.42)}px sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.fillText("🚧", x, sy - h);
    } else {
      const sale = Math.sin(st.stato.tempo * 6 + c.id) * u * 0.06;
      ctx.font = `${Math.round(u * 0.55)}px sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.fillText("📦", x, sy - u * 0.12 + sale);
    }
    ctx.globalAlpha = 1;
  }

  function disegnaFurgone(){
    const s = st.stato, u = (2 * mezzaStrada() / 3) * 0.82, base = fondoStrada();
    const meta = xCorsia(s.corsia, 1); st.x = st.x === null ? meta : st.x + (meta - st.x) * 0.3;
    const salto = s.salto > 0 ? Math.sin(Math.PI * (1 - s.salto / SALTO)) * u * 0.55 : 0;
    const x = st.x, w = u, h = u * 0.82, y = base - salto;
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.beginPath(); ctx.ellipse(x, base, w * (0.5 - salto / u * 0.25), w * 0.08, 0, 0, Math.PI * 2); ctx.fill();
    rett(x - w * 0.44, y - h * 0.08, w * 0.18, h * 0.12, "#0a0f14"); rett(x + w * 0.26, y - h * 0.08, w * 0.18, h * 0.12, "#0a0f14");   // ruote
    rett(x - w / 2, y - h, w, h * 0.94, ORO);
    rett(x - 1, y - h * 0.94, 2, h * 0.82, "#8a7300");                                      // le due porte
    rett(x - w * 0.42, y - h * 0.9, w * 0.32, h * 0.2, "#0d1b29"); rett(x + w * 0.1, y - h * 0.9, w * 0.32, h * 0.2, "#0d1b29");
    rett(x - w / 2, y - h * 0.62, w * 0.08, h * 0.16, "#ff2d3d"); rett(x + w * 0.42, y - h * 0.62, w * 0.08, h * 0.16, "#ff2d3d");
    ctx.fillStyle = "#07131f"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.font = `800 ${Math.round(w * 0.12)}px sans-serif`; ctx.fillText("ATHENA", x, y - h * 0.5);
    ctx.font = `700 ${Math.round(w * 0.075)}px sans-serif`; ctx.fillText("TRASPORTI", x, y - h * 0.36);
    rett(x - w / 2, y - h * 0.12, w, h * 0.06, "#2a2a2a");                                   // paraurti
    if (s.finito){ ctx.font = `${Math.round(w * 0.9)}px sans-serif`; ctx.fillText("💥", x, y - h * 0.7); }
  }

  function cartello(titolo, righe){
    const {W, H} = st, w = Math.min(W - 32, 340), x = (W - w) / 2, y = H * 0.3, h = 52 + righe.length * 24;
    ctx.fillStyle = "rgba(7,19,31,.88)"; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = ACCENTO; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    ctx.fillStyle = ORO; ctx.font = "800 24px sans-serif"; ctx.fillText(titolo, W / 2, y + 36);
    ctx.fillStyle = "#e6f6ff"; ctx.font = "500 15px sans-serif"; righe.forEach((r, i) => ctx.fillText(r, W / 2, y + 66 + i * 24));
  }

  function disegna(){
    const {W, H} = st;
    ctx.save(); ctx.clearRect(0, 0, W, H);
    if (st.scossa > 0) ctx.translate((Math.random() - 0.5) * 12 * st.scossa, (Math.random() - 0.5) * 12 * st.scossa);
    disegnaFondo();
    const cose = st.stato.cose.slice().sort((a, b) => b.y - a.y);
    cose.filter(c => c.y >= 0).forEach(disegnaCosa);
    disegnaFurgone();
    cose.filter(c => c.y < 0).forEach(disegnaCosa);
    if (st.lampo > 0){ ctx.fillStyle = ORO; ctx.globalAlpha = st.lampo * 0.25; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    ctx.restore();
    if (!st.partito) cartello("Il furgone in fuga", ["Tocca per partire 🚚", "◀ ▶ cambi corsia · ⤒ salti le transenne", "Prendi i pacchi 📦, evita auto e cantieri"]);
    else if (st.pausa) cartello("In pausa", ["Tocca per ripartire"]);
  }

  function aggiornaBarra(){
    const s = st.stato, p = punti(s);
    if (p !== st.punti){ st.punti = p; api.punti(p); }
    const t = `${Math.floor(s.metri)} m · ${kmh(s.velocita)} km/h · 📦 ${s.pacchi}`;
    if (t !== st.testo){ st.testo = t; api.tempo(t); }
  }

  function giro(ora){
    if (st.fermo) return;
    st.raf = requestAnimationFrame(giro);
    const dt = st.ultimo ? Math.min(0.1, (ora - st.ultimo) / 1000) : 0; st.ultimo = ora;
    if (st.partito && !st.pausa && !st.stato.finito && dt > 0){
      const prima = st.stato.pacchi;
      st.stato = avanza(st.stato, dt, Math.random);
      if (st.stato.pacchi > prima){ st.lampo = 1; api.esito(`Pacco preso! +${PUNTI_PACCO}`); }
      aggiornaBarra();
      if (st.stato.finito){
        const nomi = {auto:"un'auto", transenna:"una transenna (andava saltata!)", cantiere:"un cantiere"};
        api.esito(`Schianto contro ${nomi[st.stato.schianto.tipo] || "un ostacolo"}! ${Math.floor(st.stato.metri)} m e ${st.stato.pacchi} pacchi.`);
        st.scossa = 1; clearTimeout(st.timer); st.timer = setTimeout(() => { if (!st.fermo) api.fine(punti(st.stato)); }, 1500);
      }
    }
    st.scossa = Math.max(0, st.scossa - dt * 1.5); st.lampo = Math.max(0, st.lampo - dt * 3);
    disegna();
  }

  misura(); aggiornaBarra();
  api.esito("Tocca la strada per partire.");
  st.raf = requestAnimationFrame(giro);
  return {
    ferma(){
      st.fermo = true; cancelAnimationFrame(st.raf); clearTimeout(st.timer); if (osserva) osserva.disconnect();
      for (const [b, ev, fa, opz] of ascolti) b.removeEventListener(ev, fa, opz);
      ascolti.length = 0;
    },
    get punti(){ return punti(st.stato); },
  };
}

export const gioco = {
  id:"furgone", nome:"Il furgone in fuga", cabinato:{schermo:"🚚💨", colore:"#00B4D8"},
  regole:"Guida il furgone di Athena Trasporti su una strada a tre corsie. Scorri a sinistra o a destra (o usa ◀ ▶) per cambiare corsia, in su (o ⤒) per saltare le transenne basse. Auto e cantieri non si saltano: uno schianto e la corsa finisce. Più vai avanti, più si corre. Punti: un punto ogni 10 metri e 5 per ogni pacco 📦 preso. Un gettone ogni 10 punti, fino a 25 a partita.",
  massimo:25, gettoni:p => Math.floor(p / 10), avvia,
};
