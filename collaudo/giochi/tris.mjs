// Le prove del Tris (giochi/tris.js), le fa girare collaudo/giochi.mjs.
// La perfetta si prova contro TUTTE le partite possibili: l'avversario prova ogni mossa, a ogni turno, da X e da O.
export default async function (prova, { logica: L }) {
  const G = s => [...s].map(c => (c === "X" || c === "O" ? c : null));   // "XXO.O...." → griglia

  // vincitore: righe, colonne, diagonali, pareggio, partita aperta
  prova("vincitore: le tre righe", ["XXX......", "...OOO...", "......XXX"].map(s => L.vincitore(G(s))).join() === "X,O,X");
  prova("vincitore: le tre colonne", ["O..O..O..", ".X..X..X.", "..O..O..O"].map(s => L.vincitore(G(s))).join() === "O,X,O");
  prova("vincitore: le due diagonali", ["X...X...X", "..O.O.O.."].map(s => L.vincitore(G(s))).join() === "X,O");
  prova("vincitore: griglia piena senza tris è pareggio", L.vincitore(G("XOXXOOOXX")) === "pari");
  prova("vincitore: partita aperta, o vuota, è null", L.vincitore(G("XO.......")) === null && L.vincitore(L.vuota()) === null);
  prova("l'ultima mossa che fa tris riempiendo la griglia vince, non pareggia", L.vincitore(G("XOXOXOOXX")) === "X");
  prova("la riga vincente è quella giusta (si illumina quella)", JSON.stringify(L.rigaVincente(G("..O.O.O.."))) === "[2,4,6]" && L.rigaVincente(G("XO.......")) === null);
  prova("punti del round: vittoria 3, pareggio 1, sconfitta 0", L.puntiRound(G("XXX.OO..."), "X") === 3 && L.puntiRound(G("XOXXOOOXX"), "O") === 1 && L.puntiRound(G("XXX.OO..."), "O") === 0);

  // la media: vince se può, blocca se deve
  const caso = () => 0.99;
  prova("media: vince se può (O ha due in riga)", L.mossaMedia(G("XX.OO.X.."), caso) === 5);
  prova("media: vince se può, anche in diagonale", L.mossaMedia(G("O.X.OX.X."), caso) === 8);
  prova("media: tra vincere e bloccare, vince", L.mossaMedia(G("XX.OO.X.."), () => 0) === 5);
  prova("media: blocca se deve (X minaccia in colonna)", L.mossaMedia(G("XO.X.....")) === 6);
  prova("media: blocca se deve (X minaccia in riga)", L.mossaMedia(G("XX..O....")) === 2);
  prova("media: se no a caso, su una casella libera", (() => { const g = G("X........"); return [0, 0.3, 0.6, 0.99].every(r => { const m = L.mossaMedia(g, () => r); return m !== null && g[m] === null; }); })());
  prova("facile: sempre una casella libera, e null a griglia piena", [0, 0.5, 0.999].every(r => G("XO.XO.O..")[L.mossaFacile(G("XO.XO.O.."), () => r)] === null) && L.mossaFacile(G("XOXXOOOXX"), Math.random) === null);
  prova("perfetta: chiude il tris se può e blocca se deve", L.mossaPerfetta(G("XX.OO.X..")) === 5 && L.mossaPerfetta(G("XX..O....")) === 2);

  // la perfetta non perde MAI: tutte le partite, da X e da O
  function sconfitte(mossa) {
    let perse = 0, partite = 0;
    const gira = (g, lei) => {
      const v = L.vincitore(g);
      if (v) { partite++; if (v !== "pari" && v !== lei) perse++; return; }
      if (L.chiMuove(g) === lei) { const m = mossa(g); if (m === null || g[m]) { perse++; partite++; return; } gira(L.metti(g, m, lei), lei); }
      else for (const i of L.libere(g)) gira(L.metti(g, i, L.chiMuove(g)), lei);
    };
    gira(L.vuota(), "X"); gira(L.vuota(), "O");
    return { perse, partite };
  }
  const vera = sconfitte(L.mossaPerfetta);
  prova(`perfetta: non perde mai, in tutte le ${vera.partite} partite possibili (da X e da O)`, vera.partite > 0 && vera.perse === 0, vera);
  // controprova: una «perfetta» finta che gioca a caso deve far diventare rosso il controllo
  let seme = 7; const rnd = () => (seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648;
  const finta = sconfitte(g => L.mossaFacile(g, rnd));
  prova("controprova: una perfetta finta che gioca a caso perde (il controllo sa diventare rosso)", finta.perse > 0, finta);
  prova("perfetta: da X contro la perfetta è pareggio (il Difficile non si batte)", (() => { let g = L.vuota(); while (!L.vincitore(g)) g = L.metti(g, L.mossaPerfetta(g), L.chiMuove(g)); return L.vincitore(g) === "pari"; })());
}
