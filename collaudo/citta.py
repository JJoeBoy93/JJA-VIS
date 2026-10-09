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

parlate = []     # i messaggi arrivati alla porta finta da /parla
richieste = []   # tutto quello che la pagina chiede: il ristorante non deve chiedere niente a nessuno
async def instrada(route):
    u = route.request.url
    richieste.append(u)
    if u.startswith(BASE + "insieme.json"):   # mai il server vero dal collaudo: un indirizzo finto, preso dal finto qui sotto
        return await route.fulfill(body=json.dumps({"indirizzo": INSIEME}), content_type="application/json")
    if u.startswith(BASE):
        nome = u[len(BASE):].split("#")[0].split("?")[0] or "index.html"
        f = os.path.join(CASA, nome)
        if os.path.isfile(f):
            tipo = "text/html" if f.endswith(".html") else "text/javascript" if f.endswith(".js") else "image/png" if f.endswith(".png") else "application/manifest+json" if f.endswith(".webmanifest") else "application/json"
            return await route.fulfill(body=open(f, "rb").read(), content_type=tipo)
        return await route.fulfill(status=404, body="")
    if u.startswith(PORTA + "/video"):
        return await route.fulfill(body=json.dumps({"video": [{"url": "https://www.instagram.com/reel/PROVA1/", "titolo": "Il giro del mattino", "piattaforma": "instagram"},
                                                               {"url": "javascript:alert(1)", "titolo": "trappola", "piattaforma": "instagram"}]}),
                                   content_type="application/json", headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    if u.startswith(PORTA + "/parla"):   # Nova risponde subito e la passa anche a chi la costruisce
        parlate.append(json.loads(route.request.post_data or "{}"))
        return await route.fulfill(body=json.dumps({"id": "q1", "subito": {"testo": "Ciao! Su questa ti risponde anche chi mi costruisce.", "id": "q1-n", "passa": True}}),
                                   content_type="application/json", headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    if u.startswith(PORTA + "/risposte"):
        return await route.fulfill(body=json.dumps({"risposte": [{"id": "q1", "domanda": "Ciao dalla città", "risposta": "Risposta vera di chi mi costruisce"}] if parlate else []}),
                                   content_type="application/json", headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    if u.startswith("https://all.api.radio-browser.info/json/stations/search"):   # Radio Browser finto
        from urllib.parse import urlparse, parse_qs
        nome = parse_qs(urlparse(u).query).get("name", [""])[0]
        if nome == "RTL 102.5": return await route.abort()           # la ricerca che non va: deve dirlo
        lista = {"Radio Deejay": [{"name": "Radio Deejay", "url_resolved": "https://radio.finta/deejay.mp3"}],
                 "m2o": [{"name": "m2o", "url_resolved": "http://solo-http.finto/m2o"}]}.get(nome, [])
        return await route.fulfill(body=json.dumps(lista), content_type="application/json", headers={"Access-Control-Allow-Origin": "*"})
    if u.startswith("https://radio.finta/"):   # il flusso: c'è, ma vuoto (il telefono non lo suona: deve dirlo, non sbagliare)
        return await route.fulfill(status=200, body=b"", content_type="audio/mpeg")
    if u.startswith(PORTA + "/vetrina"):
        return await route.fulfill(body=json.dumps({"attrezzi": 42, "canzoni": 4639}), content_type="application/json",
                                   headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
    return await route.abort()

INSIEME = "wss://jjavis-citta.finta.workers.dev/entra"
def nessun_altro(ws):
    def msg(m):
        if m == "ping": ws.send("pong")
        elif json.loads(m).get("t") == "ciao": ws.send(json.dumps({"t": "tu", "id": "io1", "max": 40, "altri": []}))
    ws.on_message(msg)

async def nuova(b, profilo=None, citta=None, webgl=True):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    await ctx.add_init_script("try{ sessionStorage.setItem('jjavis-conto-dopo','1'); }catch(_){}")   # 6/10: il pannello dell'account che si apre all'ingresso qui non serve (lo prova conto.py)
    await ctx.route("**/*", instrada)
    await ctx.route_web_socket(INSIEME, nessun_altro)   # il server vero non si tocca: qui in città ci sei solo tu (gli altri: collaudo/insieme.py)
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
    await p.click(f'#foglio .elenco-vai button:has-text({json.dumps(nome, ensure_ascii=False)})')   # «Café»: \u00e9 non è un selettore
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

        # 0a. l'app (JJ, 5/10): il manifest c'è, le due pagine lo citano, e ogni icona esiste con la misura che dice
        from PIL import Image as _Im
        man = json.load(open(os.path.join(CASA, "manifest.webmanifest"), encoding="utf-8"))
        icone = man["icons"] + [i for s_ in man.get("shortcuts", []) for i in s_.get("icons", [])]
        sbagliate = [i["src"] for i in icone if not os.path.isfile(os.path.join(CASA, i["src"])) or "%dx%d" % _Im.open(os.path.join(CASA, i["src"])).size != i["sizes"]]
        prova("l'app: il manifest ha nome, avvio, icone 192 e 512 e quella mascherabile, e ogni icona esiste della misura giusta",
              man["name"] == "JJA-VIS" and man["display"] == "standalone" and {"192x192", "512x512"} <= {i["sizes"] for i in man["icons"]}
              and any(i.get("purpose") == "maskable" for i in man["icons"]) and not sbagliate, sbagliate)
        # privacy e regole (6/10): ci sono, hanno la mail di contatto di JJA-VIS, e la città le collega
        pr = open(os.path.join(CASA, "privacy.html"), encoding="utf-8").read(); rg = open(os.path.join(CASA, "regole.html"), encoding="utf-8").read()
        prova("privacy e regole esistono, con la mail di contatto di JJA-VIS, e si citano a vicenda", "19.jja.vis.93@gmail.com" in pr and "19.jja.vis.93@gmail.com" in rg and 'href="regole.html"' in pr and 'href="privacy.html"' in rg)
        import re as _re
        prova("le pagine non nominano altri giochi né il nome di prova dell'assistente (JJ, 6/10)", not _re.search(r"(?i)\bnova\b|v-buck|gemme|fortnite|clash", pr + rg), _re.findall(r"(?i)\bnova\b|v-buck|gemme|fortnite|clash", pr + rg))
        prova("i crediti dei simboli degli dèi ci sono (CC BY 3.0: lorc, delapouite, carl-olsen)", all(t in rg for t in ("lorc", "delapouite", "carl-olsen", "game-icons.net", "creativecommons.org/licenses/by/3.0")))
        prova("la privacy dice titolare, cosa, chi altro, per quanto, età e diritti", all(t in pr for t in ("Chi è il titolare", "Cosa raccogliamo", "Chi altro tocca i dati", "Per quanto tempo", "Età", "I tuoi diritti", "Garante")))
        _c = open(CITTA, encoding="utf-8").read()
        prova("la città collega privacy e regole", 'href:"privacy.html"' in _c and 'href:"regole.html"' in _c)
        prova("l'app: la pagina e la città citano il manifest e l'icona", all('rel="manifest" href="manifest.webmanifest"' in open(os.path.join(CASA, f_), encoding="utf-8").read()
              and 'rel="apple-touch-icon"' in open(os.path.join(CASA, f_), encoding="utf-8").read() for f_ in ("index.html", "citta.html")))
        # 0. le liste della Piazza delle voci sono quelle di index.html, parola per parola
        citta = open(CITTA, encoding="utf-8").read(); i = citta.find("const TEMPO_PER_MESTIERE={"); j = citta.find("\n};", i)
        copia = json.loads("{" + citta[i + len("const TEMPO_PER_MESTIERE={"):j].strip().rstrip(",") + "}")
        prova("TEMPO_PER_MESTIERE della città = PER_MESTIERE della pagina", copia == tempi_della_pagina())

        # 0b. i quattro aspetti: i colori della città sono quelli della pagina
        pagina = open(os.path.join(CASA, "index.html"), encoding="utf-8").read(); diversi = []
        for t in ("calmo", "deciso", "naturale"):
            vp = dict(re.findall(r"--([a-z0-9]+):(#[0-9A-Fa-f]{6})", re.search(r':root\[data-tema="%s"\]\{([^}]*)' % t, pagina).group(1)))
            vc = dict(re.findall(r"--([a-z0-9]+):(#[0-9A-Fa-f]{6})", re.search(r':root\[data-tema="%s"\]\{([^}]*)' % t, citta).group(1)))
            diversi += [(t, k, vc[k], vp.get(k)) for k in vc if vp.get(k) != vc[k]]
        prova("i colori dei quattro aspetti sono quelli della pagina, parola per parola", not diversi, diversi)

        # 1. si accende: niente errori, il caricamento se ne va, la scena disegna qualcosa
        ctx, p, err = await nuova(b, profilo={"nome": "Ettore", "mestiere": "Guida turistica"})
        await p.goto(BASE + "citta.html", timeout=60000)
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
        prova("si entra in piazza, a sud dell'albero (dove l'ha voluto JJ), e non dentro niente", await p.evaluate("window.CITTA.dove()") == {"x": 0, "z": 18} and not await p.evaluate("window.CITTA.nelMuro()"))
        m = await p.evaluate("window.CITTA.misure()")
        storti = {k: v for k, v in m["tetti"].items() if v["angoli"] != 4 or abs(v["largo"] - v["w"] * 1.08) > 0.05 or abs(v["profondo"] - v["d"] * 1.08) > 0.05}
        prova("i tetti a falde sono dritti: la base è il rettangolo del palazzo, con quattro angoli veri", len(m["tetti"]) == m["falde"] >= 3 and "ristorante" in m["tetti"] and not storti, storti or m["tetti"])
        prova("Torre: il logo JJA-VIS in cima, sui quattro lati", m["logoTorre"] == 4, m["logoTorre"])
        prova("nessun palazzo, lotto, lampione o albero sta sulla strada", await p.evaluate("window.CITTA.sullaStrada()") == [], await p.evaluate("window.CITTA.sullaStrada()"))
        rc = await p.evaluate("(()=>{ const P=window.CITTA.porte, r=P.ristorante, c=P.cafe; return {r:Math.hypot(r.cx,r.cz), d:Math.hypot(r.cx-c.cx,r.cz-c.cz)}; })()")
        prova("il Ristorante sta in piazza, accanto al JJA-VIS Café (JJ, 4/10)", 29 < rc["r"] < 33 and rc["d"] < 20, rc)
        prova("le vie che il cammino segue non passano dentro niente (il furgone stava sull'anello)", await p.evaluate("window.CITTA.stradeLibere()") == [], await p.evaluate("window.CITTA.stradeLibere()"))
        prova("nessun pezzo di vestito sta fermo dove si muovono le gambe (strisce JJA-VIS, camice, grembiule: si piegano con le gambe)", await p.evaluate("window.CITTA.pezziSulleGambe()") == [], await p.evaluate("window.CITTA.pezziSulleGambe()"))
        st = await p.evaluate("window.CITTA.stoffa()")
        prova("camice e grembiule: un pezzo solo, ogni lato va col piede del suo lato, e nessun punto della gamba esce dalla stoffa", all(v["pezzi"] == 1 and v["latiGiusti"] and v["provati"] > 20 and v["fuori"] == 0 for v in st.values()), st)
        prova("il camice è aperto davanti, va dalle spalle al ginocchio, copre spalle e fianchi, e le braccia non ci passano dentro (JJ: «manca tutto il pezzo sulle spalle e sui fianchi»)",
              st["sanita"]["aperto"] and st["sanita"]["daSpalleA"][0] >= 1.55 and st["sanita"]["daSpalleA"][1] <= 0.5
              and st["sanita"]["copre"] == {"fianchi": True, "spalle": True} and st["sanita"]["bracciaFuori"], st["sanita"])
        dt_ = await p.evaluate("window.CITTA.dettagli()")
        prova("niente del vestito JJA-VIS esce dalla sagoma del busto (JJ: «escono ancora dalla sagoma»)", dt_["sagoma"] == [], dt_["sagoma"])
        prova("i capelli non scendono davanti agli occhi: davanti finiscono sopra le sopracciglia (1,975)", all(v is None or v > 1.975 for v in dt_["frangia"].values()), dt_["frangia"])
        prova("il camice non è un quadrato: segue il corpo con superfici curve (JJ: «il camice è rimasto un quadrato»)", st["sanita"]["curvo"], st["sanita"])
        aq = await p.evaluate("window.CITTA.anelloQuadrato()")
        prova("il secondo anello è quadrato: quattro lati dritti che si chiudono", aq["lati"] == 4 and aq["coprono"], aq)
        prova("intorno, i quartieri: isolati di palazzi fra le vie", m["isolati"] >= 40, m["isolati"])
        await foto(p, "01-ingresso")

        # 2. il mestiere della pagina arriva in Sartoria, il vestito segue ma resta libero
        await vai(p, "Sartoria")
        await usa(p, "specchio", "L'armadietto")
        f = await foglio(p)
        prova("Sartoria: si cammina fino alla porta e si apre la stanza", f["aperto"])
        prova("dentro la Sartoria si vede l'interno in 3D (colori nella fascia alta)", await colori_in_alto(p) > 20)
        # JJ, 3/10: il lavoro detto nella pagina non si richiede
        prova("il lavoro detto nella pagina non si richiede: è scritto, e i mestieri non ci sono", "Guida turistica" in await p.inner_text("#mestiere-detto")
              and not await p.evaluate("[...document.querySelectorAll('#stanza .scelta')].some(b=>b.textContent==='Sanità')"))
        await p.click("#stanza button:has-text('Cambia')"); await p.wait_for_timeout(300)
        prova("con «Cambia» i mestieri tornano, col suo già scelto", await p.evaluate("[...document.querySelectorAll('#stanza .scelta')].some(b=>b.textContent==='Guida turistica'&&b.getAttribute('aria-pressed')==='true')"))
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
        # le skin (JJ, 4/10): la base fatta in Blender all'inizio; le altre si sbloccano coi gettoni (da 800 a 2000)
        await p.wait_for_function("window.CITTA.skinTua().skin==='base' && window.CITTA.skinTua().ossi===true", timeout=60000)
        prova("si comincia con la skin base fatta in Blender, e i suoi ossi ci sono", True)
        # il negozio (JJ, 6/10: i manichini diventano il negozio, griglia di schede con nome e prezzo; lì si compra, non si
        # indossa). Toccando una scheda la skin ti va addosso in prova, gratis: «le skin se non hai gettoni non le puoi neanche vedere... non va bene»
        await usa(p, "manichini", "Il negozio")
        schede = await p.evaluate("[...document.querySelectorAll('#negozio .scheda-skin')].map(b=>[b.dataset.skin,b.querySelector('.prezzo').textContent])")
        prova("il negozio è una griglia con tutte le skin, ognuna col suo prezzo (o «è tua»)", len(schede) == 6 and dict(schede).get("cavaliere") == "2000 🪙" and dict(schede).get("base") == "è tua", schede)
        prova("al negozio non si indossa: niente «Indossa»", not await p.evaluate("[...document.querySelectorAll('#stanza-carta button')].some(b=>/Indossa/.test(b.textContent))"))
        await p.click("#negozio .scheda-skin[data-skin='cavaliere']")
        prova("toccando una scheda la skin ti va addosso in prova, e i gettoni restano quelli",
              await p.evaluate("window.CONTO_PROVA.stato().provaSkin==='cavaliere' && window.CITTA.gettoni()===100") and "in prova" in await p.inner_text("#esito-skin")
              and "Il Cavaliere" in await p.inner_text("#vetrina"))
        await p.wait_for_function("window.CITTA.skinTua().skin==='cavaliere'", timeout=60000)
        prova("ma non diventa tua", "cavaliere" not in (await p.evaluate("window.CITTA.skinTua()"))["mie"])
        await p.click("#chiudi-carta"); await p.wait_for_timeout(400)
        prova("chiudendo la carta la prova finisce da sola", await p.evaluate("window.CONTO_PROVA.stato().provaSkin===null") and (await p.evaluate("window.CITTA.skinTua()"))["skin"] == "base")
        await usa(p, "manichini", "Il negozio")
        await p.click("#negozio .scheda-skin[data-skin='realista-uomo']"); await p.click("#vetrina button:has-text('Compra')"); await p.wait_for_timeout(400)
        prova("una skin da 800 con 100 gettoni non si compra, e dice dove vincerli", "Sala giochi" in await p.inner_text("#esito-skin")
              and not await p.evaluate("window.CONTO_PROVA.stato().skinMie.includes('realista-uomo')"))
        await p.evaluate("window.CITTA.gettoni(900)")
        await usa(p, "manichini", "Il negozio")
        await p.click("#negozio .scheda-skin[data-skin='realista-uomo']"); await p.click("#vetrina button:has-text('Compra')")
        await p.wait_for_function("window.CITTA.skinTua().skin==='realista-uomo' && window.CITTA.skinTua().ossi===true && window.CONTO_PROVA.stato().provaSkin===null", timeout=60000)
        st_ = await p.evaluate("window.CITTA.skinTua()")
        prova("con 900 gettoni la realista (800) si compra, te la tieni addosso, e restano 100 gettoni", st_["gettoni"] == 100 and "realista-uomo" in st_["mie"], st_)
        prezzi = await p.evaluate("[...document.querySelectorAll('#negozio .scheda-skin .prezzo')].map(b=>b.textContent)")
        prova("i prezzi delle skin da comprare sono fra 800 e 2000 gettoni", all(800 <= int(x.split()[0]) <= 2000 for x in prezzi if "🪙" in x) and len([x for x in prezzi if "🪙" in x]) == 3, prezzi)
        # tutte le skin si caricano e trovano i loro ossi (anche quelle coi punti nei nomi, che three toglie)
        tutte = await p.evaluate("""(async()=>{ const r={}; for(const id of ['base','realista-uomo','realista-donna','avventuriera','cavaliere']){ r[id]=await window.CITTA.provaSkin(id); } return r; })()""")
        prova("le cinque skin di Blender si caricano, coi loro ossi, e il passo muove davvero le gambe avanti e indietro", all(v["ossi"] and v["passo"] > 0.05 and v["avanti"] for v in tutte.values()), tutte)
        # l'armadietto (JJ, 6/10: lo specchio diventa l'armadietto): ci sono solo le tue, e lì si indossano
        await usa(p, "specchio", "L'armadietto")
        mie = await p.evaluate("[...document.querySelectorAll('#armadietto .scheda-skin')].map(b=>b.dataset.skin)")
        prova("all'armadietto ci sono solo le skin che hai", sorted(mie) == ["base", "classica", "realista-uomo"], mie)
        await p.click("#armadietto .scheda-skin[data-skin='classica']"); await p.wait_for_timeout(1200)
        prova("la Classica (l'omino coi vestiti dei mestieri) si rimette dall'armadietto", (await p.evaluate("window.CITTA.skinTua()"))["skin"] == "classica")
        await p.evaluate("window.CITTA.gettoni(100)")
        # JJ, 4/10: l'avatar si sceglie tutto, come nei Sims — corpo, capelli, colore dei pantaloni
        await p.click("#scelta-corpo .scelta:has-text('Donna')"); await p.wait_for_timeout(300)
        await p.click("#scelta-capelli .scelta:has-text('Coda')"); await p.wait_for_timeout(300)
        await p.click("#tinte-pantaloni .tinta:nth-child(3)"); await p.wait_for_timeout(300)
        await p.click("#tinte-capelli .tinta:nth-child(4)"); await p.wait_for_timeout(300)
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')"); tu_ = await p.evaluate("window.CITTA.tuo()")
        prova("allo specchio si sceglie il corpo, i capelli, il loro colore e il colore dei pantaloni, e l'avatar cambia davvero",
              st.get("corpo") == "donna" and st.get("capelli") == "coda" and st.get("capelliColore") == 3 and st.get("pantaloni") == 0xE63946
              and tu_["corpo"] == "donna" and tu_["capelli"] == "coda" and tu_["pantaloni"] == "#e63946" and tu_["maglia"] != tu_["pantaloni"], [st, tu_])
        await p.wait_for_timeout(2500)
        prova("allo specchio con la carta aperta la telecamera si allontana: l'avatar si vede intero (JJ: «è tagliato»)", (await p.evaluate("window.CITTA.vistaSpecchio()") or 0) > 6.5, await p.evaluate("window.CITTA.vistaSpecchio()"))
        fu = await p.evaluate("window.CITTA.formaUmana()")
        prova("gli avatar hanno forma di persona: gambe e braccia tonde, busto che si stringe, una faccia (occhi, naso, bocca)",
              all(v["gambe"] == ["CapsuleGeometry"] * 2 and v["braccia"] == ["CapsuleGeometry"] * 2 and v["busto"] == "CylinderGeometry" and v["viso"] >= 6 for v in fu.values())
              and fu["donna"]["spalle"] < fu["uomo"]["spalle"], fu)
        await p.wait_for_timeout(600); await foto(p, "03b-sartoria-donna")
        # i vestiti stanno all'armadietto («Come ti vesti?», dove c'erano già); col mestiere già detto niente spiegazione
        testo_m = await p.inner_text("#stanza-carta")
        prova("all'armadietto ci sono i vestiti, e col mestiere già detto non si rispiega", "Perché ti chiedo il mestiere" not in testo_m and "Come ti vesti" in testo_m, testo_m[:200])
        await p.click("#prova-vestito .scelta:has-text('Camice')"); await p.wait_for_timeout(400)
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("toccando un vestito te lo metti", st.get("vestito") == "sanita", st)
        await p.click("#prova-vestito .scelta:has-text('Creator')"); await p.wait_for_timeout(300)
        await p.wait_for_timeout(900); await foto(p, "03-sartoria-creator")
        await p.click("#stanza button:has-text('Fatto')")
        prova("Fatto riporta in piazza", await p.evaluate("document.getElementById('stanza-nome').textContent===''||!document.getElementById('stanza').classList.contains('aperta')"))
        prova("il giro segna la Sartoria", await p.evaluate("document.querySelectorAll('#giro .f.fatta').length===1"))

        # 3. ogni luogo: si apre e ogni link interno porta a un id vero della pagina
        nomi = ["Radio", "Bottega", "La Torre", "L'Albero della Vita", "JJA-VIS Café", "Cinema", "Athena Trasporti", "Lotto libero", "Sala giochi", "Ristorante", "Palestra"]
        senza_salti = []
        rotti = []
        for n in nomi:
            await vai(p, n)
            f = await foglio(p)
            for h in f["link"]:
                if h.startswith("index.html"):   # JJ, 4/10: dalla città non si esce cliccando, solo da «← La pagina»
                    rotti.append((n, h))
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
            if n == "La Torre":
                prova("la Reception è dentro la Torre e saluta col nome; al piano terra solo il globo, l'ascensore e le scale", "Ettore" in f["testo"]
                      and set(await p.evaluate("window.CITTA.cose()")) == {"globo", "ascensore", "scale"}, [f["testo"][:80], await p.evaluate("window.CITTA.cose()")])
                await p.click("#stanza button:has-text('Parla con Ettore')"); await p.wait_for_timeout(400)
                prova("«Parla con Ettore» apre la chat in città, non la pagina", await p.is_visible("#nova") and p.url.endswith("citta.html")
                      and await p.inner_text("#nova-titolo") == "Ettore", p.url)
                await p.fill("#nova-scrivi", "Ciao dalla città"); await p.click("#nova-manda")
                await p.wait_for_function("document.querySelectorAll('#nova .bolla').length>=2", timeout=15000)
                io_ = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-io')||'{}')")
                prova("il messaggio va alla stessa porta della pagina, come chat, con chi e nome", parlate and parlate[-1].get("da_dove") == "chat" and parlate[-1].get("chi") and parlate[-1].get("nome_assistente") == "Ettore", parlate[-1:] )
                prova("la conversazione è quella della pagina (jjavis-io.chat) e il resto del profilo non si tocca", [m["ruolo"] for m in io_.get("chat", [])] == ["tu", "io"]
                      and io_["chat"][0]["attesa"] and io_.get("nome") == "Ettore" and io_.get("mestiere") == "Guida turistica", io_)
                await foto(p, "18-nova-in-citta")
                await p.click("#chiudi-nova"); await p.wait_for_timeout(300)
                await p.click("#apri-nova-stanza"); await p.wait_for_function("document.querySelectorAll('#nova .bolla').length>=3", timeout=15000)
                io_ = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-io')||'{}')")
                prova("la risposta di chi mi costruisce arriva in città, e una volta vista non resta «nuova»", [m["ruolo"] for m in io_["chat"]] == ["tu", "io", "io"]
                      and not io_["chat"][0]["attesa"] and not any(m.get("nuovo") for m in io_["chat"]), io_["chat"])
                await p.click("#chiudi-nova"); await p.wait_for_timeout(300)
            if n == "Bottega":
                await foto(p, "04-bottega")
                prima = await p.evaluate("(document.querySelector('#stanza .prodotto h3')||{}).textContent")
                prova("in Bottega il primo prodotto segue il mestiere (corriere → Athena Trasporti)", prima == "Il sito di Athena Trasporti", prima)
            if n == "L'Albero della Vita": prova("l'albero dice che la foglia d'oro è di Ettore", "Ettore" in f["testo"])
            if n == "Bottega":
                prova("la stanza della Bottega è approfondita: Clio spiega come funziona, coi numeri veri", "Come funziona" in f["testo"] and "21" in f["testo"])
            if n == "La Torre":
                prova("l'assistente al piano terra dice tutto (cosa succede quando entri, per chiunque, i piani, i tuoi dati), fino alla terrazza; il salottino non c'è più", "Per chiunque" in f["testo"] and "Cosa succede quando entri" in f["testo"] and "I tuoi dati" in f["testo"] and "Terrazza" in f["testo"] and "Attico" in f["testo"] and "salottino" not in f["testo"].lower(), f["testo"][:120])
                await foto(p, "08-stanza-torre")
            if n == "Bottega":   # le domande del mestiere ora le fa la commessa (JJ, 4/10)
                tp = tempi_della_pagina(); manca = [x for x in tp["Corriere o autista"] if x not in f["testo"]]
                prova("in Bottega la commessa fa le domande del mestiere, le stesse della pagina", not manca and "cosa ti fa perdere tempo" in f["testo"], manca)
            if n == "Cinema":
                await p.wait_for_selector("#stanza .video", timeout=10000)
                hrefs = await p.evaluate("[...document.querySelectorAll('#stanza .video')].map(a=>a.href)")
                prova("al Cinema i video veri dalla porta, e un link non https non passa", hrefs == ["https://www.instagram.com/reel/PROVA1/"], hrefs)
                await p.click("#stanza .video"); await p.wait_for_timeout(500)
                srcv = await p.evaluate("(document.getElementById('video-cinema')||{}).src||''")
                prova("al Cinema il video si guarda dentro la città, sul grande schermo (incorporamento di Instagram)", srcv == "https://www.instagram.com/reel/PROVA1/embed/" and p.url.endswith("citta.html"), srcv)
                await p.click("#chiudi-cinema"); await p.wait_for_timeout(300)
                inc = await p.evaluate("""['https://www.youtube.com/watch?v=abc123','https://youtu.be/abc123','https://www.youtube.com/shorts/abc123',
                    'https://www.tiktok.com/@jjoe_boy93/video/7382225350710824222','https://vm.tiktok.com/ZMabc/','http://www.instagram.com/reel/X/'].map(u=>window.CITTA.incorpora(u))""")
                prova("il Cinema sa incorporare YouTube e TikTok (lettore ufficiale /player/v1), e quello che non sa o non è https resta fuori", inc == ["https://www.youtube.com/embed/abc123"] * 3 + ["https://www.tiktok.com/player/v1/7382225350710824222?description=1", None, None], inc)
                await usa(p, "poltrone", "Le poltrone")
                await p.click("#stanza-carta button:has-text('Siediti in poltrona')"); await p.wait_for_timeout(1000)
                pb = await p.evaluate("window.CITTA.bar()")
                prova("al Cinema ci si siede in poltrona, e da seduti c'è l'elenco dei video", pb["seduto"] and pb["y"] < 0 and await p.evaluate("document.querySelectorAll('#stanza-carta .video').length") == 1, pb)
                await p.click("#stanza-carta button:has-text('Alzati')"); await p.wait_for_timeout(300)
                await foto(p, "09-stanza-cinema")

            prova(f"{n}: c'è l'interno o il luogo in 3D", await colori_in_alto(p) > 12)
            if n == "Cinema":
                prima = await p.evaluate("window.CITTA.dove()")
                # un punto dove c'è davvero la scena 3D: non un punto fisso (il 6/10 il (195, 150) è finito sul tasto «Gli altri»)
                punto = await p.evaluate("(()=>{ const c=document.getElementById('scena'); for(let y=120;y<800;y+=20) for(const x of [195,120,270]) if(document.elementFromPoint(x,y)===c) return [x,y]; return null; })()")
                prova("in stanza c'è un punto libero dove toccare la vista", punto is not None)
                await p.mouse.click(*(punto or [195, 450])); await p.wait_for_timeout(800)
                prova("toccando la vista non si apre nessun pannello", await p.evaluate("document.getElementById('insieme').hidden && document.getElementById('conto').hidden"))
                prova("in stanza toccare la vista non fa camminare fuori", await p.evaluate("window.CITTA.dove()") == prima)
            await p.click("#esci-stanza")
            await p.wait_for_timeout(400)
        prova("nessuna scheda della città porta fuori, nella pagina (si esce solo da «← La pagina»); i link esterni sono solo quelli permessi", not rotti, rotti)
        prova("dentro ogni palazzo si arriva a ogni cosa camminando: niente salti, niente muri", not senza_salti, senza_salti)
        prova("il giro è chiuso dopo Sartoria, Torre e Bottega", "Giro chiuso" in await p.inner_text("#giro"))
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

        # 3d1. la Bottega (JJ, 4/10): fuori niente cartelli; dentro gli scaffali coi prodotti e il bancone col commesso,
        # dove si chiedono sopralluogo e lavoro su misura senza uscire dalla città; la Forgia è lì
        await vai(p, "Bottega")
        cose_b = await p.evaluate("window.CITTA.cose()")
        prova("in Bottega: scaffali coi prodotti (Clio, Athena) e il bancone; la Forgia non è più un palazzo", set(cose_b) == {"clio", "athena", "bancone"}
              and not await p.evaluate("[...document.querySelectorAll('#foglio .elenco-vai button')].some(b=>b.textContent.includes('Forgia'))"), cose_b)
        await usa(p, "bancone", "Il bancone")
        tb = await p.inner_text("#stanza-carta")
        prova("al bancone ci sono il sopralluogo, il su misura e la Forgia", "Il sopralluogo, gratis" in tb and "Su misura" in tb and "Cosa si forgia" in tb, tb[:200])
        await p.click("#so-cosa-c .scelta:has-text('La mia attività')")
        await p.fill("#so-link-c", "pizzeriadaluca.it"); await p.fill("#so-nome-c", "Luca"); await p.fill("#so-mail-c", "luca@esempio")
        await p.click("#so-ok-c"); await p.click("#so-manda-c"); await p.wait_for_timeout(500)
        prova("sopralluogo: una mail incompleta non parte e lo dice", "La mail non sembra completa" in await p.inner_text("#so-esito-c") and not any(x.get("da_dove") == "sopralluogo" for x in parlate))
        await p.fill("#so-mail-c", "luca@esempio.it"); await p.click("#so-manda-c")
        await p.wait_for_function("document.getElementById('so-esito-c').textContent.startsWith('Arrivato')", timeout=15000)
        ul = [x for x in parlate if x.get("da_dove") == "sopralluogo"][-1:]
        prova("il sopralluogo parte dalla città: stessa porta, come la pagina (link, mail, consenso)", ul and ul[0]["link"] == "https://pizzeriadaluca.it" and ul[0]["contatto"]["mail"] == "luca@esempio.it"
              and ul[0]["contatto"]["consenso"] and ul[0]["testo"].startswith("🔎 La mia attività"), ul)
        await p.click("#cm-cosa-c .scelta:has-text('Bot Telegram')")
        await p.fill("#cm-descrizione-c", "Un bot che mi ricorda le consegne"); await p.fill("#cm-mail-c", "luca@esempio.it"); await p.click("#cm-ok-c"); await p.click("#cm-manda-c")
        await p.wait_for_function("document.getElementById('cm-esito-c').textContent.startsWith('Arrivato')", timeout=15000)
        uc = [x for x in parlate if x.get("da_dove") == "commissione"][-1:]
        io_b = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-io')||'{}')")
        prova("il su misura parte dalla città come «commissione», e tutte e due le richieste finiscono nella stessa chat della pagina", uc and uc[0]["testo"] == "🛠 Bot Telegram — Un bot che mi ricorda le consegne"
              and sum(1 for m in io_b.get("chat", []) if m["ruolo"] == "tu" and m["testo"].startswith(("🔎", "🛠"))) == 2, [uc, io_b.get("chat")])
        prova("al bancone nessun collegamento porta fuori dalla città", not await p.evaluate("[...document.querySelectorAll('#stanza-carta a')].some(a=>a.getAttribute('href').startsWith('index.html'))"))
        await foto(p, "16a-bancone")
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3d1b. il JJA-VIS Café (JJ, 4/10): la struttura della Piazza delle voci, ora un bar
        await vai(p, "JJA-VIS Café")
        prova("il bar ha il bancone, la lavagna delle recensioni, i tavolini e il caffè da offrire", set(await p.evaluate("window.CITTA.cose()")) == {"banco-bar", "recensioni", "tavolini", "caffe"})
        # i gettoni (JJ, 4/10): 100 alla partenza, la colazione si paga, arriva al tavolino, si beve a sorsi e si mangia a morsi
        g0 = await p.evaluate("window.CITTA.gettoni()")
        await p.wait_for_function("window.CITTA._iconaPronta", timeout=30000)
        prova("l'icona dei gettoni ha i dodici dèi dell'app (gli emblemi di immagini/olimpo sono arrivati)", await p.evaluate("window.CITTA._iconaPronta===true"))
        prova("si parte con 100 gettoni, e in testata c'è l'icona di JJA-VIS", g0 == 100 and await p.evaluate("(document.getElementById('gettone-img').src||'').startsWith('data:image/png')"), g0)
        await usa(p, "banco-bar", "Il bancone del bar")
        await p.click("#bar-menu .scelta[data-voce='Caffè']"); await p.click("#bar-menu .scelta[data-voce='Brioche']"); await p.click("#bar-menu .scelta[data-voce='Biscotto']"); await p.wait_for_timeout(300)
        b1 = await p.evaluate("window.CITTA.bar()")
        tot = {v["nome"]: v["tot"] for v in b1["vassoio"]}
        prova("la colazione si paga coi gettoni (caffè 2, brioche 3, biscotto 1)", b1["gettoni"] == 94, b1)
        prova("sorsi e morsi come vuole JJ: caffè 3-4, brioche 6-7, biscotto 2-3", 3 <= tot["Caffè"] <= 4 and 6 <= tot["Brioche"] <= 7 and 2 <= tot["Biscotto"] <= 3, tot)
        await p.evaluate("window.CITTA.gettoni(1)"); await p.click("#bar-menu .scelta[data-voce='Cappuccino']"); await p.wait_for_timeout(300)
        prova("senza gettoni non si ordina, e dice dove vincerne", "Sala giochi" in await p.inner_text("#bar-ordine") and len((await p.evaluate("window.CITTA.bar()"))["vassoio"]) == 3)
        await p.evaluate("window.CITTA.gettoni(94)")
        await usa(p, "tavolini", "I tavolini")
        await p.click("#stanza-carta button:has-text('Siediti al tavolino')"); await p.wait_for_timeout(1200)
        b2 = await p.evaluate("window.CITTA.bar()")
        prova("al tavolino ci si siede davvero, e sul tavolo arriva quello che hai ordinato", b2["seduto"] and b2["y"] < -0.2 and b2["sulTavolo"] == 3, b2)
        n = 0
        while n < 10 and await p.evaluate("window.CITTA.bar().vassoio.some(v=>v.nome==='Caffè')"):
            await p.click("#vassoio button[data-consuma='Caffè']"); await p.wait_for_timeout(250); n += 1
        prova("il caffè si beve a sorsi, e quando è finito sparisce dal tavolo", n == tot["Caffè"] and (await p.evaluate("window.CITTA.bar()"))["sulTavolo"] == 2, [n, tot["Caffè"]])
        await foto(p, "16c2-al-tavolino")
        await usa(p, "recensioni", "La lavagna delle recensioni")
        await p.click("#rec-stelle .scelta >> nth=3"); await p.fill("#rec-testo", "Bella la radio"); await p.click("#rec-manda")
        await p.wait_for_function("document.getElementById('rec-esito').textContent.startsWith('Grazie')", timeout=15000)
        prova("la recensione parte e arriva a chi mi costruisce, con le stelle", any(x.get("testo", "").startswith("⭐ Recensione ★★★★: Bella la radio") for x in parlate))
        prova("andando alla lavagna ci si è alzati dal tavolino", not (await p.evaluate("window.CITTA.bar()"))["seduto"])
        await usa(p, "tavolini", "I tavolini")
        prova("ai tavolini la chat non si apre da sola (è di Twitch, coi suoi cookie)", await p.evaluate("!document.getElementById('chat-bar')"))
        await p.click("#stanza-carta button:has-text('Siediti al tavolino')"); await p.wait_for_timeout(800)
        await p.click("#stanza-carta button:has-text('Apri la chat')"); await p.wait_for_timeout(600)
        prova("nella chat, in alto, ci sono le cose del tavolino da bere e mangiare fra un messaggio e l'altro", await p.evaluate("document.querySelectorAll('#cose-tavolo button').length") == 2)
        await p.click("#cose-tavolo button[data-consuma='Biscotto']"); await p.wait_for_timeout(200)
        prova("un morso dalla chat conta", [v["resta"] for v in (await p.evaluate("window.CITTA.bar()"))["vassoio"] if v["nome"] == "Biscotto"][0] == tot["Biscotto"] - 1)
        src = await p.evaluate("(document.getElementById('chat-bar')||{}).src||''")
        prova("aprendola, è la chat del canale Twitch JJoe_Boy93 incorporata come dice Twitch (parent = il dominio della pagina)", src.startswith("https://www.twitch.tv/embed/jjoe_boy93/chat?parent=jjoeboy93.github.io"), src)
        lib = await p.evaluate("""(()=>{ const f=document.getElementById('chat-bar'); const r=f.getBoundingClientRect(); const fuori=[];
            for(let e=f; e && e!==document.documentElement; e=e.parentElement){ const c=getComputedStyle(e); if(c.transform!=='none'||c.filter!=='none'||+c.opacity<1||c.backdropFilter&&c.backdropFilter!=='none') fuori.push(e.id||e.tagName); }
            const punti=[[0.5,0.5],[0.1,0.9],[0.9,0.9],[0.9,0.1],[0.1,0.1],[0.5,0.97]].map(([x,y])=>document.elementFromPoint(r.left+r.width*x,r.top+r.height*y)===f);
            return {padre:f.parentElement.parentElement===document.body, effetti:fuori, scoperta:punti.every(Boolean), alto:r.height, largo:r.width}; })()""")
        prova("la chat di Twitch sta in uno strato suo: niente la copre e nessun contenitore ha effetti (sennò Twitch spegne lo scrivere)", lib["padre"] and not lib["effetti"] and lib["scoperta"] and lib["alto"] > 600, lib)
        await p.click("#chiudi-twitch"); await p.wait_for_timeout(300)
        prova("«Torna al Café» chiude la chat e si è di nuovo al bar", await p.evaluate("!document.getElementById('strato-twitch') && !document.body.classList.contains('con-twitch')"))
        await usa(p, "caffe", "Offri un caffè")
        await p.wait_for_timeout(1500)
        tc = await p.inner_text("#stanza-carta")
        prova("«offri un caffè» dice che non è ancora acceso (sostieni.json: pronto false), senza pulsanti finti", "Non è ancora acceso" in tc and "☕ Offri" not in tc, tc[:160])
        await foto(p, "16c-cafe")
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3d1c. la Torre a dieci piani (JJ, 4/10): ascensore, scale, la Borsa al 2°, l'attico privato, la terrazza
        await vai(p, "La Torre")
        prova("per terra, nel cerchio azzurro della Torre, c'è l'icona di JJA-VIS", await p.evaluate("window.CITTA.iconaPerTerra()"))
        await usa(p, "ascensore", "L'ascensore")
        prova("l'ascensore ha i dieci piani, e l'attico non si può scegliere", await p.evaluate("document.querySelectorAll('#piani .scelta').length") == 10
              and await p.evaluate("[...document.querySelectorAll('#piani .scelta')].find(b=>b.textContent.startsWith('Attico')).disabled"))
        await p.click("#piani .scelta:has-text('1° piano')")
        await p.wait_for_function("document.getElementById('stanza-nome').textContent==='La Torre · 1° piano' && window.CITTA.cose().length>0", timeout=20000)
        f1 = await foglio(p)
        prova("al 1° piano cosa so fare, coi numeri veri della porta", "42" in f1["testo"] and "4.639" in f1["testo"] and "8.385" in f1["testo"], f1["testo"][:120])
        await usa(p, "scale", "Le scale")
        await p.click("#stanza-carta button:has-text('Sali al 2° piano')")
        await p.wait_for_function("document.getElementById('stanza-nome').textContent==='La Torre · 2° piano' && window.CITTA.cose().length>0", timeout=20000)
        f2 = await foglio(p)
        prova("con le scale si sale: al 2° piano c'è la Borsa, investi, e le stime sono dette stime", "Stime di chi fa questo lavoro" in f2["testo"] and {"lavagna", "tavoli", "bacheca", "ascensore", "scale"} <= set(await p.evaluate("window.CITTA.cose()")), f2["testo"][:120])
        senza = []
        for k in range(3, 8):
            await usa(p, "ascensore", "L'ascensore")
            await p.click(f"#piani .scelta:has-text('{k}° piano')")
            await p.wait_for_function(f"document.getElementById('stanza-nome').textContent==='La Torre · {k}° piano' && window.CITTA.cose().length>0", timeout=20000)
            if set(await p.evaluate("window.CITTA.cose()")) != {"vetrata", "ascensore", "scale"}: senza.append(k)
        prova("i piani dal 3° al 7° ci sono, liberi, con vetrata, ascensore e scale", not senza, senza)
        await usa(p, "ascensore", "L'ascensore")
        await p.click("#piani .scelta:has-text('Terrazza')"); await p.wait_for_timeout(1500)
        tt = await p.evaluate("window.CITTA.sulTetto()")
        prova("dalla terrazza si guarda la città dall'alto: si è sul tetto della Torre", tt["su"] and tt["y"] > 29, tt)
        j = await p.query_selector("#joy"); bb = await j.bounding_box(); cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy - 55, steps=4); await p.wait_for_timeout(4000); await p.mouse.up()
        t2 = await p.evaluate("window.CITTA.sulTetto()")
        prova("sulla terrazza si cammina ma non si cade: si resta dentro il parapetto", t2["su"] and t2["y"] == tt["y"] and (abs(t2["x"] - tt["x"]) + abs(t2["z"] - tt["z"])) > 0.5
              and max(abs(t2["x"] - tt["x"]), abs(t2["z"] - tt["z"])) < 4.2, [tt, t2])
        await foto(p, "16d-terrazza")
        await p.click("#entra"); await p.wait_for_function("document.getElementById('stanza-nome').textContent==='La Torre'", timeout=20000)
        prova("«Scendi» riporta alla Reception", not (await p.evaluate("window.CITTA.sulTetto()"))["su"])
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3d1d. la Sala giochi: si vincono gettoni; la macchinetta non è accesa
        await vai(p, "Sala giochi")
        await usa(p, "macchinetta", "La macchinetta dei gettoni")
        prova("la macchinetta dei gettoni dice che comprarli coi soldi non è ancora acceso", "Non ancora accesa" in await p.inner_text("#stanza-carta"))
        await usa(p, "cab1", "Acchiappa i gettoni")
        g1 = await p.evaluate("window.CITTA.gettoni()")
        await p.click("#stanza-carta button:has-text('Gioca')")
        # 6/10: guardava a 1,5 s se c'era un gettone, e una volta su dieci c'era solo una bomba (escono a caso): si aspetta il gettone
        try:
            await p.wait_for_function("!!document.getElementById('strato-gioco') && document.querySelectorAll('#campo-gioco img').length>0", timeout=15000); gioca_ok = True
        except Exception:
            gioca_ok = False
        prova("al cabinato si gioca: uno strato a tutto schermo coi gettoni da prendere", gioca_ok)
        bar = await p.evaluate("(()=>{ const b=document.querySelector('#strato-gioco .barra-gioco'), n=document.getElementById('gioco-punti'); if(!b||!n) return null; const r=b.getBoundingClientRect(), q=n.getBoundingClientRect(); return {h:r.height, punti:q.height>0&&q.top>=0&&q.bottom<=innerHeight}; })()")
        prova("durante la partita si vedono punti e tempo (la barra c'è, alta, coi punti dentro lo schermo)", bar and bar["h"] > 30 and bar["punti"], bar)
        gc = await p.evaluate("""(()=>{ const G=window.CITTA._gioco, r={};
            for(let i=0;i<5;i++) G.prendi('gettone'); r.cinque=G.punti;
            G.prendi('bomba'); r.dopoBomba=G.punti;
            G.prendi('x2'); r.x2=G.x2(); G.prendi('gettone'); G.prendi('gettone'); r.conX2=G.punti;
            G.prendi('turbo'); r.turbo=G.turbo();
            for(let i=0;i<30;i++) G.prendi('gettone'); r.prima=G.punti; G.fine2(); return r; })()""")
        prova("la bomba fa perdere i gettoni della partita (JJ: «qualche bomba che ti fa perdere le monete guadagnate»)", gc["cinque"] == 5 and gc["dopoBomba"] == 0, gc)
        prova("col ×2 ogni gettone vale doppio, e il turbo si accende", gc["x2"] and gc["conX2"] == 4 and gc["turbo"], gc)
        await p.wait_for_selector("#gioco-classifica", timeout=10000); await p.wait_for_timeout(1500)
        fin = await p.inner_text("#gioco-classifica")
        prova("a fine partita c'è il record, e la classifica o perché non c'è (qui il server è spento)", "record" in fin and ("Classifica" in fin or "non risponde" in fin), fin)
        prova("a fine partita si vincono i gettoni presi, al massimo 25", await p.evaluate("window.CITTA.gettoni()") == g1 + 25 and "ne vinci 25" in await p.inner_text("#gioco-esito"), gc)
        await foto(p, "16e-gioco")
        await p.click("#gioco-esci"); await p.wait_for_timeout(300)
        await p.click("#esci-stanza"); await p.wait_for_timeout(400)

        # 3d2. la Radio sotto l'antenna (JJ, 3/10): le sei stazioni dell'app, e si accendono davvero
        rd = await p.evaluate("window.CITTA.radio()")
        prova("sul palazzo della vecchia Reception c'è l'antenna della Radio, e le sei stazioni sono quelle di partenza dell'app", rd["antenna"]
              and rd["stazioni"] == ["Radio 105", "Radio Italia", "Radio Deejay", "RTL 102.5", "m2o", "Radio Sportiva"] and rd["partenza"] == rd["stazioni"], rd)
        prima = sum(1 for u in richieste if "radio-browser" in u)
        await vai(p, "Radio")
        await usa(p, "radio", "La radio")
        prova("entrando non parte niente da solo: nessuna ricerca prima di toccare una stazione", sum(1 for u in richieste if "radio-browser" in u) == prima)
        await p.click("#radio-stazioni .scelta:has-text('Radio Deejay')")
        await p.wait_for_function("window.CITTA.radio().src!==''", timeout=15000); await p.wait_for_timeout(600)
        rd = await p.evaluate("window.CITTA.radio()")
        prova("toccando Radio Deejay la cerca su Radio Browser e mette il suo flusso https", rd["src"] == "https://radio.finta/deejay.mp3" and rd["inOnda"] == "Radio Deejay"
              and ("In onda" in rd["stato"] or "non l'ha fatta partire" in rd["stato"]), rd)
        await p.click("#radio-stazioni .scelta:has-text('m2o')")
        await p.wait_for_function("document.getElementById('radio-stato') && document.getElementById('radio-stato').textContent.includes('m2o') && !document.getElementById('radio-stato').textContent.startsWith('Cerco')", timeout=15000)
        prova("una stazione solo http non suona e lo dice (niente «la più simile»)", "Non ho trovato «m2o»" in await p.inner_text("#radio-stato"), await p.inner_text("#radio-stato"))
        await p.click("#radio-stazioni .scelta:has-text('RTL 102.5')")
        await p.wait_for_function("document.getElementById('radio-stato').textContent.includes('Non sono riuscito')", timeout=15000)
        prova("se la ricerca non va, lo dice: non è uguale a «non c'è»", "Non sono riuscito a cercare" in await p.inner_text("#radio-stato"))
        await foto(p, "16b-radio")
        await usa(p, "stazioni", "Le tue stazioni")
        await p.fill("#radio-caselle input >> nth=0", "Radio Capital"); await p.press("#radio-caselle input >> nth=0", "Tab"); await p.wait_for_timeout(300)
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("le tue stazioni: una casella si riscrive e resta nel telefono", st.get("radio", [None])[0] == "Radio Capital", st.get("radio"))
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

        # 3g. tre andature (JJ, 3/10): dipende da quanto si spinge il cerchio
        j = await p.query_selector("#joy"); bb = await j.bounding_box()
        cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2; raggio = bb["width"] / 2
        visti = []
        for quanto in (0.25, 0.65, 0.98):
            await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy - raggio * quanto, steps=3)
            await p.wait_for_timeout(300); visti.append(await p.evaluate("window.CITTA.andatura()")); await p.mouse.up(); await p.wait_for_timeout(200)
        prova("tre andature: piano, medio, veloce a seconda di quanto si spinge il cerchio", visti == ["piano", "medio", "veloce"], visti)
        cv = await p.evaluate("[window.CITTA.curvaVerticale(2), window.CITTA.curvaVerticale(25)]")
        prova("lo sguardo in verticale è meno sensibile sui movimenti piccoli (curva, non retta)", cv[0] < 0.004 * 2 * 0.5 and cv[1] <= 0.004 * 25, cv)

        # 4. camminare col cerchio sposta davvero, e i palazzi non si attraversano:
        # davanti al Cinema si spinge avanti, contro la facciata, per tre secondi
        await vai(p, "Cinema"); await p.click("#esci-stanza"); await p.wait_for_timeout(500)
        prima = await p.evaluate("window.CITTA.dove()")
        j = await p.query_selector("#joy"); bb = await j.bounding_box()
        cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy - 50, steps=4)
        await p.wait_for_timeout(3000); await p.mouse.up()
        dopo = await p.evaluate("window.CITTA.dove()")
        prova("il cerchio fa camminare", abs(dopo["x"] - prima["x"]) + abs(dopo["z"] - prima["z"]) > 1, (prima, dopo))
        prova("contro la facciata ci si ferma: non si entra nei muri", not await p.evaluate("window.CITTA.nelMuro()"), dopo)
        await foto(p, "06-camminato")
        # l'albero sulla collinetta, l'acqua, il muretto con la staccionata, le panchine dove sedersi (JJ, 4/10)
        al = await p.evaluate("window.CITTA.albero()"); pa = await p.evaluate("window.CITTA.panchine()")
        import math
        dmin = min(math.hypot(a_["x"] - b_["x"], a_["z"] - b_["z"]) for i, a_ in enumerate(pa) for b_ in pa[i + 1:])
        prova("l'albero sta su una collinetta, circondata dall'acqua, circondata dal muretto con la staccionata", al["collina"]["h"] > 0.5 and al["acqua"][0] <= al["collina"]["r"]
              and al["acqua"][1] < al["muretto"] and al["paletti"] >= 24, al)
        prova("l'acqua arriva fin sotto il muretto: niente pavimento a vista lungo il bordo (JJ, 6/10)", al["acqua"][1] >= al["muretto"] - 0.15, al)
        pe1 = await p.evaluate("window.CITTA._pesci()"); await p.wait_for_timeout(1500); pe2 = await p.evaluate("window.CITTA._pesci()")
        prova("nel laghetto nuotano dei pesci, sotto il pelo dell'acqua e dentro l'anello (JJ, 6/10)", len(pe1) >= 5 and all(al["acqua"][0] <= f["r"] <= al["acqua"][1] and f["y"] < 0.06 for f in pe1 + pe2), pe1)
        prova("…e si muovono", sum(abs(a["x"] - b["x"]) + abs(a["z"] - b["z"]) for a, b in zip(pe1, pe2)) > 0.1, [pe1[:2], pe2[:2]])
        prova("le panchine sono sei, fuori dal muretto e più distanziate (almeno 8 m l'una dall'altra)", len(pa) == 6 and all(math.hypot(b_["x"], b_["z"]) >= 10 for b_ in pa) and dmin >= 8, [pa, dmin])
        await p.evaluate("window.CITTA.siedi(0)"); await p.wait_for_timeout(1200)
        sd = await p.evaluate("window.CITTA.seduto()")
        prova("in panchina ci si siede: più in basso, le gambe in avanti, e resta così", sd["seduto"] and sd["y"] < -0.2 and sd["gamba"] < -1.2, sd)
        await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy + 50, steps=4); await p.wait_for_timeout(1500); await p.mouse.up()
        sd2 = await p.evaluate("window.CITTA.seduto()")
        prova("muovendo il cerchio ci si alza e si cammina", not sd2["seduto"] and sd2["y"] == 0, sd2)
        await foto(p, "06b-panchine")
        prova("nessun errore JavaScript (accesa)", not err, err[:3])
        await ctx.close()

        # 4c. il sedersi delle skin (JJ, 6/10): le skin di Blender piegano il ginocchio, e ognuna ha il bacino sul sedile
        # (0,55 m) qualunque sia la lunghezza delle sue gambe — prima le KayKit si sedevano per terra attraverso la panchina
        for sk in ("base", "realista-uomo", "avventuriera"):
            ctx, p, err = await nuova(b, citta={"skin": sk, "skinMie": ["base", "classica", sk], "corpo": "uomo", "giroVisto": True})
            await p.goto(BASE + "citta.html", timeout=60000)
            await p.wait_for_function(f"window.CITTA && window.CITTA.pronta && window.CITTA.skinTua().skin==={json.dumps(sk)} && window.CITTA.skinTua().ossi===true", timeout=60000)
            await p.evaluate("window.CITTA.siedi(0)"); await p.wait_for_timeout(1200)
            sd = await p.evaluate("window.CITTA.seduto()")
            prova(f"{sk}: seduta, col bacino sul sedile e il ginocchio piegato (lo stinco scende verso terra)",
                  sd["seduto"] and 0.45 <= sd.get("anca", 0) <= 0.6 and abs(sd.get("ginocchio", 0) - sd["anca"]) < 0.12
                  and sd.get("piede", 9) < sd.get("ginocchio", 0) - 0.1, sd)
            j = await p.query_selector("#joy"); bb = await j.bounding_box(); cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
            await p.mouse.move(cx, cy); await p.mouse.down(); await p.mouse.move(cx, cy + 50, steps=4); await p.wait_for_timeout(1500); await p.mouse.up()
            await p.wait_for_timeout(800); sd2 = await p.evaluate("window.CITTA.seduto()")
            prova(f"{sk}: alzandosi il ginocchio torna dritto", not sd2["seduto"] and sd2["y"] == 0 and abs(sd2.get("stinco", 9)) < 0.2, sd2)
            prova(f"{sk}: nessun errore JavaScript", not err, err[:3])
            await ctx.close()

        # 5. di nuovo: il vestito è rimasto, il giro chiuso non si ripete per sempre
        ctx, p, err = await nuova(b, citta={"mestiere": "Sanità", "vestito": "sanita", "pelle": 0, "giro": {"sartoria": True, "reception": True, "bottega": True}, "giroVisto": True})
        await p.goto(BASE + "citta.html", timeout=60000)
        await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CITTA.fotogrammi()>3", timeout=30000)
        prova("chi ha già fatto il giro non lo rivede", await p.evaluate("document.getElementById('giro').hidden"))
        prova("chi aveva fatto il giro alla vecchia Reception non lo rifà: vale per la Torre", "Giro chiuso" in await p.inner_text("#giro") or await p.evaluate("document.getElementById('giro').hidden"))
        await vai(p, "La Torre")
        f_ = await foglio(p)
        prova("senza nome, la Reception nella Torre dice di darne uno nella pagina, senza un collegamento che porti fuori", "nella pagina" in f_["testo"] and not any(h.startswith("index.html") for h in f_["link"]), f_["link"])
        prova("nessun errore JavaScript (ritorno)", not err, err[:3])
        await ctx.close()

        # 5b. l'aspetto scelto nella pagina colora la città e la sfera (JJ, 3/10)
        ctx, p, err = await nuova(b, profilo={"nome": "Ada", "tema": "naturale"})
        await p.goto(BASE + "citta.html", timeout=60000)
        await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CITTA.fotogrammi()>3", timeout=60000)
        sf = await p.evaluate("window.CITTA.sfera()")
        prova("aspetto «naturale»: la città e la sfera prendono i suoi colori", sf == {"tema": "naturale", "colori": ["34d399", "059669", "fbbf24"]}
              and await p.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--accento').trim()") == "#34D399", sf)
        await foto(p, "19-aspetto-naturale")
        prova("nessun errore JavaScript (aspetto)", not err, err[:3])
        await ctx.close()

        # 6. senza WebGL: la città diventa un elenco e funziona lo stesso
        ctx, p, err = await nuova(b, webgl=False)
        await p.goto(BASE + "citta.html", timeout=60000)
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
