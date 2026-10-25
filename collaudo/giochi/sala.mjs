// Le prove della Sala giochi: dove stanno i cabinati (giochi/sala.js), le fa girare collaudo/giochi.mjs.
// Non sono un gioco: collaudo/giochi.mjs le chiama una volta sola, dopo i giochi di giochi/elenco.js.
// Il controllo è scritto qui, per conto suo (non riusa le regole del modulo): una postiCabinati finta, sbagliata, lo fa diventare rosso.
import { CAB, macchinetta, ingombro, postoDavanti, postiCabinati, capienza, PASSO, righeInsegna } from "../../giochi/sala.js";

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

// il varco minimo fra due cabinati vicini della stessa fila (stessa parete, stesso verso); Infinity se nessuna fila ha due cabinati
export function varcoMinimoFila(posti) {
  const file = new Map();
  posti.forEach(p => { const lato = Math.abs(Math.sin(p.verso)) > 0.5, k = `${p.verso.toFixed(3)}|${(lato ? p.x : p.z).toFixed(3)}`; (file.get(k) || file.set(k, []).get(k)).push({ t: lato ? p.z : p.x }); });
  let min = Infinity;
  for (const f of file.values()) { f.sort((a, b) => a.t - b.t); for (let i = 1; i < f.length; i++) min = Math.min(min, f[i].t - f[i - 1].t - CAB.w); }
  return min;
}
// le etichette sopra i cabinati (1,9 m di larghezza, come etichettaFissa in citta.html): vicino a una parete laterale stanno
// parallele alla parete (orientaVersoStanza), altrove guardano la porta. Le isole schiena contro schiena, a pari x, sono
// una dietro l'altra: l'etichetta del cabinato che guarda il fondo (verso π) sta più in alto (0,55 m, come in citta.html).
export function etichetteSovrapposte(posti, L) {
  const r = posti.map((p, i) => { const lato = Math.abs(p.x) > L / 2 - 1.6; return { i, x: p.x, z: p.z, w: lato ? 0.05 : 1.9, d: lato ? 1.9 : 0.05, y: 3.45 + (Math.abs(Math.abs(p.verso) - Math.PI) < 1e-9 ? 0.55 : 0) }; });
  const g = [];
  for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) {
    const a = r[i], b = r[j];
    if (Math.abs(a.y - b.y) >= 0.475) continue;                                            // a quote diverse: una sopra l'altra, non si coprono
    const lungo = a.w > a.d && b.w > b.d, dx = Math.abs(a.x - b.x) < (a.w + b.w) / 2, dz = Math.abs(a.z - b.z) < (a.d + b.d) / 2;
    if (dx && dz) g.push(`etichette #${i} e #${j} sovrapposte`);
    else if (lungo && dx && Math.abs(a.z - b.z) < 1.5) g.push(`etichette #${i} e #${j} una davanti all'altra (stesso x, a meno di 1,5 m, stessa quota)`);
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
  const tutti = postiCabinati(capienza(L, P), L, P), sulFondo = tutti.filter(p => p.z < -P / 2 + 1 && p.verso === 0), lati = tutti.filter(p => Math.abs(Math.abs(p.verso) - Math.PI / 2) < 1e-9);
  prova("la parete di fondo: i cabinati guardano la porta; le pareti laterali guardano la stanza, uno specchio dell'altro", sulFondo.length === 9
    && lati.length > 0 && lati.every(p => (p.x < 0 && Math.abs(p.verso - Math.PI / 2) < 1e-9) || (p.x > 0 && Math.abs(p.verso + Math.PI / 2) < 1e-9))
    && lati.filter(p => p.x < 0).length === lati.filter(p => p.x > 0).length, [sulFondo.length, lati.length]);
  const isole = postiCabinati(capienza(L, P), L, P).filter(p => Math.abs(p.x) < L / 2 - 2 && p.z > -P / 2 + 1.5);
  prova("le file in mezzo stanno schiena contro schiena: ogni cabinato guarda dalla parte opposta di quello dietro", isole.length > 0 && isole.every(p => isole.some(q => q !== p && q.x === p.x && Math.abs(Math.abs(q.z - p.z) - 0.95) < 1e-9 && Math.abs(Math.abs(q.verso - p.verso) - Math.PI) < 1e-9)));
  const max = capienza(L, P);
  console.log(`   (in ${L}×${P} entrano al massimo ${max} cabinati; in 14×12, la stanza di prima: ${capienza(14, 12)}; in 24×14, la Torre: ${capienza(24, 14)})`);
  prova("quanti ne entrano al massimo: più di 24, e chiedendone di più non si sovrappone niente", max > 24 && (() => { const t = fonte(max + 50, L, P); return t.length === max && controlla(t, L, P).length === 0; })(), max);
  prova("l'ordine: 3 sul fondo, uno per parete laterale, il resto del fondo e dei lati, le isole per ultime", (() => { const t = postiCabinati(max, L, P);
    const fondo = i => t[i].verso === 0 && t[i].z < -P / 2 + 1, lato = i => Math.abs(Math.abs(t[i].verso) - Math.PI / 2) < 1e-9;
    const ultimoMuro = Math.max(...t.map((_, i) => (fondo(i) || lato(i)) ? i : -1)), primaIsola = t.findIndex((_, i) => !fondo(i) && !lato(i));
    return [0, 1, 2].every(fondo) && lato(3) && lato(4) && t[3].x < 0 && t[4].x > 0 && primaIsola > ultimoMuro; })());
  prova("n = 0 e n negativo: nessun posto", postiCabinati(0, L, P).length === 0 && postiCabinati(-3, L, P).length === 0);
  // un'altra stanza (14×12, quella di prima) e una più larga: lo stesso controllo
  for (const [l, p] of [[14, 12], [24, 14], [30, 20]]) { const t = postiCabinati(capienza(l, p), l, p), g = controlla(t, l, p); prova(`${l}×${p}: ${t.length} cabinati (al massimo), nessun guaio`, t.length > 0 && g.length === 0, g.slice(0, 4)); }
  // la distanza: fra due cabinati vicini della stessa fila almeno 0,8 m di spazio libero; con pochi giochi non stanno tutti sul fondo
  for (const n of [2, 5, 8]) { const t = fonte(n, L, P), v = varcoMinimoFila(t);
    prova(`n = ${n}: fra due cabinati vicini della stessa fila almeno 0,8 m liberi (il più stretto: ${Number.isFinite(v) ? v.toFixed(2) + " m" : "nessuna fila con due cabinati"})`, t.length === n && v >= 0.8 - 1e-9 && controlla(t, L, P).length === 0, t.length === n ? v : `entrati ${t.length}`); }
  const cinque = fonte(5, L, P);
  prova("n = 5: non sono tutti sulla parete di fondo (i cabinati si spargono per la sala)", cinque.some(p => !(p.verso === 0 && p.z < -P / 2 + 1)) && cinque.some(p => p.verso === 0 && p.z < -P / 2 + 1));
  prova("la distanza vale anche con tanti cabinati (tutte le file, fino alla capienza)", varcoMinimoFila(postiCabinati(max, L, P)) >= 0.8 - 1e-9, varcoMinimoFila(postiCabinati(max, L, P)));
  // le etichette sopra i cabinati non si sovrappongono (n = 2, 5, 8, 12, 24 e fino alla capienza)
  for (const n of [2, 5, 8, 12, 24, max]) { const g = etichetteSovrapposte(fonte(n, L, P), L); prova(`n = ${n}: le etichette sopra i cabinati non si sovrappongono`, g.length === 0, g.slice(0, 3)); }
  // il testo dell'insegna: righe intere (mai una parola spezzata), al massimo 2, per i nomi veri dei giochi (giochi/elenco.js) e per altri
  const NOMI = ["Acchiappa i gettoni", "Tris", "Serpentone", "Il furgone in fuga", "Assalto dallo spazio"];
  for (const nome of NOMI.concat(["Una parola", "A", "Nome molto lungo di un gioco di prova ancora più lungo", "  Spazi   in   mezzo  "])) {
    const r = righeInsegna(nome), parole = nome.trim().split(/\s+/);
    prova(`insegna «${nome.trim()}»: ${JSON.stringify(r)} — al massimo 2 righe, nessuna parola spezzata, tutto il testo`, r.length >= 1 && r.length <= 2 && r.join(" ") === parole.join(" ") && r.every(x => x.trim() === x && x !== "") && r.every(x => x.split(" ").every(w => parole.includes(w))), r); }
  prova("insegna: Tris e Serpentone su una riga; gli altri 3 nomi su due, tagliati fra due parole", righeInsegna("Tris").length === 1 && righeInsegna("Serpentone").length === 1
    && JSON.stringify(righeInsegna("Il furgone in fuga")) === '["Il furgone","in fuga"]' && righeInsegna("Assalto dallo spazio").length === 2 && righeInsegna("Acchiappa i gettoni").length === 2);
  prova("insegna: nome vuoto, spazi o mancante → nessuna riga (l'insegna resta spenta, senza numeri né scritte)", [righeInsegna(""), righeInsegna("   "), righeInsegna(undefined), righeInsegna(null)].every(r => r.length === 0));
  prova(`PASSO = ${PASSO}: lascia ${(PASSO - CAB.w).toFixed(1)} m fra due cabinati (≥ 0,8)`, PASSO - CAB.w >= 0.8 - 1e-9);
  // la controprova: una funzione finta che mette due cabinati nello stesso punto deve far rosso il controllo
  const finta = (n, l, p) => postiCabinati(n, l, p).map((q, i, v) => i === 1 ? { ...v[0] } : q);
  prova("controprova: due cabinati nello stesso punto → il controllo se ne accorge", controlla(finta(5, L, P), L, P).some(x => x.includes("sovrapposti")), controlla(finta(5, L, P), L, P));
  const nelCorridoio = [{ x: 0, z: 5, verso: 0 }], suMacchinetta = [{ x: macchinetta(L, P).x, z: macchinetta(L, P).z - 2, verso: Math.PI }], fuori = [{ x: L / 2, z: 0, verso: 0 }];
  prova("controprova: un cabinato davanti alla porta, uno sulla macchinetta e uno fuori dalle pareti fanno rosso", controlla(nelCorridoio, L, P).length > 0 && controlla(suMacchinetta, L, P).length > 0 && controlla(fuori, L, P).length > 0);
  // controprova: col PASSO di prima (1,3: 10 cm fra un cabinato e l'altro) la prova della distanza diventa rossa
  const vecchi = Array.from({ length: 5 }, (_, i) => ({ x: (i - 2) * 1.3, z: -P / 2 + CAB.d / 2, verso: 0 }));
  prova("controprova: col PASSO di prima (1,3) la distanza fra i cabinati della stessa fila è sotto 0,8 m", varcoMinimoFila(vecchi) < 0.8, varcoMinimoFila(vecchi));
  prova("controprova: etichette larghe 1,9 m su cabinati a 1,3 m una dall'altra si sovrappongono", etichetteSovrapposte(vecchi, L).length > 0);
}
