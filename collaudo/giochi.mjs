// Collaudo dei giochi della Sala giochi, senza browser:  node collaudo/giochi.mjs
// Per ogni id di giochi/elenco.js: il modulo giochi/<id>.js esporta `gioco` (coi campi della cornice) e `logica` (solo
// funzioni pure e valori), poi gira le sue prove, collaudo/giochi/<id>.mjs (export default async (prova, modulo) => {}).
// Ultima riga VERDE o ROSSO: n; esce 1 se rosso. Il gioco nello strato lo prova collaudo/citta.py, nel browser.
import { pathToFileURL, fileURLToPath } from "node:url";
import { existsSync } from "node:fs";
import path from "node:path";

const CASA = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const url = (...p) => pathToFileURL(path.join(CASA, ...p)).href;
let rossi = 0;
const prova = (nome, ok, dettaglio = "") => { if (!ok) rossi++; console.log((ok ? "✅ " : "❌ ") + nome + (!ok && dettaglio !== "" ? " — " + (typeof dettaglio === "string" ? dettaglio : JSON.stringify(dettaglio)) : "")); };

let GIOCHI = [];
try { ({ GIOCHI } = await import(url("giochi", "elenco.js"))); } catch (e) { prova("giochi/elenco.js si carica", false, String(e)); }
prova("giochi/elenco.js esporta GIOCHI: id diversi, in minuscolo", Array.isArray(GIOCHI) && GIOCHI.every(id => /^[a-z][a-z0-9-]*$/.test(id)) && new Set(GIOCHI).size === GIOCHI.length, GIOCHI);

for (const id of Array.isArray(GIOCHI) ? GIOCHI : []) {
  console.log(`\n── ${id}`);
  let m = null;
  try { m = await import(url("giochi", id + ".js")); } catch (e) { prova(`giochi/${id}.js si carica in node (niente DOM a livello del modulo)`, false, String(e)); continue; }
  const g = m.gioco || {};
  const campi = { id: g.id === id, nome: typeof g.nome === "string" && g.nome.trim() !== "", regole: typeof g.regole === "string" && g.regole.trim() !== "",
    cabinato: !!g.cabinato && typeof g.cabinato.schermo === "string" && /^#[0-9a-fA-F]{6}$/.test(g.cabinato.colore || ""),
    massimo: Number.isInteger(g.massimo) && g.massimo > 0, avvia: typeof g.avvia === "function",
    gettoni: g.gettoni === undefined || typeof g.gettoni === "function" };
  prova(`${id}: esporta gioco con id, nome, cabinato {schermo, colore}, regole, massimo, avvia`, !!m.gioco && Object.values(campi).every(Boolean), Object.keys(campi).filter(k => !campi[k]));
  const L = m.logica;
  prova(`${id}: esporta logica, fatta di funzioni pure e valori (nessun elemento della pagina)`, !!L && typeof L === "object" && Object.values(L).some(v => typeof v === "function")
    && Object.values(L).every(v => v === null || ["function", "number", "string", "boolean"].includes(typeof v) || (typeof v === "object" && !("nodeType" in v))));
  const file = path.join(CASA, "collaudo", "giochi", id + ".mjs");
  if (!existsSync(file)) { prova(`${id}: ha le sue prove, collaudo/giochi/${id}.mjs`, false); continue; }
  try { const p = await import(pathToFileURL(file).href); await p.default((nome, ok, d) => prova(`${id}: ${nome}`, ok, d), m); }
  catch (e) { prova(`${id}: le prove girano fino in fondo`, false, String(e && e.stack || e)); }
}
// la stanza: dove stanno i cabinati (giochi/sala.js), non è un gioco
console.log("\n── sala (la stanza, i posti dei cabinati)");
try { const p = await import(url("collaudo", "giochi", "sala.mjs")); await p.default((nome, ok, d) => prova(`sala: ${nome}`, ok, d)); }
catch (e) { prova("sala: le prove girano fino in fondo", false, String(e && e.stack || e)); }
console.log("");
console.log(rossi ? `ROSSO: ${rossi}` : "VERDE");
process.exit(rossi ? 1 : 0);
