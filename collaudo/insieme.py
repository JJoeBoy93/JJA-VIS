"""Collaudo della città insieme: si vedono gli altri, col soprannome sopra, e ci si scrive (JJ, 5 ottobre 2026: «non è
una piazza... è la città»).

    python3 collaudo/insieme.py citta.html

Il server vero (worker jjavis-citta sull'account di JJA-VIS, sorgente in JJA-VIS-Porta/citta) qui è finto:
Playwright prende il WebSocket e risponde lui, così si prova cosa fa la città quando arriva qualcuno, quando si
muove, scrive, se ne va, quando la città è piena, il server non risponde o non è ancora acceso. Il server vero ha la sua
prova (filtro compreso): JJA-VIS-Porta/citta/collaudo.mjs, contro workerd. Nato il 5/10 (Athena).
Verde = 0 errori JavaScript e tutte le prove passate.
"""
import json, asyncio, sys, os, time
from playwright.async_api import async_playwright

CITTA = os.path.abspath(sys.argv[1]); CASA = os.path.dirname(CITTA)
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
PORTA = "https://jjavis-porta.19-jjardito93.workers.dev"
INSIEME = "wss://jjavis-citta.finta.workers.dev/entra"   # finto: quello vero sta in insieme.json dopo la consegna
CAMPI = {"skin", "vestito", "corpo", "pelle", "capelli", "capelliColore", "colore", "pantaloni"}
BRUNO = {"skin": "classica", "vestito": "corriere", "corpo": "uomo", "pelle": 2, "capelli": "corti", "capelliColore": 0, "colore": None, "pantaloni": None}

prove = []
def prova(nome, ok, dettaglio=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {dettaglio}" if dettaglio and not ok else ""))

CONTO_SRV = "https://jjavis-citta.finta.workers.dev/conto"
def instradatore(indirizzo, conto=None):
    async def instrada(route):
        u = route.request.url
        if u.startswith(CONTO_SRV):   # l'account (6/10: «niente account, niente altri»): GET /conto risponde come il server
            h = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "Content-Type, Authorization", "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}
            if route.request.method == "OPTIONS": return await route.fulfill(status=204, headers=h)
            if not conto: return await route.fulfill(status=401, body='{"no":"sessione"}', content_type="application/json", headers=h)
            return await route.fulfill(body=json.dumps({"conto": {"nome": "Ada Prova", "mail": "ada@prova.it", "soprannome": None, "gettoni": 100, "skin": [], "portato": True, "admin": conto == "admin"}}), content_type="application/json", headers=h)
        if u.startswith(BASE + "insieme.json"):
            return await route.fulfill(body=json.dumps({"indirizzo": indirizzo}), content_type="application/json")
        if u.startswith(BASE):
            f = os.path.join(CASA, u[len(BASE):].split("#")[0].split("?")[0] or "index.html")
            if os.path.isfile(f):
                tipo = "text/html" if f.endswith(".html") else "text/javascript" if f.endswith(".js") else "application/octet-stream" if f.endswith(".glb") else "image/png" if f.endswith(".png") else "application/manifest+json" if f.endswith(".webmanifest") else "application/json"
                return await route.fulfill(body=open(f, "rb").read(), content_type=tipo)
            return await route.fulfill(status=404, body="")
        if u.startswith(PORTA + "/vetrina"):
            return await route.fulfill(body='{"attrezzi":42}', content_type="application/json", headers={"Access-Control-Allow-Origin": "https://jjoeboy93.github.io"})
        return await route.abort()
    return instrada

class Finta:
    """il server finto: modo «uno» (c'è già Bruno), «piena» (4001), «muta» (si chiude subito)"""
    def __init__(s, modo): s.modo, s.arrivati, s.chiusi, s.linee, s.esito_segnala = modo, [], 0, [], {"ok": True, "fatto": ["telegram", "mail"]}
    def __call__(s, ws):
        s.linee.append(ws)
        if s.modo == "piena": asyncio.ensure_future(ws.close(code=4001, reason="piena")); return
        if s.modo == "muta": asyncio.ensure_future(ws.close(code=1011, reason="giù")); return
        def msg(m):
            if m == "ping": ws.send("pong"); return
            d = json.loads(m); d["_t"] = time.monotonic(); s.arrivati.append(d)
            if d.get("t") == "ciao":
                ws.send(json.dumps({"t": "tu", "id": "io1", "n": d.get("n"), "max": 40, "altri": [{"id": "b1", "n": "Bruno", "a": BRUNO, "p": {"x": 3, "z": 15, "r": 0, "y": 0, "s": 0, "l": ""}}]}))
            if d.get("t") == "di":   # il server rimanda il messaggio anche a chi l'ha scritto
                ws.send(json.dumps({"t": "di", "id": "io1", "n": "Ada", "x": d["x"], "ora": 1}))
            if d.get("t") == "modera":
                ws.send(json.dumps({"t": "moderato", "ok": True, "azione": d["azione"], "n": d.get("n") or "Bruno"}))
            if d.get("t") == "moderati":   # chi è bloccato o zittito: prima Molesto, dopo lo sblocco nessuno
                sbloccato = any(m.get("t") == "modera" and m.get("azione") == "sblocca" for m in s.arrivati)
                ws.send(json.dumps({"t": "moderati", "ok": True, "elenco": [] if sbloccato else [{"uid": "g:42", "soprannome": "Molesto", "nome": "M", "bloccato": True, "zitto_fino": 0}]}))
            if d.get("t") == "segnala":   # il server risponde come quello vero; s.esito_segnala decide come va
                ws.send(json.dumps({"t": "segnalato", **s.esito_segnala}))
        def chiuso(c, r): s.chiusi += 1
        ws.on_message(msg); ws.on_close(chiuso)
    def manda(s, d): s.linee[-1].send(json.dumps(d))

async def nuova(b, modo, piccola=False, soprannome=None, indirizzo=INSIEME, conto="utente"):
    ctx = await b.new_context(viewport={"width": 120, "height": 220} if piccola else {"width": 390, "height": 844}, device_scale_factor=1 if piccola else 2, is_mobile=True, has_touch=True)
    await ctx.route("**/*", instradatore(indirizzo, conto))
    await ctx.add_init_script("sessionStorage.setItem('jjavis-conto-dopo','1')")   # 6/10: il pannello dell'account che si apre all'ingresso qui non serve (lo prova conto.py)
    if conto: await ctx.add_init_script("localStorage.setItem('jjavis-conto','c'.repeat(64));")
    f = Finta(modo); await ctx.route_web_socket(INSIEME, f)
    if soprannome: await ctx.add_init_script(f"if(!sessionStorage.getItem('gia')){{sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-citta',JSON.stringify({{soprannome:{json.dumps(soprannome)},regole:true}}));}}")
    p = await ctx.new_page(); errori = []
    p.on("pageerror", lambda e: errori.append(str(e)))
    p.on("console", lambda m: errori.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text else None)
    await p.goto(BASE + "citta.html", timeout=60000)
    await p.wait_for_function("window.CITTA && window.CITTA.pronta && window.CITTA.fotogrammi()>3", timeout=90000)
    return ctx, p, f, errori

async def altri(p): return await p.evaluate("window.CITTA.altri()")
async def aspetta(p, cond, ms=20000):
    try: await p.wait_for_function(f"(()=>{{const A=window.CITTA.altri(); return {cond};}})()", timeout=ms); return True
    except Exception: return False

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

        # 1. si entra col soprannome
        ctx, p, f, err = await nuova(b, "uno")
        await p.wait_for_timeout(1500)
        A = await altri(p)
        prova("senza soprannome non ci si collega agli altri: il tasto lo chiede, e nessuna linea si apre", A["stato"] == "nome" and "soprannome" in A["chip"] and not f.linee, (A, len(f.linee)))
        await p.click("#altri"); await p.wait_for_selector("#insieme-soprannome")
        prova("toccandolo si apre il pannello, che chiede un soprannome e non il nome", "Non il tuo nome vero" in await p.inner_text("#insieme"))
        await p.fill("#insieme-soprannome", "ab"); await p.click("#insieme button:has-text('Entra con gli altri')")
        prova("un soprannome troppo corto non va, e lo dice", "non va" in await p.inner_text("#esito-insieme") and not f.linee)
        await p.fill("#insieme-soprannome", "  Ada  "); await p.click("#insieme button:has-text('Entra con gli altri')")
        prova("senza accettare le regole non si entra, e lo dice (6/10, Play Store)", "accetta le regole" in await p.inner_text("#esito-insieme") and not f.linee)
        prova("le regole si aprono da lì (regole.html)", await p.locator("#insieme a[href='regole.html']").count() >= 1)
        await p.check("#insieme-regole"); await p.click("#insieme button:has-text('Entra con gli altri')")
        prova("col soprannome si entra", await aspetta(p, "A.stato==='dentro'"), await altri(p))
        prova("il soprannome e le regole accettate restano nel telefono", await p.evaluate("(()=>{const c=JSON.parse(localStorage.getItem('jjavis-citta'));return c.soprannome==='Ada'&&c.regole===true;})()"))
        ciao = next((m for m in f.arrivati if m.get("t") == "ciao"), None)
        prova("al saluto va anche il token dell'account", ciao and ciao.get("tok") == "c" * 64, ciao and ciao.get("tok"))
        prova("al saluto passano il soprannome (ripulito), l'aspetto (otto campi, niente nome vero) e dove sei: in città",
              ciao and ciao["n"] == "Ada" and set(ciao["a"]) == CAMPI and ciao["p"]["l"] == "" and abs(ciao["p"]["z"] - 18) < 0.5, ciao)
        await aspetta(p, "A.visti.length===1&&A.visti[0].inScena", 10000)   # almeno un fotogramma dopo l'arrivo
        A = await altri(p); v = A["visti"]
        prova("il tasto dice quanti siete", "siete 2" in A["chip"], A["chip"])
        prova("chi c'era già si vede, in città, dove sta", len(v) == 1 and v[0]["dentro"] == "citta" and abs(v[0]["x"] - 3) < 0.3 and abs(v[0]["z"] - 15) < 0.3, v)
        prova("sopra la testa ha il suo soprannome, ai piedi l'anello", v and v[0]["n"] == "Bruno" and v[0]["cartello"] and v[0]["anello"], v)
        prova("nel pannello si vede chi c'è", "Bruno" in await p.inner_text("#insieme-gente"))
        prova("un utente qualsiasi non ha «Zittisci» e «Blocca»", await p.locator("#insieme-modera").count() == 0)
        # la chat
        await p.fill("#insieme-scrivi", "Ciao a tutti"); await p.click("#insieme-manda"); await p.wait_for_timeout(600)
        di = [m for m in f.arrivati if m.get("t") == "di"]
        prova("scrivendo, il messaggio va al server", di and di[-1]["x"] == "Ciao a tutti", di[-1:])
        prova("e torna nella chat come tuo", (await altri(p))["chat"][-1:] == [{"n": "Ada", "x": "Ciao a tutti", "mio": True}], (await altri(p))["chat"])
        await p.click("#insieme-scrivi"); await p.keyboard.down("w"); await p.wait_for_timeout(1500); await p.keyboard.up("w"); await p.wait_for_timeout(300)   # tenuto premuto: camminerebbe un metro e più
        prova("scrivendo «w» nella chat non si cammina", await p.evaluate("window.CITTA.dove()") == {"x": 0, "z": 18}, await p.evaluate("window.CITTA.dove()"))
        await p.fill("#insieme-scrivi", "")
        f.manda({"t": "di", "id": "b1", "n": "Bruno", "x": "Ciao Ada, ci vediamo al Café?", "ora": 2})
        prova("un messaggio di Bruno arriva nella chat", await aspetta(p, "A.chat.some(c=>c.n==='Bruno'&&!c.mio)", 5000), (await altri(p))["chat"])
        prova("e gli compare il fumetto sopra la testa", await aspetta(p, "A.visti[0].fumetto===true", 3000))
        prova("il fumetto se ne va da solo (7 s), resta il soprannome", await aspetta(p, "A.visti[0].fumetto===false&&A.visti[0].cartello", 15000))
        await p.click("#insieme-gente button:has-text('Bruno')")
        prova("toccando il suo soprannome compaiono «Silenzia» e «Segnala»", await p.locator("#insieme-azioni button:has-text('Silenzia')").count() == 1 and await p.locator("#insieme-azioni button:has-text('Segnala')").count() == 1)
        # il segnala (6/10)
        await p.click("#insieme-azioni button:has-text('Segnala')")
        n0 = len([m for m in f.arrivati if m.get("t") == "segnala"])
        await p.click("#insieme-segnala button:has-text('Manda la segnalazione')"); await p.wait_for_timeout(300)
        prova("segnalare senza motivo: lo chiede, e non parte niente", "Scegli un motivo" in await p.inner_text("#esito-insieme") and len([m for m in f.arrivati if m.get("t") == "segnala"]) == n0)
        await p.click("#insieme-segnala button[data-motivo='molestie']"); await p.fill("#insieme-nota", "mi chiede dove abito")
        await p.click("#insieme-segnala button:has-text('Manda la segnalazione')"); await p.wait_for_timeout(700)
        sg = [m for m in f.arrivati if m.get("t") == "segnala"]
        prova("la segnalazione parte: chi, motivo, nota e le sue frasi che hai visto", sg and sg[-1]["id"] == "b1" and sg[-1]["motivo"] == "molestie" and sg[-1]["nota"] == "mi chiede dove abito" and "Ciao Ada, ci vediamo al Café?" in sg[-1]["visti"], sg[-1:])
        prova("e chi segnala sa che è arrivata", "arrivata" in await p.inner_text("#esito-insieme"))
        f.esito_segnala = {"ok": False, "perche": "invio"}
        await p.click("#insieme-azioni button:has-text('Segnala')"); await p.click("#insieme-segnala button[data-motivo='spam']")
        await p.click("#insieme-segnala button:has-text('Manda la segnalazione')"); await p.wait_for_timeout(700)
        prova("se il server non riesce a mandarla, lo dice forte: NON è arrivata", "NON è arrivata" in await p.inner_text("#esito-insieme"))
        await p.click("#insieme-segnala button:has-text('Annulla')")
        await p.click("#insieme-azioni button:has-text('Silenzia')")
        f.manda({"t": "di", "id": "b1", "n": "Bruno", "x": "messaggio da non leggere", "ora": 3}); await p.wait_for_timeout(800)
        A = await altri(p)
        prova("toccando il suo soprannome lo silenzi: i suoi messaggi non arrivano, niente fumetto", A["visti"][0]["silenziato"] and not any("non leggere" in c["x"] for c in A["chat"]) and not A["visti"][0]["fumetto"], A)
        await p.click("#insieme-azioni button:has-text('Togli il silenzio')")
        await p.click("#chiudi-insieme")
        f.manda({"t": "di", "id": "b1", "n": "Bruno", "x": "ci sei?", "ora": 4})
        prova("a pannello chiuso il tasto conta i messaggi nuovi", await aspetta(p, "A.chip.includes('💬 1')", 5000), (await altri(p))["chip"])
        await p.click("#altri"); await p.wait_for_timeout(300)
        prova("riaprendo, i nuovi si azzerano", "💬" not in (await altri(p))["chip"], (await altri(p))["chip"])
        await p.click("#chiudi-insieme")
        # Bruno cammina, si siede
        f.manda({"t": "qui", "id": "b1", "p": {"x": 6, "z": 12, "r": 1, "y": 0, "s": 0, "l": ""}})
        prova("si muove: arriva dove dice il server, camminando", await aspetta(p, "Math.abs(A.visti[0].x-6)<0.3&&Math.abs(A.visti[0].z-12)<0.3"), (await altri(p))["visti"])
        f.manda({"t": "qui", "id": "b1", "p": {"x": 6, "z": 12, "r": 1, "y": -0.38, "s": 2, "l": ""}})
        prova("si siede", await aspetta(p, "A.visti[0].seduto===true", 5000))
        f.manda({"t": "qui", "id": "b1", "p": {"x": 1e999, "z": "x"}}); await p.wait_for_timeout(500)
        prova("una posizione assurda non lo sposta", abs((await altri(p))["visti"][0]["x"] - 6) < 0.3)
        n0 = len([m for m in f.arrivati if m.get("t") == "qui"])
        await p.keyboard.down("w"); await p.wait_for_timeout(2500); await p.keyboard.up("w"); await p.wait_for_timeout(600)
        qui = [m for m in f.arrivati if m.get("t") == "qui"][n0:]
        prova("camminando, la tua posizione va al server", len(qui) >= 2 and qui[-1]["p"]["z"] < 17.5, qui[-2:])
        await p.wait_for_timeout(1500); n1 = len(f.arrivati); await p.wait_for_timeout(1500)
        prova("da fermo non manda niente", len(f.arrivati) == n1, f.arrivati[n1:])
        f.manda({"t": "arriva", "id": "b2", "n": "Cleo", "a": {**BRUNO, "skin": "cavaliere"}, "p": {"x": -3, "z": 15, "r": 0, "y": 0, "s": 0, "l": ""}})
        prova("arriva un'altra: siete 3", await aspetta(p, "A.visti.length===2&&A.chip.includes('siete 3')", 5000), await altri(p))
        prova("ha la sua skin (il Cavaliere), e sopra il suo soprannome", await aspetta(p, "A.visti.some(x=>x.id==='b2'&&x.skin==='cavaliere'&&x.n==='Cleo'&&x.cartello)", 60000), await altri(p))
        f.manda({"t": "qui", "id": "b2", "p": {"x": 0, "z": 0, "r": 0, "y": 0, "s": 0, "l": "sartoria"}})
        prova("chi entra in un palazzo sparisce dalla città", await aspetta(p, "A.visti.some(x=>x.id==='b2'&&!x.inScena)", 5000), await altri(p))
        f.manda({"t": "va", "id": "b1"})
        prova("chi se ne va sparisce, e siete di nuovo 2", await aspetta(p, "A.visti.length===1&&A.visti[0].id==='b2'&&A.chip.includes('siete 2')", 5000), await altri(p))
        # da solo, e di nuovo con gli altri (dal pannello)
        await p.click("#altri"); await p.click("#insieme button:has-text('Stai da solo')"); await p.wait_for_timeout(800)
        A = await altri(p)
        prova("«Stai da solo»: la linea si chiude, gli altri spariscono, e resta salvato", A["stato"] == "solo" and not A["visti"] and f.chiusi >= 1
              and await p.evaluate("JSON.parse(localStorage.getItem('jjavis-citta')).daSolo===true"), A)
        await p.click("#insieme button:has-text('Torna con gli altri')")
        prova("«Torna con gli altri» si ricollega e risaluta", await aspetta(p, "A.stato==='dentro'", 10000) and len([m for m in f.arrivati if m.get("t") == "ciao"]) == 2)
        # il server rifiuta il soprannome: si torna a sceglierlo
        f.manda({"t": "no", "perche": "soprannome"})
        prova("se il server rifiuta il soprannome, lo dice e lo richiede", await aspetta(p, "A.stato==='nome'", 5000) and await p.is_visible("#insieme-soprannome")
              and "non va" in await p.inner_text("#esito-insieme"), await altri(p))
        prova("nessun errore JavaScript (insieme)", not err, err[:3])
        await ctx.close()

        # 1a. l'amministratore (6/10): la corona sopra gli altri, e la moderazione
        ctx, p, f, err = await nuova(b, "uno", soprannome="Ada", conto="admin")
        await aspetta(p, "A.stato==='dentro'")
        f.manda({"t": "arriva", "id": "re1", "n": "JJoe", "re": True, "a": BRUNO, "p": {"x": -2, "z": 12, "r": 0, "y": 0, "s": 0, "l": ""}})
        prova("chi è amministratore ha la corona sopra la testa, gli altri no", await aspetta(p, "A.visti.some(x=>x.id==='re1'&&x.re)&&A.visti.some(x=>x.id==='b1'&&!x.re)", 5000), await altri(p))
        await p.click("#altri"); await p.click("#insieme-gente button:has-text('Bruno')")
        prova("all'amministratore, toccando qualcuno, compaiono «Zittisci» e «Blocca»", await p.locator("#insieme-modera button").count() == 2)
        await p.click("#insieme-modera button:has-text('Zittisci')"); await p.wait_for_timeout(500)
        md = [m for m in f.arrivati if m.get("t") == "modera"]
        prova("«Zittisci» manda al server chi e per quanto (un'ora)", md and md[-1]["id"] == "b1" and md[-1]["azione"] == "zittisci" and md[-1]["minuti"] == 60, md[-1:])
        prova("e dice com'è andata", "non può scrivere per un'ora" in await p.inner_text("#esito-insieme"))
        await p.click("#insieme-modera button:has-text('Blocca')"); await p.wait_for_timeout(300)
        prova("«Blocca» chiede conferma prima", "Sicuro" in await p.inner_text("#insieme-modera") and len([m for m in f.arrivati if m.get("t") == "modera"]) == 1)
        await p.click("#insieme-modera button:has-text('Sicuro')"); await p.wait_for_timeout(500)
        md = [m for m in f.arrivati if m.get("t") == "modera"]
        prova("al secondo tocco il blocco parte", len(md) == 2 and md[-1]["azione"] == "blocca", md[-1:])
        await p.click("#insieme-gente button:has-text('JJoe')")
        prova("un amministratore non vede «Zittisci» e «Blocca» su un altro amministratore", await p.locator("#insieme-modera").count() == 0)
        # lo sblocco (JJ, 6/10: «se mi blocco l'altro account senza il modo di sbloccarlo poi non posso più usarlo per provare»)
        await p.click("#insieme button:has-text('Bloccati e zittiti')")
        prova("l'amministratore vede chi è bloccato", await aspetta(p, "!!document.querySelector('#insieme-moderati') && document.querySelector('#insieme-moderati').textContent.includes('Molesto · bloccato')", 5000))
        await p.click("#insieme-moderati button:has-text('Sblocca')"); await p.wait_for_timeout(800)
        sb = [m for m in f.arrivati if m.get("t") == "modera" and m.get("azione") == "sblocca"]
        prova("«Sblocca» manda al server quell'account (per numero), e l'elenco si svuota", sb and sb[-1]["uid"] == "g:42" and "Nessuno è bloccato" in await p.inner_text("#insieme-moderati"), sb[-1:])
        prova("e dice che può tornare", "può tornare in città" in await p.inner_text("#esito-insieme"))
        prova("nessun errore JavaScript (amministratore)", not err, err[:3])
        await ctx.close()

        # 1c. senza account (6/10: «niente account, niente altri»)
        ctx, p, f, err = await nuova(b, "uno", soprannome="Ada", conto=None)
        await p.wait_for_timeout(2500)
        A = await altri(p)
        prova("senza account non ci si collega: il tasto dice «entra con Google»", A["stato"] == "account" and "entra con Google" in A["chip"] and not f.linee, (A, len(f.linee)))
        await p.click("#altri")
        prova("il pannello spiega perché e porta all'accesso", "serve l'account" in await p.inner_text("#insieme") and await p.locator("#insieme button:has-text('Entra con Google')").count() == 1)
        await p.click("#insieme button:has-text('Entra con Google')")
        prova("…che apre il pannello dell'account", await p.is_visible("#conto") and not await p.is_visible("#insieme"))
        await ctx.close()

        # 1d. bloccato: il server chiude con 4003 e non si riprova
        ctx, p, f, err = await nuova(b, "uno", soprannome="Ada")
        await aspetta(p, "A.stato==='dentro'")
        n0 = len(f.linee); f.manda({"t": "no", "perche": "bloccato"}); await asyncio.ensure_future(f.linee[-1].close(code=4003, reason="bloccato")); await p.wait_for_timeout(4000)
        A = await altri(p)
        prova("bloccato: lo dice, e non riprova a collegarsi", A["stato"] == "bloccato" and "non può stare con gli altri" in A["chip"] and len(f.linee) == n0, (A["stato"], A["chip"], len(f.linee), n0))
        await ctx.close()

        # 1b. il freno: in una finestra minuscola SwiftShader disegna abbastanza fotogrammi perché il freno si veda
        ctx, p, f, err = await nuova(b, "uno", piccola=True, soprannome="Ada")
        await aspetta(p, "A.stato==='dentro'")
        fa = await p.evaluate("window.CITTA.fotogrammi()"); n0 = len(f.arrivati)
        await p.keyboard.down("w"); await p.wait_for_timeout(3000); await p.keyboard.up("w"); await p.wait_for_timeout(300)
        fps = (await p.evaluate("window.CITTA.fotogrammi()") - fa) / 3.3
        qui = [m for m in f.arrivati[n0:] if m.get("t") == "qui"]
        gap = min((b_["_t"] - a_["_t"] for a_, b_ in zip(qui, qui[1:])), default=None)
        if fps > 6: prova(f"al massimo 4 posizioni al secondo ({fps:.0f} fotogrammi/s, {len(qui)} posizioni, intervallo minimo {gap:.2f} s)", len(qui) >= 3 and gap >= 0.2, (len(qui), gap))
        else: print(f"  --  il freno delle posizioni NON è verificato: {fps:.1f} fotogrammi/s anche nella finestra piccola")
        await ctx.close()

        # 2. la città è piena
        ctx, p, f, err = await nuova(b, "piena", soprannome="Ada")
        prova("città piena: lo dice, e la città resta tua", await aspetta(p, "A.stato==='piena'&&A.chip.includes('piena')", 15000), await altri(p))
        await ctx.close()

        # 3. il server non risponde: un guasto si dice, non si tace
        ctx, p, f, err = await nuova(b, "muta", soprannome="Ada")
        prova("server giù: «da solo · il collegamento non risponde»", await aspetta(p, "A.stato==='giu'&&A.chip.includes('non risponde')", 15000), await altri(p))
        fa = await p.evaluate("window.CITTA.fotogrammi()"); await p.wait_for_timeout(4000)
        prova("e la città continua a girare", await p.evaluate("window.CITTA.fotogrammi()") > fa)
        prova("riprova da sola (dopo 2 s, poi 4, 8… fino a un minuto)", len(f.linee) >= 2, len(f.linee))
        prova("nessun errore JavaScript (server giù)", not err, err[:3])
        await ctx.close()

        # 4. il server non è ancora acceso (insieme.json senza indirizzo): lo dice, e non prova a collegarsi
        ctx, p, f, err = await nuova(b, "uno", soprannome="Ada", indirizzo=None)
        prova("server non ancora acceso: «il collegamento non è ancora acceso», nessuna linea", await aspetta(p, "A.stato==='chiusa'", 15000) and not f.linee, await altri(p))
        await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} prove"); print("VERDE" if all(prove) else "ROSSO")

asyncio.run(main())
