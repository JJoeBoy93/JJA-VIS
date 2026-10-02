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

async def instrada(route):
    u = route.request.url
    if u.startswith(BASE):
        nome = u[len(BASE):].split("#")[0].split("?")[0] or "index.html"
        f = os.path.join(CASA, nome)
        if os.path.isfile(f):
            tipo = "text/html" if f.endswith(".html") else "text/javascript" if f.endswith(".js") else "application/json"
            return await route.fulfill(body=open(f, "rb").read(), content_type=tipo)
        return await route.fulfill(status=404, body="")
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
    return await p.evaluate("""()=>({aperto:document.getElementById('foglio').classList.contains('aperto'),
      titolo:(document.getElementById('foglio-titolo')||{}).textContent||'',
      link:[...document.querySelectorAll('#foglio a')].map(a=>a.getAttribute('href')),
      testo:document.getElementById('foglio-dentro').innerText})""")

async def vai(p, nome, attesa=60000):
    await p.click("#vai")
    await p.click(f'#foglio .elenco-vai button:has-text({json.dumps(nome)})')
    await p.wait_for_function(f"document.getElementById('foglio').classList.contains('aperto') && (document.getElementById('foglio-titolo')||{{}}).textContent==={json.dumps(nome)}", timeout=attesa)

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None,
                                     args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

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
        await foto(p, "01-ingresso")

        # 2. il mestiere della pagina arriva in Sartoria, il vestito segue ma resta libero
        await vai(p, "Sartoria")
        f = await foglio(p)
        prova("Sartoria si apre camminando", f["aperto"])
        prova("il mestiere della pagina è già scelto", await p.evaluate("[...document.querySelectorAll('#foglio .scelta')].some(b=>b.textContent==='Guida turistica'&&b.getAttribute('aria-pressed')==='true')"))
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("senza scegliere, il vestito è quello del mestiere", st.get("vestito") == "guida", st)
        await p.wait_for_timeout(900); await foto(p, "02-sartoria-guida")
        await p.click('#foglio .scelta >> text="Creator"')  # esatto: «Creator o gamer» è il mestiere
        await p.click("#foglio .scelta:has-text('Corriere o autista')")
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("cambio mestiere: il vestito scelto resta (non è obbligatorio vestirsi da lavoro)", st.get("vestito") == "creator" and st.get("mestiere") == "Corriere o autista", st)
        await p.click("#foglio .tinta[aria-label='tono della pelle 4']")
        st = await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')||'{}')")
        prova("la pelle si salva", st.get("pelle") == 3, st)
        await p.wait_for_timeout(900); await foto(p, "03-sartoria-creator")
        await p.click("#foglio button:has-text('Fatto')")
        prova("Fatto chiude il foglio", not (await foglio(p))["aperto"])
        prova("il giro segna la Sartoria", await p.evaluate("document.querySelectorAll('#giro .f.fatta').length===1"))

        # 3. ogni luogo: si apre e ogni link interno porta a un id vero della pagina
        nomi = ["Reception", "Bottega", "La Forgia", "La Torre", "L'Albero della Vita", "Piazza delle voci", "Cinema", "Borsa", "Athena Trasporti", "Lotto libero", "Sala giochi"]
        rotti = []
        for n in nomi:
            await vai(p, n)
            f = await foglio(p)
            for h in f["link"]:
                if h.startswith("index.html#"):
                    k = h.split("#", 1)[1]
                    if k not in SCHEDE and k not in ID_PAGINA: rotti.append((n, h))
                elif not h.startswith("https://jjoeboy93.github.io/"): rotti.append((n, h))
            if n == "Reception": prova("la Reception saluta col nome dato nella pagina", "Ettore" in f["testo"], f["testo"][:80])
            if n == "Bottega":
                await foto(p, "04-bottega")
                prima = await p.evaluate("(document.querySelector('#foglio .prodotto h3')||{}).textContent")
                prova("in Bottega il primo prodotto segue il mestiere (corriere → Athena Trasporti)", prima == "Il sito di Athena Trasporti", prima)
            if n == "L'Albero della Vita": prova("l'albero dice che la foglia d'oro è di Ettore", "Ettore" in f["testo"])
            await p.click("#chiudi")
        prova("tutti i link dei palazzi portano a un posto che esiste", not rotti, rotti)
        prova("il giro è chiuso dopo Sartoria, Reception e Bottega", "Giro chiuso" in await p.inner_text("#giro"))
        await p.wait_for_timeout(500); await foto(p, "05-dopo-il-giro")

        # 4. camminare col cerchio sposta davvero, e i palazzi non si attraversano:
        # davanti alla Borsa si spinge avanti, contro la facciata, per tre secondi
        await vai(p, "Borsa"); await p.click("#chiudi")
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
        await p.click("#riserva-elenco button:has-text('Bottega')")
        f = await foglio(p)
        prova("dall'elenco la Bottega si apre", f["aperto"] and f["titolo"] == "Bottega")
        await foto(p, "07-senza-3d")
        prova("nessun errore JavaScript (senza 3D)", not [e for e in err if "WebGL" not in e], err[:3])
        await ctx.close()
        await b.close()

    rossi = [n for n, ok in prove if not ok]
    print(f"\n{len(prove) - len(rossi)}/{len(prove)} prove")
    print("VERDE" if not rossi else "ROSSO")

asyncio.run(main())
