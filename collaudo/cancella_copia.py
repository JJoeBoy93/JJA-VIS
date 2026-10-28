"""Hera cancella la copia del sito (28/10): dopo la pubblicazione l'artefatto «github-pages» (~35 MB) non serve più.

    GH_TOKEN=... GITHUB_REPOSITORY=JJoeBoy93/JJA-VIS python3 collaudo/cancella_copia.py <commit portato su main>

Lo spazio delle Actions era al 91% (338,77 GB-ora su circa 372) e ogni pubblicazione ne lascia uno per un giorno.
1. aspetta che /pages/builds/latest dica «built» PER QUEL COMMIT (ogni 20 s, al massimo 5 minuti):
   cancellare durante la pubblicazione la romperebbe, quindi prima di «built» non si cancella niente
2. cancella gli artefatti di nome «github-pages» non scaduti, mai gli altri (registri-hera, reel-…)
3. scrive quanti ne ha cancellati e quanti MB

Se la pubblicazione non arriva a «built» o una chiamata cade, scrive «copia del sito NON cancellata: <motivo>»
ed esce comunque con 0: una pubblicazione lenta non deve diventare la mail rossa di Hera.
"""
import json, os, sys, time, urllib.error, urllib.request

NOME = "github-pages"
OGNI = 20           # secondi tra un controllo e l'altro
ATTESA_MAX = 300    # 5 minuti
PER_PAGINA = 100
PAGINE_MAX = 10


class NonCancellata(Exception):
    pass


def cancella_copia(chiama, repo, commit, scrivi=print, dormi=time.sleep, orologio=time.monotonic):
    """chiama(metodo, percorso) -> (codice HTTP, corpo già letto da JSON o None). Esce sempre con 0."""
    cancellati = []
    try:
        aspetta_built(chiama, repo, commit, dormi, orologio)
        for a in da_cancellare(chiama, repo):
            codice, _ = chiama("DELETE", f"/repos/{repo}/actions/artifacts/{a['id']}")
            if codice == 404:        # già andato via (scaduto nel frattempo): niente da fare
                continue
            if codice != 204:
                raise NonCancellata(f"DELETE dell'artefatto {a['id']} ha risposto {codice}")
            cancellati.append(a)
    except NonCancellata as e:
        scrivi(f"::warning::copia del sito NON cancellata: {e}{riepilogo(cancellati)}")
        return 0
    except Exception as e:           # rete, JSON, qualunque cosa: Hera non cade per questo
        scrivi(f"::warning::copia del sito NON cancellata: {type(e).__name__}: {e}{riepilogo(cancellati)}")
        return 0
    if cancellati:
        scrivi(f"copia del sito cancellata: {len(cancellati)} artefatti {NOME}, {mb(cancellati):.1f} MB")
    else:
        scrivi(f"copia del sito: nessun artefatto {NOME} non scaduto da cancellare (0 artefatti, 0.0 MB)")
    return 0


def mb(artefatti):
    return sum(a.get("size_in_bytes", 0) for a in artefatti) / (1024 * 1024)


def riepilogo(cancellati):
    return f" (già cancellati prima: {len(cancellati)}, {mb(cancellati):.1f} MB)" if cancellati else ""


def aspetta_built(chiama, repo, commit, dormi, orologio):
    inizio = orologio()
    while True:
        codice, corpo = chiama("GET", f"/repos/{repo}/pages/builds/latest")
        if codice != 200 or not isinstance(corpo, dict):
            raise NonCancellata(f"GET pages/builds/latest ha risposto {codice}")
        stato, di = corpo.get("status"), corpo.get("commit")
        if di == commit and stato == "built":
            return
        if di == commit and stato == "errored":
            raise NonCancellata(f"la pubblicazione di {commit[:7]} è finita in errore: {(corpo.get('error') or {}).get('message')}")
        if orologio() - inizio + OGNI > ATTESA_MAX:
            raise NonCancellata(f"dopo {ATTESA_MAX // 60} minuti la pubblicazione di {commit[:7]} non è «built» "
                                f"(ultima: commit {str(di)[:7]}, stato {stato})")
        print(f"pubblicazione di {commit[:7]}: ultima {str(di)[:7]} {stato}, riprovo tra {OGNI} s", flush=True)
        dormi(OGNI)


def da_cancellare(chiama, repo):
    trovati = []
    for pagina in range(1, PAGINE_MAX + 1):
        codice, corpo = chiama("GET", f"/repos/{repo}/actions/artifacts?name={NOME}&per_page={PER_PAGINA}&page={pagina}")
        if codice != 200 or not isinstance(corpo, dict):
            raise NonCancellata(f"GET actions/artifacts ha risposto {codice}")
        arrivati = corpo.get("artifacts", [])
        trovati += [a for a in arrivati if a.get("name") == NOME and not a.get("expired")]   # il nome si controlla anche qui: mai gli altri
        if len(arrivati) < PER_PAGINA:
            break
    return trovati


def chiama_github(token):
    def chiama(metodo, percorso):
        r = urllib.request.Request("https://api.github.com" + percorso, method=metodo, headers={
            "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(r, timeout=30) as ris:
                dati = ris.read()
                return ris.status, (json.loads(dati) if dati else None)
        except urllib.error.HTTPError as e:
            return e.code, None
    return chiama


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("::warning::copia del sito NON cancellata: manca il commit (uso: cancella_copia.py <commit>)")
        sys.exit(0)
    sys.exit(cancella_copia(chiama_github(os.environ.get("GH_TOKEN", "")), os.environ.get("GITHUB_REPOSITORY", ""), sys.argv[1]))
