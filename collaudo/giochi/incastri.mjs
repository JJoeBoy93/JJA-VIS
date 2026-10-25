// Le prove di Incastri (giochi/incastri.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo: si costruisce una scena (una griglia a mano, un pezzo qui), si fa una mossa e si guarda.
// Le regole importanti sono funzioni del modulo (regola(L) → vero/falso): le controprove le girano su una logica rotta apposta.
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60;
  const passa = (s, sec) => { for (let r = sec; r > 1e-9; r -= 0.1) s = L.avanza(s, Math.min(0.1, r), rnd); return s; };   // avanza al massimo 1/4 di secondo per volta
  let seme = 5; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  // una scena: la griglia vuota, con le righe date (da sotto: "#########." ecc., # = blocco) e il pezzo dato
  const riga = t => [...t].map(c => (c === "#" ? "I" : null));
  const scena = (righe = {}, pezzo = L.entra("T"), extra = {}) => {
    const g = Array.from({ length: L.RIGHE }, () => Array(L.COLONNE).fill(null));
    for (const [r, t] of Object.entries(righe)) g[r] = riga(t);
    return { ...L.nuovaPartita(rnd), griglia: g, pezzo, ...extra };
  };
  const pieno = (r, buchi = []) => Object.fromEntries([[r, [...Array(L.COLONNE).keys()].map(c => (buchi.includes(c) ? "." : "#")).join("")]]);
  const inGriglia = p => L.celle(p).every(([r, c]) => c >= 0 && c < L.COLONNE && r >= 0 && r < L.RIGHE);
  const conta = s => s.griglia.flat().filter(Boolean).length;
  const firma = (tipo, rot) => { const f = L.FORME[tipo][rot], r0 = Math.min(...f.map(([r]) => r)), c0 = Math.min(...f.map(([, c]) => c)); return f.map(([r, c]) => (r - r0) + "," + (c - c0)).sort().join(" "); };

  // gettoni
  prova("gettoni: uno ogni 400 punti, al massimo 25", [0, 399, 400, 799, 800, 4000, 10000, 99999].map(gioco.gettoni).join() === "0,0,1,1,2,10,25,25" && gioco.massimo === 25);

  // i pezzi
  prova("la griglia è 10×20 e i pezzi sono i sette classici, ognuno di 4 blocchi in ogni rotazione", L.COLONNE === 10 && L.RIGHE === 20 && L.TIPI.length === 7
    && L.TIPI.every(t => L.FORME[t].length === 4 && L.FORME[t].every(f => new Set(f.map(x => x.join())).size === 4)));
  prova("le forme dei sette pezzi sono tutte diverse, e ognuno ha il suo colore", new Set(L.TIPI.map(t => firma(t, 0))).size === 7 && new Set(L.TIPI.map(t => L.COLORI[t])).size === 7);
  prova("le rotazioni: la O non cambia, la I, la S e la Z hanno due forme, la T, la J e la L quattro", firma("O", 0) === firma("O", 1) && ["I", "S", "Z"].every(t => firma(t, 0) === firma(t, 2) && firma(t, 0) !== firma(t, 1)) && ["T", "J", "L"].every(t => new Set([0, 1, 2, 3].map(r => firma(t, r))).size === 4));

  // il sacchetto dei sette
  const regolaSacchetto = A => {
    const ok = caso => { let sac = [], fila = [];
      for (let i = 0; i < 1400; i++){ const n = A.nuovoPezzo(caso, sac); sac = n.sacchetto; fila.push(n.tipo); }
      const sette = Array.from({ length: 200 }, (_, k) => new Set(fila.slice(k * 7, k * 7 + 7)).size === 7).every(Boolean);
      const tre = fila.some((t, i) => i >= 2 && t === fila[i - 1] && t === fila[i - 2]);
      return sette && !tre; };
    return ok(rnd) && ok(() => 0) && ok(() => 0.999);
  };
  prova("sacchetto: ogni sette pezzi escono tutti e sette, e nessuno più di due volte di fila", regolaSacchetto(L));
  prova("nuovoPezzo non tocca il sacchetto che riceve", (() => { const sac = ["I", "O"], prima = JSON.stringify(sac); const n = L.nuovoPezzo(rnd, sac); return JSON.stringify(sac) === prima && n.sacchetto.length === 1; })());

  // la partita nuova
  const s0 = L.nuovaPartita(rnd);
  prova("partita nuova: griglia vuota, un pezzo in cima al centro, il prossimo, livello 1, 0 punti", s0.griglia.length === 20 && s0.griglia.every(r => r.length === 10 && r.every(c => c === null))
    && s0.pezzo && s0.pezzo.y >= -1 && L.celle(s0.pezzo).every(([r, c]) => r === 0 || r === 1 || r === 2) && L.TIPI.includes(s0.prossimo) && s0.livello === 1 && s0.punti === 0 && s0.file === 0 && !L.finita(s0));
  prova("ogni pezzo entra con le celle dentro la griglia, la più alta sulla riga 0", L.TIPI.every(t => { const p = L.entra(t); return inGriglia(p) && Math.min(...L.celle(p).map(([r]) => r)) === 0; }));

  // sposta
  prova("sposta: a destra e a sinistra di una colonna", (() => { const a = L.sposta(scena(), 1), b = L.sposta(a, -1); return a.pezzo.x === L.entra("T").x + 1 && b.pezzo.x === L.entra("T").x; })());
  prova("sposta: non esce dalla griglia, né a sinistra né a destra", (() => { let a = scena(), b = scena(); for (let i = 0; i < 20; i++){ a = L.sposta(a, -1); b = L.sposta(b, 1); }
    return inGriglia(a.pezzo) && inGriglia(b.pezzo) && Math.min(...L.celle(a.pezzo).map(([, c]) => c)) === 0 && Math.max(...L.celle(b.pezzo).map(([, c]) => c)) === 9; })());
  prova("sposta: un blocco già lì ferma il pezzo", (() => { const p = { tipo: "O", rot: 0, x: 4, y: 5 }, s = scena({ 5: "......#...", 6: "......#..." }, p); return L.sposta(s, 1) === s && L.sposta(s, -1).pezzo.x === 3; })());
  prova("le mosse non toccano lo stato che ricevono (funzioni pure)", (() => { const a = scena({ 19: "##########" }), prima = JSON.stringify(a);
    L.sposta(a, 1); L.ruota(a); L.cade(a); L.fissa(a, rnd); L.cadeSubito(a, rnd); L.avanza(a, 1, rnd); return JSON.stringify(a) === prima; })());

  // cade, ombra, cade subito
  prova("cade: scende di una riga; sul fondo non scende più", (() => { const a = L.cade(scena()), p = { tipo: "O", rot: 0, x: 4, y: 18 }, b = scena({}, p);
    return a.pezzo.y === L.entra("T").y + 1 && L.cade(b) === b && L.appoggiato(b) && !L.appoggiato(a); })());
  prova("ombra: dove cadrà il pezzo, sul fondo o sopra i blocchi", (() => { const p = { tipo: "O", rot: 0, x: 4, y: 0 };
    return L.ombra(scena({}, p)).y === 18 && L.ombra(scena({ 19: "....#....." }, p)).y === 17 && L.ombra(scena({}, p)).x === 4; })());
  prova("cade subito: il pezzo si posa sul fondo e ne entra un altro", (() => { const p = { tipo: "O", rot: 0, x: 4, y: 0 }, s = scena({}, p, { prossimo: "I" }), n = L.cadeSubito(s, rnd);
    return conta(n) === 4 && n.griglia[19][4] === "O" && n.griglia[18][5] === "O" && n.pezzo.tipo === "I"; })());

  // la rotazione, anche vicino al muro
  prova("ruota: senza ostacoli gira di un quarto e resta dov'è", (() => { const s = scena({}, { tipo: "T", rot: 0, x: 3, y: 5 }), r = L.ruota(s); return r.pezzo.rot === 1 && r.pezzo.x === 3 && r.pezzo.y === 5; })());
  prova("ruota: quattro volte e il pezzo è come prima", (() => { let s = scena({}, { tipo: "L", rot: 0, x: 3, y: 5 }); for (let i = 0; i < 4; i++) s = L.ruota(s); return JSON.stringify(s.pezzo) === JSON.stringify({ tipo: "L", rot: 0, x: 3, y: 5 }); })());
  const regolaMuro = A => {
    const sx = A.ruota(scena({}, { tipo: "T", rot: 1, x: -1, y: 5 })).pezzo;      // T in piedi contro il muro sinistro: ruotando sporgerebbe
    const dx = A.ruota(scena({}, { tipo: "T", rot: 3, x: 8, y: 5 })).pezzo;       // contro il muro destro
    const i = A.ruota(scena({}, { tipo: "I", rot: 1, x: 7, y: 5 })).pezzo;        // la lunga, contro il destro
    return inGriglia(sx) && sx.rot === 2 && sx.x === 0 && inGriglia(dx) && dx.rot === 0 && dx.x === 7 && inGriglia(i) && i.rot === 2 && i.x === 6;
  };
  prova("ruota vicino al muro: il pezzo viene spinto dentro (sinistra, destra, e la lunga)", regolaMuro(L));
  prova("ruota contro il fondo e dentro la griglia anche dalla riga in cima", (() => { const r = L.ruota(scena({}, L.entra("I"))).pezzo; return inGriglia(r) && r.rot === 1; })());
  prova("ruota: se non c'è proprio posto, il pezzo resta fermo", (() => {
    const p = { tipo: "T", rot: 0, x: 3, y: 5 }, cel = new Set(L.celle(p).map(c => c.join())), righe = {};
    for (let r = 4; r < 10; r++) righe[r] = [...Array(10).keys()].map(c => (cel.has(r + "," + c) ? "." : "#")).join("");
    const s = scena(righe, p); return L.ruota(s) === s; })());

  // le file piene
  // scena: la O in basso a sinistra (colonne 0-1, righe 18-19); riga 19 piena tranne lì, e un blocco isolato sopra, in colonna 5
  prova("fila piena: sparisce, quella sopra scende al suo posto, e valgono 100 punti", (() => { const s = scena({ 19: "..########", 18: ".....#...." }, { tipo: "O", rot: 0, x: 0, y: 18 }), n = L.fissa(s, rnd);
    return n.griglia[19][0] === "O" && n.griglia[19][1] === "O" && n.griglia[19][5] === "I" && n.griglia[19].filter(Boolean).length === 3 && n.griglia[18].every(c => c === null)
      && n.punti === 100 && n.file === 1 && n.pezzo && n.eventi.some(e => e.tipo === "file" && e.n === 1); })());
  prova("fila piena: sparisce solo quella piena, e quelle sopra scendono tutte di una riga", (() => {
    const s = scena({ 19: "..########", 17: "#.........", 16: ".#........" }, { tipo: "O", rot: 0, x: 0, y: 18 }), n = L.fissa(s, rnd);
    return n.file === 1 && n.griglia[19][0] !== null && n.griglia[19][1] !== null && n.griglia[18][0] !== null && n.griglia[18][1] === null && n.griglia[17][1] !== null && n.griglia[17][0] === null && n.griglia[16].every(c => c === null) && n.punti === 100; })());
  prova("fila non piena: non sparisce e non dà punti", (() => { const n = L.fissa(scena({ 19: "..#######." }, { tipo: "O", rot: 0, x: 0, y: 18 }), rnd); return conta(n) === 11 && n.punti === 0 && n.file === 0; })());
  // quattro file insieme: la I in piedi nell'ultima colonna
  const tetris = A => { const righe = {}; for (let r = 16; r < 20; r++) righe[r] = "#########.";
    const n = A.fissa(scena(righe, { tipo: "I", rot: 1, x: 7, y: 16 }), rnd); return n.punti === 800 && n.file === 4 && conta(n) === 0; };
  prova("quattro file insieme: tutte spariscono, e valgono 800 punti", tetris(L));
  prova("punti per 1, 2, 3 e 4 file insieme: 100, 300, 500, 800 (livello 1)", [1, 2, 3, 4].map(n => { const righe = {}; for (let r = 20 - n; r < 20; r++) righe[r] = "#########.";
    return L.fissa(scena(righe, { tipo: "I", rot: 1, x: 7, y: 16 }), rnd).punti; }).join() === "100,300,500,800");
  prova("i punti si moltiplicano per il livello", (() => { const righe = {}; for (let r = 16; r < 20; r++) righe[r] = "#########.";
    return L.fissa(scena(righe, { tipo: "I", rot: 1, x: 7, y: 16 }, { livello: 3, file: 20 }), rnd).punti === 2400; })());

  // il livello
  const livello = A => { const base = scena({ 19: "..########" }, { tipo: "O", rot: 0, x: 0, y: 18 });
    const a = A.fissa({ ...base, file: 8 }, rnd), b = A.fissa({ ...base, file: 9 }, rnd);
    return a.livello === 1 && b.livello === 2 && b.file === 10 && b.eventi.some(e => e.tipo === "livello" && e.livello === 2); };
  prova("ogni 10 file si sale di livello (e se ne parla negli eventi)", livello(L) && [0, 9, 10, 19, 20, 95].map(L.livelloDi).join() === "1,1,2,2,3,10");
  prova("al livello nuovo si cade più veloci: l'intervallo cala, e non scende sotto un minimo", (() => { const v = [1, 2, 5, 10, 30].map(L.intervallo);
    return v.every((x, i) => i === 0 || x < v[i - 1] || (x === v[i - 1] && x === 0.07)) && v[0] > v[1] && v[3] < v[0] && v[4] >= 0.07 && v[4] < 0.1; })());
  prova("il punteggio del livello vale quello in cui si è fatta la fila (non il nuovo)", (() => { const n = L.fissa(scena({ 19: "..########" }, { tipo: "O", rot: 0, x: 0, y: 18 }, { file: 9 }), rnd); return n.livello === 2 && n.punti === 100; })());

  // la fine
  const finePartita = A => { const s = scena({ 0: "...####...", 1: "...####..." }, { tipo: "O", rot: 0, x: 0, y: 18 }, { prossimo: "O" }), n = A.fissa(s, rnd);
    const ok = scena({}, { tipo: "O", rot: 0, x: 0, y: 18 }, { prossimo: "O" }); const m = A.fissa(ok, rnd);
    return n.finito === true && A.finita(n) && n.pezzo === null && n.eventi.some(e => e.tipo === "fine") && !A.finita(m) && m.pezzo !== null; };
  prova("fine partita: se il pezzo nuovo non entra la partita è finita, se entra no", finePartita(L));
  prova("a partita finita niente si muove più", (() => { const f = L.fissa(scena({ 0: "...####...", 1: "...####..." }, { tipo: "O", rot: 0, x: 0, y: 18 }, { prossimo: "O" }), rnd);
    return L.sposta(f, 1) === f && L.ruota(f) === f && L.cade(f) === f && L.fissa(f, rnd) === f && L.cadeSubito(f, rnd) === f && L.avanza(f, 1, rnd) === f; })());

  // il tempo: il pezzo scende da solo, posato aspetta e si fissa
  prova("avanza: il pezzo scende di una riga ogni «intervallo» secondi (non prima)", (() => { const y0 = L.entra("T").y; let s = scena();
    s = passa(s, L.intervallo(1) - 0.05); const prima = s.pezzo.y; s = passa(s, 0.1); return prima === y0 && s.pezzo.y === y0 + 1; })());
  prova("avanza: al livello più alto scende più in fretta", (() => { const giu = livello => { let s = scena({}, L.entra("T"), { livello }); for (let i = 0; i < 60; i++) s = L.avanza(s, F, rnd); return s.pezzo.y; };
    return giu(8) > giu(1); })());
  prova("avanza: un pezzo posato aspetta un attimo e poi si fissa; muoverlo gli dà ancora tempo", (() => {
    const p = { tipo: "O", rot: 0, x: 4, y: 18 }; let s = scena({}, p);
    s = passa(s, L.BLOCCO - 0.1); const aspetta = conta(s) === 0 && s.pezzo;
    s = L.sposta(s, 1); s = passa(s, L.BLOCCO - 0.1); const ancora = conta(s) === 0;
    s = passa(s, 0.2); return aspetta && ancora && conta(s) === 4; })());

  // una partita intera: un giocatore che butta i pezzi a caso, e uno che sta fermo
  const gioca = (mossa) => { seme = 9; let s = L.nuovaPartita(rnd), pezzi = 0, sano = true, file = 0;
    while (!s.finito && pezzi < 4000){ pezzi++;
      s = mossa(s, pezzi); s = L.cadeSubito(s, rnd); file += s.eventi.filter(e => e.tipo === "file").reduce((t, e) => t + e.n, 0);
      if (s.griglia.length !== 20 || s.griglia.some(r => r.length !== 10) || !Number.isFinite(s.punti) || s.punti % 100 !== 0 || s.livello !== L.livelloDi(s.file)) { sano = false; break; } }
    return { s, sano, pezzi, file }; };
  const caso = gioca((s, n) => { for (let i = 0, r = Math.floor(rnd() * 4); i < r; i++) s = L.ruota(s); const d = Math.floor(rnd() * 11) - 5; for (let i = 0; i < Math.abs(d); i++) s = L.sposta(s, Math.sign(d)); return s; });
  prova("una partita a caso gira senza intoppi (niente NaN, griglia sempre 10×20) e finisce", caso.sano && caso.s.finito && caso.pezzi < 4000, { pezzi: caso.pezzi, punti: caso.s.punti });
  const fermo = gioca(s => s);
  prova("chi lascia cadere tutto nel mezzo perde in fretta: dopo 5 pezzi la pila arriva su", fermo.s.finito && fermo.pezzi <= 6 * 5 && fermo.s.punti === 0, { pezzi: fermo.pezzi });
  const bravo = gioca((s, n) => { // mette ogni pezzo dove riempie meglio: la posizione più bassa
    let meglio = null, m = -1;
    for (let rot = 0; rot < 4; rot++) for (let x = -2; x < 10; x++){ let t = { ...s, pezzo: { ...s.pezzo, rot, x } }; if (!L.libero(t.griglia, t.pezzo)) continue;
      const o = L.ombra(t); const alt = Math.min(...L.celle(o).map(([r]) => r)), ok = Math.max(...L.celle(o).map(([r]) => r)); const v = ok * 3 + alt;
      if (v > m){ m = v; meglio = t; } }
    return meglio || s; });
  prova("chi gioca con giudizio fa file, prende punti e sale di livello", bravo.sano && bravo.file >= 10 && bravo.s.punti >= 1000 && bravo.s.livello >= 2, { file: bravo.file, punti: bravo.s.punti, livello: bravo.s.livello, pezzi: bravo.pezzi });

  // controprove: le stesse regole su una logica rotta apposta devono diventare rosse
  prova("controprova: se il sacchetto desse sempre lo stesso pezzo, la prova del sacchetto sarebbe rossa", !regolaSacchetto({ ...L, nuovoPezzo: (c, sac) => ({ tipo: "T", sacchetto: sac }) }));
  prova("controprova: se ruotare non spingesse dal muro, la prova della rotazione sarebbe rossa", !regolaMuro({ ...L, ruota: s => ({ ...s, pezzo: { ...s.pezzo, rot: (s.pezzo.rot + 1) % 4 } }) }));
  prova("controprova: se la fila piena non sparisse, la prova delle file sarebbe rossa", !tetris({ ...L, fissa: (s, c) => { const g = s.griglia.map(r => r.slice()); for (const [r, k] of L.celle(s.pezzo)) g[r][k] = s.pezzo.tipo; return { ...L.fissa(s, c), griglia: g }; } }));
  prova("controprova: se le quattro file valessero come una, la prova dei punti sarebbe rossa", !tetris({ ...L, fissa: (s, c) => ({ ...L.fissa(s, c), punti: 100 }) }));
  prova("controprova: se non si salisse mai di livello, la prova del livello sarebbe rossa", !livello({ ...L, fissa: (s, c) => ({ ...L.fissa(s, c), livello: 1, eventi: [] }) }));
  prova("controprova: se la partita non finisse mai, la prova della fine sarebbe rossa", !finePartita({ ...L, finita: () => false, fissa: (s, c) => ({ ...L.fissa(s, c), finito: false }) }));
}
