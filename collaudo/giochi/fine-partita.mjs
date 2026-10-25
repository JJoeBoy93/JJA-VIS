// Le prove della fine partita (giochi/fine.js), uguale per tutti i giochi. Le fa girare collaudo/giochi.mjs.
import { tettoPunti, premioRecord, assegnaPremio, primoConPunti } from "../../giochi/fine.js";

// le prove sul premio, riusabili: con un premioRecord finto servono alla controprova
function provePremio(prova, premio) {
  prova("record battuto → 5", premio({ punti: 10, recordPrima: 7, primoInClassifica: false }) === 5);
  prova("primo in classifica → 25", premio({ punti: 10, recordPrima: 7, primoInClassifica: true }) === 25);
  prova("record pari → 0 (anche se primo)", premio({ punti: 7, recordPrima: 7, primoInClassifica: false }) === 0 && premio({ punti: 7, recordPrima: 7, primoInClassifica: true }) === 0);
  prova("0 punti → 0", premio({ punti: 0, recordPrima: 0, primoInClassifica: true }) === 0 && premio({ punti: 0, recordPrima: 0, primoInClassifica: false }) === 0);
  prova("sotto il record → 0", premio({ punti: 3, recordPrima: 7, primoInClassifica: true }) === 0);
  prova("primo record della vita (record 0, punti 1) → 5", premio({ punti: 1, recordPrima: 0, primoInClassifica: false }) === 5);
}

export default async function (prova) {
  prova("tettoPunti: 200 per acchiappa", tettoPunti("acchiappa") === 200);
  prova("tettoPunti: 1.000.000 per gli altri giochi", ["tris", "serpente", "furgone", "spazio", "nuovo-gioco"].every(g => tettoPunti(g) === 1000000));

  provePremio(prova, premioRecord);

  prova("primo in classifica: il proprio soprannome, primo, con quei punti",
    primoConPunti([{ n: "Jo", punti: 50 }, { n: "Ale", punti: 40 }], "Jo", 50) === true
    && primoConPunti([{ n: "Ale", punti: 60 }, { n: "Jo", punti: 50 }], "Jo", 50) === false
    && primoConPunti([{ n: "Jo", punti: 50 }], "Jo", 40) === false
    && primoConPunti([{ n: "Jo", punti: 50 }], "", 50) === false && primoConPunti(undefined, "Jo", 50) === false);

  // una partita finita due volte (o con la classifica che arriva tardi) dà il premio una volta sola
  const incassi = [], guadagna = n => incassi.push(n), partita = {};
  const dati = { punti: 10, recordPrima: 7, primoInClassifica: false };
  const a = assegnaPremio(partita, dati, guadagna), b = assegnaPremio(partita, { ...dati, primoInClassifica: true }, guadagna);
  prova("fine chiamata due volte: il premio passa da guadagna una volta sola", a === 5 && b === 0 && incassi.length === 1 && incassi[0] === 5, incassi);
  prova("una partita nuova ha il suo premio", assegnaPremio({}, dati, guadagna) === 5 && incassi.length === 2);

  // CONTROPROVA: un premioRecord che premia anche il pari deve far diventare rosse le prove
  let rosse = 0;
  provePremio((_, ok) => { if (!ok) rosse++; }, ({ punti, recordPrima }) => (punti > 0 && punti >= recordPrima ? 5 : 0));
  prova("controprova: un premioRecord che premia anche il pari fa diventare rossa la prova", rosse > 0, rosse);
}
