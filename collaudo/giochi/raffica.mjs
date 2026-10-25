// Le prove di Raffica (giochi/raffica.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo: si costruisce una scena (un robot qui, una piattaforma lì), si avanza e si guarda.
// Le regole importanti sono funzioni del modulo (regola(L) → vero/falso): le controprove le girano su una logica rotta apposta.
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60;
  const fisso = v => () => v;
  let seme = 5; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const T = L.TERRA;
  // una scena ferma: livello 1 senza nulla dentro, il soldato a terra in x=100
  const scena = (extra = {}) => ({ ...L.nuovaPartita(), nemici: [], casse: [], prigionieri: [], piattaforme: [], buche: [], oggetti: [], capo: null, ricarica: 0, ...extra, soldato: { ...L.nuovaPartita().soldato, x: 100, ...(extra.soldato || {}) } });
  const robot = (x, y = T, extra = {}) => ({ id: 1, tipo: "robot", x, y, y0: y, min: 0, max: 3000, vita: 1, ricarica: 99, fase: 0, dir: -1, attivo: true, ...extra });
  const gira = (A, s, sec, cmd, caso = rnd) => { for (let i = 0; i < Math.round(sec * 60); i++) s = A.avanza(s, F, cmd, caso); return s; };

  prova("gettoni: uno ogni 300 punti, al massimo 25", [0, 299, 300, 900, 7500, 99999].map(gioco.gettoni).join() === "0,0,1,3,25,25" && gioco.massimo === 25);

  // i livelli: ripetibili da un seme
  const J = x => JSON.stringify(x);
  prova("livello: lo stesso numero dà sempre lo stesso livello, numeri diversi livelli diversi", J(L.livello(4)) === J(L.livello(4)) && J(L.livello(4)) !== J(L.livello(5)) && L.livello(1).seme !== L.livello(2).seme);
  prova("livello: il capo ogni 3 livelli (3, 6, 9), mai negli altri", [3, 6, 9].every(n => L.livello(n).capo) && [1, 2, 4, 5, 7, 8].every(n => !L.livello(n).capo));
  prova("livello: l'ambiente cambia ogni 3 livelli (città, giungla, deserto, poi da capo)", [1, 3, 4, 6, 7, 9, 10].map(n => L.livello(n).ambiente).join() === "citta,citta,giungla,giungla,deserto,deserto,citta");
  prova("capo: vita giusta (40 al livello 3, 60 al 6, 80 al 9)", [3, 6, 9].map(n => L.livello(n).capo.vita).join() === "40,60,80" && L.vitaCapo(3) === 40);
  const sensato = n => { const v = L.livello(n); return v.buche.every((b, i) => b.w >= 70 && b.w <= 109 && b.x > 300 && (i === 0 || b.x >= v.buche[i - 1].x + v.buche[i - 1].w + 150))
    && [...v.nemici, ...v.casse, ...v.prigionieri].filter(e => e.y === T).every(e => !L.inBuca(v.buche, e.x, 5))
    && v.nemici.filter(e => e.y === T && e.tipo !== "drone").every(e => e.min < e.x && e.x < e.max) && v.prigionieri.length >= 1
    && v.piattaforme.every(p => p.y === T - 70 || p.y === T - 90); };
  prova("livello: buche che si saltano, niente a terra dentro una buca, piattaforme raggiungibili, almeno un prigioniero", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15].every(sensato));
  prova("livello: più avanti più nemici, e più svelti", L.livello(9).nemici.length > L.livello(1).nemici.length && L.velocita(9) > L.velocita(1) && L.velocita(99) <= 1.8);
  prova("livello: i droni dal 1, le torrette dal 2", L.livello(1).nemici.every(e => e.tipo !== "torretta") && [2, 3, 4, 5, 6].some(n => L.livello(n).nemici.some(e => e.tipo === "torretta")) && [1, 2, 3, 4].some(n => L.livello(n).nemici.some(e => e.tipo === "drone")));

  // il salto: atterra sulla piattaforma e non ci passa attraverso
  const regolaSalto = A => {
    const piat = { x: 60, y: T - 70, w: 120 };
    const cade = gira(A, scena({ piattaforme: [piat], soldato: { x: 120, y: T - 160, vy: 0, aTerra: false } }), 1.5, {});
    const sale = gira(A, scena({ piattaforme: [piat], soldato: { x: 120, y: T } }), 0.1, { salta: true });   // sotto la piattaforma: la attraversa salendo
    const su = gira(A, sale, 1.5, {});
    const fuori = gira(A, scena({ piattaforme: [piat], soldato: { x: 300, y: T } }), 0.1, { salta: true });
    return cade.soldato.y === piat.y && cade.soldato.aTerra && su.soldato.y === piat.y && su.soldato.aTerra && fuori.soldato.vy < 0 && gira(A, fuori, 1.5, {}).soldato.y === T;
  };
  prova("salto: dall'alto si atterra sulla piattaforma (non la attraversa); dal basso la si supera e ci si ferma sopra; a terra torna al suolo", regolaSalto(L));
  prova("salto: da terra si sale, e non si salta in aria", (() => { let s = scena(); const alto = gira(L, s, 0.3, { salta: true }), aria = gira(L, alto, 0.1, { salta: true }); return alto.soldato.y < T - 40 && aria.soldato.vy > alto.soldato.vy; })());
  prova("corsa: ◀ ▶ muovono il soldato e ne cambiano il verso", (() => { const d = gira(L, scena(), 1, { dx: true }), sx = gira(L, scena(), 1, { sx: true }); return Math.abs(d.soldato.x - 100 - L.CORSA) < 2 && sx.soldato.x < 100 && d.soldato.dir === 1 && sx.soldato.dir === -1; })());

  // la buca toglie una vita
  const regolaBuca = A => {
    const buche = [{ x: 300, w: 90 }]; let s = scena({ buche, soldato: { x: 260, y: T } }), n = 0;
    while (s.vite === 3 && n++ < 600) s = A.avanza(s, F, { dx: true }, rnd);
    return s.vite === 2 && !s.finito && s.soldato.x < 300 && s.soldato.y === T && s.soldato.aTerra && L.intoccabile(s);
  };
  prova("buca: cadere toglie una vita, si riparte prima della buca, intoccabili per un attimo", regolaBuca(L));
  prova("buca: l'ultima vita persa in una buca finisce la partita", (() => { let s = scena({ vite: 1, buche: [{ x: 300, w: 90 }], soldato: { x: 260 } }), n = 0; while (!s.finito && n++ < 600) s = L.avanza(s, F, { dx: true }, rnd); return s.finito && s.vite === 0; })());
  prova("buca: si salta sopra una buca larga quanto la più larga", (() => { let s = scena({ buche: [{ x: 300, w: 109 }], soldato: { x: 285 } }); s = gira(L, s, 0.05, { dx: true, salta: true }); s = gira(L, s, 1.2, { dx: true }); return s.vite === 3 && s.soldato.x > 409; })());

  // le armi
  const caldo = (tipo, extra = {}) => scena({ arma: { tipo, fino: 99 }, ...extra });
  prova("arma: senza casse è la pistola; con un'arma presa vale finché dura, poi torna la pistola", L.arma(scena()).tipo === "pistola" && L.arma(caldo("fiamma")).tipo === "fiamma" && L.arma({ ...caldo("fiamma"), t: 100 }).tipo === "pistola");
  const una = tipo => gira(L, caldo(tipo), F, { spara: true }, fisso(0.5));
  prova("pistola: un colpo dritto davanti", (() => { const s = una("pistola"); return s.colpi.length === 1 && s.colpi[0].vy === 0 && s.colpi[0].vx > 0; })());
  prova("fucile a pallini: più colpi insieme, a ventaglio (direzioni tutte diverse)", (() => { const s = una("ventaglio"); return s.colpi.length >= 3 && new Set(s.colpi.map(c => Math.round(c.vy))).size === s.colpi.length && s.colpi.some(c => c.vy < 0) && s.colpi.some(c => c.vy > 0); })());
  prova("mitragliatrice: spara molto più in fretta della pistola", gira(L, caldo("pesante"), 1, { spara: true }, fisso(0.5)).colpi.length >= 2 * gira(L, caldo("pistola"), 1, { spara: true }, fisso(0.5)).colpi.length);
  const regolaPortata = A => {
    const prova1 = tipo => gira(A, caldo(tipo, { nemici: [robot(100 + 250)] }), 1.2, { spara: true }, fisso(0.5));
    const pi = prova1("pistola"), fi = prova1("fiamma");
    const maxX = tipo => Math.max(0, ...gira(A, caldo(tipo), 0.6, { spara: true }, fisso(0.5)).colpi.map(c => c.x - 100));
    return pi.nemici.length === 0 && pi.punti === 50 && fi.nemici.length === 1 && maxX("fiamma") <= A.ARMI.fiamma.portata + 15 && maxX("pistola") > 2 * A.ARMI.fiamma.portata;
  };
  prova("lanciafiamme: portata corta (il robot a 250 non brucia, alla pistola sì)", regolaPortata(L));
  prova("lanciafiamme: da vicino brucia più nemici in fila (i colpi passano)", (() => { const s = gira(L, caldo("fiamma", { nemici: [robot(150, T, { id: 1 }), robot(175, T, { id: 2 })] }), 0.3, { spara: true }, fisso(0.5)); return s.nemici.length === 0 && s.punti === 100; })());
  prova("pistola: un colpo ferma sul primo bersaglio (due robot sovrapposti, ne cade uno)", (() => { const s = L.avanza(scena({ nemici: [robot(150, T, { id: 1 }), robot(152, T, { id: 2 })], colpi: [{ x: 148, y: T - 18, x0: 148, y0: T - 18, vx: 500, vy: 0, portata: 999, danno: 1, r: 3, visti: [] }] }), F, {}, rnd); return s.nemici.length === 1 && s.punti === 50 && s.colpi.length === 0; })());
  prova("sparare guarda dove si va: a sinistra i colpi vanno a sinistra", (() => { const s = gira(L, scena(), F, { sx: true, spara: true }, fisso(0.5)); return s.colpi.length === 1 && s.colpi[0].vx < 0; })());
  prova("colpisce: dentro la scatola sì, fuori no, in alto e in basso contano", (() => { const b = { x: 100, y: T, w: 24, h: 36 }; return L.colpisce({ x: 100, y: T - 18 }, b) && !L.colpisce({ x: 130, y: T - 18 }, b) && !L.colpisce({ x: 100, y: T - 50 }, b) && !L.colpisce({ x: 100, y: T + 8 }, b) && L.colpisce({ x: 100, y: T - 38 }, b); })());

  // le granate: poche, fanno area
  const regolaGranata = A => {
    const s0 = scena({ nemici: [robot(180, T, { id: 1 }), robot(210, T, { id: 2 }), robot(520, T, { id: 3 })], bombe: [{ x: 190, y: T - 3, vx: 0, vy: 200, eta: 0 }] });
    const s = A.avanza(s0, F, {}, rnd);
    return s.nemici.length === 1 && s.nemici[0].id === 3 && s.punti === 100 && s.bombe.length === 0;
  };
  prova("granata: l'area colpisce i vicini (due robot) e non il lontano", regolaGranata(L));
  prova("granata: si lancia con GRANATA, ne restano meno, e non a vuoto", (() => { const a = gira(L, scena(), F, { granata: true }), b = gira(L, scena({ granate: 0 }), F, { granata: true }), c = gira(L, a, 3, {}, fisso(0.5)); return a.granate === L.GRANATE_INIZIO - 1 && a.bombe.length === 1 && b.bombe.length === 0 && c.bombe.length === 0; })());
  prova("granata: fa danno forte, e al capo ne leva un pezzo", (() => { const s = L.avanza(scena({ lunghezza: 500, capo: { id: "capo", tipo: "capo", x: 190, y: T, vita: 40, max: 40, dir: 1, ricarica: 99, attivo: true }, bombe: [{ x: 190, y: T - 3, vx: 0, vy: 200, eta: 0 }] }), F, {}, rnd); return s.capo && s.capo.vita === 40 - L.GRANATA_DANNO; })());

  // punti per nemico
  const abbatti = (A, e, colpi = 1) => { let s = scena({ nemici: [e] }); for (let i = 0; i < colpi; i++) s = A.avanza({ ...s, colpi: [{ x: e.x, y: e.y - 18, x0: e.x, y0: e.y - 18, vx: 100, vy: 0, portata: 999, danno: 1, r: 3, visti: [] }] }, F, {}, rnd); return s; };
  const regolaPunti = A => abbatti(A, robot(300)).punti === 50 && abbatti(A, { ...robot(300, 200), tipo: "drone" }).punti === 80
    && abbatti(A, { ...robot(300), tipo: "torretta", vita: 3 }, 3).punti === 100 && abbatti(A, { ...robot(300), tipo: "torretta", vita: 3 }, 2).punti === 0;
  prova("punti: robot 50, drone 80, torretta 100 (regge tre colpi)", regolaPunti(L));
  prova("prigioniero: liberato toccandolo vale 200, una volta sola", (() => { const s = L.avanza(scena({ prigionieri: [{ tipo: "prigioniero", x: 100, y: T }] }), F, {}, rnd); return s.punti === 200 && s.prigionieri.length === 0 && L.avanza(s, F, {}, rnd).punti === 200; })());

  // le casse
  prova("cassa: rotta da un colpo lascia il suo regalo, e prendendolo si ha l'arma per un tempo", (() => {
    let s = scena({ casse: [{ id: "c0", tipo: "cassa", x: 180, y: T, vita: 1, drop: "ventaglio" }] }); s = gira(L, s, 0.6, { spara: true }, fisso(0.5));
    const rotta = s.casse.length === 0 && s.oggetti.length === 1 && s.oggetti[0].cosa === "ventaglio";
    s = L.avanza({ ...s, colpi: [], oggetti: s.oggetti.map(o => ({ ...o, x: s.soldato.x })) }, F, {}, rnd);
    return rotta && s.oggetti.length === 0 && L.arma(s).tipo === "ventaglio" && L.arma({ ...s, t: s.t + L.ARMA_TEMPO + 1 }).tipo === "pistola"; })());
  prova("cassa di granate: più granate, non oltre il massimo", (() => { const s = L.avanza(scena({ granate: 1, oggetti: [{ tipo: "oggetto", cosa: "granate", x: 100, y: T }] }), F, {}, rnd); const t = L.avanza(scena({ granate: 9, oggetti: [{ tipo: "oggetto", cosa: "granate", x: 100, y: T }] }), F, {}, rnd); return s.granate === 4 && t.granate === 9; })());

  // il capo
  const capo = (vita, extra = {}) => ({ id: "capo", tipo: "capo", x: 300, y: T, vita, max: 40, dir: 1, ricarica: 99, attivo: true, ...extra });
  prova("capo: parte con la vita del livello, un colpo ne toglie uno, a zero muore e vale 1000", (() => {
    const n = L.nuovaPartita(); const s3 = L.avanza({ ...n, livello: 3 }, F, {}, rnd);
    const colpo = { x: 300, y: T - 30, x0: 300, y0: T - 30, vx: 100, vy: 0, portata: 999, danno: 1, r: 3, visti: [] };
    const a = L.avanza(scena({ lunghezza: 500, capo: capo(2), colpi: [{ ...colpo }] }), F, {}, rnd), b = L.avanza({ ...a, colpi: [{ ...colpo }] }, F, {}, rnd);
    return a.capo && a.capo.vita === 1 && a.punti === 0 && b.capo === null && b.punti === 1000 && s3 && L.livello(3).capo.vita === 40; })());
  prova("capo: spara a raffica di tre colpi verso di te", (() => { const s = L.avanza(scena({ lunghezza: 700, capo: capo(10, { ricarica: 0.001, x: 400 }) }), F, {}, rnd); return s.spariN.length === 3 && s.spariN.every(p => p.vx < 0); })());
  prova("capo: finché è vivo il livello non finisce; morto, si passa al successivo", (() => {
    const fondo = { x: 3000 }; const vivo = L.avanza(scena({ lunghezza: 3000, capo: capo(5, { x: 2800 }), soldato: fondo }), F, {}, rnd);
    const morto = L.avanza(scena({ lunghezza: 3000, soldato: fondo }), F, {}, rnd);
    return vivo.livello === 1 && morto.livello === 2 && morto.soldato.x < 100 && morto.vite === 3 && morto.punti === 0; })());

  // le vite e l'intoccabilità
  const regolaIntoccabile = A => {
    const colpo = s => ({ ...s, spariN: [{ x: s.soldato.x, y: s.soldato.y - 18, vx: 0, vy: 0, r: 4 }] });
    let s = A.avanza(colpo(scena()), F, {}, rnd); const primo = s.vite === 2 && A.intoccabile(s);
    s = A.avanza(colpo(s), F, {}, rnd); const subito = s.vite === 2;
    s = gira(A, s, 1.2, {}); s = A.avanza(colpo(s), F, {}, rnd); const dentro = s.vite === 2;
    s = gira(A, s, 0.5, {}); s = A.avanza(colpo(s), F, {}, rnd);
    return primo && subito && dentro && s.vite === 1 && A.INVULN === 1.5;
  };
  prova("intoccabilità: dopo un colpo 1,5 s senza perdere vite, poi di nuovo", regolaIntoccabile(L));
  prova("vite: tre vite, a zero la partita è finita e non va più avanti", (() => { let s = scena({ vite: 1 }); s = L.avanza({ ...s, spariN: [{ x: 100, y: T - 18, vx: 0, vy: 0, r: 4 }] }, F, {}, rnd); return L.nuovaPartita().vite === 3 && s.vite === 0 && s.finito && L.avanza(s, 1, { dx: true }, rnd) === s; })());
  prova("un robot che ti sbatte contro ti ferisce", L.avanza(scena({ nemici: [robot(104)] }), F, {}, rnd).vite === 2);
  prova("un robot sveglio si avvicina; uno lontano dorme", (() => { const v = gira(L, scena({ nemici: [robot(400, T, { attivo: false })] }), 0.5, {}), n = gira(L, scena({ nemici: [robot(2000, T, { attivo: false })] }), 0.5, {}); return v.nemici[0].x < 400 && n.nemici[0].x === 2000 && !n.nemici[0].attivo; })());
  prova("il drone vola a onda, la torretta spara mirando", (() => { const d = gira(L, scena({ nemici: [{ ...robot(400, 250), tipo: "drone" }] }), 1, {}), t = L.avanza(scena({ nemici: [{ ...robot(300), tipo: "torretta", vita: 3, ricarica: 0.001 }] }), F, {}, rnd); return d.nemici[0].x < 400 && d.nemici[0].y !== 250 && t.spariN.length === 1 && t.spariN[0].vx < 0; })());
  prova("avanza non tocca lo stato che riceve (funzione pura)", (() => { const a = scena({ nemici: [robot(150)] }), prima = J(a); L.avanza(a, 1, { dx: true, spara: true, granata: true }, rnd); L.ferito(a); return J(a) === prima; })());

  // una partita intera
  const partita = (cmdDi) => { seme = 9; let s = L.nuovaPartita(), n = 0, sano = true;
    while (!s.finito && s.t < 900 && n++ < 100000) { s = L.avanza(s, F, cmdDi(s), rnd);
      if (![s.punti, s.soldato.x, s.soldato.y].every(Number.isFinite) || [...s.nemici, ...s.colpi, ...s.spariN].some(o => !Number.isFinite(o.x) || !Number.isFinite(o.y))) { sano = false; break; } }
    return { s, sano }; };
  const bravo = partita(s => ({ dx: true, spara: true, salta: Math.floor(s.t * 2) % 3 === 0, granata: Math.floor(s.t) % 7 === 0 }));
  prova("una partita intera gira senza intoppi (niente NaN) e il soldato avanza", bravo.sano && (bravo.s.livello > 1 || bravo.s.soldato.x > 400 || bravo.s.finito), { livello: bravo.s.livello, x: Math.round(bravo.s.soldato.x), punti: bravo.s.punti, vite: bravo.s.vite });
  const fermo = partita(() => ({}));
  prova("chi sta fermo non va avanti: il livello resta quello, senza intoppi", fermo.sano && fermo.s.livello === 1 && fermo.s.soldato.x === 40, { t: Math.round(fermo.s.t), x: Math.round(fermo.s.soldato.x) });

  // controprove: le stesse regole su una logica rotta apposta devono diventare rosse
  prova("controprova: se la piattaforma non reggesse, la prova del salto sarebbe rossa", !regolaSalto({ ...L, avanza: (s, dt, c, k) => L.avanza({ ...s, piattaforme: [] }, dt, c, k) }));
  prova("controprova: se la buca non togliesse vite, la prova della buca sarebbe rossa", !regolaBuca({ ...L, avanza: (s, dt, c, k) => { const n = L.avanza(s, dt, c, k); return { ...n, vite: 3, finito: false }; } }));
  prova("controprova: se il lanciafiamme sparasse lontano come la pistola, la prova della portata sarebbe rossa", !regolaPortata({ ...L, ARMI: { ...L.ARMI, fiamma: { ...L.ARMI.fiamma, portata: 620 } }, avanza: (s, dt, c, k) => L.avanza({ ...s, arma: s.arma && s.arma.tipo === "fiamma" ? { tipo: "pistola", fino: 99 } : s.arma }, dt, c, k) }));
  prova("controprova: se la granata non facesse area, la prova della granata sarebbe rossa", !regolaGranata({ ...L, avanza: (s, dt, c, k) => L.avanza({ ...s, bombe: [] }, dt, c, k) }));
  prova("controprova: se i punti fossero storti, la prova dei punti sarebbe rossa", !regolaPunti({ ...L, avanza: (s, dt, c, k) => { const n = L.avanza(s, dt, c, k); return { ...n, punti: n.punti * 2 }; } }));
  prova("controprova: se non ci fosse intoccabilità, la prova sarebbe rossa", !regolaIntoccabile({ ...L, intoccabile: () => false, avanza: (s, dt, c, k) => L.avanza({ ...s, invulnFino: 0 }, dt, c, k) }));
}
