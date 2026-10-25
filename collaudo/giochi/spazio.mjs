// Le prove di Assalto dallo spazio (giochi/spazio.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo: si costruisce una scena (un nemico qui, un colpo lì), si avanza di un fotogramma e si guarda.
// Le regole importanti sono funzioni del modulo (regola(L) → vero/falso): le controprove le girano su una logica rotta apposta.
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60;                        // un fotogramma
  const fisso = v => () => v;               // un caso() che dà sempre lo stesso numero
  let seme = 11; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  // una scena ferma: niente arrivi (c'è ancora un nemico in coda, così l'ondata non finisce), la navicella non spara
  const scena = (extra = {}) => ({ ...L.nuovaPartita(390, 700), coda: ["lento"], attesa: 1e9, ricarica: 1e9, ...extra });
  const nemico = (tipo, x, y) => ({ tipo, x, x0: x, y, fase: 0, ricarica: 9 });

  // gettoni
  prova("gettoni: uno ogni 40 punti, al massimo 25", [0, 39, 40, 79, 80, 400, 1000, 99999].map(gioco.gettoni).join() === "0,0,1,1,2,10,25,25" && gioco.massimo === 25);

  // le ondate
  const O = n => L.prossimaOndata(n);
  prova("ondate: il capo ogni 4 (4, 8, 12), mai nelle altre", [4, 8, 12].every(n => O(n).capo) && [1, 2, 3, 5, 6, 7, 9].every(n => !O(n).capo));
  prova("ondate: il capo dell'ondata 8 ha più vita di quello della 4", O(8).vita > O(4).vita && O(4).vita > 0);
  prova("ondate: all'1 solo lenti, dalla 2 anche zig-zag, dalla 3 tutti e tre i tipi",
    O(1).nemici.every(t => t === "lento") && O(2).nemici.includes("zigzag") && !O(2).nemici.includes("sparo")
    && ["lento", "zigzag", "sparo"].every(t => O(3).nemici.includes(t)));
  prova("ondate: più avanti più nemici, più fitti e più veloci", O(5).nemici.length > O(1).nemici.length && O(5).ritmo < O(1).ritmo && O(5).velocita > O(1).velocita);

  // la navicella
  const s0 = L.nuovaPartita(390, 700);
  prova("partita nuova: 3 vite, 0 punti, ondata 1, navicella in basso al centro", s0.vite === 3 && s0.punti === 0 && s0.ondata === 1 && s0.nave.x === 195 && s0.nave.y > 600 && !s0.finito);
  prova("muovi: la navicella va dove le si dice, ma resta nello schermo",
    L.muovi(s0, 100).nave.x === 100 && L.muovi(s0, -50).nave.x === L.R.nave && L.muovi(s0, 9999).nave.x === 390 - L.R.nave && L.muovi(s0, NaN).nave.x === 195);
  const sparo = L.avanza(s0, 0.5, rnd);
  prova("la navicella spara da sola, e i colpi salgono", sparo.colpi.length >= 2 && sparo.colpi.every(c => c.y < s0.nave.y - L.R.nave));
  prova("avanza non tocca lo stato che riceve (funzione pura)", (() => { const a = scena({ nemici: [nemico("sparo", 100, 100)] }), prima = JSON.stringify(a);
    L.avanza(a, 1, rnd); L.colpito(a); L.muovi(a, 10); return JSON.stringify(a) === prima; })());

  // collisioni e punteggio
  const abbatte = (A, tipo) => { const s = A.avanza(scena({ nemici: [nemico(tipo, 200, 300)], colpi: [{ x: 200, y: 312 }] }), F, fisso(0.99));
    return s.nemici.length === 0 && s.colpi.length === 0 && s.punti === A.PUNTI[tipo]; };
  const regolaPunti = A => abbatte(A, "lento") && abbatte(A, "zigzag") && abbatte(A, "sparo") && A.PUNTI.lento === 10 && A.PUNTI.zigzag === 20 && A.PUNTI.sparo === 30;
  prova("un colpo abbatte il nemico che tocca: lento 10, zig-zag 20, che spara 30", regolaPunti(L));
  prova("un colpo che passa lontano non abbatte niente", (() => { const s = L.avanza(scena({ nemici: [nemico("lento", 200, 300)], colpi: [{ x: 300, y: 312 }] }), F, rnd); return s.nemici.length === 1 && s.punti === 0; })());
  prova("un colpo abbatte un nemico solo", (() => { const s = L.avanza(scena({ nemici: [nemico("lento", 200, 300), nemico("lento", 204, 300)], colpi: [{ x: 202, y: 312 }] }), F, fisso(0.99)); return s.nemici.length === 1 && s.punti === 10; })());
  prova("bonus: cade raramente da un nemico abbattuto (caso basso sì, caso alto no)", (() => {
    const g = c => L.avanza(scena({ nemici: [nemico("lento", 200, 300)], colpi: [{ x: 200, y: 312 }] }), F, fisso(c)).bonus.length;
    return g(0) === 1 && g(0.99) === 0; })());
  const capo = vita => ({ x: 195, y: 110, vita, max: 40, dir: 1, ricarica: 9 });
  prova("il capo perde un punto di vita a colpo, e abbattuto vale 200", (() => {
    const a = L.avanza(scena({ capo: capo(2), colpi: [{ x: 195, y: 150 }] }), F, rnd);
    const b = L.avanza({ ...a, colpi: [{ x: a.capo.x, y: 150 }] }, F, rnd);
    return a.capo && a.capo.vita === 1 && a.punti === 0 && b.capo === null && b.punti === 200; })());

  // le vite
  const regolaVite = A => { const s = scena(), a = A.colpito(s), b = A.colpito(a), c = A.colpito({ ...b, t: b.t + A.INVULN + 0.1 });
    return a.vite === 2 && !a.finito && b.vite === 2 && c.vite === 1; };
  prova("colpito: una vita in meno; subito dopo si è intoccabili per un attimo, poi di nuovo no", regolaVite(L));
  prova("colpito con lo scudo: nessuna vita persa", L.colpito(scena({ scudoFino: 5 })).vite === 3);
  const fine = L.colpito(scena({ vite: 1 }));
  prova("fine partita: all'ultima vita persa la partita è finita, e avanza non muove più niente", fine.vite === 0 && fine.finito && L.avanza(fine, 1, rnd) === fine);
  const nv = s0.nave;
  prova("uno sparo nemico che tocca la navicella toglie una vita e sparisce", (() => { const s = L.avanza(scena({ spari: [{ x: nv.x, y: nv.y - 12, vx: 0, vy: 240 }] }), F, rnd); return s.vite === 2 && s.spari.length === 0; })());
  prova("un nemico che sbatte contro la navicella toglie una vita (e non dà punti)", (() => { const s = L.avanza(scena({ nemici: [nemico("lento", nv.x, nv.y - 20)] }), F, rnd); return s.vite === 2 && s.punti === 0 && s.nemici.length === 0; })());
  prova("il nemico che spara spara davvero, verso il basso", (() => { const s = L.avanza(scena({ nemici: [{ ...nemico("sparo", 100, 200), ricarica: 0.001 }] }), F, fisso(0.5)); return s.spari.length === 1 && s.spari[0].vy > 0; })());
  prova("il capo spara a ventaglio, tre colpi", (() => { const s = L.avanza(scena({ capo: { ...capo(10), ricarica: 0.001 } }), F, rnd); return s.spari.length === 3 && new Set(s.spari.map(p => p.vx)).size === 3; })());

  // lo scudo
  const regolaScudo = A => { let s = A.avanza(scena({ bonus: [{ x: nv.x, y: nv.y }] }), F, rnd); const preso = A.scudo(s) && s.bonus.length === 0;
    for (let i = 0; i < 49; i++) s = A.avanza(s, 0.1, rnd); const ancora = A.scudo(s);
    s = A.avanza(s, 0.2, rnd); return preso && ancora && !A.scudo(s) && A.SCUDO === 5; };
  prova("il bonus preso dà lo scudo per 5 secondi, non uno di più", regolaScudo(L));
  prova("con lo scudo gli spari nemici non tolgono vite", (() => { const s = L.avanza(scena({ scudoFino: 5, spari: [{ x: nv.x, y: nv.y - 12, vx: 0, vy: 240 }] }), F, rnd); return s.vite === 3; })());

  // i potenziamenti delle armi
  const N = nv.x;
  const POT = { cadenza: (liv, fino = 99) => ({ cadenza: { liv, fino } }), multiplo: (liv, fino = 99) => ({ multiplo: { liv, fino } }), sparo: (tipo, liv, fino = 99) => ({ sparo: { tipo, liv, fino } }) };
  const conPot = (...p) => ({ cadenza: { liv: 0, fino: 0 }, multiplo: { liv: 0, fino: 0 }, sparo: { tipo: "base", liv: 0, fino: 0 }, ...Object.assign({}, ...p) });
  const raffiche = (A, pot, secondi) => { let s = A.avanza(scena({ ricarica: 0, pot }), F, rnd); const n0 = s.raffiche;
    for (let i = 0; i < secondi * 60 - 1; i++) s = A.avanza(s, F, rnd); return s.raffiche - n0 + 1; };
  // una raffica sola: avanza di un fotogramma con la navicella carica, poi la rimette a riposo
  const raffica = (A, pot, extra = {}) => { const s = A.avanza(scena({ ricarica: 0, pot, ...extra }), F, fisso(0.99)); return { ...s, ricarica: 1e9 }; };
  prova("CADENZA: in 5 secondi escono più colpi che senza, e più sale il livello più ne escono", (() => {
    const r = [0, 1, 2, 3].map(l => raffiche(L, conPot(POT.cadenza(l)), 5)); return r[0] < r[1] && r[1] < r[2] && r[2] < r[3] && r[3] > r[0] * 1.8; })());
  const regolaMultiplo = A => { const n = l => { const s = raffica(A, conPot(POT.multiplo(l))); return { n: s.colpi.length, dir: new Set(s.colpi.map(c => c.vx.toFixed(3))).size }; };
    const r = [n(0), n(1), n(2), n(3)]; return r.map(o => o.n).join() === "1,2,3,5" && r.map(o => o.dir).join() === "1,2,3,5"; };
  prova("MULTIPLO: 1 → 2 → 3 → 5 colpi per raffica, tutti con direzioni diverse a ventaglio (livello 3: cinque)", regolaMultiplo(L));
  prova("MULTIPLO: i colpi del ventaglio si aprono davvero salendo", (() => { let s = raffica(L, conPot(POT.multiplo(3))); for (let i = 0; i < 30; i++) s = L.avanza(s, F, rnd);
    const xs = s.colpi.map(c => c.x).sort((a, b) => a - b); return xs.length === 5 && xs[4] - xs[0] > 60; })());

  // ogni tipo di sparo fa la sua cosa
  const laser = L.avanza(scena({ ricarica: 0, pot: conPot(POT.sparo("laser", 1)), nemici: [nemico("lento", N, 400), nemico("zigzag", N, 200), nemico("lento", N + 150, 300)] }), F, fisso(0.99));
  prova("RAGGIO LASER: colpisce nello stesso istante tutti i nemici nella colonna (2), non quello a lato", laser.nemici.length === 1 && laser.nemici[0].x === N + 150 && laser.punti === 30 && laser.colpi.length === 1 && laser.colpi[0].tipo === "laser");
  prova("RAGGIO LASER: dura un attimo e poi si spegne", (() => { let s = laser; for (let i = 0; i < 40; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); return s.colpi.length === 0; })());
  prova("RAGGIO LASER: ferisce il capo a piccoli tratti, non tutta la vita in un colpo", (() => { let s = raffica(L, conPot(POT.sparo("laser", 1)), { capo: { ...capo(40), x: N } });
    for (let i = 0; i < 20; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); return s.capo && s.capo.vita < 40 && s.capo.vita > 30; })());
  const missile = (extra = {}) => raffica(L, conPot(POT.sparo("missile", 1)), { nemici: [nemico("lento", N + 110, 300)], ...extra });
  prova("MISSILE: parte dritto, poi cambia direzione verso il nemico e lo abbatte", (() => { let s = missile(); const vx0 = s.colpi[0].vx, tipo = s.colpi[0].tipo; let virato = false;
    for (let i = 0; i < 150 && s.punti === 0; i++){ s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); if (s.colpi[0] && s.colpi[0].vx > 100) virato = true; }
    return tipo === "missile" && Math.abs(vx0) < 40 && virato && s.punti === 10 && s.nemici.length === 0; })());
  prova("MISSILE: va verso il nemico più vicino, anche se è dall'altra parte", (() => { let s = missile({ nemici: [nemico("lento", N - 90, 400), nemico("lento", N + 200, 200)] });
    for (let i = 0; i < 6; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); return s.colpi[0].vx < 0; })());
  prova("MISSILE: dal livello 2 scoppia e abbatte anche il vicino; al livello 1 solo il colpito", (() => {
    const g = liv => { let s = raffica(L, conPot(POT.sparo("missile", liv)), { nemici: [nemico("lento", N, 450), nemico("lento", N + 30, 450)] });
      for (let i = 0; i < 60 && s.colpi.length; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); return s.punti; };
    return g(1) === 10 && g(2) === 20; })());
  const plasma = liv => { let s = raffica(L, conPot(POT.sparo("plasma", liv)), { nemici: [nemico("lento", N, 450), nemico("lento", N, 380), nemico("lento", N, 310), nemico("lento", N, 240), nemico("lento", N, 170)] });
    for (let i = 0; i < 90 && s.colpi.length; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, fisso(0.99)); return s; };
  prova("PLASMA: attraversa e abbatte 2 nemici in fila (livello 1), poi si spegne; salendo ne attraversa di più", plasma(1).punti === 20 && plasma(1).nemici.length === 3 && plasma(2).punti === 30 && plasma(3).punti === 40);
  prova("PLASMA: ferisce il capo e si ferma contro di lui", (() => { let s = raffica(L, conPot(POT.sparo("plasma", 1)), { capo: { ...capo(10), x: N, dir: 0 } }); for (let i = 0; i < 90; i++) s = L.avanza({ ...s, ricarica: 1e9 }, F, rnd); return s.capo.vita === 7 && s.colpi.length === 0; })());
  prova("i tre tipi di sparo sono davvero diversi: colpi, cadenza e disegno", (() => { const t = ["base", "laser", "missile", "plasma"].map(k => { const p = k === "base" ? conPot() : conPot(POT.sparo(k, 1)); return { k, cad: L.cadenzaDi({ ...s0, pot: p }), tipo: raffica(L, p).colpi[0].tipo || "base" }; });
    return new Set(t.map(o => o.tipo)).size === 4 && new Set(t.map(o => o.cad)).size === 4 && t.slice(1).every(o => o.cad > L.CADENZA); })());

  // bonus: si prendono, salgono di livello fino al massimo, scadono, si perdono con una vita
  const prendi = (s, tipo) => L.avanza({ ...s, bonus: [{ x: nv.x, y: nv.y, tipo }] }, F, rnd);
  prova("i bonus cadono di tutti i tipi e raramente (caso basso sì, alto no); la probabilità è bassa", (() => { const tipi = new Set(); for (let i = 0; i < 100; i++){ const c = i / 100;
      let k = 0; const s = L.avanza(scena({ nemici: [nemico("lento", 200, 300)], colpi: [{ x: 200, y: 312 }] }), F, () => (k++ ? c : 0)); if (s.bonus.length) tipi.add(s.bonus[0].tipo); }
    return tipi.size === 6 && L.PROB_BONUS <= 0.08 && L.PROB_BONUS >= 0.04; })());
  prova("prendere un bonus potenzia, e riprenderlo sale di livello (cadenza e multiplo)", (() => { let s = scena(); const liv = [];
    for (let i = 0; i < 3; i++){ s = prendi(s, "multiplo"); liv.push(L.potenziamenti(s).multiplo); } s = prendi(s, "cadenza"); return liv.join() === "1,2,3" && L.potenziamenti(s).cadenza === 1 && s.bonus.length === 0; })());
  prova("il livello massimo è il 3: riprendere ancora non sale più (tutti i bonus)", (() => { let s = scena(); for (let i = 0; i < 6; i++) for (const t of ["cadenza", "multiplo", "laser"]) s = prendi(s, t);
    const p = L.potenziamenti(s); return L.MAX_LIV === 3 && p.cadenza === 3 && p.multiplo === 3 && p.sparo.tipo === "laser" && p.sparo.liv === 3; })());
  prova("un tipo di sparo diverso sostituisce il precedente e riparte dal livello 1", (() => { let s = prendi(prendi(scena(), "plasma"), "plasma"); const a = L.potenziamenti(s).sparo; s = prendi(s, "missile"); const b = L.potenziamenti(s).sparo;
    return a.tipo === "plasma" && a.liv === 2 && b.tipo === "missile" && b.liv === 1; })());
  const regolaScadenza = A => { let s = A.avanza(scena({ bonus: [{ x: nv.x, y: nv.y, tipo: "multiplo" }] }), F, rnd); const preso = A.potenziamenti(s).multiplo === 1;
    for (let i = 0; i < 119; i++) s = A.avanza({ ...s, nemici: [], coda: ["lento"] }, 0.1, rnd); const ancora = A.potenziamenti(s).multiplo === 1;
    s = A.avanza(s, 0.2, rnd); return preso && ancora && A.potenziamenti(s).multiplo === 0 && A.POT_DURATA === 12; };
  prova("un potenziamento dura 12 secondi, non uno di più, poi torna tutto come prima", regolaScadenza(L));
  prova("riprendere il bonus rinnova il tempo", (() => { let s = prendi(scena(), "cadenza"); for (let i = 0; i < 100; i++) s = A_avanti(s, 0.1); s = prendi(s, "cadenza"); for (let i = 0; i < 100; i++) s = A_avanti(s, 0.1); return L.potenziamenti(s).cadenza === 2; })());
  function A_avanti(s, dt){ return L.avanza({ ...s, nemici: [], coda: ["lento"], spari: [] }, dt, rnd); }
  const regolaPerdita = A => { const s = scena({ pot: conPot(POT.cadenza(3), POT.multiplo(2), POT.sparo("plasma", 1)) }), a = A.colpito(s), p = A.potenziamenti(a), b = A.colpito({ ...a, t: a.t + A.INVULN + 0.1 }), q = A.potenziamenti(b);
    return p.cadenza === 2 && p.multiplo === 1 && p.sparo.liv === 0 && p.sparo.tipo === "base" && q.cadenza === 1 && q.multiplo === 0; };
  prova("perdere una vita: ogni potenziamento scende di un livello (a zero si torna al colpo base)", regolaPerdita(L));
  prova("colpito con lo scudo: i potenziamenti restano", L.potenziamenti(L.colpito(scena({ scudoFino: 5, pot: conPot(POT.cadenza(3)) }))).cadenza === 3);
  prova("col potenziamento scaduto la raffica torna quella di base", (() => { const s = raffica(L, conPot(POT.multiplo(3, 0.01), POT.sparo("laser", 3, 0.01)), { t: 5 }); return s.colpi.length === 1 && !s.colpi[0].tipo; })());

  // equilibrio
  prova("i punti per nemico, il tetto dei gettoni e il prezzo del gettone non cambiano", L.PER_GETTONE === 40 && gioco.massimo === 25 && L.PUNTI.lento === 10 && L.PUNTI.zigzag === 20 && L.PUNTI.sparo === 30 && L.PUNTI.capo === 200);
  prova("le ondate sono le stesse con o senza potenziamenti (la difficoltà non dipende da loro)", JSON.stringify(O(7)) === JSON.stringify(L.prossimaOndata(7)) && O(5).nemici.length === 15);

  // ondate che si susseguono
  const vuota = { coda: [], nemici: [], capo: null, capoDaFare: false };
  prova("ondata finita (nessuno in coda né in campo): parte la prossima", (() => { const s = L.avanza(scena({ ...vuota }), F, rnd); return s.ondata === 2 && s.coda.length === O(2).nemici.length; })());
  prova("dopo la terza ondata arriva il capo, con la sua vita, dopo una pausa", (() => {
    let s = L.avanza(scena({ ...vuota, ondata: 3 }), F, rnd); const pronto = s.ondata === 4 && s.capoDaFare && !s.capo;
    for (let i = 0; i < (L.PAUSA_ONDATA + 0.1) / 0.1; i++) s = L.avanza(s, 0.1, rnd); return pronto && s.capo && s.capo.vita === O(4).vita && !s.capoDaFare; })());
  prova("finché il capo è vivo l'ondata non finisce", L.avanza(scena({ ...vuota, ondata: 4, capo: capo(5) }), F, rnd).ondata === 4);

  // la difficoltà cresce
  const regolaDifficolta = A => { const discesa = extra => { const s = A.avanza(scena({ nemici: [nemico("lento", 50, 100)], ...extra }), 0.1, rnd); return s.nemici[0].y - 100; };
    return A.spinta(0) < A.spinta(60) && A.spinta(60) < A.spinta(300) && discesa({ ondata: 6 }) > discesa({}) && discesa({ t: 200 }) > discesa({}); };
  prova("la difficoltà cresce: i nemici scendono più svelti con le ondate e col tempo", regolaDifficolta(L));

  // una partita intera: la navicella insegue il nemico più basso
  const gioca = (fermo = false) => { seme = 3; let s = L.nuovaPartita(390, 700), passi = 0, sano = true;
    while (!s.finito && s.t < 1800 && passi++ < 200000){
      if (!fermo){ const bersaglio = s.capo || s.nemici.reduce((m, n) => (!m || n.y > m.y ? n : m), null); if (bersaglio) s = L.muovi(s, s.nave.x + Math.sign(bersaglio.x - s.nave.x) * Math.min(6, Math.abs(bersaglio.x - s.nave.x))); }
      s = L.avanza(s, F, rnd);
      if (!Number.isFinite(s.punti) || !Number.isFinite(s.nave.x) || [...s.nemici, ...s.spari, ...s.colpi].some(o => !Number.isFinite(o.x) || !Number.isFinite(o.y))) { sano = false; break; } }
    return { s, sano }; };
  const MASSIMI = s => ({ ...s, pot: { cadenza: { liv: 3, fino: s.t + 99 }, multiplo: { liv: 3, fino: s.t + 99 }, sparo: { tipo: ["laser", "missile", "plasma"][Math.floor(s.t / 20) % 3], liv: 3, fino: s.t + 99 } } });
  const gioca2 = () => { seme = 3; let s = MASSIMI(L.nuovaPartita(390, 700)), passi = 0, sano = true;
    while (!s.finito && s.t < 900 && passi++ < 60000){
      const bersaglio = s.capo || s.nemici.reduce((m, n) => (!m || n.y > m.y ? n : m), null); if (bersaglio) s = L.muovi(s, s.nave.x + Math.sign(bersaglio.x - s.nave.x) * Math.min(6, Math.abs(bersaglio.x - s.nave.x)));
      s = L.avanza(MASSIMI(s), F, rnd);
      if (!Number.isFinite(s.punti) || [...s.nemici, ...s.colpi].some(o => !Number.isFinite(o.x) || !Number.isFinite(o.y))){ sano = false; break; } }
    return { s, sano }; };
  const p = gioca();
  prova("una partita intera gira senza intoppi (niente NaN), passa più ondate e finisce", p.sano && p.s.ondata >= 3 && p.s.finito && p.s.punti % 10 === 0 && p.s.vite === 0,
    { ondata: p.s.ondata, punti: p.s.punti, t: Math.round(p.s.t), vite: p.s.vite });
  const m = gioca2();
  prova("partita lunga con tutti i potenziamenti al massimo: niente NaN e gettoni sempre al massimo 25", m.sano && m.s.punti >= 1000 && gioco.gettoni(m.s.punti) === 25 && gioco.gettoni(m.s.punti) <= gioco.massimo, { punti: m.s.punti, t: Math.round(m.s.t), ondata: m.s.ondata });
  const q = gioca(true);
  prova("chi sta fermo prima o poi perde: la partita finisce", q.sano && q.s.finito, { t: Math.round(q.s.t), ondata: q.s.ondata });

  // controprove: le stesse regole su una logica rotta apposta devono diventare rosse
  prova("controprova: se abbattere un nemico non desse punti, la prova del punteggio sarebbe rossa", !regolaPunti({ ...L, avanza: (s, dt, c) => ({ ...L.avanza(s, dt, c), punti: s.punti }) }));
  prova("controprova: se un colpo non togliesse vite, la prova delle vite sarebbe rossa", !regolaVite({ ...L, colpito: s => s }));
  prova("controprova: con un MULTIPLO finto che spara sempre un colpo solo, la prova del ventaglio sarebbe rossa", !regolaMultiplo({ ...L, avanza: (s, dt, c) => L.avanza({ ...s, pot: { ...s.pot, multiplo: { liv: 0, fino: 0 } } }, dt, c) }));
  prova("controprova: se il potenziamento non scadesse mai, la prova della scadenza sarebbe rossa", !regolaScadenza({ ...L, potenziamenti: s => ({ ...L.potenziamenti({ ...s, t: 0 }) }) }));
  prova("controprova: se perdere una vita non togliesse potenza, la prova della perdita sarebbe rossa", !regolaPerdita({ ...L, colpito: s => ({ ...L.colpito(s), pot: s.pot }) }));
  prova("controprova: se lo scudo non scadesse mai, la prova dello scudo sarebbe rossa", !regolaScudo({ ...L, scudo: () => true }));
  prova("controprova: se i nemici non accelerassero, la prova della difficoltà sarebbe rossa", !regolaDifficolta({ ...L, spinta: () => 1, avanza: (s, dt, c) => L.avanza({ ...s, ondata: 1, t: 0 }, dt, c) }));
}
