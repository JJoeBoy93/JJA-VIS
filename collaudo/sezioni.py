"""Le sezioni dei pannelli: chiuse finché non si toccano (28/10).

    CHROMIUM=/percorso/chrome python3 collaudo/sezioni.py index.html

JJ, 28 ottobre 2026: «le varie pagine non sono molto pratiche... devi scorrere per vedere tutto. Se clicchi ad esempio su I tuoi dati si apre
espanso tutto intero, altrimenti resta chiuso in forma contratta, per tutto così è più pratico». Ogni sezione dei pannelli (la chat e il
Calendario no) è un <details>: chiusa mostra titolo, una riga di riassunto e la freccia; toccata si apre intera; ritoccata si chiude.
Questo collaudo NON apre le sezioni in anticipo (gli altri sì: collaudo/aiuti.py). Scene, con la porta finta, telefono 390×844:
1. un visitatore nuovo: ogni pannello, appena aperto, ha le sezioni chiuse; titolo, riga e freccia si vedono, il contenuto no (offsetParent e
   checkVisibility, vedi SI_VEDE); fa eccezione il pannello con UNA sezione sola (Cosa so fare, finché non ci sono Novità né video), che resta aperto
2. toccata, la sezione si apre e il contenuto si vede; ritoccata si chiude; da tastiera (Invio, Spazio) lo stesso
3. le righe di riassunto vere: «Atlas · Deciso · Jacopo», «1 domanda per oggi · so 5 cose di te», «Acceso 0 € · costruirmi 72 € al mese»…
4. il pallino del Profilo porta a «Imparo te» aperta, con la domanda di oggi in vista, e le altre sezioni restano chiuse
5. un link dentro una sezione (#dati, #clio, #numeri-problema) la apre; «Cosa so fare →» e «nel Profilo» aprono la loro; #bottega no
6. dopo un ricaricamento, nella stessa visita, resta aperto quello che era aperto (sessionStorage); una scheda nuova riparte chiusa
7. Novità e Quanto costo arrivano dai dati: il pannello torna a sezioni chiuse, e le loro righe dicono il vero
8. animazioni ridotte, quattro aspetti (angoli e colori), testo leggibile in ognuno
9. CONTROPROVA: con tutte le sezioni aperte all'avvio la prova «chiuse all'apertura» diventa rossa
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
import aiuti

PAGINA = open(sys.argv[1], encoding="utf-8").read()
CONTO = open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "conto.json"), encoding="utf-8").read()
BASE = "https://jjoeboy93.github.io/JJA-VIS/"
CORS = {"Access-Control-Allow-Origin": "https://jjoeboy93.github.io", "Access-Control-Allow-Headers": "*"}
CHI = "4b675b9f2df739ec"
# chi ha già risposto al sondaggio: ci sono domande del ritorno da fare, quindi il pallino sul Profilo
DI_CASA = {"id": CHI, "nome": "Atlas", "tema": "deciso", "tuo": "Jacopo", "inviato": True, "mestiere": "Corriere o autista",
           "tempo": "Costruire il giro del mattino", "conosciute": {"inizio": "Cambia ogni giorno", "mestiere_di_una_vita": "Il falegname"}}
NOVITA = [{"quando": "2026-10-20T10:00:00Z", "titolo": "Le schede si aprono", "testo": "Tocchi e leggi."},
          {"quando": "2026-10-27T10:00:00Z", "titolo": "La domanda di oggi sta nel Profilo", "testo": "Una al giorno."}]
# quante sezioni si vedono in ogni pannello con la porta finta senza novità né video (Novità e Video hanno `hidden` finché non ci sono dati); conto.json c'è
PANNELLI = {"chi-sono": 5, "sa-fare": 1, "bottega": 4, "profilo": 3, "numeri": 3, "investitori": 6, "sostieni": 2}
dati = {"novita": [], "conto": True}

prove = []
def prova(nome, ok, info=""):
    prove.append(bool(ok)); print(("  ok  " if ok else "  NO  ") + nome + (f" — {info}" if info and not ok else ""))

async def instrada(route):
    r = route.request; u = r.url
    if u.startswith(BASE):
        if u.split("?")[0].split("#")[0] in (BASE, BASE + "index.html"): return await route.fulfill(body=PAGINA, content_type="text/html")
        if u.endswith("conto.json") and dati["conto"]: return await route.fulfill(body=CONTO, content_type="application/json")
        return await route.fulfill(status=404, body="")
    if "workers.dev" in u:
        if r.method == "OPTIONS": return await route.fulfill(status=204, headers={**CORS, "Access-Control-Allow-Methods": "POST, GET"})
        if u.endswith("/novita"): return await route.fulfill(body=json.dumps(dati["novita"]), content_type="application/json", headers=CORS)
        if "/risposte" in u: return await route.fulfill(body=json.dumps({"risposte": []}), content_type="application/json", headers=CORS)
        return await route.fulfill(body="{}", content_type="application/json", headers=CORS)
    return await route.fulfill(status=404, body="")

async def apri(b, io=None, reduce=False, tutte_aperte=False, url=BASE):
    """Una visita nuova (contesto nuovo: sessionStorage vuoto). `tutte_aperte` è per la controprova."""
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce" if reduce else "no-preference")
    await ctx.route("**/*", instrada)
    if io: await ctx.add_init_script("if(!localStorage.getItem('jjavis-io')) localStorage.setItem('jjavis-io', %s)" % json.dumps(json.dumps(io)))
    if tutte_aperte: await ctx.add_init_script(aiuti.APRI_TUTTE)
    errori = []
    pg = await ctx.new_page(); pg.on("pageerror", lambda e: errori.append(str(e)))
    await pg.goto(url); await pg.wait_for_timeout(900)
    return ctx, pg, errori

# «si vede»: offsetParent da solo non basta. Nel Chromium di oggi (153) il contenuto di un <details> chiuso resta «renderizzato» (content-visibility:hidden
# su ::details-content): ha offsetParent e perfino una misura, ma non si vede né si tocca. checkVisibility() lo sa, e Playwright (is_visible) pure.
SI_VEDE = "e => !!e && e.offsetParent !== null && e.checkVisibility({visibilityProperty: true})"
# com'è fatta ogni sezione di un pannello (quelle che si vedono: Novità, Video e Quanto costo hanno `hidden` finché non hanno dati)
ISPEZIONA = """k => { const vede = """ + SI_VEDE + """; const pn = document.getElementById('p-' + k);
  return [...pn.querySelectorAll('details.sezione')].filter(d => !d.hidden).map(d => {
    const s = d.querySelector(':scope>summary'), h = s.querySelector('h2'), r = s.querySelector('.sez-riga'), c = d.querySelector(':scope>.sez-corpo');
    return {id: d.id, aperta: d.open, corpo: vede(c), titolo: vede(h) ? h.textContent.trim() : '',
            riga: vede(r) ? r.textContent.trim() : '', freccia: vede(s.querySelector('.sez-freccia'))}; }); }"""
vede = lambda pg, sel: pg.evaluate("s => (" + SI_VEDE + ")(document.querySelector(s))", sel)
aperta = lambda pg, sel: pg.evaluate("s => document.querySelector(s).open", sel)
riga = lambda pg, sel: pg.evaluate("s => document.querySelector(s + ' .sez-riga').textContent.trim()", sel)

async def vai(pg, k):
    """Con la barra delle schede (chi non ha ancora un nome)."""
    await pg.click(f"#s-{k}"); await pg.wait_for_timeout(350)

async def vai_dal_menu(pg, k):
    """Chi è di casa non ha la barra: le schede stanno nel menù ☰."""
    await pg.click("#apri-conv"); await pg.wait_for_timeout(450)
    await pg.click(f'#menu-schede .menu-scheda[data-vai="{k}"]'); await pg.wait_for_timeout(450)

async def chiuse_all_apertura(pg, k, vai_a):
    """I problemi di un pannello appena aperto (lista vuota = tutto bene). Un pannello con UNA sezione visibile la tiene aperta, e il contenuto si vede."""
    await vai_a(pg, k)
    sez = await pg.evaluate(ISPEZIONA, k); problemi = []
    if not sez: return [f"{k}: nessuna sezione"]
    for s in sez:
        sola = len(sez) == 1
        if s["aperta"] != sola: problemi.append(f"{s['id']} {'chiusa' if sola else 'aperta'} all'apertura")
        if s["corpo"] != sola: problemi.append(f"{s['id']}: il contenuto {'non si vede' if sola else 'si vede'}")
        if not s["titolo"] or not s["riga"] or not s["freccia"]: problemi.append(f"{s['id']}: titolo/riga/freccia non si vedono ({s['titolo']!r}, {s['riga']!r}, {s['freccia']})")
        if "\n" in s["riga"] or len(s["riga"]) > 90: problemi.append(f"{s['id']}: la riga non è una riga breve ({s['riga']!r})")
    return problemi

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)

        print("── 1. un visitatore nuovo: ogni pannello si apre a sezioni chiuse")
        ctx, pg, errori = await apri(b)
        for k, attese in PANNELLI.items():
            problemi = await chiuse_all_apertura(pg, k, vai)
            n = len(await pg.evaluate(ISPEZIONA, k))
            prova(f"1. #p-{k}: {n} {'sezione' if n == 1 else 'sezioni'}, " + ("la sola resta aperta e si legge" if n == 1 else "chiuse, titolo e riga si vedono, il contenuto no"), not problemi and n == attese, "; ".join(problemi) or f"{n} sezioni invece di {attese}")
        await pg.goto(BASE + "#calendario"); await pg.wait_for_timeout(500)
        prova("1. Calendario: una sezione sola, aperta (non è un <details>), si legge", await pg.evaluate("document.querySelector('#p-calendario details.sezione')===null") and await vede(pg, "#tcal") and await vede(pg, "#cal-stato"))
        prova("1. nessuna sezione nella chat (Inizia)", await pg.evaluate("document.querySelectorAll('#p-inizia details').length") == 0)
        prova("1. zero errori JavaScript", not errori, errori)
        await ctx.close()

        print("── 2. toccata si apre, ritoccata si chiude; da tastiera lo stesso")
        ctx, pg, errori = await apri(b)
        await vai(pg, "bottega")
        prova("2. Clio chiusa: i campi non si vedono", not await vede(pg, "#cl-nome") and not await aperta(pg, "#clio"))
        await pg.click("#clio summary"); await pg.wait_for_timeout(300)
        prova("2. toccata: si apre, e il contenuto si vede", await aperta(pg, "#clio") and await vede(pg, "#cl-nome") and await vede(pg, "#cl-manda"))
        prova("2. le altre restano chiuse", not await aperta(pg, "#sopralluogo") and not await aperta(pg, "#costruisci") and not await vede(pg, "#so-link"))
        prova("2. la freccia si gira", await pg.evaluate("getComputedStyle(document.querySelector('#clio .sez-freccia')).transform") != await pg.evaluate("getComputedStyle(document.querySelector('#sopralluogo .sez-freccia')).transform"))
        await pg.click("#clio summary"); await pg.wait_for_timeout(300)
        prova("2. ritoccata: si chiude, il contenuto sparisce, il titolo resta", not await aperta(pg, "#clio") and not await vede(pg, "#cl-nome") and await vede(pg, "#tcl"))
        await pg.focus("#sopralluogo summary"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
        prova("2. da tastiera, Invio: si apre", await aperta(pg, "#sopralluogo") and await vede(pg, "#so-link"))
        await pg.keyboard.press("Space"); await pg.wait_for_timeout(300)
        prova("2. da tastiera, Spazio: si chiude", not await aperta(pg, "#sopralluogo"))
        prova("2. il titolo è un h2 dentro un summary (si legge e ci si arriva con la tastiera), e il nome letto ha anche la riga",
              await pg.evaluate("document.querySelector('#clio summary').matches('summary') && document.querySelector('#clio summary h2').textContent==='Clio' && document.querySelector('#clio summary').textContent.includes('ogni visitatore')"))
        prova("2. zero errori JavaScript", not errori, errori)
        await ctx.close()

        print("── 3. le righe di riassunto, vere")
        ctx, pg, errori = await apri(b, DI_CASA)
        await vai_dal_menu(pg, "profilo")
        n = await pg.evaluate("document.querySelectorAll('#so-di-te li').length")
        prova("3. «Il tuo Atlas»: nome · aspetto · il tuo nome", await riga(pg, "#il-tuo-assistente") == "Atlas · Deciso · Jacopo", await riga(pg, "#il-tuo-assistente"))
        prova("3. «Imparo te»: una domanda per oggi e quante cose so", await riga(pg, "#imparo-te") == f"1 domanda per oggi · so {n} cose di te" and n >= 3, f"{await riga(pg, '#imparo-te')} ({n} voci)")
        prova("3. «I tuoi dati»: niente cookie, chi vede cosa, dove sta", await riga(pg, "#dati") == "Niente cookie. Chi vede cosa, e dove sta", await riga(pg, "#dati"))
        await pg.evaluate("() => { const c = {}; CONOSCERTI.forEach(q => c[q.k] = 'x'); io.conosciute = c; delete io.tuo; salva(); aggiornaProfilo(); }")
        n2 = await pg.evaluate("document.querySelectorAll('#so-di-te li').length")
        prova("3. finite le domande: «so N cose di te», senza la domanda", await riga(pg, "#imparo-te") == f"so {n2} cose di te", await riga(pg, "#imparo-te"))
        prova("3. cambiati i dati la riga di «Il tuo Atlas» si rifà", await riga(pg, "#il-tuo-assistente") == "Atlas · Deciso", await riga(pg, "#il-tuo-assistente"))
        await aiuti.apri(pg, "#temi-profilo"); await pg.click('#temi-profilo [data-tema="naturale"]')
        prova("3. e cambiando aspetto", await riga(pg, "#il-tuo-assistente") == "Atlas · Naturale", await riga(pg, "#il-tuo-assistente"))
        await pg.evaluate("() => { delete io.mestiere; delete io.tempo; io.conosciute = {}; salva(); aggiornaProfilo(); }")
        prova("3. non so niente: lo dice, senza numeri finti", await riga(pg, "#imparo-te") == "1 domanda per oggi · non so ancora niente di te", await riga(pg, "#imparo-te"))
        await vai_dal_menu(pg, "numeri")
        prova("3. «Il problema, in numeri»: 2 ore al giorno per corriere", await riga(pg, "#numeri-problema") == "2 ore al giorno per corriere", await riga(pg, "#numeri-problema"))
        # 29/10: la somma si legge da conto.json, non si scrive a mano (con «Claude a consumo» misurato era diventata 3,97 €)
        _c = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "conto.json")))
        _eur = lambda x: (f"{x:.2f}".replace(".", ",").removesuffix(",00")) + " €"
        _att = _eur(sum(v["euro"] for v in _c["gruppi"][0]["voci"] if isinstance(v.get("euro"), (int, float))))
        _cos = _eur(sum(v["euro"] for v in _c["gruppi"][1]["voci"] if isinstance(v.get("euro"), (int, float))))
        _atteso = f"Acceso {_att} · costruirmi {_cos} al mese"
        prova(f"3. «Quanto costo»: {_atteso} (la somma delle voci di conto.json)", await vede(pg, "#conto") and await riga(pg, "#conto") == _atteso, await riga(pg, "#conto"))
        await vai_dal_menu(pg, "sa-fare")
        prova("3. «Cosa so già fare»: i suoi attrezzi", "attrezzi" in await riga(pg, "#cosa-so-fare"), await riga(pg, "#cosa-so-fare"))
        prova("3. zero errori JavaScript", not errori, errori)
        await ctx.close()

        print("── 4. il pallino del Profilo")
        ctx, pg, errori = await apri(b, DI_CASA)
        prova("4. c'è una domanda: il Profilo nel menù ha il pallino", await pg.evaluate("document.getElementById('s-profilo').classList.contains('domanda')"))
        await vai_dal_menu(pg, "profilo")
        prova("4. «Imparo te» è aperta", await aperta(pg, "#imparo-te"))
        prova("4. la domanda di oggi si vede, scelte comprese", await vede(pg, "#conosci") and await vede(pg, "#conosci-domanda") and await vede(pg, "#conosci-scelte .scelta"))
        prova("4. e sta dentro lo schermo", await pg.evaluate("(()=>{const r=document.getElementById('conosci-domanda').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight})()"),
              await pg.evaluate("JSON.stringify(document.getElementById('conosci-domanda').getBoundingClientRect())"))
        prova("4. «Il tuo Atlas» e «I tuoi dati» restano chiuse", not await aperta(pg, "#il-tuo-assistente") and not await aperta(pg, "#dati") and not await vede(pg, "#nuova-sigla"))
        await vai_dal_menu(pg, "numeri"); await vai_dal_menu(pg, "profilo")
        prova("4. tornati al Profilo, «Imparo te» è ancora aperta (l'hai vista tu), il resto chiuso", await aperta(pg, "#imparo-te") and not await aperta(pg, "#dati"))
        await ctx.close()
        # senza il pallino (domande finite): il Profilo si apre tutto chiuso
        ctx, pg, errori = await apri(b, DI_CASA)
        await pg.evaluate("() => { const c = {}; CONOSCERTI.forEach(q => c[q.k] = 'x'); io.conosciute = c; salva(); aggiornaProfilo(); }")
        prova("4. senza domande niente pallino, e il Profilo si apre a sezioni chiuse", not await pg.evaluate("document.getElementById('s-profilo').classList.contains('domanda')")
              and not await chiuse_all_apertura(pg, "profilo", vai_dal_menu))
        await ctx.close()
        # chi non ha il menù (nessun nome) ha la linguetta: col pallino farebbe lo stesso; qui la linguetta senza pallino non apre niente
        ctx, pg, errori = await apri(b)
        await vai(pg, "profilo")
        prova("4. la linguetta Profilo senza pallino non apre sezioni", not await pg.evaluate("document.querySelectorAll('#p-profilo details[open]').length"))
        await ctx.close()

        print("── 5. i link che portano dentro una sezione")
        ctx, pg, errori = await apri(b)
        await pg.goto(BASE + "#dati"); await pg.wait_for_timeout(500)
        prova("5. #dati apre il Profilo e «I tuoi dati»", await pg.evaluate("document.body.dataset.scheda") == "profilo" and await aperta(pg, "#dati") and await vede(pg, ".dati-corpo"))
        prova("5. …e solo quella", not await aperta(pg, "#il-tuo-assistente") and not await aperta(pg, "#imparo-te"))
        testo = await pg.inner_text("#dati")
        prova("5. il testo dice cosa vede l'intelligenza artificiale", all(x in testo for x in ["Cosa vede un'intelligenza artificiale", "Mai la tua mail", "Il tuo assistente, se hai fatto l'account"]))
        await ctx.close()
        for h, pannello, sez, chiuse in [("clio", "bottega", "#clio", ["#sopralluogo", "#costruisci", "#sez-bottega"]),
                                         ("sopralluogo", "bottega", "#sopralluogo", ["#clio", "#costruisci"]),
                                         ("numeri-problema", "numeri", "#numeri-problema", ["#sez-numeri"]),
                                         ("imparo-te", "profilo", "#imparo-te", ["#dati", "#il-tuo-assistente"]),
                                         ("profilo-mail", "profilo", "#il-tuo-assistente", ["#imparo-te", "#dati"])]:
            ctx, pg, errori = await apri(b, url=BASE + "#" + h)
            prova(f"5. #{h} apre il pannello giusto e la sezione che lo contiene", await pg.evaluate("document.body.dataset.scheda") == pannello and await aperta(pg, sez) and await vede(pg, f"#{h}"))
            prova(f"5. #{h}: le altre sezioni restano chiuse", not any([await aperta(pg, x) for x in chiuse]), [x for x in chiuse if await aperta(pg, x)])
            await ctx.close()
        # i link cliccati dentro la pagina: «Cosa so fare →», «nel Profilo», e uno che porta a un pannello e basta (con le Novità, così «Cosa so fare» ha due sezioni)
        dati["novita"] = NOVITA
        ctx, pg, errori = await apri(b)
        async def tocca_link(h):
            await pg.evaluate("h => { const a = document.createElement('a'); a.href = h; a.id = 'prova-link'; a.textContent = 'x'; document.body.appendChild(a); a.click(); a.remove(); }", h)
            await pg.wait_for_timeout(450)
        await tocca_link("#sa-fare")
        prova("5. «Cosa so fare →» (#sa-fare) porta lì e apre «Cosa so già fare», non le Novità", await pg.evaluate("document.body.dataset.scheda") == "sa-fare" and await aperta(pg, "#cosa-so-fare") and await vede(pg, "#n-canzoni") and not await aperta(pg, "#novita"))
        await tocca_link("#profilo")
        prova("5. «nel Profilo» (#profilo) apre «Il tuo Atlas» (nome e colore), non il resto", await pg.evaluate("document.body.dataset.scheda") == "profilo" and await aperta(pg, "#il-tuo-assistente")
              and not await aperta(pg, "#imparo-te") and not await aperta(pg, "#dati"))
        await tocca_link("#bottega")
        prova("5. un link al pannello Bottega non apre nessuna sezione", await pg.evaluate("document.body.dataset.scheda") == "bottega" and not await pg.evaluate("document.querySelectorAll('#p-bottega details[open]').length"))
        await tocca_link("#investitori")
        prova("5. nemmeno Investi", not await pg.evaluate("document.querySelectorAll('#p-investitori details[open]').length"))
        await ctx.close(); dati["novita"] = []

        print("── 6. dopo un ricaricamento, nella stessa visita")
        ctx, pg, errori = await apri(b)
        await vai(pg, "profilo")
        await pg.click("#dati summary"); await pg.click("#imparo-te summary"); await pg.wait_for_timeout(250)
        await pg.click("#imparo-te summary"); await pg.wait_for_timeout(250)    # aperta e richiusa: resta chiusa
        await pg.reload(); await pg.wait_for_timeout(900)
        await vai(pg, "profilo")
        prova("6. «I tuoi dati» resta aperta dopo il ricaricamento", await aperta(pg, "#dati") and await vede(pg, ".dati-corpo"))
        prova("6. quella richiusa resta chiusa, e le altre pure", not await aperta(pg, "#imparo-te") and not await aperta(pg, "#il-tuo-assistente"))
        await vai(pg, "bottega")
        prova("6. e un altro pannello resta chiuso", not await pg.evaluate("document.querySelectorAll('#p-bottega details[open]').length"))
        await vai(pg, "profilo"); await pg.click("#dati summary"); await pg.wait_for_timeout(250)
        await pg.reload(); await pg.wait_for_timeout(900); await vai(pg, "profilo")
        prova("6. richiusa da te: dopo il ricaricamento resta chiusa", not await aperta(pg, "#dati"))
        await pg.evaluate("sessionStorage.setItem('jjavis-sezioni','{rotto')")
        await pg.reload(); await pg.wait_for_timeout(900); await vai(pg, "profilo")
        prova("6. se la memoria è rotta, tutto chiuso e nessun errore", not await pg.evaluate("document.querySelectorAll('#p-profilo details[open]').length") and not errori, errori)
        pg2 = await ctx.new_page(); await pg2.goto(BASE + "#profilo"); await pg2.wait_for_timeout(700)
        prova("6. un'altra scheda del browser, un'altra visita: tutto chiuso", not await pg2.evaluate("document.querySelectorAll('details.sezione[open]:not([data-auto])').length"))
        await ctx.close()

        print("── 7. Novità e Quanto costo arrivano dai dati")
        dati["novita"] = NOVITA
        ctx, pg, errori = await apri(b)
        await vai(pg, "sa-fare")
        prova("7. con le Novità, Cosa so fare ha due sezioni: tutte e due chiuse (quella sola si è richiusa)", not await chiuse_all_apertura(pg, "sa-fare", vai) and len(await pg.evaluate(ISPEZIONA, "sa-fare")) == 2)
        prova("7. la riga delle Novità: quante, e l'ultima per data (non per posto)", await riga(pg, "#novita") == "2 novità · ultima: La domanda di oggi sta nel Profilo", await riga(pg, "#novita"))
        await pg.click("#novita summary"); await pg.wait_for_timeout(250)
        prova("7. toccata, le novità si leggono", await vede(pg, "#novita-elenco .novita"))
        await vai(pg, "numeri")
        prova("7. con Quanto costo, Numeri ha tre sezioni chiuse", not await chiuse_all_apertura(pg, "numeri", vai) and len(await pg.evaluate(ISPEZIONA, "numeri")) == 3)
        await ctx.close()
        dati["novita"] = []; dati["conto"] = False
        ctx, pg, errori = await apri(b)
        await vai(pg, "numeri")
        prova("7. senza conto.json «Quanto costo» non c'è, e Numeri ha le sue due sezioni chiuse", not await vede(pg, "#conto") and not await chiuse_all_apertura(pg, "numeri", vai) and len(await pg.evaluate(ISPEZIONA, "numeri")) == 2)
        await ctx.close()
        dati["conto"] = True

        print("── 8. animazioni ridotte, aspetti, testo leggibile")
        ctx, pg, errori = await apri(b, reduce=True)
        await vai(pg, "bottega"); await pg.click("#clio summary"); await pg.wait_for_timeout(100)
        prova("8. con prefers-reduced-motion niente animazione né rotazione lenta", await pg.evaluate("getComputedStyle(document.querySelector('#clio .sez-corpo')).animationName") == "none"
              and await pg.evaluate("getComputedStyle(document.querySelector('#clio .sez-freccia')).transitionDuration") == "0s")
        await ctx.close()
        ctx, pg, errori = await apri(b)
        await vai(pg, "bottega"); await pg.click("#clio summary"); await pg.wait_for_timeout(100)
        prova("8. senza, l'apertura ha la sua animazione (la prova sopra non è vuota)", await pg.evaluate("getComputedStyle(document.querySelector('#clio .sez-corpo')).animationName") != "none")
        await vai(pg, "profilo")   # (il visitatore nuovo non ha ancora il Profilo di nessuno: «Come lo vedi» sta in «Il tuo»)
        await aiuti.apri(pg, "#temi-profilo")
        CONTRASTO = """() => { const lum = c => { const [r, g, b] = c.match(/[\\d.]+/g).slice(0, 3).map(Number).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4 }); return .2126 * r + .7152 * g + .0722 * b };
          const rap = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05) };
          const d = document.getElementById('dati'), fondo = getComputedStyle(d).backgroundColor, s = d.querySelector('summary');
          return {titolo: rap(getComputedStyle(s.querySelector('h2')).color, fondo), riga: rap(getComputedStyle(s.querySelector('.sez-riga')).color, fondo), freccia: rap(getComputedStyle(s.querySelector('.sez-freccia')).borderBottomColor, fondo),
                  raggio: getComputedStyle(d).borderTopLeftRadius, angolo: getComputedStyle(d, '::before').display, bordo: getComputedStyle(d).borderTopColor} }"""
        for tema, tondo in [("tech", False), ("calmo", True), ("deciso", False), ("naturale", True)]:
            await pg.click(f'#temi-profilo [data-tema="{tema}"]'); await pg.wait_for_timeout(120)
            v = await pg.evaluate(CONTRASTO)
            prova(f"8. aspetto «{tema}»: titolo, riga e freccia si leggono (contrasto ≥ 3 / 4,5)", v["titolo"] >= 4.5 and v["riga"] >= 4.5 and v["freccia"] >= 3, v)
            prova(f"8. aspetto «{tema}»: il riquadro è quello di sempre ({'angoli morbidi' if tondo else 'angoli accesi'})", (v["raggio"] != "0px") == tondo and (v["angolo"] == "none") == tondo, v)
        await ctx.close()
        for schema in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=schema); await ctx.route("**/*", instrada)
            p = await ctx.new_page(); await p.goto(BASE + "#bottega"); await p.wait_for_timeout(600)
            v = await p.evaluate("""() => { const s = document.querySelector('#clio summary'), f = getComputedStyle(document.querySelector('#clio')).backgroundColor, t = getComputedStyle(s.querySelector('h2')).color;
              return {fondo: f, titolo: t, vede: s.querySelector('h2').offsetParent !== null} }""")
            prova(f"8. con il telefono in tema {'chiaro' if schema == 'light' else 'scuro'} il titolo non sparisce nel fondo", v["vede"] and v["fondo"] != v["titolo"], v)
            await ctx.close()

        print("── 9. CONTROPROVA: con tutte le sezioni aperte all'avvio la prova «chiuse all'apertura» deve diventare rossa")
        ctx, pg, errori = await apri(b, tutte_aperte=True)
        rosse = {}
        for k in ("chi-sono", "bottega", "profilo", "numeri", "investitori", "sostieni"):
            rosse[k] = await chiuse_all_apertura(pg, k, vai)
        prova("9. con tutto aperto la prova è rossa in ogni pannello (così la prova verde di sopra vale qualcosa)", all(rosse.values()), {k: len(v) for k, v in rosse.items()})
        await pg.evaluate("document.querySelectorAll('details.sezione').forEach(d => d.open = false)")   # e richiuse a mano tornano chiuse: la prova non è rossa per altro
        prova("9. richiuse, la stessa prova torna verde (non era rossa per un altro motivo)", not await chiuse_all_apertura(pg, "bottega", vai))
        await ctx.close()
        await b.close()
    print(f"\n{sum(prove)}/{len(prove)} verdi"); print("VERDE" if all(prove) else "ROSSO"); sys.exit(0 if all(prove) else 1)   # VERDE/ROSSO: è l'ultima riga che legge Hera

asyncio.run(main())
