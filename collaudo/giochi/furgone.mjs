// Le prove del Furgone in fuga (giochi/furgone.js), le fa girare collaudo/giochi.mjs.
// Le regole sulla logica, passo per passo; la corsia libera su 20 000 file generate e su lunghe corse con un pilota automatico.
export default async function (prova, { logica: L, gioco }) {
  let seme = 7; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const con = (cose, extra = {}) => ({...L.nuovo(), cose, ...extra});   // uno stato con queste cose in strada
  const auto = (corsia, y) => ({tipo:"auto", corsia, y, id:0});
  const vuoto = () => 0.999;   // con caso ~1: file da un solo ostacolo, mai pacchi
  const per = (s, secondi, caso = vuoto) => { for (let t = 0; t < secondi - 1e-9; t += 1 / 60) s = L.avanza(s, 1 / 60, caso); return s; };   // a fotogrammi

  // la partenza
  const s0 = L.nuovo();
  prova("si parte in corsia centrale, da fermi a 0 metri, 0 punti", s0.corsia === 1 && s0.metri === 0 && s0.pacchi === 0 && !s0.finito && L.punti(s0) === 0);

  // cambiare corsia
  prova("cambiaCorsia: sinistra e destra di una", L.cambiaCorsia(s0, -1).corsia === 0 && L.cambiaCorsia(s0, 1).corsia === 2);
  prova("cambiaCorsia: dal bordo non si esce", L.cambiaCorsia(L.cambiaCorsia(s0, -1), -1).corsia === 0 && L.cambiaCorsia(L.cambiaCorsia(s0, 1), 1).corsia === 2);
  prova("cambiaCorsia non tocca lo stato di prima (funzione pura)", (L.cambiaCorsia(s0, 1), s0.corsia === 1));

  // le collisioni: una regola alla volta, provata contro la collisione vera e contro una rotta
  function regoleUrto(urta) {
    const rotte = [];
    const ok = (nome, v) => { if (!v) rotte.push(nome); };
    ok("auto nella stessa corsia, addosso: schianto", !!urta(con([auto(1, 0)])));
    ok("auto nella corsia accanto: niente", !urta(con([auto(0, 0), auto(2, 0.5)])));
    ok("auto lontana davanti: niente", !urta(con([auto(1, 10)])));
    ok("auto già passata: niente", !urta(con([auto(1, -3)])));
    ok("cantiere: schianto anche saltando", !!urta(con([{tipo:"cantiere", corsia:1, y:0}], {salto:0.3})));
    ok("auto: schianto anche saltando", !!urta(con([auto(1, 0)], {salto:0.3})));
    ok("transenna senza saltare: schianto", !!urta(con([{tipo:"transenna", corsia:1, y:0.4}])));
    ok("transenna saltando: si passa", !urta(con([{tipo:"transenna", corsia:1, y:0.4}], {salto:0.3})));
    ok("un pacco non è un ostacolo", !urta(con([{tipo:"pacco", corsia:1, y:0}])));
    return rotte;
  }
  const urtoVero = regoleUrto(L.collisione);
  prova("collisione: auto, transenne (si saltano), cantieri, pacchi — tutte le regole", urtoVero.length === 0, urtoVero);
  // controprova: una collisione rotta che non guarda la corsia deve far diventare rosso il controllo
  const rotta = s => s.cose.find(c => c.tipo !== "pacco" && Math.abs(c.y) <= L.MEZZO && !(c.tipo === "transenna" && s.salto > 0)) || null;
  prova("controprova: una collisione che ignora la corsia viene scoperta", regoleUrto(rotta).includes("auto nella corsia accanto: niente"));

  // il salto
  const su = L.salta(s0);
  prova("salta: il salto dura un po' e poi finisce", su.salto === L.SALTO && per(su, L.SALTO + 0.05).salto === 0);
  prova("salta: in aria non si risalta", L.salta({...su, salto:0.2}).salto === 0.2);

  // avanzare
  const a = L.avanza({...s0, prossima:1e9}, 0.25, vuoto), atteso = 0.25 * (L.V0 + L.velocita(0.25)) / 2;
  prova("avanza: metri = velocità × tempo (e la velocità sale già)", Math.abs(a.metri - atteso) < 0.01 && Math.abs(a.tempo - 0.25) < 1e-9 && a.velocita > L.V0, [a.metri, atteso]);
  prova("avanza: un fotogramma lunghissimo (pagina bloccata) vale al più 0,25 s", Math.abs(L.avanza({...s0, prossima:1e9}, 5, vuoto).tempo - 0.25) < 1e-9);
  const b = per(con([auto(0, 20)], {prossima:1e9}), 0.5);
  prova("avanza: le cose vengono incontro al furgone", Math.abs(b.cose[0].y - (20 - b.metri)) < 1e-6);
  const c = per(con([auto(1, 5)], {prossima:1e9}), 1);
  prova("avanza: un'auto davanti nella stessa corsia chiude la partita", c.finito && c.schianto && c.schianto.tipo === "auto");
  prova("avanza: l'auto non attraversa il furgone anche con un fotogramma lungo", L.avanza(con([auto(1, 1.9)], {prossima:1e9, tempo:200, velocita:L.VMAX}), 0.25, vuoto).finito);
  const d = per(con([auto(0, 5)], {prossima:1e9}), 1);
  prova("avanza: l'auto nella corsia accanto passa e se ne va", !d.finito && d.cose.length === 0);

  // fine partita
  prova("a partita finita non si avanza e non si cambia corsia", L.avanza(c, 1, vuoto) === c && L.cambiaCorsia(c, -1) === c && L.salta(c) === c);

  // il punteggio
  const pac = per(con([{tipo:"pacco", corsia:1, y:3}, {tipo:"pacco", corsia:2, y:3}], {prossima:1e9}), 1);
  prova("pacco nella tua corsia: preso; quello accanto no", pac.pacchi === 1 && !pac.finito);
  prova("punti: metri/10 (per difetto) + 5 per pacco", L.punti({metri:237, pacchi:3}) === 23 + 15 && L.punti({metri:9.9, pacchi:0}) === 0 && L.punti(pac) === Math.floor(pac.metri / 10) + 5);
  prova("gettoni: punti/10 per difetto, al massimo 25", gioco.gettoni(0) === 0 && gioco.gettoni(19) === 1 && gioco.gettoni(120) === 12 && gioco.massimo === 25
    && Math.min(gioco.gettoni(999), gioco.massimo) === 25);

  // la difficoltà cresce col tempo
  const crescente = f => [0, 10, 20, 40, 60].every((t, i, v) => i === 0 || f(t) >= f(v[i - 1])) && f(60) > f(0);
  prova("velocità crescente col tempo, fino al massimo", crescente(L.velocita) && L.velocita(0) === L.V0 && L.velocita(1000) === L.VMAX);
  prova("file sempre più fitte, mai sotto il minimo", crescente(t => -L.distanza(t)) && L.distanza(1000) === L.FILA_MIN);
  prova("più spesso due corsie chiuse", crescente(L.doppia));
  const media = t => { let n = 0; seme = 3; for (let i = 0; i < 4000; i++) n += L.generaFila(t, rnd).filter(o => o.tipo !== "pacco").length; return n / 4000; };
  prova("ostacoli per fila: più all'80° secondo che all'inizio", media(80) > media(0) + 0.3, [media(0), media(80)]);

  // una corsia SEMPRE libera: sulle file generate…
  const sempreLibera = genera => { seme = 11; for (let i = 0; i < 20000; i++) if (L.corsieLibere(genera((i % 200) * 0.6, rnd)).length < 1) return false; return true; };
  prova("ogni fila generata lascia almeno una corsia libera (20 000 file, a ogni difficoltà)", sempreLibera(L.generaFila));
  prova("il pacco sta sempre in una corsia libera", (() => { seme = 5; for (let i = 0; i < 5000; i++){ const f = L.generaFila(90, rnd), p = f.find(o => o.tipo === "pacco");
    if (p && !L.corsieLibere(f).includes(p.corsia)) return false; } return true; })());
  // controprova: un generatore che a volte chiude tutte e tre le corsie deve essere scoperto
  const chiudeTutto = (t, caso) => (caso() < 0.01 ? [0, 1, 2].map(c => ({tipo:"auto", corsia:c, y:L.ORIZZONTE})) : L.generaFila(t, caso));
  prova("controprova: un generatore che chiude tutte le corsie viene scoperto", !sempreLibera(chiudeTutto));

  // …e sulla strada vera: un pilota automatico che va sempre nella corsia libera della prossima fila non si schianta mai
  function corsa(pilota, secondi, s = 1) {
    seme = s; let st = L.nuovo(), chiuse = 0, file = new Map();
    for (let t = 0; t < secondi && !st.finito; t += 1 / 60) {
      st = pilota(st);
      st = L.avanza(st, 1 / 60, rnd);
      // in ogni istante, attorno a ogni y, le corsie chiuse sono al massimo 2
      for (const o of st.cose) if (o.tipo !== "pacco") {
        const vicine = new Set(st.cose.filter(p => p.tipo !== "pacco" && Math.abs(p.y - o.y) < 2 * L.MEZZO).map(p => p.corsia));
        if (vicine.size >= 3) chiuse++;
      }
      for (const o of st.cose) if (o.id && !file.has(o.id)) file.set(o.id, o.y + st.metri);
    }
    const inizi = [...new Set([...file.values()].map(v => v.toFixed(3)))].map(Number).sort((x, y) => x - y);
    const strette = inizi.filter((v, i) => i > 0 && v - inizi[i - 1] < L.FILA_MIN - 1e-6).length;
    return {st, chiuse, strette};
  }
  const bravo = st => {
    const avanti = st.cose.filter(o => o.tipo !== "pacco" && o.y > -L.MEZZO - 0.01);
    if (!avanti.length) return st;
    const y0 = Math.min(...avanti.map(o => o.y)), libere = L.corsieLibere(avanti.filter(o => Math.abs(o.y - y0) < 1));
    const meta = libere.includes(st.corsia) ? st.corsia : libere[0];
    while (st.corsia !== meta) st = L.cambiaCorsia(st, meta - st.corsia);
    return st;
  };
  const corse = [1, 2, 3, 4, 5].map(s => corsa(bravo, 240, s));
  prova("il pilota che sceglie la corsia libera arriva a 4 minuti senza schianti (5 corse)", corse.every(r => !r.st.finito && r.st.tempo > 239), corse.map(r => [r.st.finito, Math.round(r.st.tempo)]));
  prova("in strada non ci sono mai tre corsie chiuse insieme", corse.every(r => r.chiuse === 0), corse.map(r => r.chiuse));
  prova("le file non sono mai più vicine del minimo (c'è tempo per cambiare corsia)", corse.every(r => r.strette === 0), corse.map(r => r.strette));
  prova("in 4 minuti si va forte e si fanno punti", corse.every(r => r.st.velocita === L.VMAX && L.punti(r.st) > 500), corse.map(r => L.punti(r.st)));
  // controprova: chi resta fermo in corsia prima o poi si schianta
  const fermo = corsa(st => st, 240);
  prova("controprova: chi non cambia mai corsia si schianta", fermo.st.finito && !!fermo.st.schianto, Math.round(fermo.st.tempo));
}
