"""Scarica i pacchetti gratuiti («name your own price», 0 €) da itch.io, per JJA-VIS (JJ, 9/10: animazioni già pronte,
«ho lo stesso problema nello scarico»). Gira nelle Actions (.github/workflows/animazioni.yml): la sandbox di Athena non
raggiunge itch.io. Usa il giro che fa il browser col tasto «No thanks, just take me to the downloads»:
  1. la pagina del gioco dà il csrf_token (meta) e i cookie
  2. POST <pagina>/download_url  -> {"url": ".../download/<chiave>"}
  3. la pagina dei download elenca i file (data-upload_id) col loro nome
  4. POST <pagina>/file/<upload_id>?source=game_download&key=<chiave>  -> {"url": <link vero>}
Prende solo i file il cui nome contiene una delle parole date. Uso: python3 itch.py <url-pagina> <parola,parola> <cartella>
"""
import json, os, re, sys, urllib.parse, urllib.request, http.cookiejar

UA = "Mozilla/5.0 (JJA-VIS; +https://jjoeboy93.github.io/JJA-VIS/)"
pagina, parole, dove = sys.argv[1].rstrip("/"), [p.strip().lower() for p in sys.argv[2].split(",")], sys.argv[3]
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def vai(url, dati=None, xhr=False):
    h = {"User-Agent": UA}
    if xhr: h["X-Requested-With"] = "XMLHttpRequest"
    r = op.open(urllib.request.Request(url, data=urllib.parse.urlencode(dati).encode() if dati else None, headers=h), timeout=120)
    return r.read()
html = vai(pagina).decode("utf-8", "replace")
csrf = re.search(r'name="csrf_token" value="([^"]+)"', html) or re.search(r'csrf_token"\s*content="([^"]+)"', html)
if not csrf: sys.exit("niente csrf_token nella pagina: itch ha cambiato il giro")
csrf = csrf.group(1)
d = json.loads(vai(pagina + "/download_url", {"csrf_token": csrf}, xhr=True))
if "url" not in d: sys.exit(f"download_url non ha dato un url: {d}")
pd = vai(d["url"]).decode("utf-8", "replace"); chiave = d["url"].rstrip("/").split("/")[-1]
files = re.findall(r'data-upload_id="(\d+)".*?class="name"[^>]*title="([^"]+)"', pd, re.S) or \
        [(u, n) for u, n in re.findall(r'data-upload_id="(\d+)"[^>]*>.*?<strong class="name"[^>]*>([^<]+)<', pd, re.S)]
print("file nella pagina:", [n for _, n in files])
if not files: sys.exit("nessun file trovato nella pagina dei download")
os.makedirs(dove, exist_ok=True); presi = []
for uid, nome in files:
    if not any(p in nome.lower() for p in parole): continue
    j = json.loads(vai(f"{pagina}/file/{uid}?source=game_download&key={chiave}", {"csrf_token": csrf}, xhr=True))
    if "url" not in j: sys.exit(f"{nome}: nessun url ({j})")
    b = vai(j["url"]); fuori = os.path.join(dove, re.sub(r"[^\w.\-]+", "_", nome)); open(fuori, "wb").write(b)
    presi.append(f"{os.path.basename(fuori)} ({len(b)//1024} kB)")
print("scaricati:", presi or "nessuno")
if not presi: sys.exit("nessun file corrispondeva alle parole date")
