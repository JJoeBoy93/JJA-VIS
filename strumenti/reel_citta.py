"""I reel della città, girati dalla macchina (19 ottobre 2026, Athena).

    python3 strumenti/reel_citta.py [tema] [--prova]      (dalla radice del repository)
    CHROMIUM=/percorso/chrome python3 strumenti/reel_citta.py cafe

Esce: reel.mp4 (1080x1920, 24 fps, traccia audio muta: la musica la mette
Afrodite su Instagram) e reel.json (tema, data, descrizione per Dioniso).
Senza tema sceglie lui: i temi ruotano col giorno, uno ogni due giorni.

Perché esiste: JJ, 11/10 — «si fa pubblicità da solo, si fa un video di come
giocare nella città». Il reel lo gira la macchina, non JJ (decisione
«le macchine producono»).

Come gira: tempo del browser finto (24 fotogrammi al secondo esatti anche se
ogni foto ne chiede quattro veri), città vera di questo repository, nessuna
richiesta esce. Si cammina a velocità vera (a doppia, JJ: «troppo veloce») e si taglia la parte
lunga del cammino: un reel che segue un avatar per 34 secondi non lo guarda nessuno.

Misurato il 19/10 in sandbox (un core, SwiftShader): un fotogramma a 432x768
costa 4,4 s, a 1,5x 16 s. Qui si gira a 540x960 (1,25x) e si raddoppia con
ffmpeg: è il prezzo per stare sotto l'ora nella Action.
--prova: 4 fotogrammi al secondo e risoluzione piena da telefono, per guardare
la sequenza senza aspettare.
"""
import asyncio, datetime, json, os, re, shutil, subprocess, sys
from playwright.async_api import async_playwright

CASA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
PROVA = "--prova" in sys.argv
FPS = 4 if PROVA else 24
DSF = 1 if PROVA else 1.25
OUT = os.path.join(CASA, "fotogrammi")

# ══ I TEMI ══ Testi pubblici: mai nomi di altri giochi o marchi, mai JARVIS
# (JJ, 6/10 e 11/10). Ogni tema: dove si va, cosa si tocca dentro, le scritte.
TEMI = {
    # il primo (JJ, 19/10): cos'è JJA-VIS e perché usarlo, col servizio di Atlas (gli appuntamenti per mail, il promemoria
    # della sera). Non è la città: è una pagina animata (strumenti/reel_jjavis.html), senza nomi né dati veri.
    "jjavis": {
        "pagina": "strumenti/reel_jjavis.html",
        "dida": [("Cos'è JJA-VIS?", None), ("Gli dai un nome, gli racconti la tua giornata", None),
                 ("Già oggi: gli appuntamenti per mail, il promemoria la sera prima", None)],
        "descrizione": "Cos'è JJA-VIS: un assistente personale che impara chi sei. Gli dai un nome e gli racconti la tua giornata. Già oggi c'è chi gli scrive i suoi appuntamenti per mail e ogni sera riceve il promemoria di quelli del giorno dopo. Si entra gratis.",
    },
    "cafe": {
        "dove": "cafe", "nome": "JJA-VIS Café", "usa": "tavolini",
        "scena": [("dialogo", "tavolini", ("Ti avvicini: <b>Interagisci</b>", "come nei giochi"), 2.6, "Ti siedi, ordini coi gettoni, chiacchieri con chi c'è."),
                  ("scelta", "Siediti", ("Ti siedi al tavolino", "e ordini coi gettoni del gioco"), 3.0, "chiudi"),
                  ("fermo", None, ("Qui conosci gli altri", "e parli col tuo assistente"), 2.4)],
        "dida": [("Una città intera per il tuo assistente", "si gioca dal telefono"),
                 ("Si va al <b>JJA-VIS Café</b>", "colazione coi gettoni del gioco"),
                 ("Ti siedi, scrivi, conosci gli altri", None)],
        "descrizione": "Un giro nella città 3D di JJA-VIS, dal telefono: l'avatar attraversa la piazza e entra al JJA-VIS Café, dove si fa colazione coi gettoni del gioco e ci si siede ai tavolini.",
    },
    "torre": {
        "dove": "torre", "nome": None, "usa": None,
        "scena": [("dialogo", "globo", ("Alla reception c'è <b>lui</b>", "col nome che gli dai tu"), 2.8),
                  ("scelta", "Chi sei?", ("Gli chiedi chi è…", None), 3.0),
                  ("piano", 3, ("Al 3° piano lavora la squadra", "che lo costruisce"), 2.6),
                  ("dialogo", "dio-hera", ("Ognuno ti dice cosa fa", None), 2.8)],
        "dida": [("Una città intera per il tuo assistente", "si gioca dal telefono"),
                 ("In fondo alla via c'è <b>la Torre</b>", "dieci piani e la terrazza"),
                 ("Al piano terra ti aspetta lui", "col nome che gli dai tu")],
        "descrizione": "Un giro nella città 3D di JJA-VIS: l'avatar va verso la Torre, dieci piani con la terrazza; alla reception c'è l'assistente personale, che ognuno chiama col nome che vuole.",
    },
    "radio": {
        "dove": "radio", "nome": None, "usa": None,
        "scena": [("dialogo", "radio", ("Accendi <b>la radio</b>", "e scegli la stazione"), 3.2, "Accendo? Scegli una delle tue stazioni."),
                  ("fermo", None, ("Le tue stazioni, salvate", "suonano anche a schermo spento"), 2.6)],
        "dida": [("In questa città c'è anche <b>la radio</b>", None),
                 ("Sei stazioni sotto l'antenna", "e le salvi come vuoi tu"),
                 ("Suona anche a schermo spento", None)],
        "descrizione": "La città 3D di JJA-VIS: l'avatar va all'antenna della radio, sei stazioni preselezionate che si cambiano a piacere e suonano anche col telefono bloccato.",
    },
    "giochi": {
        "dove": "giochi", "nome": None, "usa": None,
        "scena": [("dialogo", "cab1", ("In <b>Sala giochi</b>", "Gioca o guarda la classifica"), 3.0, "Prendi i gettoni, schiva le bombe. Si gioca dal telefono."),
                  ("fermo", None, ("I gettoni che vinci", "li spendi in città"), 2.6)],
        "dida": [("I gettoni non si comprano soltanto", None),
                 ("Si vincono in <b>Sala giochi</b>", "prendi i gettoni, schiva le bombe"),
                 ("Poi li spendi in città", "skin, colazione, caffè")],
        "descrizione": "La città 3D di JJA-VIS: l'avatar va in Sala giochi, dove si vincono i gettoni del gioco da spendere in città (skin, colazione al Café).",
    },
    "sartoria": {
        "dove": "sartoria", "nome": None, "usa": None,
        "scena": [("dialogo", "manichini", ("In <b>Sartoria</b>", "scegli chi vuoi essere"), 3.0, "Scegli il tuo mestiere e i tuoi vestiti."),
                  ("dialogo", "specchio", ("L'armadietto", "i tuoi vestiti, i tuoi colori"), 2.8, "Qui cambi colori e vestiti quando vuoi.")],
        "dida": [("Nella città di JJA-VIS sei <b>una persona</b>", "non un omino"),
                 ("In Sartoria scegli chi sei", "il tuo mestiere, i tuoi colori"),
                 ("E il tuo assistente impara da lì", None)],
        "descrizione": "La città 3D di JJA-VIS: l'avatar va in Sartoria, dove si sceglie la persona, il mestiere e i colori dei vestiti; l'assistente personale parte da quello che gli si racconta.",
    },
}
ORDINE = ["jjavis", "cafe", "torre", "sartoria", "giochi", "radio"]
PARTENZA = datetime.date(2026, 10, 19)   # il primo giro: «jjavis» (JJ, 19/10: prima di tutto, cos'è)
CTA = ("Entra gratis", "link in bio · jjoeboy93.github.io/JJA-VIS")


def tema_di_oggi(oggi=None):
    oggi = oggi or datetime.date.today()
    return ORDINE[((oggi - PARTENZA).days // 2) % len(ORDINE)]


TIPI = {".html": "text/html", ".js": "text/javascript", ".png": "image/png", ".jpg": "image/jpeg",
        ".glb": "model/gltf-binary", ".json": "application/json", ".webmanifest": "application/manifest+json"}
async def instrada(route):
    u = route.request.url
    if u.startswith(BASE):
        nome = u[len(BASE):].split("#")[0].split("?")[0] or "index.html"
        f = os.path.join(CASA, nome)
        if os.path.isfile(f):
            return await route.fulfill(body=open(f, "rb").read(), content_type=TIPI.get(os.path.splitext(f)[1], "application/octet-stream"))
        return await route.fulfill(status=404, body="")
    # niente porta, niente server degli altri: in città, nel reel, si è soli
    await route.abort()


DIDA = '''([t, piccola, finale])=>{let d=document.getElementById('dida-reel');
 if(!d){d=document.createElement('div');d.id='dida-reel';document.body.appendChild(d);}
 Object.assign(d.style,{position:'fixed',left:'6%',right:'6%',top:finale?'38%':'7%',zIndex:9999,padding:finale?'26px 16px':'14px 16px',
   background:'rgba(2,11,24,.86)',border:'1px solid rgba(0,180,216,.7)',color:'#E8F7FF',textAlign:'center',
   font:(finale?'800 34px':'800 25px')+'/1.18 "DejaVu Sans", sans-serif',boxShadow:'0 0 28px rgba(0,180,216,.4)',borderRadius:'6px',pointerEvents:'none'});
 if(!t){d.style.display='none';return;} d.style.display='block';
 d.innerHTML=t+(piccola?'<div style="font:600 15px/1.3 DejaVu Sans Mono,monospace;margin-top:8px;color:#7FDBFF">'+piccola+'</div>':'');}'''


async def main():
    tema = next((a for a in sys.argv[1:] if not a.startswith("--")), None) or tema_di_oggi()
    if tema not in TEMI: sys.exit(f"tema sconosciuto: {tema} (ci sono: {', '.join(TEMI)})")
    T = TEMI[tema]
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    n = [0]
    errori = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None,
                                     args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        # la pagina animata è leggera: si gira direttamente a 1080x1920 (2,5x)
        ctx = await b.new_context(viewport={"width": 432, "height": 768}, device_scale_factor=(1 if PROVA else 2.5) if T.get("pagina") else DSF, is_mobile=True, has_touch=True)
        # un visitatore che ha già detto nome e mestiere: niente pannelli d'ingresso davanti alla città
        await ctx.add_init_script("try{ sessionStorage.setItem('jjavis-conto-dopo','1'); localStorage.setItem('jjavis-io', JSON.stringify({nome:'Atlas', mestiere:'Corriere'})); }catch(_){}")
        await ctx.route("**/*", instrada)
        p = await ctx.new_page()
        p.on("pageerror", lambda e: errori.append(str(e)))
        # il tempo FERMO: install() da solo lascia scorrere l'orologio a tempo vero, e ogni foto (secondi, in SwiftShader)
        # spingeva avanti la scena — misurato il 19/10: 83 ms finti in più a foto anche sulla pagina leggera. Era il
        # «troppo veloce» di JJ (19/10). Da fermo il tempo avanza solo con run_for: 1/24 di secondo a fotogramma, esatto.
        await p.clock.install(time=1_800_000_000_000)
        await p.clock.pause_at(1_800_000_001_000)
        if T.get("pagina"):
            await p.goto(BASE + T["pagina"], wait_until="commit", timeout=90000)
            for _ in range(300):
                await p.clock.run_for(100)
                if await p.evaluate("!!window.PRONTA && [...document.images].every(i=>i.complete)"): break
            else:
                sys.exit("la pagina del reel non si è accesa")
            await p.evaluate("window.RIPARTI()")
            durata = await p.evaluate("window.DURATA")
            for _ in range(int(durata * FPS)):
                await p.clock.run_for(int(1000 / FPS))
                await p.screenshot(path=f"{OUT}/{n[0]:05d}.png", timeout=180000)
                n[0] += 1
            await b.close()
        else:
            await gira_citta(p, T, n, errori)
            await b.close()
    if errori: print("errori della pagina (il reel è girato lo stesso):", errori[:5])
    await monta(tema, T, n)


async def gira_citta(p, T, n, errori):
    if True:
        # col tempo finto «load» può non arrivare mai
        await p.goto(BASE + "citta.html", wait_until="commit", timeout=90000)
        for _ in range(600):
            await p.clock.run_for(100)
            if await p.evaluate("!!(window.CITTA && window.CITTA.pronta)"): break
        else:
            sys.exit("la città non si è accesa: " + "; ".join(errori[:3]))
        await p.clock.run_for(800)
        # Nel reel si vede la città, non i comandi: il cartello in alto, i tasti, il cerchio per muoversi
        # e la barra delle stanze coprivano le scritte (provini del 19/10: la didascalia sopra il cartello,
        # «Sediti · in panchina» in mezzo alla piazza, la barra delle stanze in fondo anche fuori).
        await p.add_style_tag(content="#dida-reel b{color:#FFD60A} ::-webkit-scrollbar{display:none} "
                                      ".hud,#joy,#vai,#salta,#giu,#aiuto,#foglio,.stanza-barra,#stanza-carta,#nova,#conto,#insieme{visibility:hidden!important}")

        dida = lambda t, s=None, finale=False: p.evaluate(DIDA, [t, s, finale])
        stanza = "document.getElementById('stanza').hidden?'':document.getElementById('stanza-nome').textContent"

        async def scatta(secondi, velocita=1.0):
            for _ in range(int(secondi * FPS)):
                await p.clock.run_for(int(1000 / FPS * velocita))
                await p.screenshot(path=f"{OUT}/{n[0]:05d}.png", timeout=180000)
                n[0] += 1

        # 1 — l'aggancio, camminando a velocità vera (JJ, 19/10: «il video è troppo veloce»: a velocità doppia correva)
        await p.evaluate(f"window.CITTA.vaiVerso({json.dumps(T['dove'])})")
        await dida(*T["dida"][0]); await scatta(2.2)
        # 2 — il resto del cammino non si gira: si arriva
        await dida(None)
        for _ in range(2500):
            await p.clock.run_for(50)
            if await p.evaluate(stanza): break
        else:
            sys.exit(f"l'avatar non è arrivato a «{T['dove']}» (è a {await p.evaluate('window.CITTA.dove()')})")
        await p.clock.run_for(600)
        # 3 — dentro: il dialogo, le scelte, i piani (21/10); la scritta in alto spiega cosa succede
        for (fai, cosa, scritta, secondi, *extra) in T.get("scena", []):
            if fai == "dialogo":
                await p.evaluate(f"window.CITTA.dialogo({json.dumps(cosa)})")
                if extra and extra[0] != "chiudi":
                    await p.evaluate("t=>{ const x=document.getElementById('dialogo-testo'); x.classList.remove('lungo'); x.textContent=t; }", extra[0])
            elif fai == "scelta":
                await p.evaluate("t=>{ const b=[...document.querySelectorAll('#dialogo-scelte button')].find(x=>x.textContent.includes(t)); if(b) b.click(); }", cosa)
                if extra and extra[0] == "chiudi":
                    await p.clock.run_for(200)
                    await p.evaluate("document.querySelectorAll('#dialogo-scelte button').forEach(b=>{ if(b.textContent==='Esci') b.click(); })")
            elif fai == "piano":
                await p.evaluate("document.querySelectorAll('#dialogo-scelte button').forEach(b=>{ if(b.textContent==='Esci') b.click(); })")
                await p.evaluate(f"window.CITTA.piano({int(cosa)})")
                for _ in range(400):
                    await p.clock.run_for(50)
                    if await p.evaluate(f"document.getElementById('stanza-nome').textContent.includes('{int(cosa)}° piano')"): break
                await p.clock.run_for(1500)
            await dida(*scritta); await scatta(secondi)
        if not T.get("scena"):
            await dida(*T["dida"][2]); await scatta(3.6)
        await p.evaluate("document.querySelectorAll('#dialogo-scelte button').forEach(b=>{ if(b.textContent==='Esci') b.click(); })")
        # 4 — l'invito
        await dida(*CTA, True); await scatta(2.6)


async def monta(tema, T, n):
    secondi = n[0] / FPS
    scala = [] if PROVA else ["-vf", f"scale=1080:1920:flags=lanczos,fade=t=in:st=0:d=0.3,fade=t=out:st={secondi - 0.4:.2f}:d=0.4,format=yuv420p"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{OUT}/%05d.png",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", *scala,
                    *(["-vf", "format=yuv420p"] if PROVA else []),
                    "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", "-c:a", "aac", "reel.mp4"], check=True)
    peso = os.path.getsize("reel.mp4")
    info = {"tema": tema, "data": datetime.date.today().isoformat(), "secondi": round(secondi, 1), "byte": peso,
            "descrizione": T["descrizione"], "scritte": [re.sub(r"<[^>]+>", "", x[0]) for x in T["dida"]] + [CTA[0]]}
    json.dump(info, open("reel.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))
    if peso > 20 * 1024 * 1024: sys.exit(f"reel.mp4 è {peso} byte: Telegram ne scarica al massimo 20 MB")


if __name__ == "__main__":
    asyncio.run(main())
