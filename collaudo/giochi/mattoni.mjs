// Le prove del Rompimattoni (giochi/mattoni.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo: si costruisce una scena (un mattone qui, una pallina lì), si avanza di un fotogramma e si guarda.
// Le regole importanti sono funzioni del modulo (regola(A) → vero/falso): le controprove le girano su una logica rotta apposta.
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60;                          // un fotogramma
  const fisso = v => () => v;                // un caso() che dà sempre lo stesso numero
  const palla = (x, y, vx, vy) => ({ x, y, vx, vy });
  const mat = (x, y, max = 1, colpi = max, fisso = false) => ({ c: 0, r: 0, x, y, max, colpi, fisso });
  const ancora = () => mat(300, 200, 1);      // un mattone lontano da tutto, così il livello non finisce
  // una scena ferma: pallina immobile in mezzo al campo, in volo (non attaccata), un solo mattone lontano
  const scena = (extra = {}) => ({ ...L.nuovaPartita(), attaccata: false, attesa: 0, palle: [palla(100, 450, 0, 0)], mattoni: [ancora()], ...extra });
  const colpoSotto = (A, s, m) => !m ? s : A.avanza({ ...s, palle: [palla(m.x + L.BW / 2, m.y + L.BH + L.R + 2, 0, -400)] }, F, fisso(0.99));   // una pallina arriva da sotto

  // gettoni e punteggi
  prova("gettoni: uno ogni 200 punti, al massimo 25", [0, 199, 200, 399, 400, 2000, 5000, 99999].map(gioco.gettoni).join() === "0,0,1,1,2,10,25,25" && gioco.massimo === 25);
  prova("punti: 10 / 20 / 30 per mattone, 500 per livello finito", L.PUNTI[1] === 10 && L.PUNTI[2] === 20 && L.PUNTI[3] === 30 && L.BONUS_LIVELLO === 500);

  // i livelli
  const forma = n => JSON.stringify(L.livello(n).righe);
  prova("livelli: almeno 6 forme diverse, nei primi livelli", new Set([1, 2, 3, 4, 5, 6, 7, 8].map(forma)).size >= 6, L.FORME.length);
  prova("livelli: ogni livello ha mattoni da rompere, dentro il campo, senza due nello stesso posto", (() => {
    for (let n = 1; n <= 20; n++) { const l = L.livello(n), posti = new Set(l.mattoni.map(m => m.c + "," + m.r));
      if (!l.mattoni.some(m => !m.fisso) || posti.size !== l.mattoni.length) return false;
      if (l.mattoni.some(m => m.x < 0 || m.x + L.BW > L.W || m.y < L.TOP || m.y + L.BH > L.PY - 80 || m.max < 0 || m.max > 3)) return false; }
    return true; })());
  prova("livelli: ci sono mattoni da 1, da 2 e da 3 colpi, e di ferro", (() => { const tutti = [1, 2, 3, 4, 5, 6, 7, 8].flatMap(n => L.livello(n).mattoni);
    return [1, 2, 3].every(k => tutti.some(m => !m.fisso && m.max === k && m.colpi === k)) && tutti.some(m => m.fisso); })());
  prova("livelli: la stessa forma, al secondo giro, ha mattoni più duri e la pallina parte più svelta", (() => {
    const dur = n => L.livello(n).mattoni.reduce((a, m) => a + m.max, 0);
    return dur(1 + L.FORME.length) > dur(1) && L.livello(5).velocita > L.livello(1).velocita && L.livello(0).n === 1; })());

  // la racchetta
  const rac = { x: 180, w: L.BASE };
  const regolaRimbalzo = A => { const c = A.rimbalzoRacchetta(180, rac), d = A.rimbalzoRacchetta(180 + rac.w / 2, rac), e = A.rimbalzoRacchetta(180 - rac.w / 2, rac), m = A.rimbalzoRacchetta(180 + rac.w / 4, rac);
    return Math.abs(c.dx) < 1e-9 && c.dy < -0.99 && d.dx > 0.8 && e.dx < -0.8 && d.dy < 0 && Math.abs(d.dx + e.dx) < 1e-9
      && m.dx > 0.2 && m.dx < d.dx && Math.hypot(m.dx, m.dy) > 0.999 && A.rimbalzoRacchetta(999, rac).dx === d.dx; };
  prova("rimbalzoRacchetta: al centro va dritta, al bordo obliqua (a destra o a sinistra), a metà via di mezzo", regolaRimbalzo(L));
  const sulRacchetta = (A, dx) => { const r = { x: 180, w: L.BASE }; return A.avanza(scena({ racchetta: r, palle: [palla(180 + dx, L.PY - L.R - 2, 0, 300)] }), F, fisso(0.99)).palle[0]; };
  const regolaRacchetta = A => { const c = sulRacchetta(A, 0), b = sulRacchetta(A, L.BASE / 2 - 2), a = sulRacchetta(A, -(L.BASE / 2 - 2));
    return Math.abs(c.vx) < 1 && c.vy < -200 && b.vx > Math.abs(b.vy) && b.vy < 0 && a.vx < -Math.abs(a.vy) && a.vy < 0; };
  prova("la pallina che cade sulla racchetta: al centro torna dritta in su, al bordo parte obliqua", regolaRacchetta(L));
  prova("la pallina che passa di lato alla racchetta non rimbalza", (() => { const s = L.avanza(scena({ palle: [palla(300, L.PY - L.R - 2, 0, 300)] }), F, fisso(0.99)); return s.palle[0].vy > 0; })());
  prova("muovi: la racchetta va dove le si dice, ma resta nel campo (anche se larga)",
    L.muovi(L.nuovaPartita(), 100).racchetta.x === 100 && L.muovi(L.nuovaPartita(), -50).racchetta.x === L.BASE / 2 && L.muovi(L.nuovaPartita(), 9999).racchetta.x === L.W - L.BASE / 2
    && L.muovi(L.nuovaPartita(), NaN).racchetta.x === 180);

  // le pareti
  const rimbalza = (palleIn) => L.avanza(scena({ palle: [palleIn] }), F, fisso(0.99)).palle[0];
  prova("pareti: a sinistra, a destra e in alto la pallina rimbalza e resta dentro", (() => {
    const a = rimbalza(palla(8, 300, -300, -200)), b = rimbalza(palla(L.W - 8, 300, 300, -200)), c = rimbalza(palla(200, 8, 100, -300));
    return a.vx > 0 && a.x >= L.R && b.vx < 0 && b.x <= L.W - L.R && c.vy > 0 && c.y >= L.R; })());

  // la partita e il lancio
  const s0 = L.nuovaPartita();
  prova("partita nuova: 3 vite, 0 punti, livello 1, una pallina attaccata alla racchetta che la segue", s0.vite === 3 && s0.punti === 0 && s0.livello === 1 && s0.attaccata && s0.palle.length === 1
    && L.muovi(s0, 90).palle[0].x === 90 && L.avanza(L.muovi(s0, 90), F, fisso(0.5)).palle[0].x === 90);
  prova("lancia: la pallina parte in su; da sola parte dopo un attimo", (() => { const a = L.lancia(s0, fisso(0.5)); let b = s0; for (let i = 0; i < 90; i++) b = L.avanza(b, F, fisso(0.5));
    return !a.attaccata && a.palle[0].vy < -200 && Math.abs(a.palle[0].vx) < 1 && !b.attaccata && L.lancia(a) === a; })());
  prova("avanza non tocca lo stato che riceve (funzione pura)", (() => { const a = scena({ mattoni: [mat(200, 300, 3), ancora()], bonus: [{ tipo: "tre", x: 100, y: 300 }], palle: [palla(221, 329, 0, -400)] }), prima = JSON.stringify(a);
    L.avanza(a, 1, fisso(0)); L.muovi(a, 10); L.lancia(a); return JSON.stringify(a) === prima; })());

  // i mattoni: la pallina non li attraversa, neanche velocissima
  const regolaVeloce = A => {
    const muro = [0, 1, 2].flatMap(r => Array.from({ length: 8 }, (_, c) => ({ ...mat(12 + c * 42, 48 + r * 20, 1), c, r })));
    const su = A.avanza(scena({ mattoni: muro, palle: [palla(200, 200, 0, -9000)] }), F, fisso(0.99)), b = su.palle[0];
    const intatti = su.mattoni.filter(m => m.x === 180 && (m.r === 0 || m.r === 1)).length === 2;
    const lato = A.avanza(scena({ mattoni: [mat(200, 290, 1), ancora()], palle: [palla(80, 300, 9000, 0)] }), F, fisso(0.99)), c = lato.palle[0];
    const giu = A.avanza(scena({ mattoni: [mat(200, 300, 1), ancora()], palle: [palla(221, 200, 0, 9000)] }), F, fisso(0.99)), d = giu.palle[0];
    return su.mattoni.length === 23 && su.punti === 10 && intatti && b.vy > 0 && b.y > 100
      && lato.mattoni.length === 1 && lato.punti === 10 && c.vx < 0 && c.x < 200
      && giu.mattoni.length === 1 && giu.punti === 10 && d.vy < 0 && d.y < 300; };
  prova("una pallina velocissima non passa attraverso un mattone: lo rompe e rimbalza (da sotto, di lato, dall'alto)", regolaVeloce(L));
  prova("una pallina che passa lontano dai mattoni non ne tocca nessuno", (() => { const s = L.avanza(scena({ mattoni: [mat(200, 300, 1), ancora()], palle: [palla(100, 300, -50, -300)] }), F, fisso(0.99)); return s.mattoni.length === 2 && s.punti === 0; })());
  prova("la pallina rompe un mattone solo per volta", (() => { const s = L.avanza(scena({ mattoni: [mat(200, 300, 1), mat(242, 300, 1), ancora()], palle: [palla(242, 329, 0, -400)] }), F, fisso(0.99)); return s.mattoni.length === 2 && s.punti === 10; })());

  // mattoni da 1, 2, 3 colpi, e di ferro
  const regolaColpi = A => {
    let s = scena({ mattoni: [mat(200, 300, 3), ancora()] }); const m = () => s.mattoni.find(k => k.x === 200);
    s = colpoSotto(A, s, m()); const uno = !!m() && m().colpi === 2 && s.punti === 0;
    s = colpoSotto(A, s, m()); const due = !!m() && m().colpi === 1 && s.punti === 0;
    s = colpoSotto(A, s, m()); const tre = !m() && s.punti === 30;
    return uno && due && tre; };
  prova("il mattone da 3 colpi regge 2 colpi e si rompe al terzo (30 punti)", regolaColpi(L));
  const regolaPunti = A => [1, 2, 3].every(max => { let s = scena({ mattoni: [mat(200, 300, max), ancora()] });
    for (let i = 0; i < max; i++) { const m = s.mattoni.find(k => k.x === 200); if (!m) return false; s = colpoSotto(A, s, m); }
    return !s.mattoni.some(k => k.x === 200) && s.punti === A.PUNTI[max] && A.PUNTI[max] === max * 10; });
  prova("un mattone da 1 colpo vale 10, da 2 colpi 20, da 3 colpi 30", regolaPunti(L));
  prova("il mattone di ferro non si rompe e non dà punti, la pallina rimbalza", (() => { let s = scena({ mattoni: [mat(200, 300, 0, 0, true), ancora()] });
    for (let i = 0; i < 5; i++) { s = colpoSotto(L, s, s.mattoni.find(k => k.x === 200)); if (s.palle[0].vy <= 0) return false; }
    return s.mattoni.length === 2 && s.punti === 0; })());

  // i bonus
  const bonusSu = (tipo, extra = {}) => scena({ bonus: [{ tipo, x: 180, y: L.PY - 4 }], palle: [palla(100, 450, 0, 0)], ...extra });
  const regolaTre = A => { const s = A.avanza(bonusSu("tre", { palle: [palla(100, 450, 150, -200)] }), F, fisso(0.5)), p = s.palle;
    return p.length === 3 && s.bonus.length === 0 && new Set(p.map(b => b.vx.toFixed(1))).size === 3 && p.every(b => b.vy < 0 && Math.abs(Math.hypot(b.vx, b.vy) - Math.hypot(150, 200)) < 60); };
  prova("il bonus tre palline ne fa tre (che vanno ognuna per la sua strada)", regolaTre(L));
  prova("con tre palline basta tenerne una: le altre cadute non tolgono vite", (() => { const s = L.avanza(scena({ palle: [palla(100, 450, 0, 0), palla(200, L.H + 30, 0, 300), palla(250, L.H + 30, 0, 300)] }), F, fisso(0.99));
    return s.palle.length === 1 && s.vite === 3; })());
  const regolaLarga = A => { let s = A.avanza(bonusSu("larga"), F, fisso(0.5)); const larga = s.racchetta.w === A.LARGA;
    for (let i = 0; i < 99; i++) s = A.avanza(s, 0.1, fisso(0.5)); const ancoraLarga = s.racchetta.w === A.LARGA;
    s = A.avanza(s, 0.5, fisso(0.5)); return larga && ancoraLarga && s.racchetta.w === A.BASE && A.LARGA > A.BASE; };
  prova("il bonus racchetta larga allarga la racchetta per 10 secondi, poi torna normale", regolaLarga(L));
  prova("il bonus pallina lenta la rallenta e poi finisce", (() => { let s = L.avanza(bonusSu("lenta"), F, fisso(0.5)); const piano = L.velocita(s) < L.velocita({ ...s, lentaFino: 0 });
    for (let i = 0; i < 90; i++) s = L.avanza({ ...s, palle: [palla(100, 450, 0, 0)] }, 0.1, fisso(0.5)); return piano && L.velocita(s) === L.velocita({ ...s, lentaFino: 0 }); })());
  prova("il bonus racchetta che spara: i colpi salgono e rompono i mattoni", (() => { let s = L.avanza(L.avanza(bonusSu("spara", { mattoni: [mat(150, 100, 1), ancora()] }), F, fisso(0.99)), F, fisso(0.99));
    const parte = s.colpi.length >= 2 && s.colpi.every(c => c.y < L.PY);
    for (let i = 0; i < 60; i++) s = L.avanza(s, F, fisso(0.99)); return parte && !s.mattoni.some(k => k.x === 150) && s.punti === 10; })());
  prova("i colpi sparati non rompono il ferro: si fermano lì", (() => { let s = L.avanza(bonusSu("spara", { mattoni: [mat(150, 100, 0, 0, true), ancora()] }), F, fisso(0.99));
    for (let i = 0; i < 90; i++) s = L.avanza(s, F, fisso(0.99)); return s.mattoni.some(k => k.x === 150) && s.punti === 0 && s.colpi.filter(c => c.x >= 150 && c.x <= 192).every(c => c.y > 100 + L.BH); })());
  prova("bonus: dal mattone rotto cade raramente (caso basso sì, alto no); se non lo prendi esce dal campo", (() => {
    const g = c => L.avanza(scena({ mattoni: [mat(200, 300, 1), ancora()], palle: [palla(221, 329, 0, -400)] }), F, fisso(c)).bonus.length;
    let s = scena({ bonus: [{ tipo: "larga", x: 20, y: L.H }] }); s = L.avanza(s, 0.5, fisso(0.5));
    return g(0) === 1 && g(0.99) === 0 && s.bonus.length === 0 && s.racchetta.w === L.BASE; })());
  prova("bonus: i quattro tipi esistono e il caso li sceglie tutti", (() => { const t = c => L.avanza(scena({ mattoni: [mat(200, 300, 1), ancora()], palle: [palla(221, 329, 0, -400)] }), F, (() => { let n = 0; return () => (n++ ? c : 0); })()).bonus[0].tipo;
    return new Set([0, 0.3, 0.6, 0.9].map(t)).size === 4; })());

  // le vite
  const regolaVita = A => { const s = A.avanza(scena({ palle: [palla(200, L.H + 20, 0, 300)] }), F, fisso(0.5));
    return s.vite === 2 && s.attaccata && s.palle.length === 1 && s.palle[0].y < L.PY && !s.finito; };
  prova("la pallina che cade sotto toglie una vita e ne arriva una nuova, attaccata alla racchetta", regolaVita(L));
  prova("la vita persa fa sparire i bonus attivi", (() => { const s = L.avanza(scena({ largaFino: 99, sparaFino: 99, bonus: [{ tipo: "tre", x: 10, y: 10 }], palle: [palla(200, L.H + 20, 0, 300)] }), F, fisso(0.5));
    return s.racchetta.w === L.BASE && s.bonus.length === 0 && s.t >= s.largaFino; })());
  prova("fine partita: all'ultima vita persa la partita è finita, e avanza non muove più niente", (() => { const f = L.avanza(scena({ vite: 1, palle: [palla(200, L.H + 20, 0, 300)] }), F, fisso(0.5));
    return f.vite === 0 && f.finito && L.avanza(f, 1) === f; })());

  // il livello finito
  const regolaLivello = A => { const s = colpoSotto(A, scena({ mattoni: [mat(200, 300, 1)], punti: 40 }), mat(200, 300, 1));
    return s.punti === 40 + 10 + A.BONUS_LIVELLO && s.livello === 2 && s.attaccata && s.mattoni.length === A.livello(2).mattoni.length && s.vite === 3; };
  prova("rotto l'ultimo mattone: +500, livello dopo (nuova forma), pallina attaccata, vite intatte", regolaLivello(L));
  prova("con solo mattoni di ferro rimasti il livello è finito", (() => { const s = L.avanza(scena({ mattoni: [mat(200, 300, 0, 0, true)] }), F, fisso(0.5)); return s.livello === 2 && s.punti === 500; })());

  // la difficoltà cresce
  const regolaDifficolta = A => A.spinta(0) === 1 && A.spinta(0) < A.spinta(60) && A.spinta(60) < A.spinta(240) && A.spinta(1e6) === 1.5
    && A.velocita({ livello: 3, t: 0, lentaFino: 0 }) > A.velocita({ livello: 1, t: 0, lentaFino: 0 }) && A.velocita({ livello: 1, t: 120, lentaFino: 0 }) > A.velocita({ livello: 1, t: 0, lentaFino: 0 });
  prova("la difficoltà cresce: la pallina va più svelta coi livelli e (piano) col tempo", regolaDifficolta(L));
  prova("la pallina accelera davvero: dopo un po' di tempo va più svelta che all'inizio", (() => { const vel = t => { let s = scena({ t, palle: [palla(200, 400, 120, -160)], mattoni: [mat(340, 60, 1)] });
    for (let i = 0; i < 40; i++) { s = L.avanza(s, 0.05, fisso(0.99)); s = { ...s, palle: s.palle.map(b => ({ ...b, y: Math.min(500, Math.max(300, b.y)) })) }; } return Math.hypot(s.palle[0].vx, s.palle[0].vy); };
    return vel(200) > vel(0) * 1.2; })());

  // una partita intera: un giocatore che insegue la pallina
  let seme = 5; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const gioca = (insegue = true) => { seme = 5; let s = L.nuovaPartita(), passi = 0, sano = true, dentro = true;
    while (!s.finito && s.t < 900 && passi++ < 100000) {
      if (insegue) { const b = s.palle.reduce((m, k) => (!m || k.y > m.y ? k : m), null); if (b) s = L.muovi(s, s.racchetta.x + Math.max(-10, Math.min(10, b.x + 14 * Math.sin(s.t) - s.racchetta.x))); }
      s = L.avanza(s, F, rnd);
      if (!Number.isFinite(s.punti) || !Number.isFinite(s.racchetta.x) || s.palle.some(b => !Number.isFinite(b.x) || !Number.isFinite(b.y) || !Number.isFinite(b.vx) || !Number.isFinite(b.vy))) { sano = false; break; }
      if (s.palle.some(b => b.x < 0 || b.x > L.W || b.y < 0)) dentro = false; }
    return { s, sano, dentro }; };
  const p = gioca();
  prova("una partita intera gira senza intoppi (niente NaN, la pallina resta nei muri), passa almeno un livello", p.sano && p.dentro && p.s.livello >= 2 && p.s.punti >= L.BONUS_LIVELLO,
    { livello: p.s.livello, punti: p.s.punti, t: Math.round(p.s.t), vite: p.s.vite });
  const q = gioca(false);
  prova("chi sta fermo prima o poi perde: la partita finisce", q.sano && q.s.finito && q.s.vite === 0, { t: Math.round(q.s.t), vite: q.s.vite });

  // controprove: le stesse regole su una logica rotta apposta devono diventare rosse
  prova("controprova: se il rimbalzo fosse sempre dritto, la prova del rimbalzo sarebbe rossa", !regolaRimbalzo({ ...L, rimbalzoRacchetta: () => ({ dx: 0, dy: -1 }) }));
  prova("controprova: se la racchetta non rimandasse la pallina, la prova della racchetta sarebbe rossa", !regolaRacchetta({ ...L, avanza: (s, dt, c) => ({ ...L.avanza(s, dt, c), palle: s.palle.map(b => ({ ...b, vy: 300, vx: 0 })) }) }));
  prova("controprova: se la pallina attraversasse i mattoni, la prova della pallina veloce sarebbe rossa",
    !regolaVeloce({ ...L, avanza: (s, dt) => ({ ...s, palle: s.palle.map(b => ({ ...b, x: b.x + b.vx * dt, y: b.y + b.vy * dt })) }) }));
  prova("controprova: se un colpo rompesse subito ogni mattone, la prova dei 3 colpi sarebbe rossa", !regolaColpi({ ...L, avanza: (s, dt, c) => { const n = L.avanza(s, dt, c); return { ...n, mattoni: n.mattoni.filter(m => m.colpi === m.max) }; } }));
  prova("controprova: se i mattoni valessero tutti 10, la prova dei punti sarebbe rossa", !regolaPunti({ ...L, PUNTI: { 1: 10, 2: 10, 3: 10 } }));
  prova("controprova: se il bonus non facesse niente, la prova delle tre palline sarebbe rossa", !regolaTre({ ...L, avanza: (s, dt, c) => ({ ...L.avanza(s, dt, c), palle: s.palle }) }));
  prova("controprova: se la racchetta restasse larga, la prova della racchetta larga sarebbe rossa", !regolaLarga({ ...L, avanza: (s, dt, c) => { const n = L.avanza(s, dt, c); return { ...n, racchetta: { ...n.racchetta, w: L.LARGA } }; } }));
  prova("controprova: se cadere non togliesse vite, la prova della vita sarebbe rossa", !regolaVita({ ...L, avanza: (s, dt, c) => ({ ...L.avanza(s, dt, c), vite: s.vite }) }));
  prova("controprova: se il livello finito non desse 500, la prova del livello sarebbe rossa", !regolaLivello({ ...L, avanza: (s, dt, c) => { const n = L.avanza(s, dt, c); return { ...n, punti: s.punti + 10 }; } }));
  prova("controprova: se la pallina non accelerasse, la prova della difficoltà sarebbe rossa", !regolaDifficolta({ ...L, spinta: () => 1, velocita: s => L.velocitaBase(1) }));
}
