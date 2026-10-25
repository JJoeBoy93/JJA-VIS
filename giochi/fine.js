// La fine partita, uguale per tutti i giochi della Sala giochi e per Acchiappa (citta.html: giocaSala, giocaAcchiappa, mostraClassifica).
// Solo funzioni pure, provate in node da collaudo/giochi/fine-partita.mjs (lanciato da collaudo/giochi.mjs).

export const PREMIO_RECORD = 5, PREMIO_PRIMO = 25;

// il tetto dei punti mandati al server: la stessa regola di citta/conti.js (JJA-VIS-Porta)
export const tettoPunti = gioco => (gioco === "acchiappa" ? 200 : 1000000);

// 0 senza punti o senza record battuto (il pari non vale); +5 se batte il record, +25 se in più si è primi in classifica
export function premioRecord({ punti, recordPrima, primoInClassifica } = {}) {
  const p = Number(punti) || 0, r = Number(recordPrima) || 0;
  if (!(p > 0) || !(p > r)) return 0;
  return primoInClassifica ? PREMIO_PRIMO : PREMIO_RECORD;
}

// primo in classifica: il proprio soprannome al primo posto, con quei punti
export const primoConPunti = (classifica, io, punti) =>
  !!io && Array.isArray(classifica) && !!classifica[0] && classifica[0].n === io && Number(classifica[0].punti) === Number(punti);

// il premio si dà UNA volta per partita: `partita.premiato` si segna prima di tutto, quindi un secondo giro non paga
export function assegnaPremio(partita, dati, guadagna) {
  if (!partita || partita.premiato) return 0;
  partita.premiato = true;
  const n = premioRecord(dati);
  if (n > 0) guadagna(n);
  return n;
}

export const testoPremio = n => (n >= PREMIO_PRIMO ? `👑 Primo in classifica! +${n} gettoni di premio` : n > 0 ? `🏆 Nuovo record! +${n} gettoni di premio` : "");
