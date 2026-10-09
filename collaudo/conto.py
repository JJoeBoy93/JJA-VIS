"""Collaudo dell'account nella città (JJ, 5/10: «ognuno un suo account, il mio può fare tutto senza gettoni»).

    python3 collaudo/conto.py citta.html

Google e il server sono finti: la libreria di Google è sostituita da un bottone che chiama la callback con un biglietto,
il server (/conto/*) è un dizionario in memoria che risponde come JJA-VIS-Porta/citta/conti.js (che ha la sua prova vera,
collaudo-conti.mjs contro workerd). Qui si prova la città: il tasto, il pannello, l'età, i gettoni e le skin che passano
dal server, l'amministratore che non spende, uscire, cancellarsi. Nato il 5/10 (Athena). Verde = tutte le prove.
"""
import json, asyncio, sys, os, re
from playwright.async_api import async_playwright

CITTA = os.path.abspath(sys.argv[1]); CASA = os.path.dirname(CITTA)
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
SRV = "https://jjavis-citta.finta.workers.dev"
GIS = re.compile(r"^https://accounts\.google\.com/gsi/client")
FINTA_GIS = """window.google={accounts:{id:{_cb:null,initialize(o){this._cb=o.callback; window.__gisId=o.client_id;},
  renderButton(el,o){const b=document.createElement('button');b.id='gis-finto';b.textContent='Accedi con Google (finto)';
  b.onclick=()=>this._cb({credential:window.__biglietto||'buono'});el.appendChild(b);}}}};"""

prove = []
def prova(nome, ok, dettaglio=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {dettaglio}" if dettaglio and not ok else ""))

class Server:
    def __init__(s, admin=False): s.conti, s.sessioni, s.chiamate, s.admin, s.uscite, s.codici = {}, {}, [], admin, [], {}
    def vedi(s, c): return {**c, "admin": s.admin}
    async def __call__(s, route):
        req = route.request; via = req.url[len(SRV):].split("?")[0]
        h = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "Content-Type, Authorization", "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}
        if req.method == "OPTIONS": return await route.fulfill(status=204, headers=h)
        corpo = json.loads(req.post_data or "{}") if req.method == "POST" else {}
        s.chiamate.append((via, corpo))
        def ok(d, st=200): return route.fulfill(status=st, body=json.dumps(d), content_type="application/json", headers=h)
        if via == "/conto/mail/codice":
            s.codici[corpo["mail"]] = "424242"; return await ok({"fatto": True})
        if via == "/conto/mail/entra":
            if s.codici.get(corpo.get("mail")) != corpo.get("codice"): return await ok({"no": "codice", "restano": 4}, 401)
            s.conti["m1"] = {"nome": "", "mail": corpo["mail"], "soprannome": None, "gettoni": 100, "skin": [], "portato": False}
            s.sessioni["t" * 64] = "m1"
            return await ok({"token": "t" * 64, "conto": s.vedi(s.conti["m1"]), "nuovo": True})
        if via == "/conto/google":
            if corpo.get("credential") != "buono": return await ok({"no": "google"}, 401)
            nuovo = "g1" not in s.conti
            if nuovo and corpo.get("eta14") is not True: return await ok({"no": "eta"}, 400)
            if nuovo: s.conti["g1"] = {"nome": "Anna Prova", "mail": "anna@prova.it", "soprannome": None, "gettoni": 100, "skin": [], "portato": False}
            s.sessioni["t" * 64] = "g1"
            return await ok({"token": "t" * 64, "conto": s.vedi(s.conti["g1"]), "nuovo": nuovo})
        tok = (req.headers.get("authorization") or "").replace("Bearer ", "")
        if via == "/conto/esci": s.uscite.append((via, corpo, tok))
        uid = s.sessioni.get(tok)
        if not uid or uid not in s.conti: return await ok({"no": "sessione"}, 401)
        c = s.conti[uid]
        if via == "/conto" : return await ok({"conto": s.vedi(c)})
        if via == "/conto/porta":
            if not c["portato"]: c["gettoni"] = max(c["gettoni"], min(1000, corpo.get("gettoni", 0))); c["skin"] = list(dict.fromkeys(c["skin"] + corpo.get("skin", []))); c["portato"] = True
            return await ok({"conto": s.vedi(c)})
        if via == "/conto/spendi":
            if s.admin: return await ok({"conto": s.vedi(c)})
            if c["gettoni"] < corpo["n"]: return await ok({"no": "pochi", "conto": s.vedi(c)}, 409)
            c["gettoni"] -= corpo["n"]; return await ok({"conto": s.vedi(c)})
        if via == "/conto/guadagna": c["gettoni"] += corpo["n"]; return await ok({"conto": s.vedi(c), "dati": corpo["n"]})
        if via == "/conto/skin":
            if corpo["id"] not in c["skin"]:
                if not s.admin:
                    if c["gettoni"] < corpo["prezzo"]: return await ok({"no": "pochi", "conto": s.vedi(c)}, 409)
                    c["gettoni"] -= corpo["prezzo"]
                c["skin"].append(corpo["id"])
            return await ok({"conto": s.vedi(c)})
        if via == "/conto/esci": s.sessioni.clear(); return await ok({"fatto": True})
        if via == "/conto/elimina": s.conti.pop(uid, None); s.sessioni.clear(); return await ok({"fatto": True})
        return await ok({"no": "via"}, 404)

def instradatore(server):
    async def instrada(route):
        u = route.request.url
        if u.startswith(BASE + "insieme.json"):
            return await route.fulfill(body=json.dumps({"indirizzo": SRV.replace("https:", "wss:") + "/entra"}), content_type="application/json")
        if u.startswith(SRV + "/conto"): return await server(route)
        if GIS.match(u): return await route.fulfill(body=FINTA_GIS, content_type="text/javascript")
        if u.startswith(BASE):
            f = os.path.join(CASA, u[len(BASE):].split("#")[0].split("?")[0] or "index.html")
            if os.path.isfile(f):
                tipo = "text/html" if f.endswith(".html") else "text/javascript" if f.endswith(".js") else "application/octet-stream" if f.endswith(".glb") else "image/png" if f.endswith(".png") else "application/manifest+json" if f.endswith(".webmanifest") else "application/json"
                return await route.fulfill(body=open(f, "rb").read(), content_type=tipo)
            return await route.fulfill(status=404, body="")
        return await route.abort()
    return instrada

async def nuova(b, server, prima=None):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
    await ctx.route("**/*", instradatore(server))
    await ctx.route_web_socket(re.compile(r"^wss://jjavis-citta\.finta"), lambda ws: None)   # gli altri non c'entrano qui
    if prima: await ctx.add_init_script(prima)
    p = await ctx.new_page(); errori = []
    p.on("pageerror", lambda e: errori.append(str(e)))
    p.on("console", lambda m: errori.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text else None)
    await p.goto(BASE + "citta.html", timeout=90000)
    await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CONTO_PROVA", timeout=120000)
    return ctx, p, errori

st = lambda p: p.evaluate("window.CONTO_PROVA.stato()")

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

        # 1. un utente: il telefono ha 261 gettoni e il Cavaliere
        srv = Server()
        ctx, p, err = await nuova(b, srv, "if(!sessionStorage.getItem('gia')){sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-citta',JSON.stringify({gettoni:261,skinMie:['base','classica','cavaliere']}));}")
        S = await st(p)
        prova("senza account il tasto dice «Accedi con Google» e i gettoni sono quelli del telefono", "Accedi con Google" in S["tasto"] and S["gettoni"] == 261 and not S["conto"], S)
        # 6/10, JJ: «l'account va fatto quando entri nella città, non devi schiacciare tu accedi»
        try:
            await p.wait_for_selector("#conto-eta", state="visible", timeout=15000); aperto = True
        except Exception:
            aperto = False
        prova("appena entri in città senza account, il pannello dell'account si apre da solo", aperto)
        prova("il pannello spiega cosa sa Google e cosa resta a JJA-VIS", "Google ci dice solo chi sei" in await p.inner_text("#conto"))
        prova("senza «ho almeno 14 anni» il bottone di Google non c'è", await p.locator("#gis-finto").count() == 0)
        await p.check("#conto-eta"); await p.wait_for_selector("#gis-finto", timeout=10000)
        prova("con la casella spuntata compare il bottone, col nostro ID client", await p.evaluate("window.__gisId") == "644831505498-sb1lrkalu9maun2f8vcv2e7l3au31akm.apps.googleusercontent.com")
        await p.click("#gis-finto")
        await p.wait_for_function("window.CONTO_PROVA.stato().conto!==null", timeout=10000)
        S = await st(p)
        g = next((c for v, c in srv.chiamate if v == "/conto/google"), {})
        prova("entrando, al server va il biglietto di Google con l'età", g.get("credential") == "buono" and g.get("eta14") is True, g)
        porta = next((c for v, c in srv.chiamate if v == "/conto/porta"), None)
        prova("al primo accesso il telefono porta i suoi gettoni e le sue skin", porta == {"gettoni": 261, "skin": ["base", "classica", "cavaliere"]}, porta)
        prova("ora i gettoni sono quelli dell'account, e il tasto dice chi sei", S["gettoni"] == 261 and "Anna Prova" in S["tasto"] and "amministratore" not in S["tasto"], S)
        prova("il token della sessione resta nel telefono", len(await p.evaluate("localStorage.getItem('jjavis-conto')") or "") == 64)
        ok = await p.evaluate("window.CONTO_PROVA.spendi(61)"); await p.wait_for_timeout(500)
        prova("spendere passa dal server: scala lì", ok and srv.conti["g1"]["gettoni"] == 200 and (await st(p))["gettoni"] == 200, srv.conti["g1"])
        ok = await p.evaluate("window.CONTO_PROVA.spendi(5000)")
        prova("più gettoni di quelli che hai: no, come prima", ok is False)
        await p.evaluate("window.CONTO_PROVA.guadagna(150)"); await p.wait_for_timeout(500)
        gu = [c["n"] for v, c in srv.chiamate if v == "/conto/guadagna"]
        prova("vincere passa dal server, a pezzi da 100 al massimo", gu == [100, 50] and srv.conti["g1"]["gettoni"] == 350, gu)
        await p.reload(); await p.wait_for_function("window.CONTO_PROVA && window.CONTO_PROVA.stato().conto!==null", timeout=60000)
        prova("ricaricando la pagina si resta dentro, coi gettoni del server", (await st(p))["gettoni"] == 350)
        await p.click("#conto-tasto"); await p.click("#conto button:has-text('Esci')"); await p.wait_for_timeout(500)
        S = await st(p)
        prova("«Esci»: fuori dall'account, token tolto dal telefono", not S["conto"] and "Accedi" in S["tasto"] and not await p.evaluate("localStorage.getItem('jjavis-conto')"), S)
        esci = [h for v, c, h in srv.uscite]
        prova("…e il server lo sa: «esci» arriva col token, quella sessione non vale più", esci == ["t" * 64] and not srv.sessioni, esci)
        await p.check("#conto-eta"); await p.wait_for_selector("#gis-finto"); await p.click("#gis-finto")
        await p.wait_for_function("window.CONTO_PROVA.stato().conto!==null", timeout=10000)
        prova("rientrando non si riportano i gettoni una seconda volta", len([1 for v, c in srv.chiamate if v == "/conto/porta"]) == 1)
        await p.click("#conto button:has-text('Cancella')")
        prova("cancellare chiede conferma", "Sicuro" in await p.inner_text("#conto"))
        await p.click("#conto button:has-text('Sicuro')"); await p.wait_for_timeout(500)
        prova("al secondo tocco l'account sparisce dal server e dal telefono", "g1" not in srv.conti and not (await st(p))["conto"] and "cancellato" in await p.inner_text("#esito-conto"))
        prova("nessun errore JavaScript (utente)", not err, err[:3])
        await ctx.close()

        # 2. l'amministratore
        srv = Server(admin=True)
        ctx, p, err = await nuova(b, srv, "if(!sessionStorage.getItem('gia')){sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-citta',JSON.stringify({gettoni:261,eta14:true}));}")
        await p.wait_for_selector("#gis-finto", timeout=15000); await p.click("#gis-finto")
        await p.wait_for_function("window.CONTO_PROVA.stato().conto!==null", timeout=10000)
        S = await st(p)
        prova("l'amministratore lo dice il tasto (👑) e il pannello", "👑" in S["tasto"] and "amministratore" in S["tasto"] and "non spendi gettoni" in await p.inner_text("#conto"), S)
        prova("all'amministratore tutte le skin sono sue", {"base", "classica", "realista-uomo", "realista-donna", "avventuriera", "cavaliere"} <= set(S["skinMie"]), S["skinMie"])
        ok = await p.evaluate("window.CONTO_PROVA.spendi(5000)"); await p.wait_for_timeout(300)
        prova("l'amministratore «spende» 5000 gettoni: va bene, e ne ha ancora 261", ok is True and (await st(p))["gettoni"] == 261 and not any(v == "/conto/spendi" for v, c in srv.chiamate), (await st(p))["gettoni"])
        prova("nessun errore JavaScript (amministratore)", not err, err[:3])
        await ctx.close()

        # 2b. «Più tardi»: si chiude, e in questa visita non torna
        srv = Server()
        ctx, p, err = await nuova(b, srv)
        await p.wait_for_selector("#conto button:has-text('Più tardi')", state="visible", timeout=15000)
        await p.click("#conto button:has-text('Più tardi')"); await p.reload()
        await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CONTO_PROVA", timeout=120000); await p.wait_for_timeout(2500)
        prova("«Più tardi»: il pannello si chiude e, ricaricando, in questa visita non si riapre", not await p.is_visible("#conto"))
        await ctx.close()

        # 2c. senza Google: la mail e il codice di 6 cifre (JJ, 6/10)
        srv = Server()
        ctx, p, err = await nuova(b, srv, "if(!sessionStorage.getItem('gia')){sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-citta',JSON.stringify({eta14:true}));}")
        await p.wait_for_selector("#conto-mail", state="visible", timeout=15000)
        prova("con la casella spuntata, sotto Google c'è l'accesso con la mail", True)
        await p.fill("#conto-mail", "gino@prova.it"); await p.click("#conto button:has-text('Mandami il codice')")
        await p.wait_for_selector("#conto-codice", timeout=10000)
        prova("«Mandami il codice»: il server lo manda a quella mail, e la città chiede il codice", srv.codici.get("gino@prova.it") and "gino@prova.it" in await p.inner_text("#esito-conto"))
        await p.fill("#conto-codice", "000000"); await p.click("#conto button:has-text('Entra')"); await p.wait_for_timeout(500)
        prova("un codice sbagliato: lo dice, coi tentativi che restano", "sbagliato" in await p.inner_text("#esito-conto") and not (await st(p))["conto"])
        await p.fill("#conto-codice", srv.codici["gino@prova.it"]); await p.click("#conto button:has-text('Entra')")
        await p.wait_for_function("window.CONTO_PROVA.stato().conto!==null", timeout=10000)
        S = await st(p)
        prova("col codice giusto si entra: account aperto, token nel telefono", S["conto"]["mail"] == "gino@prova.it" and len(await p.evaluate("localStorage.getItem('jjavis-conto')") or "") == 64, S)
        altri_err = [e for e in err if "status of 401" not in e]   # il 401 del codice sbagliato messo apposta: il browser lo annota sempre
        prova("nessun errore JavaScript (mail; il 401 del codice sbagliato è voluto)", not altri_err, altri_err[:3])
        await ctx.close()

        # 3. la sessione scaduta: si dice, non si tace
        srv = Server()
        ctx, p, err = await nuova(b, srv, "if(!sessionStorage.getItem('gia')){sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-conto','x'.repeat(64));}")
        await p.wait_for_timeout(1500)
        S = await st(p)
        prova("con una sessione che il server non riconosce si esce, e il pannello lo dice", not S["conto"] and not await p.evaluate("localStorage.getItem('jjavis-conto')"), S)
        await p.click("#conto-tasto")
        prova("…con «la sessione è scaduta»", "scaduta" in await p.inner_text("#esito-conto"))
        await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} prove"); print("VERDE" if all(prove) else "ROSSO")

asyncio.run(main())
