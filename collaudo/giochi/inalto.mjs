// Le prove di In alto! (giochi/inalto.js), le fa girare collaudo/giochi.mjs.
// Tutto sulla logica, passo per passo: si costruisce una scena (una piattaforma qui, un mostro lì), si avanza di un fotogramma e si guarda.
// Le regole importanti sono funzioni del modulo (regola(L) → vero/falso): le controprove le girano su una logica rotta apposta.
export default async function (prova, { logica: L, gioco }) {
  const F = 1 / 60;
  const fisso = v => () => v;
  let seme = 5; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const W = 390, A = 844;
  // una scena ferma: niente piattaforme e niente mostri oltre a quelli che si mettono; la visuale sta in basso
  const piatt = (x, y, extra = {}) => ({ x, y, w: 70, tipo: "fissa", rotta: false, ...extra });
  const scena = (extra = {}) => ({ ...L.nuovaPartita(W, A, fisso(0.9999)), piatt: [], mostri: [], razzi: [], alto: 1e9, cam: 0, massimo: 0, ...extra });
  const passo = (s, x) => L.avanza(s, F, x, fisso(0.9999));
  const controprova = (nome, regola, rotta) => prova(`controprova: ${nome}`, regola(L) === true && regola(rotta) === false);

  // gettoni e cabinato
  prova("gettoni: uno ogni 100 punti, al massimo 25", [0, 99, 100, 250, 1000, 2499, 2500, 99999].map(gioco.gettoni).join() === "0,0,1,2,10,24,25,25" && gioco.massimo === 25);
  prova("cabinato: schermo corto senza emoji, nome e regole senza altri giochi", /^[\x20-\x7e]{1,12}$/.test(gioco.cabinato.schermo) && gioco.id === "inalto" && !/tris|serpente|furgone|spazio|doodle/i.test(gioco.nome + gioco.regole));

  // partita nuova
  const s0 = L.nuovaPartita(W, A, rnd);
  prova("partita nuova: punti 0, base larga sotto i piedi, visuale in basso, non finita", s0.punti === 0 && !L.finita(s0) && s0.cam === 0 && s0.piatt.some(p => p.y === s0.y && p.w >= W) && s0.piatt.length > 5);
  prova("avanza non tocca lo stato che riceve (ne dà uno nuovo)", (() => { const j = JSON.stringify(s0); L.avanza(s0, 0.1, 100, rnd); return JSON.stringify(s0) === j; })());

  // rimbalza solo scendendo
  const scende = L.avanza.length >= 0 && (Lx => { const s = scena({ piatt: [piatt(195, 300)], x: 195, y: 303, vy: -400 }); return Lx.avanza(s, F, 195, fisso(0.9999)); });
  const rimbalzaScendendo = Lx => { const r = scende(Lx); return r.vy === Lx.V_SALTO && r.y === 300 && r.eventi.some(e => e.tipo === "salto"); };
  const nonDaSotto = Lx => { const s = scena({ piatt: [piatt(195, 300)], x: 195, y: 295, vy: 500 }); const r = Lx.avanza(s, F, 195, fisso(0.9999));
    const r2 = Lx.avanza(scena({ piatt: [piatt(195, 300)], x: 195, y: 299, vy: 500 }), 3 * F, 195, fisso(0.9999));
    return r.vy < 500 && r.y > 295 && r2.y > 299 && !r2.eventi.some(e => e.tipo === "salto") && r2.vy > 0; };
  prova("rimbalza sulla piattaforma scendendo: vy diventa quella del salto, i piedi sulla piattaforma", rimbalzaScendendo(L), scende(L));
  prova("da sotto la piattaforma si passa attraverso, senza rimbalzare", nonDaSotto(L));
  prova("lontano dalla piattaforma non rimbalza (cade)", (() => { const r = passo(scena({ piatt: [piatt(60, 300)], x: 300, y: 303, vy: -400 }), 300); return r.vy < -400 && r.y < 303; })());
  prova("salto automatico: dopo il rimbalzo sale quanto dice H_SALTO e poi ricade", (() => {
    let s = scena({ piatt: [piatt(195, 100)], x: 195, y: 100, vy: L.V_SALTO, cam: 0, massimo: 100 }), alto = 0;
    for (let i = 0; i < 80 && s.vy >= 0; i++){ s = passo(s, 195); alto = Math.max(alto, s.y - 100); }
    return Math.abs(alto - L.H_SALTO) < 6 && s.vy < 0; })());
  controprova("un rimbalzo anche da sotto fa diventare rossa la prova", nonDaSotto, { ...L, avanza: (s, dt, x, c) => { const r = L.avanza(s, dt, x, c);
    for (const p of s.piatt) if (s.vy > 0 && s.y < p.y && r.y >= p.y){ r.y = p.y; r.vy = L.V_SALTO; r.eventi = [{ tipo: "salto" }]; } return r; } });

  // la piattaforma che si sbriciola regge un salto solo
  const fragile = Lx => {
    let s = scena({ piatt: [piatt(195, 300, { tipo: "fragile" })], x: 195, y: 303, vy: -400 });
    s = Lx.avanza(s, F, 195, fisso(0.9999));
    const primo = s.vy === Lx.V_SALTO && s.piatt[0].rotta === true && s.eventi.some(e => e.tipo === "rompe");
    // la figura ricade sulla stessa piattaforma: ormai sbriciolata, non regge
    s = { ...s, x: 195, y: 303, vy: -400, piatt: s.piatt.map(p => ({ ...p, y: 300 })) };
    const r = Lx.avanza(s, F, 195, fisso(0.9999));
    return primo && r.vy < 0 && !r.eventi.some(e => e.tipo === "salto");
  };
  prova("la piattaforma che si sbriciola regge un salto solo", fragile(L));
  prova("la piattaforma rotta cade giù da sola", (() => { let s = scena({ piatt: [piatt(195, 300, { tipo: "fragile", rotta: true, cade: 0 })], y: 600, vy: 0, cam: 400 }); for (let i = 0; i < 30; i++) s = passo(s, 195); return s.piatt.length === 0 || s.piatt[0].y < 290; })());
  prova("la piattaforma normale regge tanti salti", (() => { let s = scena({ piatt: [piatt(195, 300)], x: 195, y: 303, vy: -400 }), salti = 0;
    for (let k = 0; k < 3; k++){ s = { ...s, x: 195, y: 303, vy: -400 }; s = passo(s, 195); salti += s.eventi.filter(e => e.tipo === "salto").length; } return salti === 3; })());
  controprova("una piattaforma che si sbriciola solo a parole fa diventare rossa la prova", fragile, { ...L, avanza: (s, dt, x, c) => { const r = L.avanza(s, dt, x, c); r.piatt = r.piatt.map(p => ({ ...p, rotta: false })); return r; } });

  // la molla
  const molla = Lx => { const s = scena({ piatt: [piatt(195, 300, { molla: { dx: 0 } })], x: 195, y: 303, vy: -400 });
    const r = Lx.avanza(s, F, 195, fisso(0.9999)), n = Lx.avanza(scena({ piatt: [piatt(195, 300)], x: 195, y: 303, vy: -400 }), F, 195, fisso(0.9999));
    return r.vy === Lx.V_MOLLA && r.vy > n.vy * 1.5 && Lx.H_MOLLA > 2.5 * Lx.H_SALTO; };
  prova("la molla lancia più in alto del salto normale", molla(L));
  prova("la molla si prende solo cadendoci sopra, non di fianco", (() => { const s = scena({ piatt: [piatt(195, 300, { molla: { dx: 25 } })], x: 175, y: 303, vy: -400 }); return passo(s, 175).vy === L.V_SALTO; })());
  prova("dopo una molla la figura sale davvero più alto (in cima al salto)", (() => {
    const alto = v => { let s = scena({ piatt: [], x: 195, y: 100, vy: v, massimo: 100 }), m = 100; for (let i = 0; i < 200 && s.vy > -1; i++){ s = passo(s, 195); m = Math.max(m, s.y); } return m - 100; };
    return alto(L.V_MOLLA) > 2.5 * alto(L.V_SALTO); })());
  controprova("una molla debole come il salto fa diventare rossa la prova", molla, { ...L, avanza: (s, dt, x, c) => { const r = L.avanza(s, dt, x, c); if (r.vy === L.V_MOLLA) r.vy = L.V_SALTO; return r; } });

  // di lato: uscendo da un lato si rientra dall'altro
  const giro = Lx => { const d = Lx.avanza(scena({ x: W - 1, y: 500, vy: 0 }), F, W + 20, fisso(0.9999)), s = Lx.avanza(scena({ x: 1, y: 500, vy: 0 }), F, -20, fisso(0.9999));
    return Math.abs(d.x - 20) < 1e-6 && Math.abs(s.x - (W - 20)) < 1e-6 && d.x >= 0 && d.x < W; };
  prova("uscendo a destra rientra a sinistra, e a sinistra rientra a destra", giro(L));
  prova("senza dito la figura resta dov'è; col dito va dove le si dice", passo(scena({ x: 123, y: 500, vy: 0 })).x === 123 && passo(scena({ x: 123, y: 500, vy: 0 }), 200).x === 200);
  prova("una piattaforma a destra si prende anche rientrando dall'altro lato (la figura mezza fuori)", (() => { const s = scena({ piatt: [piatt(W - 20, 300)], x: 10, y: 303, vy: -400 }); return passo(s, 10).vy === L.V_SALTO; })());
  controprova("uno schermo con i muri (la figura si ferma al bordo) fa diventare rossa la prova", giro, { ...L, avanza: (s, dt, x, c) => { const r = L.avanza(s, dt, x, c); r.x = Math.max(0, Math.min(W, x)); return r; } });

  // le piattaforme: sempre raggiungibili
  const raggiungibili = Lx => {
    const casi = [fisso(0), fisso(0.9999), fisso(0.5), rnd];
    for (const caso of casi){
      let s = Lx.nuovaPartita(W, A, caso);
      for (const alt of [0, 1500, 5000, 12000, 30000, 80000]){
        s = { ...s, cam: alt, y: alt + 100, massimo: alt + 100 }; s = Lx.generaPiattaforme(s, caso);
        const ys = s.piatt.filter(p => !p.rotta).map(p => p.y).sort((a, b) => a - b);
        for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] > Lx.H_SALTO) return false;
      }
    }
    return true;
  };
  prova("la distanza fra due piattaforme non supera mai l'altezza del salto (a ogni quota, con ogni caso)", raggiungibili(L));
  prova("la distanza massima sta sotto il salto con un po' di margine", L.GAP_MAX < L.H_SALTO && L.GAP_MAX > 0.7 * L.H_SALTO);
  prova("generaPiattaforme riempie fin sopra lo schermo e non tocca lo stato che riceve", (() => { const s = { ...s0, cam: 2000, y: 2100, massimo: 2100 }, j = JSON.stringify(s), g = L.generaPiattaforme(s, rnd);
    return JSON.stringify(s) === j && Math.max(...g.piatt.map(p => p.y)) >= 2000 + A; })());
  prova("le piattaforme nuove stanno dentro lo schermo", (() => { const g = L.generaPiattaforme({ ...s0, cam: 9000, y: 9100, massimo: 9100 }, rnd); return g.piatt.every(p => p.x - p.w / 2 >= -0.01 && p.x + p.w / 2 <= W + 0.01); })());
  prova("più si sale, più sono rade (la distanza media cresce) e più strette", (() => {
    const media = alt => { const g = L.generaPiattaforme({ ...s0, cam: alt, y: alt + 100, massimo: alt + 100, alto: alt, piatt: [], mostri: [], razzi: [] }, rnd), ys = g.piatt.map(p => p.y).sort((a, b) => a - b); return (ys.at(-1) - ys[0]) / (ys.length - 1); };
    const largh = alt => L.generaPiattaforme({ ...s0, cam: alt, y: alt + 100, massimo: alt + 100, alto: alt, piatt: [], mostri: [], razzi: [] }, fisso(0.9999)).piatt[0].w;
    return media(0) < media(7000) && media(7000) < media(20000) && largh(0) > largh(20000); })());
  prova("le piattaforme sbriciolabili non sono mai due di fila", (() => { const g = L.generaPiattaforme({ ...s0, cam: 5000, y: 5100, massimo: 5100, alto: 5000, piatt: [], ultimo: "fissa" }, fisso(0)); const ys = g.piatt.sort((a, b) => a.y - b.y).map(p => p.tipo);
    return ys.every((t, i) => !(t === "fragile" && ys[i - 1] === "fragile")); })());
  prova("tutti i tipi in alto: fisse, mobili, sbriciolabili, con molla", (() => { const tutte = []; let s = { ...s0, cam: 6000, y: 6100, massimo: 6100, alto: 6000, piatt: [], mostri: [], razzi: [] };
    for (let i = 0; i < 40; i++){ s = L.generaPiattaforme({ ...s, cam: s.cam + 300 }, rnd); tutte.push(...s.piatt); }
    return ["fissa", "mobile", "fragile"].every(t => tutte.some(p => p.tipo === t)) && tutte.some(p => p.molla); })());
  prova("la piattaforma mobile si muove da sola e resta nello schermo", (() => { let s = scena({ piatt: [piatt(195, 900, { tipo: "mobile", x0: 195, amp: 70, vel: 2, fase: 0 })], y: 800, vy: 0, cam: 400 }), xs = [];
    for (let i = 0; i < 90; i++){ s = passo({ ...s, y: 800, vy: 0 }, 195); xs.push(s.piatt[0].x); } return Math.max(...xs) - Math.min(...xs) > 60 && xs.every(x => x > 35 && x < W - 35); })());

  // mostri e razzi: solo in alto
  prova("mostri e razzi compaiono solo in alto (non prima di 200 m e 400 m)", (() => {
    const bassi = L.generaPiattaforme({ ...s0, cam: 0, y: 100, massimo: 100, alto: 0, piatt: [], mostri: [], razzi: [] }, fisso(0));
    const alti = L.generaPiattaforme({ ...s0, cam: 6000, y: 6100, massimo: 6100, alto: 6000, piatt: [], mostri: [], razzi: [] }, fisso(0));
    return bassi.mostri.length === 0 && bassi.razzi.length === 0 && alti.mostri.length > 0; })());
  prova("un razzo compare, raro, più in alto", (() => { let s = { ...s0, cam: 9000, y: 9100, massimo: 9100, alto: 9000, piatt: [], mostri: [], razzi: [] }, n = 0, r = 0;
    for (let i = 0; i < 60; i++){ s = L.generaPiattaforme({ ...s, cam: s.cam + 400 }, rnd); n += s.piatt.length; } r = s.razzi.length + 0;
    return s.razzi.every(x => !x.preso) && r > 0 && r < n / 8; })());
  const mostroQui = (x, y) => ({ x, x0: x, amp: 0, vel: 1, fase: 0, y, vivo: true });
  const schiaccia = Lx => { const r = Lx.avanza(scena({ mostri: [mostroQui(195, 300)], x: 195, y: 306, vy: -300, cam: 100 }), F, 195, fisso(0.9999));
    return !r.finito && r.mostri[0].vivo === false && r.vy > 0 && r.eventi.some(e => e.tipo === "schiaccia"); };
  const tocca = Lx => { const r = Lx.avanza(scena({ mostri: [mostroQui(195, 300)], x: 195, y: 280, vy: 200, cam: 100 }), F, 195, fisso(0.9999)); return r.finito === true && r.causa === "mostro"; };
  prova("saltare su un mostro dall'alto lo schiaccia e rimbalza", schiaccia(L));
  prova("toccare un mostro di lato o da sotto è la fine", tocca(L));
  prova("un mostro lontano non fa niente", !passo(scena({ mostri: [mostroQui(60, 300)], x: 300, y: 300, vy: -10, cam: 100 })).finito);
  controprova("un mostro che non fa male fa diventare rossa la prova", tocca, { ...L, avanza: (s, dt, x, c) => { const r = L.avanza(s, dt, x, c); r.finito = false; r.causa = null; return r; } });
  const razzo = Lx => { let s = scena({ razzi: [{ x: 195, y: 316, preso: false }], x: 195, y: 300, vy: 100, cam: 100 }); s = Lx.avanza(s, F, 195, fisso(0.9999));
    const preso = s.razzi[0].preso && s.razzo > 0; const y0 = s.y; for (let i = 0; i < 30; i++) s = Lx.avanza(s, F, 195, fisso(0.9999)); return preso && s.y - y0 > 500 && !s.finito; };
  prova("il razzo porta su veloce (molto più di un salto) per un po'", razzo(L));
  prova("col razzo i mostri non fanno male", (() => { const r = passo(scena({ razzo: 1, mostri: [mostroQui(195, 316)], x: 195, y: 300, vy: 100, cam: 100 })); return !r.finito; })());
  prova("finito il razzo si ricade", (() => { let s = scena({ razzo: 0.1, x: 195, y: 500, vy: 1500, cam: 300 }); for (let i = 0; i < 20; i++) s = passo(s, 195); return s.razzo <= 0 && s.vy < 1500; })());

  // la visuale sale, i punti sono i metri
  prova("la visuale sale con la figura e non scende mai", (() => { let s = scena({ x: 195, y: 900, vy: 0, cam: 0 }); s = passo(s, 195); const c1 = s.cam; s = { ...s, y: 800, vy: -1 }; s = passo(s, 195); return c1 > 0 && s.cam === c1; })());
  prova("punti = metri saliti (10 px per metro) e non calano scendendo", (() => { let s = { ...L.nuovaPartita(W, A, fisso(0.9999)), y: 60 + 1234, vy: 0 }; s = passo(s, 195); const p = s.punti; s = { ...s, y: s.y - 80, vy: -1 }; s = passo(s, 195);
    return p === 123 && s.punti === 123 && L.metriDi({ massimo: 60 }) === 0; })());
  prova("salendo davvero col gioco intero i punti crescono", (() => { let s = L.nuovaPartita(W, A, rnd); const p0 = s.punti; s = { ...s, vy: L.V_MOLLA }; for (let i = 0; i < 40; i++) s = L.avanza(s, F, 195, rnd); return s.punti > p0 + 10; })());
  prova("lo sfondo cambia con l'altezza: prato, nuvole, notte, spazio", (() => { const n = [0, 100, 200, 500, 900, 5000].map(m => L.sfondo(m).nome).join(); const c = [0, 200, 500, 900].map(m => L.sfondo(m).cima);
    return n === "prato,prato,nuvole,notte,spazio,spazio" && new Set(c).size === 4 && /^#[0-9a-f]{6}$/.test(L.sfondo(380).cima) && L.sfondo(900).stelle > L.sfondo(0).stelle; })());
  prova("lo sfondo sfuma prima di un cambio (nessuno scatto)", L.sfondo(399).cima !== L.sfondo(390).cima && L.sfondo(440).cima === L.sfondo(500).cima);

  // fine partita
  const fine = Lx => { let s = scena({ x: 195, y: 700, vy: 0, cam: 600 }), n = 0; const ok0 = !Lx.finita(s);
    while (!Lx.finita(s) && n++ < 600) s = Lx.avanza(s, F, 195, fisso(0.9999));
    return ok0 && Lx.finita(s) && s.finito === true && s.causa === "caduto" && n < 600 && Lx.avanza(s, 1, 195, fisso(0.9999)) === s; };
  prova("cadendo sotto il bordo dello schermo la partita finisce (e poi non si muove più)", fine(L));
  prova("finita: no sul bordo basso, sì appena sotto", !L.finita(scena({ y: 0, cam: 0 })) && L.finita(scena({ y: -100, cam: 0 })) && L.finita(scena({ y: 500, cam: 0, finito: true })));
  controprova("una partita che non finisce mai cadendo fa diventare rossa la prova", fine, { ...L, finita: s => false });
  prova("una pausa lunga (dt enorme) non fa saltare niente: al massimo 1/10 di secondo per volta", (() => { const s = scena({ x: 195, y: 700, vy: 0, cam: 600 }); const a = L.avanza(s, 5, 195, fisso(0.9999)), b = L.avanza(s, 0.1, 195, fisso(0.9999)); return Math.abs(a.y - b.y) < 1e-6; })());
  prova("dt zero o strano non cambia niente", [0, -1, NaN, undefined].every(dt => { const s = scena({ y: 700, cam: 600 }); return L.avanza(s, dt, 195) === s; }));
}
