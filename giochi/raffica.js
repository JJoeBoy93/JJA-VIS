// ── Raffica (Sala giochi): sparatutto a piattaforme a scorrimento laterale, col telefono in verticale.
//   Un soldato corre verso destra in un mondo invaso da un esercito di robot: città in rovina, poi giungla, poi base nel deserto
//   (un ambiente ogni 3 livelli). Il mondo sta nella metà alta del campo, sotto ci sono i comandi grandi:
//   ◀ ▶ corrono, SALTA, SPARA (tenuto premuto spara a raffica), GRANATA (poche, fanno area).
//   Nemici: robot a terra 50 punti, droni a onda 80, torrette ferme 100; ogni 3 livelli un mezzo corazzato 1000.
//   Prigioniero liberato 200. Le casse lasciano un'arma per 12 s (mitragliatrice, fucile a pallini, lanciafiamme) o granate.
//   3 vite, 1,5 s intoccabili dopo un colpo; una buca toglie una vita. Livello dopo livello i nemici sono più fitti e più svelti.
// Gettoni: un gettone ogni 300 punti, al massimo 25.
// Il mondo è in unità del livello (alto 400, il suolo a 330, x verso destra, y verso il basso: la y di una cosa è dove poggia
// i piedi); lo stato è un oggetto semplice che `avanza` non tocca mai: ne restituisce uno nuovo. Le prove: collaudo/giochi/raffica.mjs.

const H = 400, TERRA = 330, PASSO = 1 / 60;
const VITE = 3, INVULN = 1.5, CORSA = 170, SALTO = 580, GRAVITA = 1500, ARMA_TEMPO = 12, ATTIVO = 520;
const GRANATE_INIZIO = 3, GRANATE_MAX = 9, GRANATE_CASSA = 3, GRANATA_ATTESA = 0.5, GRANATA_RAGGIO = 70, GRANATA_DANNO = 4;
const PER_GETTONE = 300, OGNI_CAPO = 3, PRIGIONIERO = 200;
const AMBIENTI = ["citta", "giungla", "deserto"];
// misure e valori: w e h sono la scatola (x al centro, y ai piedi)
const DIM = {
  soldato:{w:20, h:36}, robot:{w:24, h:36, vita:1, punti:50}, drone:{w:28, h:20, vita:1, punti:80}, torretta:{w:26, h:28, vita:3, punti:100},
  capo:{w:130, h:64, punti:1000}, cassa:{w:28, h:28, vita:1}, prigioniero:{w:20, h:32}, oggetto:{w:22, h:22},
};
const ARMI = {
  pistola:{nome:"Pistola", cadenza:0.28, vel:560, portata:620, danno:1, angoli:[0], r:3},
  pesante:{nome:"Mitragliatrice pesante", cadenza:0.08, vel:720, portata:700, danno:1, angoli:[0], dispersione:0.05, r:3},
  ventaglio:{nome:"Fucile a pallini", cadenza:0.5, vel:520, portata:360, danno:1, angoli:[-0.36, -0.18, 0, 0.18, 0.36], r:3},
  fiamma:{nome:"Lanciafiamme", cadenza:0.09, vel:340, portata:120, danno:1, angoli:[0], dispersione:0.25, passa:true, r:7},
};
const DROP = ["pesante", "ventaglio", "fiamma", "granate"];

// ══ la logica: solo funzioni pure, niente DOM (si prova in node)
const limita = (v, a, b) => Math.max(a, Math.min(b, v));
const gettoni = p => Math.min(25, Math.floor(Math.max(0, Number(p) || 0) / PER_GETTONE));
function seme(n){ let a = n >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const ambiente = n => AMBIENTI[Math.floor((Math.max(1, n) - 1) / OGNI_CAPO) % AMBIENTI.length];
const conCapo = n => n % OGNI_CAPO === 0;
const vitaCapo = n => 40 + 20 * (Math.floor(n / OGNI_CAPO) - 1);
const velocita = n => Math.min(1.8, 1 + 0.06 * (Math.max(1, n) - 1));
const inBuca = (buche, x, m = 0) => buche.some(b => x > b.x - m && x < b.x + b.w + m);

// il livello n (da 1): lo stesso seme dà sempre lo stesso livello. Le buche si saltano (larghe 70–109), le piattaforme si salgono
// con un salto (alte 70 o 90); più avanti ci sono più nemici, più fitti. Ogni 3 livelli, in fondo, c'è il capo.
function livello(n){
  n = Math.max(1, Math.floor(Number(n) || 1));
  const r = seme(n * 7919 + 104729), capo = conCapo(n);
  const lunghezza = Math.min(6400, 2400 + 260 * n), fine = lunghezza - (capo ? 560 : 260);
  const piattaforme = [], buche = [], nemici = [], casse = [], prigionieri = [];
  const passo = Math.max(120, 230 - 12 * n), pBuca = Math.min(0.28, 0.12 + 0.02 * n);
  const drop = () => DROP[Math.floor(r() * DROP.length)];
  let x = 380, ultimaBuca = false;
  while (x < fine){
    if (!ultimaBuca && r() < pBuca){ const w = 70 + Math.floor(r() * 40); buche.push({x:Math.round(x), w}); x += w + 150; ultimaBuca = true; continue; }
    ultimaBuca = false;
    const k = r(), X = Math.round(x);
    if (k < 0.42){ nemici.push({tipo:"robot", x:X, y:TERRA}); if (n >= 4 && r() < 0.4) nemici.push({tipo:"robot", x:X + 40, y:TERRA}); }
    else if (k < 0.66) nemici.push({tipo:"drone", x:X + 200, y:250});
    else if (k < 0.82 && n >= 2) nemici.push({tipo:"torretta", x:X, y:TERRA});
    else {
      const p = {x:X, y:TERRA - (r() < 0.5 ? 70 : 90), w:100 + Math.floor(r() * 45)}; piattaforme.push(p);
      if (r() < 0.6) casse.push({x:X + Math.round(p.w / 2), y:p.y, drop:drop()});
      else nemici.push({tipo:"robot", x:X + Math.round(p.w / 2), y:p.y, min:p.x + 12, max:p.x + p.w - 12});
    }
    if (r() < 0.22) casse.push({x:X + 60, y:TERRA, drop:drop()});
    if (r() < 0.12) prigionieri.push({x:X + 40, y:TERRA});
    x += passo + r() * 100;
  }
  if (!prigionieri.length){ let px = Math.round(lunghezza / 2); while (inBuca(buche, px, 30)) px -= 10; prigionieri.push({x:px, y:TERRA}); }
  // i robot e le torrette a terra: il tratto di suolo su cui stanno (tra una buca e l'altra)
  for (const e of nemici) if (e.y === TERRA){
    e.min = buche.reduce((m, b) => (b.x + b.w <= e.x ? Math.max(m, b.x + b.w) : m), 0) + 10;
    e.max = buche.reduce((m, b) => (b.x >= e.x ? Math.min(m, b.x) : m), lunghezza) - 10;
  }
  return {n, seme:n * 7919 + 104729, ambiente:ambiente(n), lunghezza, piattaforme, buche, nemici, casse, prigionieri,
    capo:capo ? {x:lunghezza - 300, y:TERRA, vita:vitaCapo(n)} : null};
}

// la scatola di una cosa (x al centro, y ai piedi) e il colpo che la tocca (cerchio di raggio r)
const scatola = o => ({x:o.x, y:o.y, w:DIM[o.tipo].w, h:DIM[o.tipo].h});
function colpisce(colpo, bersaglio){
  const r = colpo.r == null ? 3 : colpo.r, {x, y, w, h} = bersaglio;
  return colpo.x + r > x - w / 2 && colpo.x - r < x + w / 2 && colpo.y + r > y - h && colpo.y - r < y;
}
const sovrappone = (a, b) => Math.abs(a.x - b.x) < (a.w + b.w) / 2 && a.y > b.y - b.h && a.y - a.h < b.y;
const scatolaSoldato = s => ({x:s.soldato.x, y:s.soldato.y, w:DIM.soldato.w, h:DIM.soldato.h});

// l'arma in mano: quella presa da una cassa finché dura, se no la pistola
function arma(stato){
  const tipo = stato.arma && stato.t < stato.arma.fino && ARMI[stato.arma.tipo] ? stato.arma.tipo : "pistola";
  return {tipo, ...ARMI[tipo]};
}
const intoccabile = s => s.t < s.invulnFino;

function caricaLivello(s, n){
  const L = livello(n); let id = 0;
  s.livello = n; s.ambiente = L.ambiente; s.lunghezza = L.lunghezza;
  s.piattaforme = L.piattaforme.map(p => ({...p})); s.buche = L.buche.map(b => ({...b}));
  s.nemici = L.nemici.map(e => ({...e, id:id++, vita:DIM[e.tipo].vita, y0:e.y, fase:0, dir:-1, ricarica:1 + (id % 3) * 0.6, attivo:false}));
  s.casse = L.casse.map((c, i) => ({...c, id:"c" + i, tipo:"cassa", vita:DIM.cassa.vita}));
  s.prigionieri = L.prigionieri.map(p => ({...p, tipo:"prigioniero"}));
  s.capo = L.capo && {...L.capo, tipo:"capo", id:"capo", max:L.capo.vita, dir:-1, ricarica:2, attivo:false};
  s.oggetti = []; s.colpi = []; s.spariN = []; s.bombe = [];
  s.soldato = {x:40, y:TERRA, vx:0, vy:0, dir:1, aTerra:true};
  return s;
}
function nuovaPartita(){
  return caricaLivello({t:0, punti:0, vite:VITE, finito:false, granate:GRANATE_INIZIO, arma:null, ricarica:0, ricGranata:0, invulnFino:0, eventi:[]}, 1);
}
const copia = s => ({...s, soldato:{...s.soldato}, arma:s.arma && {...s.arma}, piattaforme:s.piattaforme.map(o => ({...o})), buche:s.buche.map(o => ({...o})),
  nemici:s.nemici.map(o => ({...o})), casse:s.casse.map(o => ({...o})), prigionieri:s.prigionieri.map(o => ({...o})), capo:s.capo && {...s.capo},
  oggetti:s.oggetti.map(o => ({...o})), colpi:s.colpi.map(o => ({...o, visti:o.visti.slice()})), spariN:s.spariN.map(o => ({...o})), bombe:s.bombe.map(o => ({...o})), eventi:[]});

// un colpo al soldato: appena colpiti si è intoccabili 1,5 s; a zero vite la partita è finita
function ferisci(s){
  if (s.finito || intoccabile(s)) return false;
  s.vite = Math.max(0, s.vite - 1); s.invulnFino = s.t + INVULN; s.eventi.push({tipo:"ahi", x:s.soldato.x, y:s.soldato.y});
  if (s.vite === 0){ s.finito = true; s.eventi.push({tipo:"fine"}); }
  return true;
}
function ferito(stato){ const s = copia(stato); ferisci(s); return s; }
// caduto in una buca: una vita in meno comunque; si riparte dal suolo prima della buca, intoccabile per un attimo
function cadi(s){
  s.vite = Math.max(0, s.vite - 1); s.eventi.push({tipo:"buca"});
  if (s.vite === 0){ s.finito = true; s.eventi.push({tipo:"fine"}); return; }
  const so = s.soldato; let x = so.x; while (x > 20 && inBuca(s.buche, x, 40)) x -= 10;
  so.x = Math.max(20, x); so.y = TERRA; so.vy = 0; so.vx = 0; so.aTerra = true; s.invulnFino = s.t + INVULN;
}

// un danno a una cosa colpibile (nemico, capo, cassa): se muore, punti o regalo
function danneggia(s, b, danno){
  b.vita -= danno;
  if (b.vita > 0){ s.eventi.push({tipo:"tac", x:b.x, y:b.y - DIM[b.tipo].h / 2}); return; }
  b.via = true;
  if (b.tipo === "cassa"){ s.oggetti.push({tipo:"oggetto", cosa:b.drop, x:b.x, y:b.y}); s.eventi.push({tipo:"cassa", x:b.x, y:b.y - 14}); }
  else { s.punti += DIM[b.tipo].punti; s.eventi.push({tipo:"boom", x:b.x, y:b.y - DIM[b.tipo].h / 2, chi:b.tipo}); }
}
const bersagli = s => [...s.nemici, ...(s.capo ? [s.capo] : []), ...s.casse].filter(b => !b.via);

function spara(s, caso){
  const a = arma(s), so = s.soldato, d = so.dir;
  for (const a0 of a.angoli){
    const ang = a0 + (a.dispersione ? (caso() - 0.5) * a.dispersione : 0), x = so.x + d * 14, y = so.y - 22;
    s.colpi.push({x, y, x0:x, y0:y, vx:d * Math.cos(ang) * a.vel, vy:Math.sin(ang) * a.vel, portata:a.portata, danno:a.danno, r:a.r, passa:!!a.passa, tipo:a.tipo, visti:[]});
  }
  s.eventi.push({tipo:"sparo", arma:a.tipo});
}
function esplodi(s, g){
  s.eventi.push({tipo:"bum", x:g.x, y:g.y}); g.via = true;
  for (const b of bersagli(s)){
    const d = DIM[b.tipo], dist = Math.hypot(b.x - g.x, b.y - d.h / 2 - g.y);
    if (dist <= GRANATA_RAGGIO + d.w / 2) danneggia(s, b, GRANATA_DANNO);
  }
}
function atterra(s, so, yPrima){
  if (so.vy < 0) return false;
  let sy = null;
  for (const p of s.piattaforme) if (so.x >= p.x - 4 && so.x <= p.x + p.w + 4 && yPrima <= p.y + 0.5 && so.y >= p.y && (sy === null || p.y < sy)) sy = p.y;
  if (!inBuca(s.buche, so.x) && yPrima <= TERRA + 0.5 && so.y >= TERRA && (sy === null || TERRA < sy)) sy = TERRA;
  if (sy === null) return false;
  so.y = sy; so.vy = 0; return true;
}

function passo(s, h, cmd, caso){
  s.t += h;
  const so = s.soldato, v = velocita(s.livello);
  // il soldato: corre, salta, cade
  const verso = (cmd.dx ? 1 : 0) - (cmd.sx ? 1 : 0);
  if (verso) so.dir = verso;
  so.vx = verso * CORSA;
  if (cmd.salta && so.aTerra){ so.vy = -SALTO; so.aTerra = false; s.eventi.push({tipo:"salto"}); }
  const yPrima = so.y;
  so.vy += GRAVITA * h; so.x = limita(so.x + so.vx * h, 12, s.lunghezza); so.y += so.vy * h;
  so.aTerra = atterra(s, so, yPrima);
  // spara a raffica e lancia le granate
  if (s.ricarica > 0) s.ricarica -= h;
  if (cmd.spara && s.ricarica <= 0){ spara(s, caso); s.ricarica = arma(s).cadenza; }
  if (s.ricGranata > 0) s.ricGranata -= h;
  if (cmd.granata && s.granate > 0 && s.ricGranata <= 0){
    s.granate--; s.ricGranata = GRANATA_ATTESA;
    s.bombe.push({x:so.x + so.dir * 10, y:so.y - 26, vx:so.dir * 230 + so.vx * 0.3, vy:-320, eta:0}); s.eventi.push({tipo:"lancio"});
  }
  // i colpi in volo
  for (const c of s.colpi){ c.x += c.vx * h; c.y += c.vy * h; if (Math.hypot(c.x - c.x0, c.y - c.y0) > c.portata || c.y < -20 || c.y > H + 20) c.via = true; }
  for (const p of s.spariN){ p.x += p.vx * h; p.y += p.vy * h; if (Math.abs(p.x - so.x) > 700 || p.y < -20 || p.y > H + 20) p.via = true; }
  // i nemici: si svegliano quando il soldato è vicino
  const mira = (x, y, vel, extra = 0) => { const dx = so.x - x, dy = so.y - 18 - y, d = Math.hypot(dx, dy) || 1; return {vx:dx / d * vel, vy:dy / d * vel + extra}; };
  for (const n of s.nemici){
    if (Math.abs(n.x - so.x) < ATTIVO) n.attivo = true;
    if (!n.attivo) continue;
    const dx = so.x - n.x;
    if (n.tipo === "robot"){
      if (Math.abs(dx) > 10) n.x = limita(n.x + Math.sign(dx) * 60 * v * h, n.min, n.max);
      n.ricarica -= h;
      if (n.ricarica <= 0 && Math.abs(dx) < 300){ s.spariN.push({x:n.x, y:n.y - 22, vx:Math.sign(dx) * 220 * v, vy:0, r:4}); n.ricarica = 2.2 / v + caso() * 1.5; }
    } else if (n.tipo === "drone"){
      n.fase += 3 * h; n.x -= 90 * v * h; n.y = n.y0 + Math.sin(n.fase) * 45;
      if (n.x < so.x - 600) n.via = true;
    } else if (n.tipo === "torretta"){
      n.ricarica -= h;
      if (n.ricarica <= 0 && Math.abs(dx) < 380){ s.spariN.push({x:n.x, y:n.y - 14, ...mira(n.x, n.y - 14, 190 * v), r:4}); n.ricarica = 1.8 / v + caso(); }
    }
  }
  const capo = s.capo;
  if (capo){
    if (Math.abs(capo.x - so.x) < ATTIVO) capo.attivo = true;
    if (capo.attivo){
      const a = s.lunghezza - 460, b = s.lunghezza - 140;
      capo.x += capo.dir * 50 * v * h; if (capo.x > b){ capo.x = b; capo.dir = -1; } if (capo.x < a){ capo.x = a; capo.dir = 1; }
      capo.ricarica -= h;
      if (capo.ricarica <= 0){ const m = mira(capo.x, capo.y - 40, 210 * v);
        for (const rot of [-0.2, 0, 0.2]){ const c = Math.cos(rot), sn = Math.sin(rot); s.spariN.push({x:capo.x - 50, y:capo.y - 40, vx:m.vx * c - m.vy * sn, vy:m.vx * sn + m.vy * c, r:5}); }
        capo.ricarica = Math.max(1, 2.2 / v); }
    }
  }
  // le granate: arco, poi esplodono a terra, su una piattaforma, su un bersaglio o dopo 1,4 s
  for (const g of s.bombe){
    const yp = g.y; g.eta += h; g.vy += GRAVITA * 0.8 * h; g.x += g.vx * h; g.y += g.vy * h;
    const sopra = s.piattaforme.some(p => g.x >= p.x && g.x <= p.x + p.w && yp <= p.y && g.y >= p.y);
    const suolo = !inBuca(s.buche, g.x) && yp <= TERRA && g.y >= TERRA;
    const bersaglio = bersagli(s).some(b => colpisce({x:g.x, y:g.y, r:5}, scatola(b)));
    if (g.y > H + 20) g.via = true;
    else if (sopra || suolo || bersaglio || g.eta > 1.4) esplodi(s, g);
  }
  // i miei colpi contro nemici, capo e casse: quelli che «passano» (fiamma) colpiscono ognuno una volta sola
  for (const c of s.colpi){
    if (c.via) continue;
    for (const b of bersagli(s)){
      if (c.visti.includes(b.id) || !colpisce(c, scatola(b))) continue;
      danneggia(s, b, c.danno);
      if (c.passa) c.visti.push(b.id); else { c.via = true; break; }
    }
  }
  // quello che tocca il soldato
  const sc = scatolaSoldato(s);
  for (const p of s.spariN) if (!p.via && colpisce(p, sc)){ p.via = true; ferisci(s); }
  for (const n of s.nemici) if (!n.via && sovrappone(sc, scatola(n))) ferisci(s);
  if (s.capo && sovrappone(sc, scatola(s.capo))) ferisci(s);
  for (const p of s.prigionieri) if (!p.via && sovrappone(sc, scatola(p))){ p.via = true; s.punti += PRIGIONIERO; s.eventi.push({tipo:"libero", x:p.x, y:p.y - 16}); }
  for (const o of s.oggetti) if (!o.via && sovrappone(sc, scatola(o))){
    o.via = true;
    if (o.cosa === "granate") s.granate = Math.min(GRANATE_MAX, s.granate + GRANATE_CASSA); else s.arma = {tipo:o.cosa, fino:s.t + ARMA_TEMPO};
    s.eventi.push({tipo:"preso", cosa:o.cosa});
  }
  if (so.y > H + 60 && !s.finito) cadi(s);
  // via quello che è finito
  if (s.capo && s.capo.via) s.capo = null;
  s.colpi = s.colpi.filter(c => !c.via); s.spariN = s.spariN.filter(p => !p.via); s.bombe = s.bombe.filter(g => !g.via);
  s.nemici = s.nemici.filter(n => !n.via); s.casse = s.casse.filter(c => !c.via); s.prigionieri = s.prigionieri.filter(p => !p.via); s.oggetti = s.oggetti.filter(o => !o.via);
  // fondo del livello (e il capo abbattuto): il prossimo
  if (!s.finito && !s.capo && s.soldato.x >= s.lunghezza - 1){
    const n = s.livello; caricaLivello(s, n + 1); s.eventi.push({tipo:"livello", n:n + 1});
  }
}
// avanza di dt secondi (a passi di 1/60 s, al massimo 1/4 di secondo per volta). comandi: {sx, dx, salta, spara, granata}
function avanza(stato, dt, comandi = {}, caso = Math.random){
  if (stato.finito || !(dt > 0)) return stato;
  const s = copia(stato);
  let resto = Math.min(dt, 0.25);
  while (resto > 1e-9 && !s.finito){ const h = Math.min(resto, PASSO); passo(s, h, comandi || {}, caso); resto -= h; }
  return s;
}

export const logica = {H, TERRA, VITE, INVULN, CORSA, SALTO, GRAVITA, ARMA_TEMPO, GRANATE_INIZIO, GRANATA_RAGGIO, GRANATA_DANNO, PER_GETTONE, OGNI_CAPO, DIM, ARMI,
  gettoni, ambiente, conCapo, vitaCapo, velocita, inBuca, livello, colpisce, arma, nuovaPartita, ferito, avanza, intoccabile};

// ══ il gioco nello strato: un canvas che riempie il campo; il mondo in alto, i comandi in basso
const TITOLI = "Archivo,system-ui,sans-serif", MONO = '"DM Mono",ui-monospace,monospace';
const COLORI = {citta:{cielo:["#0a1424", "#1d2b44"], suolo:"#2a3340", bordo:"#00B4D8"}, giungla:{cielo:["#04160f", "#0f3a26"], suolo:"#1d3b1f", bordo:"#6bd16b"},
  deserto:{cielo:["#2a1708", "#6a4216"], suolo:"#6b4a22", bordo:"#FFD60A"}};
const SIGLA = {pesante:"M", ventaglio:"V", fiamma:"F", granate:"G"}, COL_COSA = {pesante:"#FFD60A", ventaglio:"#00B4D8", fiamma:"#ff7b00", granate:"#8ac926"};
const frac = x => x - Math.floor(x), cas = i => frac(Math.sin(i * 127.1 + 311.7) * 43758.5453);

function avvia(campo, api){
  const tinta = (n, d) => (getComputedStyle(campo).getPropertyValue(n).trim() || d);
  const C = {oro:tinta("--oro", "#FFD60A"), accento:tinta("--accento", "#00B4D8"), tenue:tinta("--tenue", "#48CAE4"), fondo:"#050d18", nemico:"#ff4d6d"};
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:100%;touch-action:none;user-select:none;-webkit-user-select:none";
  cv.setAttribute("aria-label", "Raffica: in basso i comandi per correre, saltare, sparare e lanciare granate");
  campo.textContent = ""; campo.appendChild(cv);
  const ctx = cv.getContext("2d");
  let s = nuovaPartita(), fase = "pronto", raf = 0, prima = 0, timerFine = 0, fermo = false, dpr = 1;
  let l = 390, a = 700, hm = 350, k = 0.875, visW = 445, cam = 0, bott = [], particelle = [], granataSosp = false, scritte = {punti:-1, tempo:""};
  const toccati = new Map(), tasti = {};

  function misura(){
    const r = campo.getBoundingClientRect(); l = Math.max(240, r.width || 390); a = Math.max(360, r.height || 700);
    dpr = Math.min(3, window.devicePixelRatio || 1);
    cv.width = Math.round(l * dpr); cv.height = Math.round(a * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    hm = Math.round(a * 0.5); k = hm / H; visW = l / k;
    const m = 8, y0 = hm + 10, ah = a - hm - 18, rg = ah * 0.28, y1 = y0 + rg + m, h2 = ah - rg - m, q = l * 0.25;
    bott = [{k:"sx", x:m, y:y1, w:q - m * 1.5, h:h2}, {k:"dx", x:q + m * 0.5, y:y1, w:q - m * 1.5, h:h2},
      {k:"salta", x:l * 0.5 + m * 0.5, y:y1, w:l * 0.22 - m, h:h2, t:"SALTA"}, {k:"spara", x:l * 0.72 + m * 0.5, y:y1, w:l * 0.28 - m * 1.5, h:h2, t:"SPARA"},
      {k:"granata", x:l * 0.5 + m * 0.5, y:y0, w:l * 0.5 - m * 1.5, h:rg, t:"GRANATA"}];
  }
  misura();
  const trova = (x, y) => { const b = bott.find(b => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h); return b ? b.k : null; };
  const comandi = () => { const att = new Set(toccati.values());
    return {sx:att.has("sx") || !!tasti.ArrowLeft, dx:att.has("dx") || !!tasti.ArrowRight, salta:att.has("salta") || !!tasti.ArrowUp || !!tasti.z,
      spara:att.has("spara") || !!tasti[" "] || !!tasti.x, granata:granataSosp}; };

  const pausa = () => { if (fase !== "gioco") return; fase = "pausa"; toccati.clear(); api.esito("In pausa: tocca lo schermo per riprendere."); };
  const riprendi = () => { if (fase !== "pausa" && fase !== "pronto") return; fase = "gioco"; prima = 0; api.esito("Corri a destra: spara ai robot, salta le buche."); };
  function giu(e){
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    e.preventDefault(); if (fase === "fine") return;
    if (fase !== "gioco"){ riprendi(); return; }
    if (x > l - 56 && y < 56){ pausa(); return; }
    const b = trova(x, y); toccati.set(e.pointerId, b); if (b === "granata") granataSosp = true;
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
  }
  function sposta(e){
    if (!toccati.has(e.pointerId)) return;
    const r = cv.getBoundingClientRect(), b = trova(e.clientX - r.left, e.clientY - r.top);
    if (b === "granata" && toccati.get(e.pointerId) !== "granata") granataSosp = true;
    toccati.set(e.pointerId, b); e.preventDefault();
  }
  const su = e => { toccati.delete(e.pointerId); };
  function tasto(e){
    const premuto = e.type === "keydown", t = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (["ArrowLeft", "ArrowRight", "ArrowUp", " ", "z", "x"].includes(t)){ tasti[t] = premuto; e.preventDefault(); if (premuto && fase !== "gioco" && fase !== "fine") riprendi(); }
    else if (premuto && t === "g"){ granataSosp = true; }
    else if (premuto && (t === "p" || t === "Escape")){ if (fase === "gioco") pausa(); else if (fase !== "fine") riprendi(); }
  }
  const visibile = () => { if (document.hidden) pausa(); };
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => misura()) : null;
  if (ro) ro.observe(campo); else window.addEventListener("resize", misura);
  cv.addEventListener("pointerdown", giu); cv.addEventListener("pointermove", sposta);
  cv.addEventListener("pointerup", su); cv.addEventListener("pointercancel", su);
  window.addEventListener("keydown", tasto); window.addEventListener("keyup", tasto);
  document.addEventListener("visibilitychange", visibile);

  function scintille(x, y, tanti, colori, forza = 160){
    for (let i = 0; i < tanti; i++){ const ang = Math.random() * 6.28, v = 30 + Math.random() * forza;
      particelle.push({x, y, vx:Math.cos(ang) * v, vy:Math.sin(ang) * v - 30, vita:0.6, colore:colori[i % colori.length]}); }
  }
  function racconta(eventi){
    for (const e of eventi){
      if (e.tipo === "boom") scintille(e.x, e.y, e.chi === "capo" ? 50 : 14, [C.oro, C.accento, "#ff7b00"], e.chi === "capo" ? 300 : 160);
      else if (e.tipo === "bum") scintille(e.x, e.y, 36, ["#ff7b00", C.oro, "#fff"], 260);
      else if (e.tipo === "cassa") scintille(e.x, e.y, 10, ["#b8793a", C.oro]);
      else if (e.tipo === "tac") scintille(e.x, e.y, 3, [C.oro], 80);
      else if (e.tipo === "ahi") api.esito(s.vite ? `Colpito! Ti restano ${s.vite} ${s.vite === 1 ? "vita" : "vite"}.` : "Colpito!");
      else if (e.tipo === "buca") api.esito(s.vite ? `Sei caduto in una buca! Ti restano ${s.vite} ${s.vite === 1 ? "vita" : "vite"}.` : "Sei caduto in una buca!");
      else if (e.tipo === "libero") api.esito("Prigioniero liberato: +200!");
      else if (e.tipo === "preso") api.esito(e.cosa === "granate" ? `+${GRANATE_CASSA} granate!` : `${ARMI[e.cosa].nome} per ${ARMA_TEMPO} secondi!`);
      else if (e.tipo === "livello") api.esito(`Livello ${e.n}${conCapo(e.n) ? ": in fondo c'è un mezzo corazzato!" : "!"}`);
    }
  }
  function scriviBarra(){
    if (s.punti !== scritte.punti){ scritte.punti = s.punti; api.punti(s.punti); }
    const t = `Livello ${s.livello} · vite ${s.vite} · granate ${s.granate}`;
    if (t !== scritte.tempo){ scritte.tempo = t; api.tempo(t); }
  }

  // ── il disegno
  function strato(par, larg, f){ const off = cam * par; for (let i = Math.floor(off / larg); i * larg - off < visW; i++) f(i, i * larg - off, larg); }
  function sfondo(){
    const co = COLORI[s.ambiente] || COLORI.citta, g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, co.cielo[0]); g.addColorStop(1, co.cielo[1]);
    ctx.fillStyle = g; ctx.fillRect(0, 0, visW, H);
    if (s.ambiente === "citta"){
      strato(0.25, 90, (i, x, w) => { const h = 110 + cas(i) * 150; ctx.fillStyle = "#0f1d30"; ctx.beginPath(); ctx.moveTo(x, TERRA); ctx.lineTo(x, TERRA - h);
        ctx.lineTo(x + w * 0.35, TERRA - h + 18 * cas(i + 9)); ctx.lineTo(x + w * 0.6, TERRA - h - 10); ctx.lineTo(x + w * 0.85, TERRA - h + 30); ctx.lineTo(x + w * 0.85, TERRA); ctx.fill();
        ctx.fillStyle = "rgba(255,214,10,.25)"; for (let j = 0; j < 5; j++) if (cas(i * 7 + j) > 0.55) ctx.fillRect(x + 8 + (j % 3) * 18, TERRA - h + 30 + Math.floor(j / 3) * 26, 6, 8); });
      strato(0.5, 70, (i, x, w) => { const h = 50 + cas(i + 40) * 80; ctx.fillStyle = "#16294a"; ctx.fillRect(x, TERRA - h, w * 0.8, h); });
    } else if (s.ambiente === "giungla"){
      strato(0.25, 110, (i, x) => { ctx.fillStyle = "#0b3324"; ctx.beginPath(); ctx.arc(x + 40, TERRA - 120 - cas(i) * 60, 60 + cas(i + 3) * 25, 0, 6.29); ctx.fill(); });
      strato(0.5, 80, (i, x) => { const h = 90 + cas(i + 20) * 70; ctx.fillStyle = "#3b2a14"; ctx.fillRect(x + 28, TERRA - h, 10, h);
        ctx.fillStyle = "#14532d"; ctx.beginPath(); ctx.arc(x + 33, TERRA - h, 34, 0, 6.29); ctx.fill(); });
    } else {
      ctx.fillStyle = "#7a5424"; ctx.beginPath(); ctx.moveTo(0, TERRA); strato(0.2, 40, (i, x) => ctx.lineTo(x, TERRA - 60 - Math.sin(i * 0.5) * 40 - cas(i) * 20)); ctx.lineTo(visW, TERRA); ctx.fill();
      strato(0.5, 200, (i, x) => { ctx.fillStyle = "#4a3418"; ctx.fillRect(x + 20, TERRA - 70 - cas(i) * 40, 110, 90); ctx.fillStyle = "#2a1b0a"; ctx.fillRect(x + 50, TERRA - 40, 28, 40); });
    }
  }
  const sx = x => x - cam;
  function suolo(){
    const co = COLORI[s.ambiente] || COLORI.citta;
    ctx.fillStyle = co.suolo; ctx.fillRect(0, TERRA, visW, H - TERRA); ctx.fillStyle = co.bordo; ctx.fillRect(0, TERRA, visW, 3);
    for (const b of s.buche){ const x = sx(b.x); if (x > visW || x + b.w < 0) continue;
      ctx.fillStyle = "#02060c"; ctx.fillRect(x, TERRA, b.w, H - TERRA); ctx.fillStyle = C.nemico; for (let i = 0; i < b.w; i += 14) ctx.fillRect(x + i, TERRA, 7, 3); }
    for (const p of s.piattaforme){ const x = sx(p.x); if (x > visW || x + p.w < 0) continue;
      ctx.fillStyle = co.suolo; ctx.fillRect(x, p.y, p.w, 12); ctx.fillStyle = co.bordo; ctx.fillRect(x, p.y, p.w, 3); }
  }
  function soldato(){
    const so = s.soldato, x = sx(so.x), y = so.y, d = so.dir, corre = Math.abs(so.vx) > 1 && so.aTerra, passo = corre ? Math.sin(s.t * 16) * 5 : 0;
    if (s.t < s.invulnFino && Math.floor(s.t * 14) % 2) return;
    ctx.fillStyle = "#3d5a40"; ctx.fillRect(x - 6 + passo, y - 14, 5, 14); ctx.fillRect(x + 1 - passo, y - 14, 5, 14);
    ctx.fillStyle = "#4f7a52"; ctx.fillRect(x - 8, y - 28, 16, 16);
    ctx.fillStyle = "#e0b184"; ctx.beginPath(); ctx.arc(x, y - 32, 6, 0, 6.29); ctx.fill();
    ctx.fillStyle = C.oro; ctx.beginPath(); ctx.arc(x, y - 34, 6.5, Math.PI, 0); ctx.fill(); ctx.fillRect(x - 6.5, y - 34, 13, 2);
    ctx.fillStyle = "#222"; ctx.fillRect(d > 0 ? x : x - 20, y - 25, 20, 5);
  }
  function robot(n){ const x = sx(n.x), y = n.y, d = Math.sign(s.soldato.x - n.x) || 1, p = Math.sin(s.t * 10 + n.id) * 4;
    ctx.fillStyle = "#566377"; ctx.fillRect(x - 7 + p, y - 12, 5, 12); ctx.fillRect(x + 2 - p, y - 12, 5, 12);
    ctx.fillStyle = "#7a8aa0"; ctx.fillRect(x - 10, y - 28, 20, 18); ctx.fillRect(x - 7, y - 36, 14, 9);
    ctx.fillStyle = C.nemico; ctx.fillRect(x + (d > 0 ? 1 : -6), y - 33, 5, 4); ctx.fillStyle = "#222"; ctx.fillRect(d > 0 ? x : x - 18, y - 22, 18, 4); }
  function drone(n){ const x = sx(n.x), y = n.y - 10;
    ctx.fillStyle = "#6b7a92"; ctx.beginPath(); ctx.ellipse(x, y, 14, 7, 0, 0, 6.29); ctx.fill();
    ctx.strokeStyle = C.tenue; ctx.lineWidth = 2; const r = Math.sin(s.t * 40) * 14; ctx.beginPath(); ctx.moveTo(x - r, y - 9); ctx.lineTo(x + r, y - 9); ctx.stroke();
    ctx.fillStyle = C.nemico; ctx.beginPath(); ctx.arc(x - 6, y + 1, 3, 0, 6.29); ctx.fill(); }
  function torretta(n){ const x = sx(n.x), y = n.y, so = s.soldato, ang = Math.atan2(so.y - 18 - (y - 14), so.x - n.x);
    ctx.fillStyle = "#566377"; ctx.beginPath(); ctx.moveTo(x - 13, y); ctx.lineTo(x - 8, y - 12); ctx.lineTo(x + 8, y - 12); ctx.lineTo(x + 13, y); ctx.fill();
    ctx.fillStyle = "#7a8aa0"; ctx.beginPath(); ctx.arc(x, y - 14, 9, 0, 6.29); ctx.fill();
    ctx.save(); ctx.translate(x, y - 14); ctx.rotate(ang); ctx.fillStyle = "#222"; ctx.fillRect(0, -2.5, 18, 5); ctx.restore();
    if (n.vita < 3){ ctx.fillStyle = C.nemico; ctx.fillRect(x - 10, y - 32, 20 * n.vita / 3, 3); } }
  function capo(c){ const x = sx(c.x), y = c.y;
    ctx.fillStyle = "#2b3442"; ctx.fillRect(x - 65, y - 16, 130, 16); ctx.fillStyle = "#566377"; for (let i = -55; i <= 55; i += 22){ ctx.beginPath(); ctx.arc(x + i, y - 8, 8, 0, 6.29); ctx.fill(); }
    ctx.fillStyle = "#7a8aa0"; ctx.fillRect(x - 58, y - 44, 116, 30); ctx.fillStyle = "#566377"; ctx.fillRect(x - 28, y - 62, 52, 20);
    ctx.fillStyle = "#222"; ctx.fillRect(x - 75, y - 54, 52, 8); ctx.fillStyle = C.nemico; ctx.fillRect(x - 20, y - 56, 8, 6);
    const w = 130; ctx.fillStyle = "#13283b"; ctx.fillRect(x - 65, y - 76, w, 8); ctx.fillStyle = C.oro; ctx.fillRect(x - 65, y - 76, w * Math.max(0, c.vita) / c.max, 8); }
  function oggetti(){
    for (const c of s.casse){ const x = sx(c.x); ctx.fillStyle = "#8a5a2b"; ctx.fillRect(x - 14, c.y - 28, 28, 28); ctx.strokeStyle = "#c98b4a"; ctx.lineWidth = 2; ctx.strokeRect(x - 13, c.y - 27, 26, 26);
      ctx.fillStyle = C.oro; ctx.font = `800 16px ${TITOLI}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("?", x, c.y - 14); }
    for (const o of s.oggetti){ const x = sx(o.x), y = o.y - 12 - Math.sin(s.t * 5) * 3; ctx.fillStyle = COL_COSA[o.cosa]; ctx.beginPath(); ctx.arc(x, y, 11, 0, 6.29); ctx.fill();
      ctx.fillStyle = "#050d18"; ctx.font = `800 14px ${TITOLI}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(SIGLA[o.cosa], x, y + 1); }
    for (const p of s.prigionieri){ const x = sx(p.x); ctx.fillStyle = "#c9b79c"; ctx.fillRect(x - 5, p.y - 24, 10, 16); ctx.beginPath(); ctx.arc(x, p.y - 29, 5, 0, 6.29); ctx.fill();
      ctx.fillStyle = "#6b4a22"; ctx.fillRect(x - 5, p.y - 8, 10, 8); ctx.strokeStyle = C.tenue; ctx.lineWidth = 1.5; ctx.strokeRect(x - 11, p.y - 34, 22, 34);
      ctx.beginPath(); ctx.moveTo(x - 4, p.y - 34); ctx.lineTo(x - 4, p.y); ctx.moveTo(x + 4, p.y - 34); ctx.lineTo(x + 4, p.y); ctx.stroke(); }
  }
  function colpi(){
    for (const c of s.colpi){ const x = sx(c.x);
      if (c.tipo === "fiamma"){ ctx.globalAlpha = 0.7; ctx.fillStyle = Math.random() < 0.5 ? "#ff7b00" : C.oro; ctx.beginPath(); ctx.arc(x, c.y, 7, 0, 6.29); ctx.fill(); ctx.globalAlpha = 1; }
      else { ctx.strokeStyle = C.oro; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, c.y); ctx.lineTo(x - c.vx * 0.02, c.y - c.vy * 0.02); ctx.stroke(); } }
    ctx.fillStyle = C.nemico; for (const p of s.spariN){ ctx.beginPath(); ctx.arc(sx(p.x), p.y, p.r, 0, 6.29); ctx.fill(); }
    ctx.fillStyle = "#c9d6e2"; for (const g of s.bombe){ ctx.beginPath(); ctx.arc(sx(g.x), g.y, 5, 0, 6.29); ctx.fill(); }
  }
  function comandiGrafici(){
    ctx.fillStyle = "#07111d"; ctx.fillRect(0, hm, l, a - hm); ctx.fillStyle = C.accento; ctx.fillRect(0, hm, l, 2);
    const att = new Set(toccati.values()); if (tasti.ArrowLeft) att.add("sx"); if (tasti.ArrowRight) att.add("dx");
    for (const b of bott){
      const premuto = att.has(b.k) || (b.k === "spara" && (tasti[" "] || tasti.x)) || (b.k === "salta" && (tasti.ArrowUp || tasti.z)), cx = b.x + b.w / 2, cy = b.y + b.h / 2;
      ctx.fillStyle = premuto ? "rgba(0,180,216,.45)" : "#0b1a2a"; ctx.strokeStyle = b.k === "spara" ? C.oro : C.accento; ctx.lineWidth = 2;
      ctx.fillRect(b.x, b.y, b.w, b.h); ctx.strokeRect(b.x + 1, b.y + 1, b.w - 2, b.h - 2);
      ctx.fillStyle = b.k === "spara" ? C.oro : "#e6f6ff";
      if (b.k === "sx" || b.k === "dx"){ const d = b.k === "dx" ? 1 : -1; ctx.beginPath(); ctx.moveTo(cx + d * 16, cy); ctx.lineTo(cx - d * 12, cy - 20); ctx.lineTo(cx - d * 12, cy + 20); ctx.fill(); }
      else { ctx.font = `800 ${b.k === "granata" ? 18 : 20}px ${TITOLI}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(b.t, cx, cy); }
    }
    // vite, granate, arma in mano
    const y = hm + 22; ctx.fillStyle = C.nemico; for (let i = 0; i < VITE; i++){ ctx.globalAlpha = i < s.vite ? 1 : 0.2; ctx.beginPath(); ctx.arc(20 + i * 24, y, 8, 0, 6.29); ctx.fill(); } ctx.globalAlpha = 1;
    ctx.fillStyle = C.tenue; ctx.font = `600 13px ${MONO}`; ctx.textAlign = "left"; ctx.textBaseline = "middle";
    const ar = arma(s); ctx.fillText(`Granate ${s.granate}`, 12, y + 24);
    ctx.fillStyle = ar.tipo === "pistola" ? C.tenue : C.oro; ctx.fillText(ar.tipo === "pistola" ? ar.nome : `${ar.nome} ${Math.ceil(s.arma.fino - s.t)}s`, 12, y + 44);
  }
  function disegna(dt){
    ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, l, a);
    const bersaglioCam = limita(s.soldato.x - visW * 0.38, 0, Math.max(0, s.lunghezza + 40 - visW));
    cam += (bersaglioCam - cam) * Math.min(1, 10 * dt) || 0;
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, l, hm); ctx.clip(); ctx.scale(k, k);
    sfondo(); suolo(); oggetti();
    for (const n of s.nemici){ if (sx(n.x) < -60 || sx(n.x) > visW + 60) continue; (n.tipo === "robot" ? robot : n.tipo === "drone" ? drone : torretta)(n); }
    if (s.capo) capo(s.capo);
    soldato(); colpi();
    for (const p of particelle){ p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 300 * dt; p.vita -= dt; ctx.globalAlpha = Math.max(0, p.vita / 0.6); ctx.fillStyle = p.colore; ctx.fillRect(sx(p.x) - 2, p.y - 2, 4, 4); }
    particelle = particelle.filter(p => p.vita > 0); ctx.globalAlpha = 1;
    ctx.restore();
    // pausa
    if (fase === "gioco"){ ctx.fillStyle = "rgba(19,40,59,.85)"; ctx.fillRect(l - 54, 10, 44, 44); ctx.fillStyle = C.tenue; ctx.fillRect(l - 40, 22, 6, 20); ctx.fillRect(l - 30, 22, 6, 20); }
    comandiGrafici();
    if (fase === "pronto" || fase === "pausa"){
      const [titolo, riga] = fase === "pronto" ? ["Raffica", "Tocca per partire"] : ["Pausa", "Tocca per riprendere"];
      ctx.fillStyle = "rgba(5,13,24,.8)"; ctx.fillRect(0, hm / 2 - 60, l, 120); ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = C.oro; ctx.font = `800 28px ${TITOLI}`; ctx.fillText(titolo, l / 2, hm / 2 - 16); ctx.fillStyle = C.tenue; ctx.font = `500 16px ${MONO}`; ctx.fillText(riga, l / 2, hm / 2 + 20);
    }
  }
  function fotogramma(ora){
    if (fermo) return;
    const dt = prima ? Math.min(0.05, (ora - prima) / 1000) : 0; prima = ora;
    if (fase === "gioco" && dt > 0){
      s = avanza(s, dt, comandi()); granataSosp = false; racconta(s.eventi); scriviBarra();
      if (s.finito){ fase = "fine"; toccati.clear(); api.esito(`Partita finita al livello ${s.livello}.`); timerFine = setTimeout(() => { if (!fermo) api.fine(s.punti); }, 1500); }
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
  id:"raffica", nome:"Raffica", cabinato:{schermo:"RAFFICA", colore:"#FFB703"},
  regole:"Un soldato corre verso destra tra robot e rovine: ◀ ▶ per correre, SALTA, SPARA (tienilo premuto per la raffica) e GRANATA (poche, fanno area). Robot a terra 50 punti, droni 80, torrette 100, prigioniero liberato 200; ogni 3 livelli un mezzo corazzato da 1000. Rompi le casse per armi a tempo (mitragliatrice, fucile a pallini, lanciafiamme) e granate. Hai 3 vite: un colpo ti rende intoccabile per 1,5 secondi, una buca costa una vita. Un gettone ogni 300 punti, fino a 25 a partita.",
  massimo:25, gettoni, avvia,
};
