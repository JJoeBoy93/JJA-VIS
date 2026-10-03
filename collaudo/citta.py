"""Collaudo della città (citta.html), in un browser vero col telefono finto.

    python3 collaudo/citta.py citta.html [cartella-foto]
    CHROMIUM=/percorso/chrome python3 collaudo/citta.py citta.html

Nessuna richiesta esce: la città, three e la porta finta sono serviti da qui.
Verde = 0 errori JavaScript e tutte le prove passate. Nato il 2 ottobre 2026
(Athena), insieme alla città. Ogni link della città deve portare a un id che
esiste davvero in index.html: è la prova che i palazzi non portano nel vuoto.
"""
import json, asyncio, sys, os, re
from playwright.async_api import async_playwright

CITTA = os.path.abspath(sys.argv[1])
CASA = os.path.dirname(CITTA)
FOTO = sys.argv[2] if len(sys.argv) > 2 else None
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
PORTA = "https://jjavis-porta.19-jjardito93.workers.dev"
INDICE = open(os.path.join(CASA, "index.html"), encoding="utf-8").read()
ID_PAGINA = set(re.findall(r'id="([^"]+)"', INDICE))
SCHEDE = {"inizia", "chi-sono", "sa-fare", "bottega", "profilo", "numeri", "investitori", "sostieni"}

prove = []
def prova(nome, ok, dettaglio=""):
    prove.append((nome, bool(ok)))
    print(("  ok  " if ok else "  NO  ") + nome + (f" — {dettaglio}" if dettaglio and not ok else ""))

richieste = []   # tutto quello che la pagina chiede: il ristorante non deve chiedere niente a nessuno
async def instrada(route):
    u = route.request.url
    richieste.append(u)
    if u.startswith(BASE):
        nome = u[len(BASE):].split("#")[0].split("?")[0] or "index.html"
        f = os.path.join(CASA, nome)
        if os.path.isfile(f):
            tipo = "text/html" if f.endswith(".html") else "text/javascript" if f.endswith(".js") else "application/json"
            return await route.fulfill(body=open(f, "rb").read(), content_type=tipo)
        return await route.fulfill(status=404, body="")
    if u.startswith(PORTA + "/video"):
        return await route.fulfill(body=json.dumps({"video": [{"url": "https://www.instagram.com/reel/PROVA1/", "titolo": "Il giro del mattino", "piattaforma": "instagram"},
                                                               {"url": "javascript:alert(1)", "titolo": "trappola", "piattaforma": "instagram"}]}),
                                   content_type="application/json", headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    if u.startswith(PORTA + "/vetrina"):
        return await route.fulfill(body=json.dumps({"attrezzi": 42, "canzoni": 4639}), content_type="application/json",
                                   headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    return await route.abort()

async def nuova(b, profilo=None, citta=None, webgl=True):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    await ctx.route("**/*", instrada)
    script = ""
    if profilo is not None: script += f"localStorage.setItem('jjavis-io', {json.dumps(json.dumps(profilo))});"
    if citta is not None: script += f"localStorage.setItem('jjavis-citta', {json.dumps(json.dumps(citta))});"
    if not webgl: script += "HTMLCanvasElement.prototype.getContext=function(){return null};"
    if script: await ctx.add_init_script(f"if(location.href.indexOf('citta.html')>=0 && !sessionStorage.getItem('gia')){{sessionStorage.setItem('gia','1');{script}}}" if webgl else script)
    p = await ctx.new_page()
    errori = []
    p.on("pageerror", lambda e: errori.append(str(e)))
    p.on("console", lambda m: errori.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text else None)  # i font di Google qui sono tagliati apposta
    return ctx, p, errori

async def foto(p, nome):
    if FOTO:
        os.makedirs(FOTO, exist_ok=True)
        await p.screenshot(path=os.path.join(FOTO, nome + ".png"))

async def foglio(p):
    """la stanza aperta: titolo, link, testo. Dentro un palazzo la carta è chiusa finché
    non si tocca una cosa: qui si apre la scheda intera, che ha tutto."""
    if await p.evaluate("!document.getElementById('stanza').hidden && !document.getElementById('stanza').classList.contains('con-carta')"):
        await p.click("#apri-scheda"); await p.wait_for_timeout(300)
    return await p.evaluate("""()=>({aperto:!document.getElementById('stanza').hidden && document.getElementById('stanza').classList.contains('aperta'),
      titolo:(document.getElementById('stanza-titolo')||{}).textContent||'',
      link:[...document.querySelectorAll('#stanza a')].map(a=>a.getAttribute('href')),
      testo:document.getElementById('stanza-dentro').innerText})""")

async def colori_in_alto(p):
    """quanti colori diversi ci sono nella fascia alta, dove si vede l'interno"""
    from PIL import Image; import io as _io
    im = Image.open(_io.BytesIO(await p.screenshot())).convert("RGB")
    w, h = im.size; im = im.crop((0, int(h * 0.08), w, int(h * 0.30))).resize((60, 30))
    return len({(r >> 4, g >> 4, b >> 4) for r, g, b in im.getdata()})

def tempi_della_pagina():
    i = INDICE.find("const PER_MESTIERE={"); j = INDICE.find("\n};", i)
    return {k: json.loads(v) for k, v in re.findall(r'"([^"]+)":\{\s*tempo:(\[[^\]]*\])', INDICE[i:j])}

async def vai(p, nome, attesa=120000):
    await p.click("#vai")
    await p.click(f'#foglio .elenco-vai button:has-text({json.dumps(nome)})')
    await arrivato(p, nome, attesa)

async def arrivato(p, nome, attesa=120000):
    """si è dentro il palazzo (si cammina) o davanti al luogo all'aperto (la scheda è già aperta)"""
    await p.wait_for_function(f"!document.getElementById('stanza').hidden && document.getElementById('stanza-nome').textContent==={json.dumps(nome)}"
                              " && (window.CITTA.cose().length>0 || document.getElementById('stanza').classList.contains('con-carta'))", timeout=attesa)
    await p.wait_for_timeout(600)

async def usa(p, cosa, nome, attesa=60000):
    """dentro il palazzo: si cammina fino alla cosa e la sua carta si apre col suo nome"""
    if await p.evaluate("document.getElementById('stanza').classList.contains('con-carta')"):
        await p.click("#chiudi-carta"); await p.wait_for_timeout(300)
    await p.evaluate(f"window.CITTA.usa({json.dumps(cosa)})")
    await p.wait_for_function(f"document.getElementById('stanza').classList.contains('con-carta') && (document.getElementById('stanza-titolo')||{{}}).textContent==={json.dumps(nome)}", timeout=attesa)
    await p.wait_for_timeout(400)

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None,
                                     args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

        # 0. le liste della Piazza delle voci sono quelle di index.html, parola per parola
        citta = open(CITTA, encoding="utf-8").read(); i = citta.find("const TEMPO_PER_MESTIERE={"); j = citta.find("\n};", i)
        copia = json.loads("{" + citta[i + len("const TEMPO_PER_MESTIERE={"):j].strip().rstrip(",") + "}")
        prova("TEMPO_PER_MESTIERE della città = PER_MESTIERE della pagina", copia == tempi_della_pagina())

        # 1. si accende: niente errori, il caricamento se ne va, la scena disegna qualcosa
        ctx, p, err = await nuova(b, profilo={"nome": "Ettore", "mestiere": "Guida turistica"})
        await p.goto(BASE + "citta.html")
        await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CITTA.fotogrammi()>5", timeout=30000)
        await p.wait_for_timeout(800)
        prova("la città si accende", True)
        prova("il caricamento se ne va", await p.evaluate("document.getElementById('carica').classList.contains('via')"))
        from PIL import Image; import io as _io
        im = Image.open(_io.BytesIO(await p.screenshot())).convert("RGB").resize((60, 120))
        px = len({(r >> 4, g >> 4, bl >> 4) for r, g, bl in im.getdata()})
        prova("la scena non è vuota (colori diversi nel disegno)", px > 25, f"{px} colori")
        prova("i numeri veri dalla porta in testata", "4.639" in await p.inner_text("#numeri"))
        prova("il primo giro parte dalla Sartoria", "Sartoria" in await p.inner_text("#giro"))
        m = await p.evaluate("window.CITTA.misure()")
        storti = {k: v for k, v in m["tetti"].items() if v["angoli"] != 4 or abs(v["largo"] - v["w"] * 1.08) > 0.05 or abs(v["profondo"] - v["d"] * 1.08) > 0.05}
        prova("i tetti a falde sono dritti: la base è il rettangolo del palazzo, con quattro angoli veri", len(m["tetti"]) == m["falde"] >= 4 and "ristorante" in m["tetti"] and not storti, storti or m["tetti"])
        prova("Borsa: l'insegna sta davanti alle colonne", m["borsa"]["davantiColonne"] is not None and m["borsa"]["davantiColonne"] > m["borsa"]["colonne"], m["borsa"])
        prova("Torre: il logo JJA-VIS in cima, sui quattro lati", m["logoTorre"] == 4, m["logoTorre"])
        prova("nessun palazzo, lotto, lampione o albero sta sulla strada", await p.evaluate("window.CITTA.sullaStrada()") == [], await p.evaluate("window.CITTA.sullaStrada()"))
        prova("le vie che il cammino segue non passano dentro niente (il furgone stava sull'anello)", await p.evaluate("window.CITTA.stradeLibere()") == [], await p.evaluate("window.CITTA.stradeLibere()"))
        aq = await p.evaluate("window.CITTA.anelloQuadrato()")
        prova("il secondo anello è quadrato: quattro lati dritti che si chiudono", aq["lati"] == 4 and aq["coprono"], aq)
        prova("intorno, i quartieri: isolati di palazzi fra le vie", m["isolati"] >= 40, m["isolati"])
        await foto(p, "01-ingresso")

        # 2. il mestiere della pagina arriva in Sartoria, il vestito segue ma resta libero
        await vai(p, "Sartoria")
        await usa(p, "specchio", "Lo specchio")
        f = await foglio(p)
        prova("Sartoria: si cammina fino alla porta e si apre la stanza", f["aperto"])
        prova("dentro la Sartoria si vede l'interno in 3D (colori nella fascia alta)", await colori_in_alto(p) > 20)
        prova("il mestiere della pagina è già scelto", await p.evaluate("[...document.querySelectorAll('#stanza .scelta')].some(b=>b.textContent==='Guida turistica'&&b.getAttribute('aria-pressed')==='true')"))
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("senza scegliere, il vestito è quello del mestiere", st.get("vestito") == "guida", st)
        await p.wait_for_timeout(900); await foto(p, "02-sartoria-guida")
        await p.click('#stanza .scelta >> text="Creator"')  # esatto: «Creator o gamer» è il mestiere
        await p.click("#stanza .scelta:has-text('Corriere o autista')")
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("cambio mestiere: il vestito scelto resta (non è obbligatorio vestirsi da lavoro)", st.get("vestito") == "creator" and st.get("mestiere") == "Corriere o autista", st)
        await p.click("#stanza .tinta[aria-label='tono della pelle 4']")
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("la pelle si salva", st.get("pelle") == 3, st)
        await p.wait_for_timeout(900); await foto(p, "03-sartoria-creator")
        await p.click("#stanza button:has-text('Fatto')")
        prova("Fatto riporta in piazza", await p.evaluate("document.getElementById('stanza-nome').textContent===''||!document.getElementById('stanza').classList.contains('aperta')"))
        prova("il giro segna la Sartoria", await p.evaluate("document.querySelectorAll('#giro .f.fatta').length===1"))

        # 3. ogni luogo: si apre e ogni link interno porta a un id vero della pagina
        nomi = ["Reception", "Bottega", "La Forgia", "La Torre", "L'Albero della Vita", "Piazza delle voci", "Cinema", "Borsa", "Athena Trasporti", "Lotto libero", "Sala giochi", "Ristorante", "Palestra"]
        senza_salti = []
        rotti = []
        for n in nomi:
            await vai(p, n)
            f = await foglio(p)
            for h in f["link"]:
                if h.startswith("index.html#"):
                    k = h.split("#", 1)[1]
                    if k not in SCHEDE and k not in ID_PAGINA: rotti.append((n, h))
                elif not h.startswith("https://jjoeboy93.github.io/") and not (n == "Cinema" and re.match(r"https://(www\.)?(instagram\.com|youtube\.com|youtu\.be|tiktok\.com)/", h)): rotti.append((n, h))
            parti = await p.evaluate("window.CITTA.parti()")
            if parti:
                prova(f"{n}: dentro ci sono le cose del palazzo", len(parti) >= 2 and sorted(k for k, _ in parti) == sorted(await p.evaluate("window.CITTA.cose()")), parti)
                s0 = await p.evaluate("window.CITTA.saltiDentro()")
                for k, nome_cosa in parti:
                    await usa(p, k, nome_cosa)
                    if await p.evaluate("window.CITTA.nelMuroDentro()"): senza_salti.append((n, k, "nel muro"))
                if await p.evaluate("window.CITTA.saltiDentro()") != s0: senza_salti.append((n, "salti", await p.evaluate("window.CITTA.saltiDentro()") - s0))
                await p.click("#chiudi-carta"); await p.wait_for_timeout(300); f = await foglio(p)   # di nuovo la scheda intera
            if n == "Reception": prova("la Reception saluta col nome dato nella pagina", "Ettore" in f["testo"], f["testo"][:80])
            if n == "Bottega":
                await foto(p, "04-bottega")
                prima = await p.evaluate("(document.querySelector('#stanza .prodotto h3')||{}).textContent")
                prova("in Bottega il primo prodotto segue il mestiere (corriere → Athena Trasporti)", prima == "Il sito di Athena Trasporti", prima)
            if n == "L'Albero della Vita": prova("l'albero dice che la foglia d'oro è di Ettore", "Ettore" in f["testo"])
            if n == "Bottega":
                prova("la stanza della Bottega è approfondita: Clio spiega come funziona, coi numeri veri", "Come funziona" in f["testo"] and "21" in f["testo"])
            if n == "La Torre":
                prova("la Torre ha i numeri veri della porta", "42" in f["testo"] and "4.639" in f["testo"] and "8.385" in f["testo"])
                await foto(p, "08-stanza-torre")
            if n == "Piazza delle voci":
                tp = tempi_della_pagina(); manca = [x for x in tp["Corriere o autista"] if x not in f["testo"]]
                prova("Piazza delle voci: le domande del mestiere sono quelle della pagina", not manca, manca)
            if n == "Cinema":
                await p.wait_for_selector("#stanza .video", timeout=10000)
                hrefs = await p.evaluate("[...document.querySelectorAll('#stanza .video')].map(a=>a.href)")
                prova("al Cinema i video veri dalla porta, e un link non https non passa", hrefs == ["https://www.instagram.com/reel/PROVA1/"], hrefs)
                await foto(p, "09-stanza-cinema")
            if n == "Borsa": prova("in Borsa le stime sono dette stime", "Stime di chi fa questo lavoro" in f["testo"])
            prova(f"{n}: c'è l'interno o il luogo in 3D", await colori_in_alto(p) > 12)
            if n == "Borsa":
                prima = await p.evaluate("window.CITTA.dove()")
                await p.mouse.click(195, 150); await p.wait_for_timeout(800)
                prova("in stanza toccare la vista non fa camminare fuori", await p.evaluate("window.CITTA.dove()") == prima)
            await p.click("#esci-stanza")
            await p.wait_for_timeout(400)
        prova("tutti i link dei palazzi portano a un posto che esiste", not rotti, rotti)
        prova("dentro ogni palazzo si arriva a ogni cosa camminando: niente salti, niente muri", not senza_salti, senza_salti)
        prova("il giro è chiuso dopo Sartoria, Reception e Bottega", "Giro chiuso" in await p.inner_text("#giro"))
        await p.wait_for_timeout(500); await foto(p, "05-dopo-il-giro")

        # 3b. la città è più grande: i lotti dell'anello 2, e ci si arriva per strada senza saltare
        n_lotti = await p.evaluate("window.CITTA.lotti()")
        prova("ci sono i lotti dell'anello 2 (almeno 12)", n_lotti >= 12, n_lotti)
        lontano = await p.evaluate("""()=>{const d=window.CITTA.dove(); let m=null,dm=-1; for(const [k,P] of Object.entries(window.CITTA.porte)){ if(P.id!=='lotto') continue;
           const x=Math.hypot(P.x-d.x,P.z-d.z); if(x>dm){dm=x;m=k;} } return m}""")
        prima_salti = await p.evaluate("window.CITTA.salti()")
        await p.evaluate(f"window.CITTA.vaiVerso({json.dumps(lontano)})")
        await p.wait_for_function("!document.getElementById('stanza').hidden && (document.getElementById('stanza-titolo')||{}).textContent==='Lotto libero'", timeout=120000)
        prova("al lotto più lontano si arriva camminando per strada, senza salti", await p.evaluate("window.CITTA.salti()") == prima_salti, (lontano, await p.evaluate("window.CITTA.salti()")))
        prova("il lotto promette il palazzo (JJ ha detto sì)", "avrà il suo palazzo" in (await foglio(p))["testo"])
        await foto(p, "11-lotto-lontano")
        await p.click("#esci-stanza"); await p.wait_for_timeout(500)

        # 3c. la visuale: davanti alla Torre, con lo sguardo di prima la cima non si vede; alzandolo sì
        await vai(p, "La Torre"); await p.click("#esci-stanza"); await p.wait_for_timeout(500)
        yaw = await p.evaluate("""()=>{const P=window.CITTA.porte.torre, d=window.CITTA.dove(); return Math.atan2(-(P.cx-d.x),-(P.cz-d.z))}""")
        await p.evaluate(f"window.CITTA.guarda({yaw},0.38)"); await p.wait_for_timeout(2500)
        prima = await p.evaluate("window.CITTA.vedo('globo')")
        await p.evaluate(f"window.CITTA.guarda({yaw},-0.22)"); await p.wait_for_timeout(2500)
        dopo = await p.evaluate("window.CITTA.vedo('globo')")
        await foto(p, "12-cima-della-torre")
        prova("con lo sguardo alzato si vede la cima della torre (prima no)", (not prima) and dopo, (prima, dopo))
        await p.evaluate(f"window.CITTA.guarda({yaw},1.3)"); await p.wait_for_timeout(2500); await foto(p, "13-dall-alto")
        await p.evaluate(f"window.CITTA.guarda({yaw},0.38)"); await p.wait_for_timeout(800)

        # 3d. il Ristorante: alla cassa il menù, si sceglie, si arriva al conto, e il pagamento dice che non è acceso
        await vai(p, "Ristorante")
        await usa(p, "cassa", "La cassa")
        for voce, volte in (("margherita", 2), ("caffe", 1)):
            for _ in range(volte):
                await p.click(f'#stanza .menu-voce[data-voce="{voce}"] button[aria-label^="Aggiungi"]'); await p.wait_for_timeout(150)
        tot = await p.inner_text("#totale-ordine")
        prova("alla cassa: 2 Margherita e 1 Caffè fanno 15,20 €", tot.replace("\u00a0", " ") == "15,20 €", tot)
        await foto(p, "14-ristorante-cassa")
        await p.click("#stanza button:has-text('Vai al conto')"); await p.wait_for_timeout(300)
        conto = await p.inner_text("#stanza-dentro")
        prova("il conto ha le righe giuste", "2 × Margherita" in conto and "1 × Caffè" in conto, conto[:200])
        await p.click("#stanza .scelta:has-text('A domicilio')")
        prima = len(richieste)
        await p.click("#stanza button:has-text('Paga')"); await p.wait_for_timeout(1500)
        partite = [u for u in richieste[prima:] if not u.startswith(BASE) and "fonts." not in u]
        prova("pagare dice chiaro che il pagamento non è acceso", await p.is_visible("#pagamento-spento") and "nessun soldo si è mosso" in await p.inner_text("#pagamento-spento"))
        prova("pagando non parte nessuna richiesta: nessun ordine, nessun soldo", not partite, partite)
        await foto(p, "15-ristorante-pagato")
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3e. la Palestra: il test di forma dà un livello, si salva nel telefono, e gli esercizi sono del livello
        await vai(p, "Palestra")
        await usa(p, "bilancia", "La bilancia")
        prova("il test non si chiude a metà (Calcola spento finché mancano risposte)", await p.is_disabled("#stanza button:has-text('Calcola il mio livello')"))
        for d, v in ((0, 2), (1, 1), (2, 2), (3, 1)):   # 6 punti → intermedio
            await p.click(f'#stanza .scelta[data-domanda="{d}"][data-valore="{v}"]'); await p.wait_for_timeout(150)
        await p.click("#stanza button:has-text('Calcola il mio livello')"); await p.wait_for_timeout(400)
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("il livello si calcola e resta nel telefono (6 punti → intermedio)", (st.get("forma") or {}).get("livello") == "intermedio" and st["forma"]["punti"] == 6, st.get("forma"))
        prova("il test dice che è una stima, non una misura", "stima" in await p.inner_text("#stanza-dentro"))
        await p.click("#stanza button:has-text('I miei esercizi')"); await p.wait_for_timeout(400)
        prova("gli esercizi sono quelli del mio livello", await p.evaluate("(document.getElementById('elenco-esercizi')||{dataset:{}}).dataset.livello") == "intermedio"
              and await p.evaluate("document.getElementById('stanza-titolo').textContent") == "Gli esercizi")
        await foto(p, "16-palestra-esercizi")
        await p.click("#stanza .scelta:has-text('Avanzato')"); await p.wait_for_timeout(300)
        prova("si può guardare anche un altro livello", "Burpee" in await p.inner_text("#elenco-esercizi"))
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3f. dentro si cammina col cerchio, e i muri e i mobili non si attraversano
        await vai(p, "Bottega")
        prima = await p.evaluate("window.CITTA.doveDentro()")
        j = await p.query_selector("#joy"); bb = await j.bounding_box()
        cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy - 50, steps=4)
        await p.wait_for_timeout(5000); await p.mouse.up()
        dopo = await p.evaluate("window.CITTA.doveDentro()")
        prova("dentro, il cerchio fa camminare", abs(dopo["x"] - prima["x"]) + abs(dopo["z"] - prima["z"]) > 1, (prima, dopo))
        prova("dentro, contro il muro di fondo ci si ferma", not await p.evaluate("window.CITTA.nelMuroDentro()"), dopo)
        await foto(p, "17-bottega-camminata")
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 4. camminare col cerchio sposta davvero, e i palazzi non si attraversano:
        # davanti alla Borsa si spinge avanti, contro la facciata, per tre secondi
        await vai(p, "Borsa"); await p.click("#esci-stanza"); await p.wait_for_timeout(500)
        prima = await p.evaluate("window.CITTA.dove()")
        j = await p.query_selector("#joy"); bb = await j.bounding_box()
        cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy - 50, steps=4)
        await p.wait_for_timeout(3000); await p.mouse.up()
        dopo = await p.evaluate("window.CITTA.dove()")
        prova("il cerchio fa camminare", abs(dopo["x"] - prima["x"]) + abs(dopo["z"] - prima["z"]) > 1, (prima, dopo))
        prova("contro la facciata ci si ferma: non si entra nei muri", not await p.evaluate("window.CITTA.nelMuro()"), dopo)
        await foto(p, "06-camminato")
        prova("nessun errore JavaScript (accesa)", not err, err[:3])
        await ctx.close()

        # 5. di nuovo: il vestito è rimasto, il giro chiuso non si ripete per sempre
        ctx, p, err = await nuova(b, citta={"mestiere": "Sanità", "vestito": "sanita", "pelle": 0, "giro": {"sartoria": True, "reception": True, "bottega": True}, "giroVisto": True})
        await p.goto(BASE + "citta.html")
        await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CITTA.fotogrammi()>3", timeout=30000)
        prova("chi ha già fatto il giro non lo rivede", await p.evaluate("document.getElementById('giro').hidden"))
        await vai(p, "Reception")
        prova("senza nome, la Reception manda a darne uno", "Dai un nome" in (await foglio(p))["testo"])
        prova("nessun errore JavaScript (ritorno)", not err, err[:3])
        await ctx.close()

        # 6. senza WebGL: la città diventa un elenco e funziona lo stesso
        ctx, p, err = await nuova(b, webgl=False)
        await p.goto(BASE + "citta.html")
        await p.wait_for_selector("#riserva:not([hidden])", timeout=15000)
        prova("senza 3D si vede l'elenco, e dice perché", "3D" in await p.inner_text("#riserva-perche"))
        await p.click("#riserva-elenco button:has-text('Bottega')"); await p.wait_for_timeout(500)
        f = await foglio(p)
        prova("dall'elenco la Bottega si apre", f["aperto"] and f["titolo"] == "Bottega")
        await foto(p, "07-senza-3d")
        prova("nessun errore JavaScript (senza 3D)", not [e for e in err if "WebGL" not in e], err[:3])
        await ctx.close()
        # 7. si entra dalla pagina: la porta della città sta nella testata, una volta dato il nome
        ctx, p, err = await nuova(b)
        await p.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({nome:'Ettore'}))")
        await p.goto(BASE + "index.html"); await p.wait_for_timeout(1500)
        porta = await p.evaluate("""()=>{const a=document.querySelector('header .in-citta'); if(!a) return null; const r=a.getBoundingClientRect();
           return {href:a.getAttribute('href'), visibile:r.width>0&&r.height>0&&r.right<=innerWidth+1&&r.top>=0}}""")
        prova("nella pagina la porta della città è in testata, visibile e dentro lo schermo", porta and porta["href"] == "citta.html" and porta["visibile"], porta)
        await foto(p, "10-pagina-testata")
        await p.click("header .in-citta"); await p.wait_for_function("location.pathname.endsWith('citta.html')", timeout=10000)
        prova("toccandola si entra in città", True)
        await ctx.close()
        await b.close()

    rossi = [n for n, ok in prove if not ok]
    print(f"\n{len(prove) - len(rossi)}/{len(prove)} prove")
    print("VERDE" if not rossi else "ROSSO")

asyncio.run(main())
