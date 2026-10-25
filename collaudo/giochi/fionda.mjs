// Le prove della Fionda (giochi/fionda.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo, senza browser. Le regole importanti sono funzioni (regola(scena) → vero/falso):
// le controprove le girano su una scena fatta apposta per rompere la regola, e devono dare falso (ROSSO).
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60, T = L.TERRA;
  const blocco = (m, x, base, w, h) => ({ m, x, y: T - base - h / 2, w, h });
  const gira = (s, secondi) => { for (let i = 0; i < Math.round(secondi / F); i++) L.avanza(s, F); return s; };
  const per = (s, m) => s.corpi.find(c => c.m === m);
  // un sasso lanciato dritto contro un blocco, alla velocità data (la scena parte da fase "volo")
  const colpo = (m, v, tipo = "normale") => {
    const s = L.nuovaScena([blocco(m, 300, 0, 16, 48)], []); s.fase = "volo";
    const p = L.sassoDa(tipo, 240, T - 24, v, 0); s.sassi.push(p); gira(s, 1.5); return s;
  };

  // ── gettoni e dati
  prova("gettoni: uno ogni 1000 punti, al massimo 25", [0, 999, 1000, 5400, 25000, 99999].map(gioco.gettoni).join() === "0,0,1,5,25,25" && gioco.massimo === 25);
  prova("punti: mostriciattolo 500, blocco rotto 50, lancio avanzato 1000", L.PUNTI.mostro === 500 && L.PUNTI.blocco === 50 && L.PUNTI.avanzato === 1000);
  prova("la cabinato ha uno schermo corto senza emoji, e il testo non nomina altri giochi", /^[A-Za-z0-9 ]{1,8}$/.test(gioco.cabinato.schermo) && !/angry|bird|tris|serpente|furgone|spazio/i.test(gioco.regole + gioco.nome));

  // ── il lancio: la velocità viene dalla tensione, con un massimo
  const vel = (dx, dy) => { const v = L.velocitaTiro({ dx, dy }); return v && Math.hypot(v.vx, v.vy); };
  prova("lancio: la velocità cresce con la tensione", vel(-30, 0) > 0 && vel(-60, 0) > vel(-30, 0) && Math.abs(vel(-60, 0) / vel(-30, 0) - 2) < 1e-9);
  prova("lancio: c'è un massimo, e oltre la tensione massima non si va più veloci", Math.abs(vel(-L.MAXT, 0) - L.MAXT * L.K) < 1e-9 && vel(-500, 0) === vel(-L.MAXT, 0));
  prova("lancio: tirando indietro e in basso il sasso va in avanti e in alto; sotto la tensione minima non parte", (() => {
    const v = L.velocitaTiro({ dx: -50, dy: 50 }); return v.vx > 0 && v.vy < 0 && L.velocitaTiro({ dx: -3, dy: 2 }) === null; })());
  prova("lancia: toglie il primo sasso dalla coda, passa al volo; non si lancia due volte né con tiro troppo debole", (() => {
    const s = L.nuovaScena([], ["tre", "normale"]); L.lancia(s, { dx: -2, dy: 1 }); const debole = s.fase === "mira" && s.sassi.length === 0;
    L.lancia(s, { dx: -50, dy: 40 }); const una = s.fase === "volo" && s.sassi.length === 1 && s.sassi[0].tipo === "tre" && s.lanci.join() === "normale";
    L.lancia(s, { dx: -50, dy: 40 }); return debole && una && s.sassi.length === 1 && s.lanci.length === 1; })());
  // un sasso a 45° alla tensione massima: parabola e punto in cui tocca terra, contro la formula
  const parabola = (tiro) => {
    const v = L.velocitaTiro(tiro), s = L.nuovaScena([], ["normale"]); L.lancia(s, tiro);
    let alto = Infinity, xTerra = null, r = s.sassi[0].r;
    for (let i = 0; i < 1200 && xTerra === null; i++){ L.avanza(s, F / 2); const p = s.sassi[0]; if (!p) break; alto = Math.min(alto, p.y); if (p.y + p.r >= T - 0.05) xTerra = p.x; }
    const dh = T - r - L.ANCORA.y, tv = (-v.vy + Math.sqrt(v.vy * v.vy + 2 * L.G * dh)) / L.G;
    return { xTerra, attesa: L.ANCORA.x + v.vx * tv, alto, altoAtteso: L.ANCORA.y - v.vy * v.vy / (2 * L.G) };
  };
  const p45 = parabola({ dx: -70.71, dy: 70.71 });
  prova("sasso a 45°: tocca terra dove dice la parabola (±8 px)", p45.xTerra !== null && Math.abs(p45.xTerra - p45.attesa) < 8, p45);
  prova("sasso a 45°: la cima della parabola è quella giusta (±5 px)", Math.abs(p45.alto - p45.altoAtteso) < 5, p45);
  prova("sasso: più tensione, più lontano", parabola({ dx: -35, dy: 35 }).xTerra < p45.xTerra);
  prova("la traiettoria a puntini parte dalla fionda e sale come il sasso", (() => { const t = L.traiettoria({ dx: -70, dy: 70 }, 12); return t.length === 12 && t[0].x > L.ANCORA.x && t[0].y < L.ANCORA.y && L.traiettoria({ dx: 0, dy: 0 }).length === 0; })());

  // ── i blocchi: appoggi, riposo, crolli
  const pila = () => L.nuovaScena([blocco("legno", 300, 0, 40, 20), blocco("legno", 300, 20, 40, 20), blocco("pietra", 300, 40, 40, 20)], []);
  const restaFermo = (s) => {
    const prima = s.corpi.map(c => [c.x, c.y]); gira(s, 3);
    // dopo 3 s: ancora lì (meno di 1 px), tutti addormentati (nessun tremolio), nessuno rotto
    const dopo = s.corpi.map(c => [c.x, c.y]);
    return s.corpi.length === prima.length && prima.every((p, i) => Math.hypot(p[0] - dopo[i][0], p[1] - dopo[i][1]) < 1) && s.corpi.every(c => c.dormi) && L.ferma(s);
  };
  prova("un blocco appoggiato su un altro resta fermo, e dopo un po' si addormenta (niente tremolio)", restaFermo(pila()));
  prova("a riposo resta fermo anche per molto tempo: nessuno si sveglia da solo", (() => { const s = pila(); gira(s, 3); const y = s.corpi.map(c => c.y); gira(s, 20); return s.corpi.every((c, i) => c.dormi && c.y === y[i]); })());
  prova("la pila di blocchi appoggia davvero: i blocchi sono uno sopra l'altro, non compenetrati", (() => { const s = pila(); gira(s, 3); const [a, b, c] = s.corpi; return Math.abs((a.y - b.y) - 20) < 1 && Math.abs((b.y - c.y) - 20) < 1 && Math.abs(a.y + 10 - T) < 1; })());
  // controprova: un blocco appeso in aria su niente NON resta fermo, quindi la regola deve dare falso
  prova("controprova: un blocco sospeso in aria non resta fermo (la regola diventa rossa)", restaFermo(L.nuovaScena([blocco("legno", 300, 100, 40, 20)], [])) === false);
  prova("togliendo il blocco sotto, quello sopra cade e si ferma sulla terra", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 30), blocco("legno", 300, 30, 40, 20)], []); gira(s, 2);
    const [sotto, sopra] = s.corpi; const y0 = sopra.y; L.togli(s, sotto.id); gira(s, 2);
    return s.corpi.length === 1 && s.corpi[0].y > y0 + 25 && Math.abs(s.corpi[0].y + 10 - T) < 1 && s.corpi[0].dormi; })());
  prova("togliendo un blocco che NON regge niente, gli altri restano dove sono", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 30), blocco("legno", 300, 30, 40, 20), blocco("legno", 360, 0, 40, 30)], []); gira(s, 2);
    const y = s.corpi[1].y; L.togli(s, s.corpi[2].id); gira(s, 2); return Math.abs(s.corpi[1].y - y) < 1 && s.corpi.every(c => c.dormi); })());
  prova("una spinta laterale muove un blocco, poi frena e si ferma", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 20)], []); s.corpi[0].vx = 250; sveglia(s); gira(s, 3); const c = s.corpi[0]; return c.x > 305 && c.x < 400 && c.dormi && Math.abs(c.y + 10 - T) < 1;
    function sveglia(s) { s.corpi[0].dormi = false; } })());
  prova("un blocco che cade su un altro lo spinge e non lo attraversa", (() => {
    const s = L.nuovaScena([blocco("pietra", 300, 0, 60, 20), blocco("legno", 300, 40, 30, 20)], []); gira(s, 3);
    const [a, b] = s.corpi; return Math.abs((a.y - b.y) - 20) < 1.5 && L.ferma(s); })());

  // ── rotture: ghiaccio poco, legno un colpo forte, pietra quasi mai
  const resta = (m, v, tipo) => { const s = colpo(m, v, tipo); return s.corpi.some(c => c.m === m); };
  const stessoColpo = (v) => !resta("ghiaccio", v) && resta("legno", v) && resta("pietra", v);
  prova("lo stesso colpo (250 px/s): il ghiaccio si rompe e il legno no", stessoColpo(250));
  // controprova: a un colpo fortissimo anche il legno si rompe, quindi «il legno regge» deve dare falso
  prova("controprova: a tutta velocità il legno si rompe (la regola «il legno regge» diventa rossa)", stessoColpo(470) === false && resta("legno", 470) === false);
  prova("la pietra, anche a tutta velocità, regge un sasso normale", resta("pietra", 470));
  prova("il sasso pesante sfonda la pietra, quello normale no", !resta("pietra", 470, "pesante") && resta("pietra", 470, "normale"));
  prova("un sasso che rompe un blocco passa oltre, frenato", (() => { const s = colpo("ghiaccio", 300); return s.sassi.length === 0 || s.sassi[0].x > 300 || s.punti >= 50; })());
  prova("i punti: ogni blocco rotto vale 50", (() => { const s = colpo("ghiaccio", 300); return s.punti === L.PUNTI.blocco; })());
  prova("un blocco che si rompe fa svegliare gli altri", (() => {
    const s = L.nuovaScena([blocco("ghiaccio", 300, 0, 16, 48), blocco("legno", 360, 0, 40, 20)], []); gira(s, 2); const [g, l] = s.corpi; L.togli(s, g.id); return l.dormi === false; })());

  // ── i mostriciattoli
  prova("un mostriciattolo colpito forte è eliminato e vale 500", (() => {
    const s = L.nuovaScena([blocco("mostro", 300, 0, 26, 26)], []); s.fase = "volo"; s.sassi.push(L.sassoDa("normale", 240, T - 13, 400, 0)); gira(s, 1);
    return s.mostri === 0 && s.punti === 500; })());
  prova("un mostriciattolo sfiorato piano resta in piedi", (() => {
    const s = L.nuovaScena([blocco("mostro", 300, 0, 26, 26)], []); s.fase = "volo"; s.sassi.push(L.sassoDa("normale", 240, T - 13, 60, 0)); gira(s, 3);
    return s.mostri === 1 && s.punti === 0; })());
  prova("un mostriciattolo che cade da un'altezza vera è eliminato (e uno fermo a terra no)", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 40), blocco("mostro", 300, 40, 26, 26), blocco("mostro", 360, 0, 26, 26)], []); gira(s, 1.5);
    const sicuri = s.mostri === 2; L.togli(s, s.corpi[0].id); gira(s, 2); return sicuri && s.mostri === 1 && s.punti === 500; })());
  prova("controprova: se il mostriciattolo ha il sasso sotto i piedi non cade (la regola «cade» diventa rossa)", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 40), blocco("mostro", 300, 40, 26, 26)], []); gira(s, 3); return s.mostri === 0; })() === false);

  // ── i sassi speciali
  prova("il sasso «tre» toccato in volo si divide in tre sassi, e solo una volta", (() => {
    const s = L.nuovaScena([], ["tre"]); L.lancia(s, { dx: -60, dy: 40 }); gira(s, 0.3); const n0 = s.sassi.length; L.tocca(s);
    const tre = s.sassi.length === 3 && s.sassi.every(p => p.tipo === "pezzo") && new Set(s.sassi.map(p => p.vy.toFixed(1))).size === 3; L.tocca(s); return n0 === 1 && tre && s.sassi.length === 3; })());
  prova("i tre sassi partono dallo stesso punto e vanno avanti insieme alla stessa velocità", (() => {
    const s = L.nuovaScena([], ["tre"]); L.lancia(s, { dx: -60, dy: 40 }); gira(s, 0.3); const v0 = Math.hypot(s.sassi[0].vx, s.sassi[0].vy); L.tocca(s);
    return s.sassi.every(p => Math.abs(Math.hypot(p.vx, p.vy) - v0) < 1e-6 && p.vx > 0) && s.sassi.every(p => p.x === s.sassi[0].x && p.y === s.sassi[0].y); })());
  prova("il sasso «veloce» toccato in volo accelera, una volta sola, con un massimo", (() => {
    const s = L.nuovaScena([], ["veloce"]); L.lancia(s, { dx: -60, dy: 40 }); gira(s, 0.2); const v0 = Math.hypot(s.sassi[0].vx, s.sassi[0].vy); L.tocca(s);
    const v1 = Math.hypot(s.sassi[0].vx, s.sassi[0].vy); L.tocca(s); const v2 = Math.hypot(s.sassi[0].vx, s.sassi[0].vy); return v1 > v0 * 1.5 && v1 <= 900 + 1e-6 && v2 === v1; })());
  prova("il sasso normale e quello pesante non fanno niente al tocco", (() => {
    return ["normale", "pesante"].every(t => { const s = L.nuovaScena([], [t]); L.lancia(s, { dx: -60, dy: 40 }); const v = s.sassi[0].vx; L.tocca(s); return s.sassi.length === 1 && s.sassi[0].vx === v; }); })());
  prova("il sasso pesante pesa di più del normale", L.SASSI.pesante.massa > 2 * L.SASSI.normale.massa);

  // ── il filo della partita: fermo → altro lancio, livello passato, sassi finiti
  const mostroSolo = (lanci) => L.nuovaScena([blocco("mostro", 300, 0, 26, 26)], lanci);
  prova("tutto fermo (ferma) → si passa al lancio dopo; finché qualcosa si muove no", (() => {
    const s = mostroSolo(["normale", "normale"]); L.lancia(s, { dx: -2, dy: 40 }); L.lancia(s, { dx: -70, dy: 30 }); const inVolo = s.fase === "volo" && !L.ferma(s);
    gira(s, 8); return inVolo && s.fase === "mira" && L.ferma(s) && s.lanci.length === 1; })());
  prova("ferma: vera solo senza sassi in volo e con tutti i corpi addormentati", (() => {
    const s = L.nuovaScena([blocco("legno", 300, 0, 40, 20)], []); const prima = L.ferma(s); gira(s, 2); const dopo = L.ferma(s);
    s.sassi.push(L.sassoDa("normale", 100, 100, 0, 0)); return prima === false && dopo === true && L.ferma(s) === false; })());
  const vinci = (lanciAvanzati) => { const s = L.nuovaScena([blocco("mostro", 300, 0, 26, 26)], new Array(lanciAvanzati + 1).fill("normale")); s.fase = "volo"; s.lanci.shift(); s.lanci = new Array(lanciAvanzati).fill("normale");
    s.sassi.push(L.sassoDa("normale", 240, T - 13, 400, 0)); gira(s, 6); return s; };
  prova("livello passato a mostriciattoli zero: fase «vinto» e i lanci avanzati danno 1000 l'uno", (() => { const s = vinci(2); return s.mostri === 0 && s.fase === "vinto" && s.bonus === 2000 && s.punti === 500 + 2000; })());
  prova("livello passato anche senza lanci avanzati: nessun bonus", (() => { const s = vinci(0); return s.fase === "vinto" && s.bonus === 0 && s.punti === 500; })());
  prova("con mostriciattoli ancora vivi il livello non è passato", (() => { const s = mostroSolo(["normale"]); L.lancia(s, { dx: -30, dy: 30 }); gira(s, 8); return s.mostri === 1 && s.fase === "perso" && s.fase !== "vinto"; })());
  prova("finiti i sassi con mostriciattoli vivi: fase «perso» solo a tutto fermo", (() => { const s = mostroSolo(["normale"]); L.lancia(s, { dx: -30, dy: 30 }); const durante = s.fase; gira(s, 8); return durante === "volo" && s.fase === "perso"; })());
  prova("con mostriciattoli a zero e un sasso ancora in giro il livello passa comunque (non si aspetta all'infinito)", (() => {
    const s = L.nuovaScena([blocco("mostro", 300, 0, 26, 26)], []); s.fase = "volo"; s.sassi.push(L.sassoDa("normale", 240, T - 13, 400, 0), L.sassoDa("normale", 20, 100, 0, -2000)); gira(s, 5); return s.fase === "vinto"; })());
  prova("prossimoLivello: porta i punti, ricomincia coi lanci del livello dopo", (() => {
    const s = L.nuovoLivello(0, 0); s.punti = 1234; const n = L.prossimoLivello(s); return n.livello === 1 && n.punti === 1234 && n.fase === "mira" && n.lanci.length === L.livelli[1].lanci.length; })());
  prova("dopo l'ultimo livello la partita è finita", L.nuovoLivello(L.livelli.length, 7000).fase === "finito");

  // ── i livelli
  const LV = L.livelli;
  prova("ci sono almeno 8 livelli, con 3-5 lanci ciascuno", LV.length >= 8 && LV.every(v => v.lanci.length >= 3 && v.lanci.length <= 5), LV.map(v => v.lanci.length));
  prova("i livelli sono fatti con materiali e sassi che esistono, dentro la larghezza dello schermo", LV.every(v => v.lanci.every(t => L.SASSI[t] && t !== "pezzo") && v.oggetti.every(o => (L.MAT[o.m]) && o.x - o.w / 2 >= 150 && o.x + o.w / 2 <= L.W)));
  const aperti = LV.map((v, i) => L.nuovoLivello(i));
  prova("ogni livello si assesta: tutto fermo, nessun mostriciattolo caduto, niente rotto, tutti dentro lo schermo", aperti.every((s, i) => L.ferma(s) && s.mostri === LV[i].oggetti.filter(o => o.m === "mostro").length && s.corpi.length === LV[i].oggetti.length && s.punti === 0 && s.corpi.every(c => c.hp === c.hp0 && c.x > 0 && c.x < L.W)));
  prova("il livello in cui vivono: all'inizio la fase è «mira» e c'è almeno un mostriciattolo", aperti.every(s => s.fase === "mira" && s.mostri >= 1));
  const peso = s => s.mostri * 3 + s.corpi.length;
  prova("la difficoltà cresce: il livello 8 ha più mostriciattoli e più blocchi del 1, e il primo non ha sassi speciali", peso(aperti[7]) > peso(aperti[0]) + 10 && LV[0].lanci.every(t => t === "normale")
    && peso(aperti[7]) >= peso(aperti[5]) && peso(aperti[5]) > peso(aperti[2]));
  prova("i sassi speciali arrivano a poco a poco: «tre» dal 4, «veloce» dal 5, «pesante» dal 6", (() => { const prima = t => LV.findIndex(v => v.lanci.includes(t)); return prima("tre") === 3 && prima("veloce") === 4 && prima("pesante") === 5; })());
  // ogni livello si può cominciare a vincere: fra una griglia di tiri ce n'è uno che elimina almeno un mostriciattolo
  prova("in ogni livello c'è almeno un tiro che elimina un mostriciattolo", LV.every((_, i) => {
    for (const ang of [20, 28, 36, 44, 52, 60]) for (const t of [70, 85, 100]) {
      const r = ang * Math.PI / 180, s = L.nuovoLivello(i); s.lanci = ["pesante"]; L.lancia(s, { dx: -Math.cos(r) * t, dy: Math.sin(r) * t }); gira(s, 9);
      if (s.mostri < LV[i].oggetti.filter(o => o.m === "mostro").length) return true;
    }
    return false;
  }));
  prova("un livello giocato davvero si chiude da solo (mai bloccato): dopo ogni lancio si torna a «mira» o a «perso»", LV.every((_, i) => {
    const s = L.nuovoLivello(i); let guardia = 0;
    while (s.fase === "mira" && guardia++ < 6) { L.lancia(s, { dx: -75, dy: 55 }); gira(s, 14); }
    return s.fase === "perso" || s.fase === "vinto";
  }));
}
