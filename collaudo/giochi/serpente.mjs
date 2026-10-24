// Le prove del Serpentone (giochi/serpente.js), le fa girare collaudo/giochi.mjs. Passo per passo, sulla sola logica.
// Ogni controllo importante è una funzione che conta gli errori di una regola: girata sulla logica vera deve dare 0,
// girata su una logica rotta apposta (controprova) deve dare più di 0, cioè sa diventare rossa.
export default async function (prova, { logica: L, gioco }) {
  const J = v => JSON.stringify(v);
  let seme = 11; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const zero = () => 0;
  // uno stato fatto a mano: celle "x,y", la prima è la testa
  const S = (pezzi, altro = {}) => { const [t, ...c] = pezzi.map(p => { const [x, y] = p.split(",").map(Number); return {x, y}; });
    return {larghezza:L.LARGHEZZA, altezza:L.ALTEZZA, testa:t, corpo:c, direzione:"su", cibo:{x:0, y:0}, oro:null, vivo:true, morte:null, punti:0, mangiati:0, passi:0, ...altro}; };
  const sul = (s, c) => !!c && (L.uguale(s.testa, c) || s.corpo.some(p => L.uguale(p, c)));

  // ── l'inizio
  const s0 = L.inizio(rnd);
  prova("inizio: griglia 15×21, vivo, 0 punti, lungo 3, va su", s0.larghezza === 15 && s0.altezza === 21 && s0.vivo && s0.punti === 0 && L.lunghezza(s0) === 3 && s0.direzione === "su");
  prova("inizio: il gettone è sulla griglia e non sul serpente", !!s0.cibo && s0.cibo.x >= 0 && s0.cibo.x < 15 && s0.cibo.y >= 0 && s0.cibo.y < 21 && !sul(s0, s0.cibo), s0.cibo);

  // ── il movimento
  const lontano = {x:0, y:0};
  const m = L.passo(S(["7,10", "7,11", "7,12"], {cibo:lontano}), "destra");
  prova("passo: la testa avanza di una cella, il corpo la segue, la lunghezza resta", J([m.testa, ...m.corpo]) === J([{x:8, y:10}, {x:7, y:10}, {x:7, y:11}]) && m.vivo && m.direzione === "destra" && m.passi === 1);
  const tutte = ["su", "giu", "sinistra", "destra"].map(d => L.passo(S(["7,10"], {direzione:d, cibo:lontano}), d).testa);
  prova("passo: su, giù, sinistra, destra vanno dove dicono", J(tutte) === J([{x:7, y:9}, {x:7, y:11}, {x:6, y:10}, {x:8, y:10}]));
  // non si gira di 180°: il comando contrario si ignora e il serpente va dritto
  function giri180(passo) {
    let errori = 0;
    for (const [dir, contro] of [["su", "giu"], ["giu", "su"], ["sinistra", "destra"], ["destra", "sinistra"]]) {
      const [dx, dy] = L.DIREZIONI[dir], s = S(["7,10", `${7 - dx},${10 - dy}`, `${7 - 2 * dx},${10 - 2 * dy}`], {direzione:dir, cibo:lontano});
      const n = passo(s, contro, zero);
      if (!n.vivo || n.direzione !== dir || !L.uguale(n.testa, {x:7 + dx, y:10 + dy})) errori++;
    }
    return errori;
  }
  prova("passo: non si gira di 180° in un colpo (il comando contrario si ignora, va dritto e non muore)", giri180(L.passo) === 0);
  prova("passo: una direzione che non esiste si ignora", L.uguale(L.passo(S(["7,10", "7,11"], {cibo:lontano}), "boh").testa, {x:7, y:9}));

  // ── le collisioni: il bordo
  function muri(passo) {
    let errori = 0;
    const casi = [["7,0", "su"], ["7,20", "giu"], ["0,10", "sinistra"], ["14,10", "destra"], ["0,0", "su"], ["14,20", "destra"]];
    for (const [t, d] of casi) { const n = passo(S([t], {direzione:d, cibo:lontano}), d, zero); if (n.vivo || n.morte !== "bordo") errori++; }
    // lungo il bordo, senza uscire, si vive
    for (const [t, d] of [["0,5", "su"], ["14,5", "giu"], ["5,0", "destra"], ["5,20", "sinistra"]]) if (!passo(S([t], {direzione:d, cibo:lontano}), d, zero).vivo) errori++;
    return errori;
  }
  prova("collisioni: toccare uno dei quattro bordi (anche negli angoli) uccide; scorrerci accanto no", muri(L.passo) === 0);
  // ── le collisioni: sé stesso
  function morsi(passo) {
    let errori = 0;
    // a forma di U: la testa in 5,5 va giù e trova il corpo in 5,6
    const u = S(["5,5", "6,5", "6,6", "5,6", "4,6"], {direzione:"sinistra", cibo:lontano});
    const n = passo(u, "giu", zero); if (n.vivo || n.morte !== "sé stesso") errori++;
    // la coda però si sposta: inseguirla (senza crescere) si può
    const q = S(["5,5", "6,5", "6,6", "5,6"], {direzione:"sinistra", cibo:lontano});
    if (!passo(q, "giu", zero).vivo) errori++;
    // ma se in quel passo mangia, la coda resta e ci sbatte
    if (passo({...q, cibo:{x:5, y:6}}, "giu", zero).vivo) errori++;
    return errori;
  }
  prova("collisioni: mordersi il corpo uccide; inseguire la coda che si sposta no (ma se cresce sì)", morsi(L.passo) === 0);
  const morto = L.passo(S(["7,0"], {cibo:lontano}), "su");
  prova("fine partita: da morto il serpente non si muove più e i punti restano", !morto.vivo && L.finita(morto) && J(L.passo({...morto, punti:4}, "giu")) === J({...morto, punti:4}));

  // ── mangiare e i punti
  const pasto = L.passo(S(["7,10", "7,11", "7,12"], {cibo:{x:7, y:9}}), "su", rnd);
  prova("mangiare: +1 punto, il serpente si allunga di 1, la coda resta dov'era", pasto.punti === 1 && pasto.mangiati === 1 && L.lunghezza(pasto) === 4 && L.uguale(pasto.corpo[pasto.corpo.length - 1], {x:7, y:12}));
  prova("mangiare: spunta subito un gettone nuovo, non sul serpente", !!pasto.cibo && !sul(pasto, pasto.cibo), pasto.cibo);
  // nuovoCibo: mai sul serpente, per tanti casi e con il serpente che riempie quasi tutta la griglia
  function cibiSbagliati(nuovoCibo) {
    let errori = 0;
    const lungo = []; for (let y = 0; y < 21; y++) for (let x = 0; x < 15; x++) if (!(x === 14 && y === 20) && !(x === 13 && y === 20)) lungo.push(`${y % 2 ? 14 - x : x},${y}`);
    const quasiPieno = S(lungo.filter(c => c !== "13,20" && c !== "14,20" && c !== "1,20" && c !== "0,20"), {cibo:null});
    for (const s of [s0, pasto, quasiPieno]) for (let i = 0; i < 200; i++) {
      const c = nuovoCibo(s, rnd);
      if (!c || sul(s, c) || L.uguale(c, s.cibo) || c.x < 0 || c.y < 0 || c.x >= 15 || c.y >= 21) errori++;
    }
    for (const r of [0, 0.5, 0.999999]) { const c = nuovoCibo(quasiPieno, () => r); if (!c || sul(quasiPieno, c)) errori++; }
    return errori;
  }
  prova("nuovoCibo: mai sul serpente né fuori dalla griglia (600 tiri, anche a griglia quasi piena)", cibiSbagliati(L.nuovoCibo) === 0);
  const pieno = []; for (let y = 0; y < 21; y++) for (let x = 0; x < 15; x++) pieno.push(`${y % 2 ? 14 - x : x},${y}`);
  prova("nuovoCibo: a griglia piena non c'è posto (null), e la partita è finita", L.nuovoCibo(S(pieno, {cibo:null}), rnd) === null && L.finita(S(pieno, {cibo:null})));

  // ── il gettone d'oro
  let s = S(["7,10", "7,11", "7,12"], {cibo:{x:7, y:9}}), oro = null;
  for (let i = 1; i <= L.OGNI_ORO; i++) { s = L.passo(s, "su", rnd); if (s.punti !== i) break; if (i < L.OGNI_ORO && s.oro) break;
    if (i < L.OGNI_ORO) s = {...s, cibo:{x:s.testa.x, y:s.testa.y - 1}}; }
  oro = s.oro;
  prova(`oro: spunta dopo ${L.OGNI_ORO} gettoni mangiati, non prima, e non sul serpente né sul gettone`, s.punti === L.OGNI_ORO && !!oro && oro.resta === 5000 && !sul(s, oro) && !L.uguale(oro, s.cibo), {punti:s.punti, oro});
  prova("oro: dopo 4,9 s c'è ancora, dopo 5 s è sparito", !!L.invecchia(s, 4900).oro && L.invecchia(s, 5000).oro === null && L.invecchia(L.invecchia(s, 2500), 2500).oro === null);
  const so = {...S(["7,10", "7,11"], {cibo:lontano}), oro:{x:7, y:9, resta:3000}, punti:2};
  const preso = L.passo(so, "su", rnd);
  prova("oro: mangiarlo vale 3 punti, lo fa sparire e allunga il serpente", preso.punti === 5 && preso.oro === null && L.lunghezza(preso) === 3 && preso.mangiati === 0);

  // ── la difficoltà: velocità
  const v = Array.from({length:60}, (_, p) => L.velocita(p));
  prova("velocità: 7 passi al secondo all'inizio, 8 a 5 punti, 9 a 10", L.velocita(0) === 7 && L.velocita(4) === 7 && L.velocita(5) === 8 && L.velocita(10) === 9);
  prova("velocità: non cala mai e non supera 14 (ci arriva a 35 punti)", v.every((x, i) => i === 0 || x >= v[i - 1]) && Math.max(...v) === 14 && L.velocita(34) === 13 && L.velocita(35) === 14 && L.velocita(1000) === 14);

  // ── una partita intera, passo per passo: un giocatore automatico che va verso il gettone senza suicidarsi
  function partita(passo, quanti = 4000) {
    let s = L.inizio(rnd), passi = 0, velocita = [L.velocita(0)], errori = [];
    const sicura = (s, d) => passo(s, d, () => 0.5).vivo;
    while (!L.finita(s) && passi < quanti) {
      const meta = s.oro || s.cibo, dirs = ["su", "giu", "sinistra", "destra"].filter(d => !L.contraria(s.direzione, d));
      dirs.sort((a, b) => { const da = L.DIREZIONI[a], db = L.DIREZIONI[b];
        return (Math.abs(s.testa.x + da[0] - meta.x) + Math.abs(s.testa.y + da[1] - meta.y)) - (Math.abs(s.testa.x + db[0] - meta.x) + Math.abs(s.testa.y + db[1] - meta.y)); });
      const prima = s; s = passo(s, dirs.find(d => sicura(s, d)) || dirs[0], rnd); s = L.invecchia(s, 1000 / L.velocita(s.punti)); passi++;
      if (s.punti < prima.punti) errori.push("i punti calano");
      if (s.vivo && (s.punti - prima.punti) && L.lunghezza(s) !== L.lunghezza(prima) + 1) errori.push("mangia ma non cresce");
      if (s.vivo && !(s.punti - prima.punti) && L.lunghezza(s) !== L.lunghezza(prima)) errori.push("cresce senza mangiare");
      if (s.vivo && s.cibo && sul(s, s.cibo)) errori.push("gettone sul serpente");
      if (s.vivo && [s.testa, ...s.corpo].some(p => p.x < 0 || p.y < 0 || p.x >= 15 || p.y >= 21)) errori.push("fuori dalla griglia ma vivo");
      if (s.vivo && new Set([s.testa, ...s.corpo].map(p => p.x + "," + p.y)).size !== L.lunghezza(s)) errori.push("si sovrappone ma è vivo");
      velocita.push(L.velocita(s.punti));
    }
    return {s, passi, velocita, errori:[...new Set(errori)]};
  }
  const p = partita(L.passo);
  prova("partita: tutte le regole tengono a ogni passo (punti, crescita, gettone, bordo, corpo)", p.errori.length === 0, p.errori);
  prova("partita: la difficoltà cresce col tempo (la velocità sale con i gettoni mangiati, mai giù)", p.s.punti >= 10 && p.velocita.at(-1) > p.velocita[0] && p.velocita.every((x, i) => i === 0 || x >= p.velocita[i - 1]), {punti:p.s.punti, da:p.velocita[0], a:p.velocita.at(-1)});
  prova("partita: prima o poi finisce, e da finita il serpente è fermo", L.finita(p.s) && J(L.passo(p.s, "su", rnd)) === J(p.s), {passi:p.passi, vivo:p.s.vivo});

  // ── controprove: regole rotte apposta, i controlli devono diventare rossi
  const senzaMuri = (s, d, c) => { const n = L.passo(s, d, c); return n.morte === "bordo" ? {...s, testa:{x:(s.testa.x + L.DIREZIONI[d][0] + 15) % 15, y:(s.testa.y + L.DIREZIONI[d][1] + 21) % 21}} : n; };
  prova("controprova: un serpente che passa attraverso i muri fa diventare rosso il controllo dei bordi", muri(senzaMuri) > 0);
  const senzaMorsi = (s, d, c) => { const n = L.passo(s, d, c); return n.morte === "sé stesso" ? {...n, vivo:true, morte:null} : n; };
  prova("controprova: un serpente che non si morde mai fa diventare rosso il controllo del corpo", morsi(senzaMorsi) > 0);
  const giraTutto = (s, d, c) => L.passo({...s, direzione:L.DIREZIONI[d] ? d : s.direzione, corpo:[]}, d, c);
  prova("controprova: un serpente che si gira di 180° fa diventare rosso il controllo", giri180((s, d, c) => { const n = giraTutto(s, d, c); return {...n, corpo:s.corpo}; }) > 0);
  prova("controprova: un nuovoCibo che mette il gettone sulla testa fa diventare rosso il controllo", cibiSbagliati(s => s.testa) > 0);
  const vRotta = punti => 7 + Math.floor(punti / 5);   // senza il tetto di 14
  prova("controprova: una velocità senza tetto si vede (supera 14)", Array.from({length:60}, (_, p) => vRotta(p)).some(x => x > 14));

  // ── punti → gettoni
  prova("gettoni: uno per punto, e la partita ne dà al massimo 25", gioco.massimo === 25 && [0, 1, 7, 25, 40].every(p => gioco.gettoni(p) === p) && Math.min(gioco.gettoni(40), gioco.massimo) === 25);
}
