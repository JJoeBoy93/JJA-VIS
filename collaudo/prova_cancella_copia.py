"""Prova offline di collaudo/cancella_copia.py (28/10): risposte finte dell'API, niente rete, niente attese vere.

    python3 collaudo/prova_cancella_copia.py

1. «built» al terzo controllo: cancella solo i github-pages non scaduti, e solo DOPO il «built»
2. «building» per sempre: dopo 5 minuti esce con 0, «NON cancellata», e non ha cancellato niente
3. mai artefatti con altri nomi (registri-hera, reel-…)
4. una chiamata che cade (DELETE 500, GET 403): esce con 0 e lo dice
5. «built» ma di un altro commit: non basta; «errored»: non cancella
"""
import io, os, sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cancella_copia import cancella_copia

REPO, SHA, ALTRO = "JJoeBoy93/JJA-VIS", "e06525dc116c8c0f0d1e697c85c2936328b3dcc2", "0123456789abcdef0123456789abcdef01234567"
MB = 1024 * 1024
prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))


def art(id, nome="github-pages", mb=35, scaduto=False):
    return {"id": id, "name": nome, "size_in_bytes": mb * MB, "expired": scaduto}

ARTEFATTI = [art(1), art(2, scaduto=True), art(3, "registri-hera", 2), art(4, mb=36), art(5, "reel-ciao", 80), art(6, "github-pages", 34, True)]


class Finta:
    """L'API finta: i controlli di /pages/builds/latest escono dalla lista (l'ultimo si ripete), il tempo è finto."""
    def __init__(self, builds, artefatti=ARTEFATTI, delete=204, lista=200, commit=SHA):
        self.builds, self.artefatti, self.delete, self.lista, self.commit = list(builds), artefatti, delete, lista, commit
        self.t, self.controlli, self.chiamate, self.cancellati, self.dormito = 0.0, 0, [], [], []
        self.cancellati_prima_di_built = []
    def dormi(self, s): self.dormito.append(s); self.t += s
    def orologio(self): return self.t
    def chiama(self, metodo, percorso):
        self.chiamate.append((metodo, percorso))
        if percorso.endswith("/pages/builds/latest"):
            stato = self.builds[min(self.controlli, len(self.builds) - 1)]; self.controlli += 1
            if isinstance(stato, int): return stato, None
            self.ultimo = stato
            return 200, {"status": stato, "commit": self.commit, "error": {"message": "boom" if stato == "errored" else None}}
        if "/actions/artifacts?" in percorso:
            if self.lista != 200: return self.lista, None
            return 200, {"total_count": len(self.artefatti), "artifacts": self.artefatti}
        if metodo == "DELETE":
            self.cancellati.append(int(percorso.rsplit("/", 1)[1]))
            if getattr(self, "ultimo", None) != "built": self.cancellati_prima_di_built.append(percorso)   # cancellato quando l'ultimo stato visto non era «built»
            return self.delete, None
        raise AssertionError(f"chiamata inattesa {metodo} {percorso}")


def lancia(finta, commit=SHA):
    out = io.StringIO()
    with redirect_stdout(out):
        codice = cancella_copia(finta.chiama, REPO, commit, scrivi=print, dormi=finta.dormi, orologio=finta.orologio)
    return codice, out.getvalue()


print("── 1. «built» al terzo controllo")
f = Finta(["building", "building", "built"])
codice, out = lancia(f)
prova("1. esce con 0", codice == 0, codice)
prova("1. cancella solo i github-pages non scaduti (1 e 4)", f.cancellati == [1, 4], f.cancellati)
prova("1. ha controllato 3 volte, aspettando 20 s tra l'una e l'altra", f.controlli == 3 and f.dormito == [20, 20], (f.controlli, f.dormito))
prova("1. nessuna cancellazione prima di «built»", f.cancellati_prima_di_built == [], f.cancellati_prima_di_built)
prova("1. nel registro: quanti e quanti MB (2 artefatti, 71.0 MB)", "2 artefatti" in out and "71.0 MB" in out, out)
prova("1. non dice «NON cancellata»", "NON cancellata" not in out, out)

print("── 2. «building» per sempre")
f = Finta(["building"])
codice, out = lancia(f)
prova("2. esce con 0", codice == 0, codice)
prova("2. dice «NON cancellata»", "copia del sito NON cancellata:" in out, out)
prova("2. non cancella niente (nemmeno ha elencato gli artefatti)", f.cancellati == [] and not any("/actions/artifacts" in p for _, p in f.chiamate), f.chiamate)
prova("2. aspetta 5 minuti, ogni 20 s (15 attese, 16 controlli)", f.t == 300 and f.controlli == 16, (f.t, f.controlli))

print("── 3. mai gli altri nomi")
f = Finta(["built"], artefatti=[art(10, "registri-hera"), art(11, "reel-ciao"), art(12, "reel-2"), art(13, "github-pages-vecchio")])
codice, out = lancia(f)
prova("3. non cancella registri-hera, reel-…, né nomi simili", f.cancellati == [], f.cancellati)
prova("3. esce con 0 e dice che non c'era niente", codice == 0 and "0 artefatti" in out, out)

print("── 4. una chiamata cade")
f = Finta(["built"], delete=500)
codice, out = lancia(f)
prova("4. DELETE 500: esce con 0 e dice «NON cancellata»", codice == 0 and "copia del sito NON cancellata:" in out and "500" in out, out)
f = Finta(["built"], lista=403)
codice, out = lancia(f)
prova("4. elenco 403: esce con 0, «NON cancellata», niente DELETE", codice == 0 and "NON cancellata" in out and f.cancellati == [], out)
f = Finta([502])
codice, out = lancia(f)
prova("4. controllo della pubblicazione 502: esce con 0, «NON cancellata», niente DELETE", codice == 0 and "NON cancellata" in out and f.cancellati == [], out)

print("── 5. commit sbagliato, errore")
f = Finta(["built"], commit=ALTRO)
codice, out = lancia(f)
prova("5. «built» ma di un altro commit: aspetta e poi NON cancella", codice == 0 and "NON cancellata" in out and f.cancellati == [] and f.t == 300, (out, f.t))
f = Finta(["errored"])
codice, out = lancia(f)
prova("5. «errored»: subito «NON cancellata», niente DELETE, niente attese", codice == 0 and "NON cancellata" in out and "boom" in out and f.cancellati == [] and f.t == 0, out)

print(f"\n{sum(prove)}/{len(prove)} verdi"); print("VERDE" if all(prove) else "ROSSO"); sys.exit(0 if all(prove) else 1)
