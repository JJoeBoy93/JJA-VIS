// Dove stanno i cabinati nella Sala giochi (citta.html, ARREDI.giochi). Puro: nessun elemento della pagina, si prova in node
// (collaudo/giochi/sala.mjs). Un cabinato per ogni gioco, senza un numero massimo fisso: finché c'è spazio.
// Ordine dei posti, come nelle sale giochi vere: la parete di fondo (dal centro verso gli angoli), le due pareti laterali
// (una a sinistra e una a destra, dal fondo verso la porta), poi le isole in mezzo: due file schiena contro schiena, con
// il corridoio d'ingresso (dalla porta al centro e oltre) sempre libero.
// Le misure sono in metri, nel sistema della stanza: x verso destra, z verso la porta (la porta è a z = +profondo/2).
// verso = la rotazione y del cabinato: il suo schermo guarda (sin verso, cos verso). 0 → guarda la porta (+z), π → il fondo,
// ±π/2 → le pareti laterali. Sono solo questi quattro, così l'ingombro resta un rettangolo dritto.

export const CAB = { w: 1.2, d: 0.9 };   // larghezza (lungo lo schermo) e profondità del cabinato
const PASSO = 1.3;        // da un cabinato al vicino della stessa fila: 10 cm di fessura
const DAVANTI = 1.35;     // dal centro del cabinato al punto da cui si gioca (90 cm davanti allo schermo)
const ARIA = 0.4;         // intorno al punto da cui si gioca (e a chi cammina) non c'è niente: il raggio della persona
const CORRIDOIO = 1.4;    // fra due file, o fra una fila e la parete, ci si passa: almeno 1,4 m...
const FESSURA = 0.3;      // ...o i cabinati si toccano (stessa fila, schiena contro schiena, contro la parete): al massimo 30 cm
const TRA_FILE = 2.0;     // fra due file che si guardano: 1 m di corridoio ci sta, ma la partita si fa in piedi, davanti allo schermo
const INGRESSO = 1.1;     // mezza larghezza del corridoio dalla porta al centro (e oltre, fino al fondo)

// la macchinetta dei gettoni, accanto alla porta, sulla parete di destra; ci si arriva da (posto)
export function macchinetta(largo, profondo) {
  const x = largo / 2 - 1.4, z = profondo / 2 - 1.4;
  return { x, z, w: 1, d: 0.8, posto: { x: x - 1.2, z: z - 0.2 } };
}
// il rettangolo dritto occupato da un posto (x, z, w, d), e il punto da cui si gioca
export function ingombro(p) {
  const lato = Math.abs(Math.sin(p.verso)) > 0.5;   // ±π/2: ruotato, largo e profondo si scambiano
  return { x: p.x, z: p.z, w: lato ? CAB.d : CAB.w, d: lato ? CAB.w : CAB.d };
}
export function postoDavanti(p) { return { x: p.x + Math.sin(p.verso) * DAVANTI, z: p.z + Math.cos(p.verso) * DAVANTI }; }

// distanza libera fra due rettangoli (negativa se si sovrappongono)
const spazio = (a, b) => Math.max(Math.abs(a.x - b.x) - (a.w + b.w) / 2, Math.abs(a.z - b.z) - (a.d + b.d) / 2);
const dentroR = (p, r, m) => Math.abs(p.x - r.x) < r.w / 2 + m && Math.abs(p.z - r.z) < r.d / 2 + m;
const EPS = 1e-9;

// tutti i posti possibili, nell'ordine in cui si riempiono (lazy: se ne prende quanti servono); un'isola è una coppia [A, B]
function* candidati(L, P) {
  const mezzoL = L / 2, mezzoP = P / 2;
  // 1. la parete di fondo, dal centro: 0, −1, +1, −2, +2… (il primo cabinato sta in mezzo)
  const m = Math.floor((L - CAB.w) / PASSO + EPS) + 1;
  const fondo = Array.from({ length: m }, (_, k) => k - (m - 1) / 2).sort((a, b) => Math.abs(a) - Math.abs(b) || a - b);
  for (const k of fondo) yield { x: k * PASSO, z: -mezzoP + CAB.d / 2, verso: 0 };
  // 2. le pareti laterali: la prima fila parte dopo l'angolo (il punto da cui si gioca dell'ultimo cabinato del fondo non si tocca)
  const z0 = -mezzoP + CAB.d + CORRIDOIO + CAB.w / 2;
  //    (fino alla macchinetta dei gettoni, da tutte e due le parti: la stanza resta simmetrica)
  const mac = macchinetta(L, P), zMax = mac.z - mac.d / 2 - CORRIDOIO - CAB.w / 2;
  for (let k = 0, z = z0; z <= zMax + EPS; k++, z = z0 + k * PASSO) {
    yield { x: -mezzoL + CAB.d / 2, z, verso: Math.PI / 2 };
    yield { x: mezzoL - CAB.d / 2, z, verso: -Math.PI / 2 };
  }
  // 3. le isole: due file schiena contro schiena (A guarda il fondo, B la porta), da una parte e dall'altra del corridoio
  const colonne = Math.floor((mezzoL - INGRESSO) / PASSO) + 1;
  for (let i = 0; ; i++) {
    const zA = -mezzoP + CAB.d + TRA_FILE + CAB.d / 2 + i * (2 * CAB.d + 0.05 + TRA_FILE), zB = zA + CAB.d + 0.05;
    if (zB + CAB.d / 2 > mezzoP) return;
    for (let j = 0; j < colonne; j++) for (const s of [-1, 1]) {
      const x = s * (INGRESSO + CAB.w / 2 + j * PASSO);
      yield [{ x, z: zA, verso: Math.PI }, { x, z: zB, verso: 0 }];   // la coppia: o ci stanno tutti e due, o nessuno
    }
  }
}

// un cabinato nuovo ci sta, dati quelli già messi (con i loro punti da cui si gioca)?
function ci_sta(c, messi, L, P) {
  const ing = ingombro(c), pt = postoDavanti(c), mezzoL = L / 2, mezzoP = P / 2;
  // dentro le pareti; una fila in mezzo alla stanza sta a distanza da passarci (una attaccata a una parete non guarda le altre:
  // le file si riempiono dal centro, e per un po' hanno la parete di fianco a più di 30 cm)
  const pareti = [ing.x - ing.w / 2 + mezzoL, mezzoL - ing.x - ing.w / 2, ing.z - ing.d / 2 + mezzoP, mezzoP - ing.z - ing.d / 2];
  if (pareti.some(d => d < -EPS)) return false;
  if (!pareti.some(d => d <= EPS) && pareti.some(d => d > FESSURA && d < CORRIDOIO - EPS)) return false;
  if (Math.abs(pt.x) > mezzoL - ARIA || Math.abs(pt.z) > mezzoP - ARIA) return false;
  // niente nel corridoio dalla porta al centro
  if (Math.abs(ing.x) - ing.w / 2 < INGRESSO && ing.z + ing.d / 2 > 0) return false;
  // la macchinetta, e il suo punto d'arrivo
  const mac = macchinetta(L, P);
  if (spazio(ing, mac) < CORRIDOIO - EPS || dentroR(mac.posto, ing, ARIA)) return false;
  for (const o of messi) {
    const s = spazio(ing, o.ing);
    if (s < 0.05 - EPS || (s > FESSURA && s < CORRIDOIO - EPS)) return false;   // sovrapposti, o un varco da non passarci
    if (dentroR(pt, o.ing, ARIA) || dentroR(o.pt, ing, ARIA)) return false;      // il punto da cui si gioca è occupato
  }
  return true;
}

// n posti {x, z, verso}, nell'ordine di sopra. Se non entrano tutti, ne restituisce meno: quelli entrati (.length).
export function postiCabinati(n, largo, profondo) {
  const out = [], messi = [];
  if (!(n > 0)) return out;
  for (const c of candidati(largo, profondo)) {
    const coppia = Array.isArray(c) ? c : [c], presi = [];
    for (const q of coppia) {
      if (!ci_sta(q, messi, largo, profondo)) break;
      presi.push(q); messi.push({ ing: ingombro(q), pt: postoDavanti(q) });
    }
    if (presi.length < coppia.length) { messi.length -= presi.length; continue; }
    for (const q of presi) if (out.length < n) out.push(q);
    if (out.length >= n) break;
  }
  return out;
}
// quanti cabinati entrano al massimo in una stanza di queste misure
export const capienza = (largo, profondo) => postiCabinati(Infinity, largo, profondo).length;
