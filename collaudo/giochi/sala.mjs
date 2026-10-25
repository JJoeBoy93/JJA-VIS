// Le prove della Sala giochi: dove stanno i cabinati (giochi/sala.js), le fa girare collaudo/giochi.mjs.
// Non sono un gioco: collaudo/giochi.mjs le chiama una volta sola, dopo i giochi di giochi/elenco.js.
// Il controllo è scritto qui, per conto suo (non riusa le regole del modulo): una postiCabinati finta, sbagliata, lo fa diventare rosso.
import { CAB, macchinetta, ingombro, postoDavanti, postiCabinati, capienza } from "../../giochi/sala.js";

export const MISURE = [22, 18];   // DIM_STANZE.giochi in citta.html: 22×18 (396 m²; la Torre è 24×14, la stanza di prima 14×12)

// → l'elenco dei guai (vuoto: tutto bene)
export function controlla(posti, L, P) {
  const g = [], EPS = 1e-6;
  const ing = posti.map(p => { const lato = Math.abs(Math.sin(p.verso)) > 0.5; return { x: p.x, z: p.z, w: lato ? CAB.d : CAB.w, d: lato ? CAB.w : CAB.d }; });
  const sp = (a, b) => Math.max(Math.abs(a.x - b.x) - (a.w + b.w) / 2, Math.abs(a.z - b.z) - (a.d + b.d) / 2);
  const mac = macchinetta(L, P), M = { x: mac.x, z: mac.z, w: mac.w, d: mac.d };
  posti.forEach((p, i) => {
    const a = ing[i], q = postoDavanti(p);
    if (![p.x, p.z, p.verso].every(Number.isFinite)) { g.push(`#${i}: x, z, verso non sono numeri`); return; }
    // dentro le pareti
    if (a.x - a.w / 2 < -L / 2 - EPS || a.x + a.w / 2 > L / 2 + EPS || a.z - a.d / 2 < -P / 2 - EPS || a.z + a.d / 2 > P / 2 + EPS) g.push(`#${i}: fuori dalle pareti`);
    // dal lato dello schermo c'è il punto da cui si gioca: dentro la stanza, e non dentro un altro solido (cabinati, macchinetta)
    if (Math.abs(q.x) > L / 2 - 0.4 || Math.abs(q.z) > P / 2 - 0.4) g.push(`#${i}: il punto da cui si gioca (${q.x.toFixed(2)}, ${q.z.toFixed(2)}) è fuori o contro la parete`);
    ing.forEach((b, j) => { if (j !== i && Math.abs(q.x - b.x) < b.w / 2 + 0.4 && Math.abs(q.z - b.z) < b.d / 2 + 0.4) g.push(`#${i}: il punto da cui si gioca è dentro il cabinato #${j}`); });
    if (Math.abs(q.x - M.x) < M.w / 2 + 0.4 && Math.abs(q.z - M.z) < M.d / 2 + 0.4) g.push(`#${i}: il punto da cui si gioca è sulla macchinetta`);
    // il corridoio dall'ingresso al centro: la porta è a z = +P/2, a x = 0
    if (Math.abs(a.x) - a.w / 2 < 1.0 && a.z + a.d / 2 > 0) g.push(`#${i}: nel corridoio dalla porta al centro`);
    // la macchinetta: distanza, e il suo punto d'arrivo libero
    if (sp(a, M) < 1.4 - EPS) g.push(`#${i}: troppo vicino alla macchinetta dei gettoni (${sp(a, M).toFixed(2)} m)`);
    if (Math.abs(mac.posto.x - a.x) < a.w / 2 + 0.4 && Math.abs(mac.posto.z - a.z) < a.d / 2 + 0.4) g.push(`#${i}: davanti alla macchinetta`);
    // le pareti: attaccato (≤30 cm) oppure a un corridoio di distanza — ma una fila che si riempie ha l'estremità libera: vale se non sta attaccato a nessuna
    const dp = [a.x - a.w / 2 + L / 2, L / 2 - a.x - a.w / 2, a.z - a.d / 2 + P / 2, P / 2 - a.z - a.d / 2];
    if (!dp.some(d => d <= 0.3) && dp.some(d => d < 1.4 - EPS)) g.push(`#${i}: a ${Math.min(...dp).toFixed(2)} m da una parete, né attaccato né un corridoio`);
  });
  // fra loro: niente sovrapposti, e fra un cabinato e l'altro o si toccano (≤30 cm) o ci si passa (≥1,4 m)
  for (let i = 0; i < ing.length; i++) for (let j = i + 1; j < ing.length; j++) {
    const s = sp(ing[i], ing[j]);
    if (s < -EPS) g.push(`#${i} e #${j}: sovrapposti`);
    else if (s > 0.3 && s < 1.4 - EPS) g.push(`#${i} e #${j}: un varco di ${s.toFixed(2)} m, troppo stretto per passare`);
  }
  return g;
}

export default async function (prova, { fonte = postiCabinati } = {}) {
  const [L, P] = MISURE;
  for (const n of [1, 5, 12, 24]) {
    const posti = fonte(n, L, P), g = controlla(posti, L, P);
    prova(`${n} cabinati in ${L}×${P}: tutti entrano, e il controllo non trova guai`, posti.length === n && g.length === 0, g.slice(0, 5).concat(posti.length === n ? [] : [`entrati ${posti.length}`]));
  }
  const a = postiCabinati(5, L, P), b = postiCabinati(12, L, P);
  prova("i posti sono gli stessi qualunque sia n (il primo cabinato non si sposta quando ne arrivano altri)", a.every((p, i) => p.x === b[i].x && p.z === b[i].z && p.verso === b[i].verso));
  prova("fino a 17 sulla parete di fondo, guardano la porta; le pareti laterali guardano la stanza", postiCabinati(17, L, P).every(p => p.z < -P / 2 + 1 && p.verso === 0)
    && (() => { const t = postiCabinati(25, L, P).slice(17); return t.length === 8 && t.every(p => (p.x < 0 && Math.abs(p.verso - Math.PI / 2) < 1e-9) || (p.x > 0 && Math.abs(p.verso + Math.PI / 2) < 1e-9)); })());
  const isole = postiCabinati(capienza(L, P), L, P).filter(p => Math.abs(p.x) < L / 2 - 2 && p.z > -P / 2 + 1.5);
  prova("le file in mezzo stanno schiena contro schiena: ogni cabinato guarda dalla parte opposta di quello dietro", isole.length > 0 && isole.every(p => isole.some(q => q !== p && q.x === p.x && Math.abs(Math.abs(q.z - p.z) - 0.95) < 1e-9 && Math.abs(Math.abs(q.verso - p.verso) - Math.PI) < 1e-9)));
  const max = capienza(L, P);
  console.log(`   (in ${L}×${P} entrano al massimo ${max} cabinati; in 14×12, la stanza di prima: ${capienza(14, 12)}; in 24×14, la Torre: ${capienza(24, 14)})`);
  prova("quanti ne entrano al massimo: più di 24, e chiedendone di più non si sovrappone niente", max > 24 && (() => { const t = fonte(max + 50, L, P); return t.length === max && controlla(t, L, P).length === 0; })(), max);
  prova("l'ordine: il fondo prima di tutto, poi i lati, poi le isole", (() => { const t = postiCabinati(max, L, P); const f = t.filter(p => p.z < -P / 2 + 1 && p.verso === 0).length;
    const prima = t.slice(0, f).every(p => p.z < -P / 2 + 1), poi = t.slice(f, f + 4).every(p => Math.abs(Math.abs(p.x) - (L / 2 - CAB.d / 2)) < 1e-9); return prima && poi; })());
  prova("n = 0 e n negativo: nessun posto", postiCabinati(0, L, P).length === 0 && postiCabinati(-3, L, P).length === 0);
  // un'altra stanza (14×12, quella di prima) e una più larga: lo stesso controllo
  for (const [l, p] of [[14, 12], [24, 14], [30, 20]]) { const t = postiCabinati(capienza(l, p), l, p), g = controlla(t, l, p); prova(`${l}×${p}: ${t.length} cabinati (al massimo), nessun guaio`, t.length > 0 && g.length === 0, g.slice(0, 4)); }
  // la controprova: una funzione finta che mette due cabinati nello stesso punto deve far rosso il controllo
  const finta = (n, l, p) => postiCabinati(n, l, p).map((q, i, v) => i === 1 ? { ...v[0] } : q);
  prova("controprova: due cabinati nello stesso punto → il controllo se ne accorge", controlla(finta(5, L, P), L, P).some(x => x.includes("sovrapposti")), controlla(finta(5, L, P), L, P));
  const nelCorridoio = [{ x: 0, z: 5, verso: 0 }], suMacchinetta = [{ x: macchinetta(L, P).x, z: macchinetta(L, P).z - 2, verso: Math.PI }], fuori = [{ x: L / 2, z: 0, verso: 0 }];
  prova("controprova: un cabinato davanti alla porta, uno sulla macchinetta e uno fuori dalle pareti fanno rosso", controlla(nelCorridoio, L, P).length > 0 && controlla(suMacchinetta, L, P).length > 0 && controlla(fuori, L, P).length > 0);
}
