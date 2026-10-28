"""Collaudo della pagina a schede, in un browser vero con la porta finta.

    python3 collaudo/schede.py index.html
    CHROMIUM=/percorso/chrome python3 collaudo/schede.py index.html

Nessuna richiesta esce: pagina, conto.json, sostieni.json e porta sono
serviti da qui. Verde = 0 errori JavaScript e tutte le prove passate.
Nato il 26 settembre 2026 (Athena): era rosso sull'errore d'avvio che
avrebbe fermato la pagina a chi torna.
"""
import json, asyncio, sys, os
from playwright.async_api import async_playwright
PAGINA=open(sys.argv[1],encoding="utf-8").read()
PORTA="https://jjavis-porta.19-jjardito93.workers.dev"
BASE="https://jjoeboy93.github.io/JJA-VIS/"
inviati=[]
CAL={"impegni":[],"scadenze":[],"fatti":[],"giu":False,"n":0,"invito":"mandato","invito_errore":None}   # il calendario della porta finta (26/10)
conta_risposte=[]
risposte_di={}   # quante volte ha chiesto /risposte ogni pagina: altre pagine aperte nello stesso browser chiedono per conto loro
async def instrada(route):
    u=route.request.url
    if u.startswith(BASE) and (u==BASE or "#" in u or u.endswith("index.html")):
        return await route.fulfill(body=PAGINA, content_type="text/html")
    if u.endswith("conto.json"): return await route.fulfill(body=open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])),"conto.json")).read(), content_type="application/json")
    if u.endswith("sostieni.json"): return await route.fulfill(body=json.dumps(SOST), content_type="application/json")
    if u.startswith(PORTA):
        if route.request.method=="POST":
            corpo=json.loads(route.request.post_data); inviati.append((u.split("/")[-1], corpo))
            if u.endswith("/assistente/fatto") or u.endswith("/assistente/annulla"):
                CORS={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"}
                if CAL["giu"]: return await route.fulfill(status=502, body='{"errore":"non riesco a salvare: riprova tra poco"}', content_type="application/json", headers=CORS)
                i=corpo["id"]
                if u.endswith("/fatto"):
                    for k in ("impegni","scadenze"):
                        for x in list(CAL[k]):
                            if x["id"]==i: CAL[k].remove(x); CAL["fatti"].append({**x,"id":i,"tipo":"impegno" if k=="impegni" else "scadenza","quando_fatto":"2026-10-26T10:00:00Z"})
                else:
                    for x in list(CAL["fatti"]):
                        if x["id"]==i:
                            CAL["fatti"].remove(x); CAL["scadenze" if x["tipo"]=="scadenza" else "impegni"].append({k:v for k,v in x.items() if k not in ("tipo","quando_fatto")})
                return await route.fulfill(status=200, body=json.dumps({"ok":True,"id":i}), content_type="application/json", headers=CORS)
            if u.endswith("/assistente/invito"):
                # 27/10: rimanda la mail dell'invito (la porta vera: 404 se non è suo, 429 oltre 5 al giorno)
                CORS={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"}
                if CAL["invito_errore"]: return await route.fulfill(status=502, body=json.dumps({"errore":CAL["invito_errore"]}), content_type="application/json", headers=CORS)
                return await route.fulfill(status=200, body=json.dumps({"ok":True,"id":corpo["id"],"invito":"mandato"}), content_type="application/json", headers=CORS)
            if u.endswith("/assistente/aggiungi") or u.endswith("/assistente/elimina"):
                # 26/10, il calendario vero: aggiungere a mano e eliminare (la porta vera controlla di più: qui basta il rifiuto su richiesta)
                CORS={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"}
                if CAL["giu"]: return await route.fulfill(status=502, body='{"errore":"non riesco a salvare: riprova tra poco"}', content_type="application/json", headers=CORS)
                if u.endswith("/aggiungi"):
                    if CAL.get("rifiuta"): return await route.fulfill(status=400, body=json.dumps({"errore":CAL["rifiuta"]}), content_type="application/json", headers=CORS)
                    k="impegni" if corpo["tipo"]=="impegno" else "scadenze"; CAL["n"]+=1
                    riga={"id":("n%d"%CAL["n"]) if k=="impegni" else ("sn%d"%CAL["n"]),"cosa":corpo["cosa"],"giorno":corpo["giorno"]}
                    if k=="impegni": riga["ora"]=corpo.get("ora")
                    else: riga.update(importo=corpo.get("importo"), ogni_mese=bool(corpo.get("ogni_mese")))
                    if corpo.get("nota"): riga["nota"]=corpo["nota"]
                    CAL[k].append(riga)
                    # 27/10: per un impegno la porta ha già mandato (o no) la mail dell'invito: `invito` = "mandato" | "niente mail" | "errore: …"
                    return await route.fulfill(status=201, body=json.dumps({"ok":True,"tipo":corpo["tipo"],**riga,**({"invito":CAL["invito"]} if k=="impegni" else {})}), content_type="application/json", headers=CORS)
                for k in ("impegni","scadenze"):
                    for x in list(CAL[k]):
                        if x["id"]==corpo["id"]: CAL[k].remove(x); return await route.fulfill(status=200, body=json.dumps({"ok":True,"id":corpo["id"]}), content_type="application/json", headers=CORS)
                return await route.fulfill(status=404, body='{"errore":"non è tuo, o non esiste"}', content_type="application/json", headers=CORS)
            if NOVA["acceso"] and u.endswith("/parla") and corpo.get("da_dove")=="chat":
                sub={"id":"abc12345-n","testo":"Posso prepararti uno strumento per le interrogazioni.","azione":{"servizio":"commissione","tipo":"Strumento web","bozza":"Uno strumento per preparare le interrogazioni"},"passa":False}
                return await route.fulfill(status=201, body=json.dumps({"ok":True,"id":"abc12345","subito":sub}), content_type="application/json", headers={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"})
            return await route.fulfill(status=201, body='{"ok":true,"id":"abc12345"}', content_type="application/json", headers={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"})
        if u.endswith("/assistente/calendario"):
            CORS={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"}
            if CAL["giu"]: return await route.abort()
            ordina=lambda l: sorted(l,key=lambda x:(x["giorno"],x.get("ora") or ""))
            return await route.fulfill(body=json.dumps({"impegni":ordina(CAL["impegni"]),"scadenze":ordina(CAL["scadenze"]),"fatti":CAL["fatti"]}), content_type="application/json", headers=CORS)
        if u.endswith("/nova"): return await route.fulfill(body=json.dumps({"acceso":NOVA["acceso"]}), content_type="application/json")
        # 28/10: senza l'intestazione CORS il browser buttava la risposta e «i numeri della vetrina arrivano» era rossa da prima
        if u.endswith("/vetrina"): return await route.fulfill(body='{"canzoni":5747,"attrezzi":41}', content_type="application/json", headers={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"})
        if "/risposte" in u:
            conta_risposte.append(1); risposte_di[route.request.frame.page]=risposte_di.get(route.request.frame.page,0)+1
            return await route.fulfill(body=json.dumps({"risposte":RISPOSTE}), content_type="application/json")
        return await route.fulfill(body='[]', content_type="application/json")
    await route.fulfill(status=404, body="")
async def vai_a(pg, k):
    """26/10: per chi è di casa la barra delle schede in basso non c'è più: le schede si raggiungono dal menù ☰ («Chat» è la prima)."""
    await pg.click("#apri-conv"); await pg.wait_for_timeout(450)
    await pg.click(f'#menu-schede .menu-scheda[data-vai="{k}"]'); await pg.wait_for_timeout(350)
async def apri_resto(pg):
    """26/10: chi è di casa apre sulla chat; il benvenuto e le domande del giorno stanno dietro il collegamento nel pannello ☰."""
    await pg.click("#apri-conv"); await pg.wait_for_timeout(400)
    await pg.click("#conv-resto"); await pg.wait_for_timeout(400)
SOST={"pronto":False,"modi":[]}
NOVA={"acceso":False}
RISPOSTE=[]
def ok(c,m):
    print(("  ✅ " if c else "  ❌ ")+m); 
    if not c: ok.errori+=1
ok.errori=0
async def main():
    global SOST, PAGINA
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        ctx=await b.new_context(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True)
        await ctx.route("**/*", instrada)
        pg=await ctx.new_page(); errori=[]
        pg.on("pageerror", lambda e: errori.append(str(e)))
        print("── primo arrivo")
        # 26/10: l'ingresso ora viene prima di #o1, ma qui il server dei conti non c'è (insieme.json non è servito): un guasto
        # non chiude la porta, l'ingresso fa solo un lampo di icona e la pagina esce da sotto. L'ingresso vero: in fondo
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        ok(await pg.is_visible("#o1"), "si apre su Inizia, «Come vuoi chiamarmi?»")
        ok(await pg.inner_text("#et-inizia")=="Inizia", "la prima scheda si chiama Inizia")
        ok(not await pg.is_visible("#p-chi-sono"), "le altre schede sono chiuse")
        await pg.click("#s-chi-sono"); await pg.wait_for_timeout(300)
        ok(await pg.is_visible("#tcs") and "#chi-sono" in pg.url, "tocco «Chi sono»: pannello e indirizzo")
        testo_chi=await pg.inner_text("#p-chi-sono")
        ok("Non rispondo: anticipo" in testo_chi and "Imparo te" in testo_chi and "Per chiunque" in testo_chi and not await pg.evaluate("!!document.querySelector('#p-chi-sono #tf')"), "Chi sono parla di chi è JJA-VIS; l'elenco di cosa so fare non c'è più (JJ, 29/9)")
        ok(not any(p in testo_chi for p in ["Albero","JARVIS privato","Stark","archetip"]), "dal blueprint solo quello che si può dire in pubblico")
        ok(testo_chi.count("Chi mi costruisce")==1 and testo_chi.count("corriere")<=2, "«Da dove nasco» non si ripete (JJ, 29/9)")
        await pg.click("#s-sa-fare"); await pg.wait_for_timeout(300)
        ok(await pg.is_visible("#tf") and "#sa-fare" in pg.url, "«Cosa so fare» è una scheda sua")
        ok(await pg.inner_text("#n-canzoni")=="5.747", "i numeri della vetrina arrivano")
        await pg.click("#s-chi-sono"); await pg.wait_for_timeout(300)
        ok(not await pg.evaluate("!!document.querySelector('#p-chi-sono #conto')"), "Quanto costo non è più in Chi sono")
        ok(await pg.inner_text("#prova")=="Comincia", "Provami dice Comincia, senza nome")
        await pg.click("#s-profilo"); await pg.wait_for_timeout(200)
        ok(await pg.is_visible("#profilo-vuoto") and not await pg.is_visible("#profilo-nome"), "profilo senza nome: manda a Inizia")
        await pg.click('#temi-profilo [data-tema="naturale"]')
        ok(await pg.evaluate("document.documentElement.dataset.tema")=="naturale", "il tema cambia dal profilo")
        await pg.click("#s-sostieni"); await pg.wait_for_timeout(200)
        ok(await pg.is_visible("#sostieni-presto") and await pg.inner_html("#sostieni-modi")=="", "sostieni senza link: nessun pulsante finto")
        print("── il dito")
        await pg.click("#s-inizia"); await pg.wait_for_timeout(200)
        async def scorri(dx):
            await pg.evaluate("""dx=>{const m=document.querySelector('main');const T=(x,y)=>new Touch({identifier:1,target:m,clientX:x,clientY:y});
              m.dispatchEvent(new TouchEvent('touchstart',{touches:[T(300,400)],changedTouches:[T(300,400)],bubbles:true}));
              m.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[T(300+dx,410)],bubbles:true}));}""", dx)
            await pg.wait_for_timeout(250)
        await scorri(-150); ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "a sinistra: Chi sono")
        await scorri(-150); ok(await pg.evaluate("document.body.dataset.scheda")=="sa-fare", "ancora: Cosa so fare")
        await scorri(150); ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "a destra: torna")
        await scorri(-30); ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "un tocco corto non cambia scheda")
        await pg.click("#s-inizia"); await scorri(150); ok(await pg.evaluate("document.body.dataset.scheda")=="inizia", "dalla prima non si va oltre")
        print("── la prima conversazione")
        await pg.click('#nomi .scelta:has-text("Atlas")'); await pg.click("#avanti-o1"); await pg.wait_for_timeout(300)
        await pg.click("#avanti-o2"); await pg.fill("#tuo-nome","Marco"); await pg.click("#avanti-o3"); await pg.wait_for_timeout(3200)
        ok(await pg.inner_text("#et-inizia")=="Atlas", "la scheda prende il nome dato: Atlas")
        ok(await pg.is_visible("#d0") and not await pg.is_visible("#parla"), "sotto il benvenuto le domande (prima la vita, 27/10); la chat arriva a questionario finito (JJ, 29/9)")
        await pg.click('#d0 .scelta:has-text("Lavoro")'); await pg.wait_for_timeout(300)
        await pg.click('#d1 .scelta:has-text("Corriere")'); await pg.wait_for_timeout(200)
        await pg.click('#salto-cosa'); await pg.wait_for_timeout(300)
        ok(await pg.evaluate("document.body.dataset.scheda")=="sa-fare", "«Cosa so fare →» porta a Cosa so fare, non più a Chi sono")
        await pg.click("#s-chi-sono"); await pg.wait_for_timeout(300)
        ok(await pg.inner_text("#prova")=="Parla con Atlas", "Provami adesso dice Parla con Atlas")
        await pg.click("#s-profilo"); await pg.wait_for_timeout(200)
        so=await pg.inner_text("#so-di-te")
        ok("Marco" in so and "Corriere" in so, "Cosa so di te: nome e mestiere")
        ok(await pg.input_value("#nuova-sigla")=="Atlas", "il nome nel campo del profilo")
        await pg.fill("#nuova-sigla","Iris"); await pg.click("#cambia-nome")
        ok(await pg.inner_text("#nome-testata")=="Iris" and await pg.inner_text("#et-inizia")=="Iris", "cambio nome: testata e scheda")
        print("── investitori")
        await pg.click("#s-investitori"); await pg.wait_for_timeout(200)
        ok(await pg.is_disabled("#inv-manda"), "Manda spento finché mancano i campi")
        await pg.click('#inv-interesse .scelta:has-text("Investire")'); await pg.fill("#inv-nome","Anna Rossi"); await pg.fill("#inv-mail","anna@esempio")
        await pg.click("#inv-manda"); ok("mail" in (await pg.inner_text("#inv-esito")), "mail incompleta: lo dice")
        await pg.fill("#inv-mail","anna@esempio.it"); await pg.click("#inv-manda")
        ok("spunta" in (await pg.inner_text("#inv-esito")), "senza consenso non parte")
        await pg.check("#inv-ok"); await pg.fill("#inv-messaggio","Vorrei il dossier."); await pg.click("#inv-manda"); await pg.wait_for_timeout(300)
        inv=[d for (r,d) in inviati if r=="parla"]
        ok(len(inv)==1 and inv[0]["da_dove"]=="investitori", "parte su /parla con da_dove investitori")
        if inv: print("     testo:", json.dumps(inv[0]["testo"], ensure_ascii=False))
        ok(inv and "anna@" not in inv[0]["testo"] and "Anna" not in inv[0]["testo"], "nome e mail NON nel testo (va all'IA)")
        ok(inv and inv[0].get("contatto",{}).get("mail")=="anna@esempio.it" and inv[0]["contatto"].get("consenso") is True, "nome e mail viaggiano in «contatto», con consenso")
        t=await pg.inner_text("#inv-esito"); print("     esito:",t); ok("Arrivato" in t, "dice Arrivato")
        print("── costruiscimi qualcosa")
        await pg.click("#s-bottega"); await pg.wait_for_timeout(200)
        ok(await pg.is_visible("#costruisci") and await pg.is_visible("#clio") and await pg.is_visible("#sopralluogo"), "Clio, Sopralluogo e commissioni sono nella Bottega")
        ok(not await pg.evaluate("!!document.querySelector('#p-chi-sono #costruisci, #p-chi-sono #clio, #p-chi-sono #sopralluogo')"), "e non più in Chi sono")
        await pg.click('#cm-cosa .scelta:has-text("Sito")'); await pg.fill("#cm-descrizione","Il sito della pizzeria col menù")
        await pg.fill("#cm-mail","luca@pizzeria.it"); await pg.fill("#cm-nome","Luca")
        await pg.click("#cm-manda"); ok("spunta" in await pg.inner_text("#cm-esito"), "senza consenso non parte")
        await pg.check("#cm-ok"); await pg.click("#cm-manda"); await pg.wait_for_timeout(300)
        cm=[d for (r,d) in inviati if r=="parla" and d.get("da_dove")=="commissione"]
        ok(len(cm)==1 and cm[0]["testo"].startswith("🛠 Sito o pagina web — ") and "luca@" not in cm[0]["testo"], "parte come commissione, senza mail nel testo")
        ok(cm and cm[0]["contatto"]["mail"]=="luca@pizzeria.it", "la mail nel contatto")
        ok("preventivo" in await pg.inner_text("#cm-esito"), "dice che il preventivo arriva per mail")
        print("── chi torna (il caso che si rompeva)")
        e_prima=len(errori)
        pg2=await ctx.new_page(); pg2.on("pageerror", lambda e: errori.append(str(e)))
        await pg2.goto(BASE+"#investitori"); await pg2.wait_for_timeout(400)
        ok(len(errori)==e_prima, "nessun errore all'avvio con un nome già salvato")
        ok(await pg2.evaluate("document.body.dataset.scheda")=="investitori", "un link a #investitori apre quella scheda")
        ok(await pg2.inner_text("#et-inizia")=="Iris", "ritrova il nome")
        await pg2.goto(BASE+"#dati"); await pg2.wait_for_timeout(300)
        ok(await pg2.evaluate("document.body.dataset.scheda")=="profilo", "#dati apre il profilo, dov'è l'informativa")
        print("── sostieni con un link vero")
        SOST={"pronto":True,"modi":[{"nome":"Offrimi un caffè","url":"https://ko-fi.com/esempio"}]}
        await pg2.goto(BASE+"#sostieni"); await pg2.reload(); await pg2.wait_for_timeout(400)
        ok("Offrimi un caffè" in await pg2.inner_text("#sostieni-modi"), "col link compare il pulsante")
        print("── la prima scheda, al ritorno")
        await pg2.goto(BASE+"#inizia"); await pg2.wait_for_timeout(300)
        ok(await pg2.locator("#benvenuto #ricomincia").count()==0 and "Ricomincia" not in await pg2.inner_text("#benvenuto"), "niente «Ricomincia» nella prima scheda")
        ok(await pg2.locator('#benvenuto a[href="#profilo"]').count()==1, "rimanda al Profilo")
        print("── le domande del ritorno, in fila")
        pg3=await ctx.new_page(); pg3.on("pageerror", lambda e: errori.append(str(e)))
        await pg3.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'a1b2c3d4e5f60718',nome:'Nova',tema:'deciso',tuo:'Jacopo',inviato:true,mestiere:'Corriere o autista',tempo:'Preventivi, conti, fatture'}))")
        await pg3.goto(BASE); await pg3.wait_for_timeout(300)
        await apri_resto(pg3)   # 26/10: chi è di casa apre sulla chat; le domande del giorno stanno nel benvenuto, dietro ☰
        d1=await pg3.evaluate("document.getElementById('conosci-domanda').textContent"); ok("ora comincia" in d1, "prima domanda: "+d1)
        await pg3.click('#conosci-scelte .scelta:has-text("Cambia ogni giorno")'); await pg3.wait_for_timeout(1200)
        d2=await pg3.evaluate("document.getElementById('conosci-domanda').textContent"); ok(d2!=d1 and d2, "dopo un secondo, senza ricaricare: "+d2)
        for _ in range(10):
            if not await pg3.is_visible("#conosci-scelte .scelta:not([disabled])"): break
            await pg3.click("#conosci-scelte .scelta:not([disabled]) >> nth=0")
            if await pg3.is_visible("#conosci-ok") and not await pg3.is_disabled("#conosci-ok"): await pg3.click("#conosci-ok")   # 28/10: a scelta multipla si manda con «Segna»
            await pg3.wait_for_timeout(1100)
        ok(await pg3.is_visible("#conosci-fine") and not await pg3.is_visible("#conosci"), "finite le domande: «di te so già parecchio»")
        await pg3.close()
        print("── le risposte arrivano da sole")
        pg4=await ctx.new_page(); pg4.on("pageerror", lambda e: errori.append(str(e)))
        await pg4.clock.install()
        await pg4.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'a1b2c3d4e5f60718',nome:'Nova',inviato:true,mestiere:'Ufficio'}))")
        await pg4.goto(BASE+"#parla"); await pg4.wait_for_timeout(300)
        await pg4.fill("#scrivi","Mi faresti il sito della mia azienda?"); await pg4.click("#manda-chat"); await pg4.wait_for_timeout(300)
        prima=risposte_di.get(pg4,0)
        await vai_a(pg4, "chi-sono")   # 26/10: dal menù ☰, la barra delle schede non c'è più
        RISPOSTE.append({"id":"abc12345","domanda":"Mi faresti il sito della mia azienda?","risposta":"Sì, si può fare: lasciami la mail.","quando":"2026-09-26T10:00:00Z"})
        await pg4.clock.fast_forward(21000); await pg4.wait_for_timeout(400)
        ok(risposte_di.get(pg4,0)>prima, "dopo 20 secondi chiede da sola")
        ok("si può fare" in await pg4.inner_text("#chat"), "la risposta è nella chat senza ricaricare")
        ok(await pg4.evaluate("document.getElementById('apri-conv').classList.contains('nuovo')"), "il puntino sul «☰», perché sei altrove")
        await pg4.click("#apri-conv"); await pg4.wait_for_timeout(450)
        ok(await pg4.evaluate("document.querySelector('#menu-schede .menu-scheda[data-vai=inizia]').classList.contains('nuovo')"), "e anche sulla voce «Chat» del menù")
        await pg4.click('#menu-schede .menu-scheda[data-vai="inizia"]'); await pg4.wait_for_timeout(300)
        ok(not await pg4.evaluate("document.getElementById('apri-conv').classList.contains('nuovo')"), "tornando alla chat, il puntino si spegne")
        # (solo le richieste di QUESTA pagina: le altre aperte nello stesso browser aspettano risposte loro e chiedono ogni 20 secondi)
        dopo=risposte_di.get(pg4,0); await pg4.clock.fast_forward(180000); await pg4.wait_for_timeout(300)
        ok(risposte_di.get(pg4,0)==dopo, "niente più in attesa: smette di chiedere")
        RISPOSTE.clear(); await pg4.close()
        print("── Clio, per le guide")
        pg5=await ctx.new_page(); pg5.on("pageerror", lambda e: errori.append(str(e)))
        await pg5.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'b1b2c3d4e5f60718',nome:'Nova'}))")
        await pg5.goto(BASE+"#clio"); await pg5.wait_for_timeout(300)
        ok(await pg5.evaluate("document.body.dataset.scheda")=="bottega" and await pg5.is_visible("#cl-manda"), "#clio apre la Bottega sulla sezione Clio")
        await pg5.fill("#cl-lingue","italiano, inglese"); await pg5.fill("#cl-mail","giulia@guide.it"); await pg5.fill("#cl-nome","Giulia")
        await pg5.click("#cl-manda"); ok("spunta" in await pg5.inner_text("#cl-esito"), "senza consenso non parte")
        await pg5.check("#cl-ok"); await pg5.click("#cl-manda"); await pg5.wait_for_timeout(300)
        cl=[d for (r,d) in inviati if r=="parla" and d.get("da_dove")=="clio"]
        ok(len(cl)==1 and cl[0]["testo"].startswith("🏛 Clio — lingue: italiano, inglese") and "giulia@" not in cl[0]["testo"] and cl[0]["contatto"]["mail"]=="giulia@guide.it", "parte come clio, mail nel contatto e non nel testo")
        ok("invito" in await pg5.inner_text("#cl-esito"), "dice che l'invito arriva per mail")
        await pg5.goto(BASE+"#d1"); await pg5.wait_for_timeout(200)
        if await pg5.is_visible("#d0"): await pg5.click('#d0 .scelta:has-text("Lavoro")'); await pg5.wait_for_timeout(300)   # 27/10: prima la vita
        await pg5.click('#d1 .scelta:has-text("Guida turistica")'); await pg5.wait_for_timeout(200)
        ok(await pg5.locator('#r1 a[href="#clio"]').count()==1, "chi sceglie Guida turistica si sente dire di Clio, col link")
        ok("Ripetere lo stesso tour" in await pg5.inner_text('.scelte[data-campo="tempo"]'), "e le domande dopo sono da guida")
        await pg5.close()
        print("── sopralluogo")
        pg6=await ctx.new_page(); pg6.on("pageerror", lambda e: errori.append(str(e)))
        await pg6.goto(BASE+"#sopralluogo"); await pg6.wait_for_timeout(300)
        ok(await pg6.evaluate("document.body.dataset.scheda")=="bottega" and await pg6.is_visible("#so-manda"), "#sopralluogo apre la Bottega sulla sezione")
        await pg6.click('#so-cosa .scelta:has-text("La mia attività")'); await pg6.fill("#so-link","pizzeria"); await pg6.fill("#so-mail","luca@pizzeria.it")
        await pg6.click("#so-manda"); ok("link" in await pg6.inner_text("#so-esito"), "un link senza punto: lo dice")
        await pg6.fill("#so-link","pizzeriadaluca.it"); await pg6.click("#so-manda")
        ok("spunta" in await pg6.inner_text("#so-esito"), "senza consenso non parte")
        await pg6.check("#so-ok"); await pg6.fill("#so-note","il menù non si trova"); await pg6.click("#so-manda"); await pg6.wait_for_timeout(300)
        so=[d for (r,d) in inviati if r=="parla" and d.get("da_dove")=="sopralluogo"]
        ok(len(so)==1 and so[0]["link"]=="https://pizzeriadaluca.it/" or (so and so[0]["link"]=="https://pizzeriadaluca.it"), "il link parte a parte, con https:// aggiunto")
        ok(so and so[0]["testo"].startswith("🔎 La mia attività: https://pizzeriadaluca.it") and "luca@" not in so[0]["testo"] and so[0]["contatto"]["mail"]=="luca@pizzeria.it", "testo col link, mail solo nel contatto")
        ok("per mail" in await pg6.inner_text("#so-esito"), "dice che arriva per mail")
        await pg6.close()
        await pg2.goto(BASE+"#bottega"); await pg2.wait_for_timeout(200)
        ok(await pg2.evaluate("document.body.dataset.scheda")=="bottega", "#bottega apre la Bottega")
        larghe=await pg2.evaluate("[...document.querySelectorAll('.schede .et')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.textContent)")
        ok(larghe==[] or larghe==["Iris"], "le sei etichette ci stanno a 390 px: "+(",".join(larghe) or "tutte intere"))
        print("── una sola chat nella prima scheda")
        pg9=await b.new_page(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True)
        await pg9.route("**/*", instrada); pg9.on("pageerror", lambda e: errori.append(str(e)))
        await pg9.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'d1b2c3d4e5f60718',nome:'Nova',tuo:'Jacopo',inviato:true,mestiere:'Ufficio',mail:'jacopo@esempio.it'}))")
        await pg9.goto(BASE+"#inizia"); await pg9.wait_for_timeout(300)
        scrivibili=await pg9.evaluate("[...document.querySelectorAll('#p-inizia textarea')].filter(t=>t.offsetParent!==null).map(t=>t.id)")
        ok(scrivibili==["scrivi"], "chi torna ha un posto solo dove scrivere: "+",".join(scrivibili))
        ok(not await pg9.is_visible("#d4") and "scrivermi ancora" not in await pg9.inner_text("#p-inizia"), "«Vuoi scrivermi ancora?» non c'è più")
        await pg9.fill("#scrivi","Mi rispondi per mail?"); await pg9.click("#manda-chat"); await pg9.wait_for_timeout(300)
        ch=[d for (r,d) in inviati if r=="parla" and d.get("testo")=="Mi rispondi per mail?"]
        ok(ch and ch[0].get("contatto",{}).get("mail")=="jacopo@esempio.it" and "jacopo@" not in ch[0]["testo"], "con la mail salvata, la chat la manda nel contatto: la risposta arriva anche lì")
        ok("per mail" in await pg9.inner_text("#esito-chat"), "e lo dice")
        print("── la mail dal Profilo")
        await pg9.goto(BASE+"#profilo"); await pg9.wait_for_timeout(300)
        ok(await pg9.input_value("#profilo-mail")=="jacopo@esempio.it", "il Profilo mostra la mail")
        await pg9.fill("#profilo-mail",""); await pg9.click("#salva-mail")
        ok(not await pg9.evaluate("JSON.parse(localStorage.getItem('jjavis-io')).mail"), "svuotata e salvata: tolta")
        await pg9.fill("#profilo-mail","nuova@esempio.it"); await pg9.click("#salva-mail")
        ok("spunta" in await pg9.inner_text("#esito-profilo"), "senza consenso non si salva")
        await pg9.check("#profilo-mail-ok"); await pg9.click("#salva-mail")
        ok(await pg9.evaluate("JSON.parse(localStorage.getItem('jjavis-io')).mail")=="nuova@esempio.it", "con la spunta sì")
        print("── Numeri")
        await pg9.goto(BASE+"#numeri"); await pg9.wait_for_timeout(300)
        ok(await pg9.evaluate("document.body.dataset.scheda")=="numeri" and await pg9.is_visible("#conto") and await pg9.is_visible("#numeri-problema .numeri"), "Numeri: Quanto costo e il problema in numeri")
        ok(not await pg9.evaluate("!!document.querySelector('#p-investitori .numeri')") and await pg9.locator('#p-investitori a[href="#numeri-problema"]').count()==1, "Investi non ha più i numeri e rimanda lì")
        await pg9.goto(BASE+"#conto"); await pg9.wait_for_timeout(300)
        ok(await pg9.evaluate("document.body.dataset.scheda")=="numeri", "i vecchi link a #conto aprono Numeri")
        await pg9.close()
        print("── la prima volta")
        pga=await b.new_page(viewport={"width":390,"height":844}); await pga.route("**/*", instrada)
        await pga.goto(BASE); await pga.wait_for_timeout(200)
        ok(await pga.locator("#messaggio").count()==0 and "Manda le risposte" in await pga.inner_text("#d4"), "l'ultimo passo del sondaggio non ha più il campo messaggio")
        await pga.close()
        print("── la barra scorre")
        pg7=await b.new_page(viewport={"width":320,"height":700}, has_touch=True, is_mobile=True)
        await pg7.route("**/*", instrada); pg7.on("pageerror", lambda e: errori.append(str(e)))
        await pg7.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'c1b2c3d4e5f60718',nome:'Nova'}))")   # senza il sondaggio mandato: la barra delle schede c'è ancora (26/10: per chi è di casa la sostituisce il menù ☰)
        await pg7.goto(BASE+"#inizia"); await pg7.wait_for_timeout(300)
        m=await pg7.evaluate("(()=>{const c=document.querySelector('.schede');return {sw:c.scrollWidth,cw:c.clientWidth,min:Math.min(...[...c.children].map(b=>b.getBoundingClientRect().width)),tagliate:[...document.querySelectorAll('.schede .et')].filter(e=>e.scrollWidth>e.clientWidth+1).length,pagina:document.documentElement.scrollWidth}})()")
        ok(m["sw"]>m["cw"], f"a 320 px la barra scorre ({m['sw']} su {m['cw']} px)")
        ok(m["min"]>=74 and m["tagliate"]==0, f"nessuna scheda schiacciata: la più stretta {m['min']:.0f} px, etichette intere")
        ok(m["pagina"]<=320, "la pagina non scorre di lato")
        ok(await pg7.evaluate("document.querySelector('.schede').classList.contains('piu-dx')"), "la sfumatura a destra dice che ce ne sono altre")
        await pg7.goto(BASE+"#sostieni"); await pg7.wait_for_timeout(60)
        ok(await pg7.evaluate("document.documentElement.scrollWidth")<=320, "anche mentre il pannello entra, la pagina non si allarga")
        await pg7.wait_for_timeout(640)
        r=await pg7.evaluate("(()=>{const b=document.getElementById('s-sostieni').getBoundingClientRect();return [b.left,b.right]})()")
        ok(r[0]>=0 and r[1]<=321, f"aprendo Sostieni, la sua scheda si porta in vista ({r[0]:.0f}–{r[1]:.0f} px)")
        await pg7.close()
        pg8=await b.new_page(viewport={"width":800,"height":700})
        await pg8.route("**/*", instrada); await pg8.goto(BASE); await pg8.wait_for_timeout(300)
        c=await pg8.evaluate("(()=>{const c=document.querySelector('.schede');const a=c.firstElementChild.getBoundingClientRect().left, z=c.clientWidth-c.lastElementChild.getBoundingClientRect().right;return [c.scrollWidth<=c.clientWidth, Math.abs(a-z)<2]})()")
        ok(c[0] and c[1], "su uno schermo largo non scorre e resta centrata")
        await pg8.close()
        print("── Creator o gamer")
        await pg2.goto(BASE+"#d1"); await pg2.wait_for_timeout(200)
        ok(await pg2.locator('#d1 .scelta:has-text("Creator o gamer")').count()==1, "c'è il mestiere Creator o gamer")
        print("── la testata di JARVIS (29 settembre)")
        pg2=await ctx.new_page(); pg2.on("pageerror", lambda e: errori.append(str(e)))
        await pg2.goto(BASE); await pg2.evaluate("localStorage.clear()"); await pg2.reload(); await pg2.wait_for_timeout(300)
        ok(await pg2.evaluate("getComputedStyle(document.querySelector('.testa')).position")!="fixed", "senza nome il globo resta grande al centro, non fisso")
        await pg2.evaluate("localStorage.setItem(CHIAVE, JSON.stringify({nome:'Nova',tema:'tech',id:'x1'}))")
        for sch in ["inizia","bottega","numeri","investitori"]:
            await pg2.goto(BASE+"#"+sch); await pg2.reload(); await pg2.wait_for_timeout(300)
            await pg2.mouse.wheel(0,1200); await pg2.wait_for_timeout(200)
            t=await pg2.evaluate("(()=>{const r=document.querySelector('.testa').getBoundingClientRect(),g=document.querySelector('#globo').getBoundingClientRect();return {pos:getComputedStyle(document.querySelector('.testa')).position,top:r.top,gx:g.left,nome:document.querySelector('#nome-testata').textContent,sotto:document.querySelector('#sotto-testata').textContent}})()")
            ok(t["pos"]=="fixed" and t["top"]<=1 and t["gx"]<40 and t["nome"]=="Nova" and t["sotto"]=="il tuo JJA-VIS", f"{sch}: testata fissa in alto anche scorrendo, globo a sinistra, «Nova» e «il tuo JJA-VIS»")
        coperto=await pg2.evaluate("(()=>{window.scrollTo(0,0);const t=document.querySelector('.testa').getBoundingClientRect().bottom;const p=document.querySelector('.pannello.attivo .etichetta');return p.getBoundingClientRect().top<t})()")
        ok(not coperto, "la testata non copre il primo pannello")
        print("── Nova è una chat, come JARVIS (29 settembre)")
        await pg2.evaluate("localStorage.setItem(CHIAVE, JSON.stringify({nome:'Nova',tema:'tech',id:'x1',tuo:'Jacopo',inviato:true,mestiere:'Corriere o autista',tempo:'Preventivi, conti, fatture',chat:[{ruolo:'tu',testo:'Come mi potresti aiutare?'},{ruolo:'io',testo:'Ultima risposta di prova',nuovo:true}]}))")
        await pg2.goto(BASE+"#inizia"); await pg2.reload(); await pg2.wait_for_timeout(700)
        c=await pg2.evaluate("""(()=>{const b=document.querySelector('#barra-chat').getBoundingClientRect(), n=document.querySelector('.schede').getBoundingClientRect();
          const bolle=[...document.querySelectorAll('#chat .bolla')], u=bolle[bolle.length-1].getBoundingClientRect();
          return {pos:getComputedStyle(document.querySelector('#parla')).position, sopra:Math.abs(b.bottom-innerHeight)<=1,
            titolo:document.querySelector('#nome-testata').innerText, globo:document.querySelector('#globo').getBoundingClientRect().width>=40, nav:n.height>0, ultima:u.bottom<=b.top+1 && u.top>=0,
            spiega:getComputedStyle(document.querySelector('.spiega-chat')).display!=='none'}})()""")
        ok(c["pos"]=="fixed" and c["sopra"] and not c["nav"], "la chat è a tutto schermo e la casella sta in fondo allo schermo: la barra delle schede non c'è più")
        ok(c["globo"] and c["titolo"].strip()=="Nova", "in alto la testata: il globo e il nome dell'assistente, non il titolo «Parla con»: la chat è la pagina")
        nav_=await pg2.evaluate("[...document.querySelectorAll('.schede button[data-scheda]')].map(b=>b.dataset.scheda)")
        await pg2.click("#apri-conv"); await pg2.wait_for_timeout(450)
        voci=await pg2.evaluate("[...document.querySelectorAll('#menu-schede .menu-scheda')].map(b=>b.dataset.vai)")
        ok(voci==nav_ and len(voci)>=7, f"il menù ☰ ha una voce per ogni scheda della barra ({len(voci)})")
        await pg2.click("#chiudi-conv"); await pg2.wait_for_timeout(450)
        ok(c["ultima"], "aprendo Nova si vede l'ultimo messaggio, sopra la casella")
        ok(c["spiega"] and "Non rispondo in automatico" in await pg2.inner_text("#spiega-chat"), "sotto la chat c'è la frase vera: senza account non rispondo in automatico")
        await apri_resto(pg2)
        ordine=await pg2.evaluate("""(()=>{const y=id=>document.getElementById(id).getBoundingClientRect().top;
          return y('saluto')<y('ricordo') && y('ricordo')<y('salto-cosa') && y('salto-cosa')<y('saluto2')})()""")
        ok(ordine, "dietro il collegamento, chi torna: saluto, poi «Mi ricordo di te», poi «Cosa so fare →», poi il resto")
        ok(not await pg2.is_visible("#barra-chat"), "col benvenuto in vista la chat non c'è: o l'una o l'altro, mai uno sopra l'altra")
        await pg2.click("#torna-chat"); await pg2.wait_for_timeout(300)
        await pg2.goto(BASE+"#bottega"); await pg2.wait_for_timeout(300)
        ok(not await pg2.is_visible("#barra-chat"), "sulle altre schede la casella non c'è")
        vede_=lambda sel: pg2.is_visible(sel)
        print("── Nova risponde subito e porta alla Bottega (2 ottobre)")
        NOVA["acceso"]=True
        await pg2.evaluate("localStorage.setItem(CHIAVE, JSON.stringify({nome:'Nova',tema:'tech',id:'abcdef0123456789',inviato:true,mestiere:'Altro',tempo:'Altro lavoro ripetitivo'}))")
        await pg2.goto(BASE+"#inizia"); await pg2.reload(); await pg2.wait_for_timeout(600)
        ok("Ti rispondo subito" in await pg2.inner_text("#spiega-chat") and "Non rispondo in automatico" not in await pg2.inner_text("#spiega-chat"), "con Nova accesa la frase sotto la chat dice la cosa vera")
        await pg2.fill("#scrivi","Sono un insegnante e perdo tempo con le interrogazioni"); await pg2.click("#manda-chat"); await pg2.wait_for_timeout(600)
        bolle=await pg2.evaluate("[...document.querySelectorAll('#chat .bolla')].map(b=>b.className+'|'+b.innerText)")
        ok(any("io|Posso prepararti" in b for b in bolle) and not any("appena posso" in b for b in bolle), "la risposta arriva subito, niente «ti rispondo appena posso»")
        await pg2.click("#chat .azione"); await pg2.wait_for_timeout(500)
        ok(await pg2.evaluate("document.body.dataset.scheda")=="bottega" and await pg2.input_value("#cm-descrizione")=="Uno strumento per preparare le interrogazioni"
           and await pg2.evaluate("[...document.querySelectorAll('#cm-cosa .scelta')].find(x=>x.getAttribute('aria-pressed')==='true').textContent.trim()")=="Strumento web",
           "il pulsante apre la Bottega su «Costruiscimi qualcosa», col tipo scelto e la richiesta già scritta")
        await pg2.reload(); await pg2.wait_for_timeout(500)
        # 2/10, JJ: letta e rientrato, la chat è pulita; la conversazione va nelle precedenti, col suo pulsante
        # (26/10: le precedenti stanno nella scheda ☰, e toccata una riga diventa la conversazione in corso)
        await vai_a(pg2, "inizia"); await pg2.click("#apri-conv"); await pg2.wait_for_timeout(450)
        ok(await pg2.evaluate("document.querySelectorAll('#chat .bolla').length")==0, "ricaricando, la chat è pulita")
        await pg2.click("#conv-elenco .riga-apri >> nth=0"); await pg2.wait_for_timeout(300)
        ok(await pg2.evaluate("document.querySelectorAll('#chat .azione').length")==1,
           "toccata la conversazione precedente, si riapre nella chat, con la risposta e il suo pulsante")
        NOVA["acceso"]=False
        await pg2.goto(BASE+"#inizia"); await pg2.reload(); await pg2.wait_for_timeout(500)
        ok("Non rispondo in automatico" in await pg2.inner_text("#spiega-chat"), "con Nova spenta resta la frase di prima")
        print("── finite le domande del giorno, la frase se ne va (29 settembre)")
        await pg2.evaluate("(()=>{const c={};CONOSCERTI.slice(0,-1).forEach(q=>c[q.k]='x');localStorage.setItem(CHIAVE, JSON.stringify({nome:'Nova',tema:'tech',id:'x1',inviato:true,mestiere:'Creator o gamer',tempo:'Trovare idee per i contenuti',conosciute:c}))})()")
        await pg2.goto(BASE+"#inizia"); await pg2.reload(); await pg2.wait_for_timeout(600)
        await apri_resto(pg2)   # 26/10: le domande del giorno stanno nel benvenuto, dietro ☰
        ok("Oggi voglio sapere una cosa in più" in await pg2.inner_text("#saluto2"), "con una domanda ancora da fare, Nova dice «Oggi voglio sapere una cosa in più»")
        await pg2.click("#conosci-scelte .scelta >> nth=0"); await pg2.wait_for_timeout(1300)
        ok("Oggi voglio sapere" not in await pg2.inner_text("#saluto2") and await vede_("#conosci-fine"), "risposta l'ultima, la frase sparisce subito, senza ricaricare")
        print("── i passi fatti se ne vanno (29 settembre)")
        await pg2.evaluate("localStorage.clear()"); await pg2.goto(BASE+"#inizia"); await pg2.reload(); await pg2.wait_for_timeout(400)
        vede=lambda sel: pg2.is_visible(sel)
        await pg2.click("#nomi .scelta >> text=Nova"); await pg2.click("#avanti-o1"); await pg2.wait_for_timeout(250)
        grande=await pg2.evaluate("getComputedStyle(document.querySelector('.testa')).position!=='fixed' && document.querySelector('#globo').getBoundingClientRect().width>90 && Math.abs(document.querySelector('#globo').getBoundingClientRect().left+document.querySelector('#globo').getBoundingClientRect().width/2-innerWidth/2)<4")
        ok(grande, "scelto il nome, la sfera resta grande al centro: si fa piccola solo col saluto")
        await pg2.reload(); await pg2.wait_for_timeout(500)
        ok(await vede("#o2") and not await vede("#benvenuto") and not await vede("#o1"), "ricaricato dopo il nome: si riparte da «Come mi vuoi vedere?», non si salta")
        await pg2.click("#avanti-o2"); await pg2.wait_for_timeout(250)
        await pg2.reload(); await pg2.wait_for_timeout(500)
        ok(await vede("#o3") and not await vede("#benvenuto"), "ricaricato dopo il colore: si riparte da «E tu come ti chiami?»")
        await pg2.fill("#tuo-nome","Jacopo"); await pg2.click("#avanti-o3"); await pg2.wait_for_timeout(250)
        subito=await pg2.evaluate("""(()=>{const t=document.querySelector('#benvenuto').innerText;return {
          ordine: t.indexOf('Mi ricordo')>=0 && t.indexOf('Mi ricordo')<t.indexOf('scorrendo a destra'), scopri: t.includes('li scopri scorrendo a destra'),
          fissa: getComputedStyle(document.querySelector('.testa')).position==='fixed',
          tocca: document.querySelector('#tocca').offsetParent!==null, d0: document.querySelector('#d0').offsetParent!==null}})()""")
        ok(subito["ordine"] and subito["scopri"], "il saluto: «Mi ricordo di te… nel Profilo» sta sopra «Cosa so già fare lo scopri scorrendo a destra»")
        ok(await pg2.evaluate("(()=>{const y=id=>document.getElementById(id).getBoundingClientRect().top;return y('saluto')<y('ricordo')&&y('ricordo')<y('scopri')&&y('scopri')<y('salto-cosa')})()"), "primo saluto: saluto, «Mi ricordo», «lo scopri scorrendo a destra», «Cosa so fare →»")
        ok(await pg2.inner_text("#avanti-o1")=="Salva" and await pg2.inner_text("#avanti-o2")=="Salva" and await pg2.inner_text("#avanti3")=="Vai avanti", "pulsanti: «Salva», «Salva», «Vai avanti» (JJ, 29/9)")
        ok(not subito["fissa"] and not subito["tocca"] and not subito["d0"], "non compare tutto insieme: prima solo il saluto, la sfera ancora grande")
        await pg2.wait_for_timeout(900)
        ok(await pg2.evaluate("getComputedStyle(document.querySelector('.testa')).position")=="fixed" and not await vede("#tocca"), "poi la sfera e il nome vanno su")
        await pg2.wait_for_timeout(900)
        ok(await vede("#tocca") and not await vede("#d0"), "poi «Adesso imparo te»")
        await pg2.wait_for_timeout(1000)
        ok(await vede("#d0") and not await vede("#d1"), "dopo qualche istante «Cosa fai nella vita?» (27/10: la vita prima del lavoro)")
        ok(not await vede("#o2") and not await vede("#o3") and await vede("#benvenuto"), "scelti nome, colore e il mio nome: quei passi spariscono, resta il saluto")
        ok(await pg2.evaluate("getComputedStyle(document.querySelector('.testa')).position")=="fixed", "col saluto la sfera va in alto a sinistra")
        ok(not await vede("#barra-chat") and not await vede("#manda-chat"), "durante il questionario niente casella né Manda della chat")
        await pg2.click('#d0 .scelta >> text=Lavoro'); await pg2.wait_for_timeout(300)
        ok(await vede("#d1") and not await vede("#d0") and "Che lavoro fai?" in await pg2.inner_text("#d1"), "risposto «Lavoro»: ecco «Che lavoro fai?»")
        await pg2.click('#d1 .scelta >> text=Corriere o autista'); await pg2.wait_for_timeout(300)
        ok(not await vede("#d1") and await vede("#d2") and "interessa davvero" in await pg2.inner_text("#d2"), "risposto «che lavoro fai»: la domanda sparisce, la risposta di Nova apre la seguente")
        ok(not await vede("#tocca"), "anche «Adesso imparo te» se ne va")
        visibili=await pg2.evaluate("[...document.querySelectorAll('#p-inizia .domanda')].filter(x=>x.offsetParent!==null && x.id!=='benvenuto').map(x=>x.id)")
        ok(visibili==["d2"], f"sulla pagina c'è solo la domanda di adesso ({visibili})")
        await pg2.click("#d2 .scelta >> nth=0"); await pg2.click("#avanti2"); await pg2.wait_for_timeout(250)
        ok("interessa davvero" not in await pg2.inner_text("#d3"), "alla domanda del prezzo «Bene. Adesso la parte che mi interessa davvero» non si ripete")
        print("── si riprende da dove ci si era fermati (29 settembre)")
        await pg2.evaluate("(()=>{const r=document.querySelector('#prezzo');r.value=40;r.dispatchEvent(new Event('input'));r.dispatchEvent(new Event('change'))})()")
        await pg2.reload(); await pg2.wait_for_timeout(700)
        vis=await pg2.evaluate("[...document.querySelectorAll('#p-inizia .domanda, #tocca')].filter(x=>x.offsetParent!==null && x.id!=='benvenuto').map(x=>x.id)")
        ok(vis==["d3"], f"ricaricato alla domanda del prezzo: si riapre lì, non da capo ({vis})")
        ok(await pg2.input_value("#prezzo")=="40" and await pg2.inner_text("#valore")=="40", "e il prezzo scelto c'è ancora")
        ok(not await pg2.is_disabled("#avanti3"), "e, mosso prima di ricaricare, «Vai avanti» è già acceso (27/10)")
        ok(await pg2.evaluate("document.querySelector('#continua').getAttribute('href')")=="#d3", "«Continuiamo ↓» porta alla domanda di adesso")
        await pg2.click("#avanti3"); await pg2.wait_for_timeout(250)
        await pg2.click("#d5 .scelta >> nth=0"); await pg2.click("#avanti5"); await pg2.wait_for_timeout(250)
        t4=await pg2.inner_text("#d4")
        ok("Come ti chiami" not in t4 and not await pg2.evaluate("document.querySelector('#nome').type!=='hidden'"), "l'ultima domanda non richiede il nome: l'ha già detto all'inizio")
        ok("Parla con" not in t4 and "si apre appena mandi" in t4, "e non rimanda più a «Parla con», che non c'è")
        await pg2.fill("#mail","jacopo@esempio.it"); await pg2.check("#ok"); await pg2.click("#manda"); await pg2.wait_for_timeout(1800)
        inv4=[d for (r,d) in inviati if d.get("mail")=="jacopo@esempio.it"]
        ok(inv4 and inv4[-1].get("nome")=="Jacopo", "con la mail parte il nome detto all'inizio")
        rimaste=await pg2.evaluate("[...document.querySelectorAll('#p-inizia .domanda, #tocca')].filter(x=>x.offsetParent!==null && x.id!=='benvenuto').map(x=>x.id)")
        ok(rimaste==[], f"mandate le risposte, il sondaggio se ne va tutto ({rimaste})")
        ok("Ricevuto" in (await pg2.inner_text("#chat")), "e Nova dice «Ricevuto» nella chat")
        ok(await vede("#barra-chat"), "questionario finito: adesso compare la casella per scrivere")
        await pg2.close()
        print("── i primi passi stanno in uno schermo (29 settembre)")
        for w,h in [(393,740),(360,640)]:
            c3=await b.new_context(viewport={"width":w,"height":h}, is_mobile=True, has_touch=True)
            await c3.route("**/*", instrada); p3=await c3.new_page(); p3.on("pageerror", lambda e: errori.append(str(e)))
            await p3.goto(BASE); await p3.wait_for_timeout(300)
            async def in_vista(sel):
                return await p3.evaluate(f"(()=>{{const n=document.querySelector('.schede').getBoundingClientRect().top,r=document.querySelector('{sel}').getBoundingClientRect();return window.scrollY===0 && r.bottom<=n && r.top>=0}})()")
            await p3.click("#nomi .scelta >> text=Nova"); a1=await in_vista("#avanti-o1")
            await p3.click("#avanti-o1"); await p3.wait_for_timeout(300); await p3.click('.tema[data-tema="naturale"]'); await p3.wait_for_timeout(200); a2=await in_vista("#avanti-o2")
            await p3.click("#avanti-o2"); await p3.wait_for_timeout(300); a3=await in_vista("#salta-o3")
            ok(a1 and a2 and a3, f"{w}x{h}: «Salva», «Salva», «Piacere / Preferisco non dirlo» in vista senza scorrere, con la sfera sopra")
            await c3.close()
        print("── prima l'ingresso, poi le tre domande (26 ottobre)")
        # JJ, 26/10: chi arriva vedeva «Come vuoi chiamarmi?» e subito dopo gli si accendeva sopra l'ingresso. Qui il server dei
        # conti c'è (finto): insieme.json dà l'indirizzo, la classifica risponde, «Accedi» dà il token. Un campionatore parte
        # prima della pagina e segna ogni 5 ms (e a ogni fotogramma e a ogni cambio del DOM) chi si vede: l'ingresso con l'icona, #o1
        CONTI="https://jjavis-citta.finta.workers.dev"
        CASA_IO={"nome":"Nova","tema":"calmo","id":"casa0123456789ab","mail":"gino@prova.it","agg":1}
        async def conti(route):
            u=route.request.url; r=route.request
            if u.startswith(BASE+"insieme.json"): return await route.fulfill(body=json.dumps({"indirizzo":CONTI.replace("https:","wss:")+"/entra"}), content_type="application/json")
            if u.startswith(CONTI):
                cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"Content-Type, Authorization","Access-Control-Allow-Methods":"GET, POST"}
                if r.method=="OPTIONS": return await route.fulfill(status=204, headers=cors)
                via_=u[len(CONTI):].split("?")[0]
                if via_=="/conto/classifica": d={"classifica":[]}
                elif via_=="/conto/accedi": d={"token":"t"*64,"conto":{"mail":"gino@prova.it","io":{}}}
                elif via_=="/conto": d={"conto":{"mail":"gino@prova.it","io":CASA_IO}} if r.headers.get("authorization") else {"no":"token"}
                else: d={"fatto":True}
                return await route.fulfill(body=json.dumps(d), content_type="application/json", headers=cors)
            return await instrada(route)
        CAMPIONA="""(()=>{ const v=id=>{ const e=document.getElementById(id); return !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden"; };
          const c=window.__visto=[]; const segna=()=>{ const ic=document.querySelector("#ingresso .ingresso-icona");
            c.push({t:performance.now(), ing:v("ingresso"), icona:!!ic&&v("ingresso")&&ic.getClientRects().length>0, o1:v("o1")}); };
          setInterval(segna,5); const f=()=>{ segna(); requestAnimationFrame(f); }; requestAnimationFrame(f); segna();
          new MutationObserver(segna).observe(document,{childList:true,subtree:true,attributes:true}); })()"""
        async def telefono(moto="no-preference", init=None):
            c=await b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, reduced_motion=moto)
            await c.route("**/*", conti); await c.add_init_script(CAMPIONA)
            if init: await c.add_init_script(init)
            q=await c.new_page(); q.on("pageerror", lambda e: errori.append(str(e)))
            return c, q
        visto=lambda q: q.evaluate("window.__visto")
        # da quando la pagina arriva (responseStart), non da quando Playwright la chiede
        arrivo=lambda q: q.evaluate("performance.getEntriesByType('navigation')[0].responseStart")
        def buco(v):   # il tratto più lungo, dopo il primo ingresso, in cui non si vedono né l'ingresso né #o1 (la schermata bianca)
            peggio=0; da=None; visto_ing=False
            for x in v:
                visto_ing=visto_ing or x["ing"]
                if not visto_ing: continue
                if not x["ing"] and not x["o1"]: da=x["t"] if da is None else da; peggio=max(peggio,x["t"]-da)
                else: da=None
            return peggio
        for moto in ("no-preference","reduce"):
            dice="" if moto=="no-preference" else " (animazioni ridotte)"
            c4,p4=await telefono(moto)
            await p4.goto(BASE); await p4.wait_for_timeout(600)
            v=await visto(p4); t0=await arrivo(p4)
            primo=next((x["t"] for x in v if x["ing"] and x["icona"]), None)
            # CONTROPROVA: senza la classe «fuori» messa nella testa, #o1 si vede finché la porta non ha risposto, e qui diventa rosso
            # 26/10, Athena: 100 ms era un numero preso a occhio; con la pagina cresciuta (chat, calendario) su GitHub esce 99-1xx ms e
            # va e viene. Quello che conta per JJ è che «Come vuoi chiamarmi?» non si veda MAI prima dell'ingresso (resta qui sotto,
            # identico); il tempo si tiene largo: 300 ms, ancora meno di un battito di ciglia.
            ok(primo is not None and primo-t0<=300 and not any(x["o1"] for x in v), f"telefono nuovo{dice}: entro 300 ms c'è l'ingresso con l'icona, e #o1 mai ({None if primo is None else round(primo-t0)} ms)")
            ok("Il tuo assistente personale" in await p4.inner_text("#ingresso") and await p4.is_visible("#acc-entra") and not await p4.is_visible(".testa"), f"in cima l'icona, «JJA-VIS» e «Il tuo assistente personale»; sotto accedi/registrati, la pagina no{dice}")
            await p4.evaluate("window.__visto.length=0")
            await p4.fill("#acc-chi","gino"); await p4.fill("#acc-pw","password1"); await p4.click("#acc-entra")
            await p4.wait_for_selector("#o1", state="visible", timeout=5000); await p4.wait_for_timeout(700)
            v=await visto(p4)
            ok(buco(v)<=500 and await p4.is_visible("#o1") and not await p4.is_visible("#ingresso"), f"entrato{dice}: l'ingresso se ne va e c'è #o1, senza schermata bianca in mezzo (buco {round(buco(v))} ms)")
            insieme=[x["t"] for x in v if x["ing"] and x["o1"]]
            if moto=="reduce": ok(not insieme or insieme[-1]-insieme[0]<100, "animazioni ridotte: niente dissolvenza, l'ingresso sparisce subito")
            else: ok(insieme and insieme[-1]-insieme[0]>=200, "l'ingresso sfuma mentre #o1 appare (una dissolvenza, non uno scatto)")
            await p4.click("#nomi .scelta >> text=Nova"); await p4.click("#avanti-o1"); await p4.wait_for_timeout(100)
            anim=await p4.evaluate("getComputedStyle(document.querySelector('#o2')).animationName")
            ok(await p4.is_visible("#o2") and anim==("none" if moto=="reduce" else "dissolvi"), f"da #o1 a #o2 con la stessa dissolvenza{dice} ({anim})")
            await p4.click("#avanti-o2"); await p4.wait_for_timeout(100)
            ok(await p4.is_visible("#o3") and not await p4.is_visible("#o2"), f"poi #o3, «E tu come ti chiami?»{dice}")
            await c4.close()
        print("── chi è già di casa non ripassa dall'ingresso")
        c5,p5=await telefono(init="if(!sessionStorage.getItem('gia')){sessionStorage.setItem('gia','1');localStorage.setItem('jjavis-conto','t'.repeat(64));localStorage.setItem('jjavis-io',JSON.stringify("+json.dumps(CASA_IO)+"));}")
        await p5.goto(BASE); await p5.wait_for_timeout(1500)
        v=await visto(p5)
        ok(not any(x["ing"] for x in v) and not any(x["o1"] for x in v) and await p5.is_visible("#benvenuto"), "con l'account e nome e tema: né l'ingresso né «Come vuoi chiamarmi?», nemmeno per un attimo; si va al saluto")
        await c5.close()
        print("── il calendario vero (26 ottobre): il mese, l'agenda del giorno, aggiungere, aprire")
        # 26/10, il calendario diventa un calendario vero. Le prove di prima presupponevano UN elenco unico («Da fare» con i gruppi «Rimasti indietro»,
        # «Oggi», «Domani» una riga dopo l'altra, `.cal-giorno`): ora c'è la griglia del mese, sotto l'agenda del giorno scelto e, a parte, «⚠️ Rimasti
        # indietro»; le righe e il «✓ Fatto» sono gli stessi, ma si cercano nell'agenda del giorno, non in un elenco di tutto il calendario. Cambiano
        # quindi: «Da fare/Rimasti indietro/Oggi/Domani nell'ordine» (ora: griglia + agenda), «tre righe con tre bottoni» (ora: le righe del giorno scelto),
        # «i giorni passati di un altro colore» (ora: la sezione «Rimasti indietro»), e il «vuoto» (che dice anche «Niente in questo giorno»).
        from datetime import date, timedelta
        iso=lambda d: d.isoformat()
        MESI=["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
        GIORNI=["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
        bello=lambda d,anno=False: f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month-1]}"+(f" {d.year}" if anno else "")
        oggi_=date.today(); ieri_=oggi_-timedelta(days=1); domani_=oggi_+timedelta(days=1); dopo_=oggi_+timedelta(days=2)
        CAL.update(giu=False, rifiuta=None, n=0, invito="mandato", invito_errore=None, fatti=[], impegni=[
            {"id":"i-ieri","cosa":"l'oculista","giorno":iso(ieri_),"ora":"10:00"},
            {"id":"i-oggi","cosa":"chiamare il commercialista","giorno":iso(oggi_),"ora":"15:30","nota":"porta il badge\nsecondo piano"},
            {"id":"i-dopo","cosa":"la revisione","giorno":iso(dopo_),"ora":"09:00"}],
          scadenze=[{"id":"s-bollo","cosa":"bollo auto","giorno":iso(domani_),"importo":"€ 180","ogni_mese":False}])
        async def calendario_aperto(larg=390, alt=844, **kw):
            """un telefono con l'account, il calendario aperto dal menù ☰"""
            c=await b.new_context(viewport={"width":larg,"height":alt}, has_touch=True, is_mobile=True, **kw); await c.route("**/*", instrada)
            await c.add_init_script("localStorage.setItem('jjavis-conto','t'.repeat(64));localStorage.setItem('jjavis-io', JSON.stringify({id:'e1b2c3d4e5f60718',nome:'Nova',tema:'tech',tuo:'Jacopo',inviato:true,mestiere:'Ufficio',tempo:'Altro lavoro ripetitivo'}))")
            p=await c.new_page(); p.on("pageerror", lambda e: errori.append(str(e)))
            await p.goto(BASE); await p.wait_for_timeout(1200)
            await p.click("#apri-conv"); await p.wait_for_timeout(450); await p.click("#menu-calendario"); await p.wait_for_timeout(700)
            return c,p
        async def riapri(p):
            await p.click("#apri-conv"); await p.wait_for_timeout(450); await p.click("#menu-calendario"); await p.wait_for_timeout(700)
        async def a_mese(p, anno, mese):
            """clicca ‹ o › (da «Oggi») fino a quel mese"""
            await p.click('[data-az="oggi"]'); n=(anno*12+mese)-(oggi_.year*12+oggi_.month)
            for _ in range(abs(n)): await p.click('[data-az="avanti"]' if n>0 else '[data-az="indietro"]')
            await p.wait_for_timeout(100)
        async def posto_del_primo_novembre(p):
            """in che colonna cade il 1° novembre 2026 (una domenica): per chi comincia di lunedì è l'ultima, la settima, indice 6"""
            await a_mese(p, 2026, 11)
            return await p.evaluate("[...document.querySelectorAll('.cal-cella')].findIndex(c=>c.dataset.giorno==='2026-11-01')")
        cella=lambda g: f'.cal-cella[data-giorno="{iso(g)}"]'
        c11=await b.new_context(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True); await c11.route("**/*", instrada)
        await c11.add_init_script("localStorage.setItem('jjavis-conto','t'.repeat(64));localStorage.setItem('jjavis-io', JSON.stringify({id:'e1b2c3d4e5f60718',nome:'Nova',tema:'tech',tuo:'Jacopo',inviato:true,mestiere:'Ufficio',tempo:'Altro lavoro ripetitivo'}))")
        pg11=await c11.new_page(); pg11.on("pageerror", lambda e: errori.append(str(e)))
        await pg11.goto(BASE); await pg11.wait_for_timeout(1200)
        await pg11.click("#apri-conv"); await pg11.wait_for_timeout(450)
        ok(await pg11.evaluate("!!(document.getElementById('menu-calendario').compareDocumentPosition(document.getElementById('menu-citta')) & Node.DOCUMENT_POSITION_FOLLOWING) && !!(document.getElementById('conv-elenco').compareDocumentPosition(document.getElementById('menu-calendario')) & Node.DOCUMENT_POSITION_FOLLOWING)"), "nel menù ☰: «📅 Calendario» dopo le conversazioni e prima della Città")
        await pg11.click("#menu-calendario"); await pg11.wait_for_timeout(500)
        ok(await pg11.evaluate("document.body.dataset.scheda")=="calendario" and await pg11.is_visible("#p-calendario") and "Calendario" in await pg11.inner_text("#tcal"), "dal ☰ si apre la scheda «📅 Calendario»")
        # il mese
        ok(await pg11.locator(".cal-cella").count()==42, "all'apertura la griglia del mese ha 42 caselle (6 righe da 7)")
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[oggi_.month-1]} {oggi_.year}", f"l'intestazione è il mese corrente («{MESI[oggi_.month-1]} {oggi_.year}»)")
        ok(await pg11.locator(".cal-cella.oggi").count()==1 and await pg11.get_attribute(".cal-cella.oggi","data-giorno")==iso(oggi_) and await pg11.get_attribute(".cal-cella.oggi","aria-pressed")=="true", "oggi è evidenziato e selezionato")
        ok(await pg11.evaluate("getComputedStyle(document.querySelector('.cal-cella.oggi .cal-num')).borderTopColor")==await pg11.evaluate("(()=>{const e=document.createElement('i');e.style.color='var(--accento)';document.body.appendChild(e);const c=getComputedStyle(e).color;e.remove();return c})()"), "oggi è cerchiato col colore d'accento del tema")
        ok(date.fromisoformat(await pg11.get_attribute(".cal-cella >> nth=0","data-giorno")).weekday()==0 and await pg11.inner_text(".cal-sett")=="lun\nmar\nmer\ngio\nven\nsab\ndom", "si comincia di lunedì: lun–dom")
        ok(await pg11.locator(".cal-cella.altro").count()>0 and await pg11.evaluate("getComputedStyle(document.querySelector('.cal-cella.altro')).opacity")<"1" and await pg11.evaluate("getComputedStyle(document.querySelector('.cal-cella:not(.altro)')).opacity")=="1", "i giorni degli altri mesi sono tenui")
        ok(await pg11.inner_text("#cal-giorno-titolo")==bello(oggi_), f"sotto, l'agenda di oggi: «{bello(oggi_)}»")
        ok("chiamare il commercialista" in await pg11.inner_text("#cal-giorno-casa") and "15:30" in await pg11.inner_text("#cal-giorno-casa") and await pg11.locator("#cal-giorno-casa .cal-riga").count()==1, "nell'agenda di oggi c'è l'impegno, con l'ora")
        ok((await pg11.evaluate("document.querySelector('.cal-cella').getBoundingClientRect().height"))>=44, "le caselle sono alte almeno 44 px")
        ok("chiamare" in await pg11.inner_text(cella(oggi_)+" .cal-et.imp"), "oggi nella griglia ha l'etichetta dell'impegno")
        ok(await pg11.evaluate("getComputedStyle(document.querySelector('.cal-et')).textOverflow")=="ellipsis", "le etichette si troncano con «…»")
        ok(await pg11.evaluate("getComputedStyle(document.querySelector('.cal-et.imp')).backgroundColor")!=await pg11.evaluate("(()=>{const e=document.querySelector('.cal-et.sca');return e?getComputedStyle(e).backgroundColor:''})()"), "impegni e scadenze hanno colori diversi")
        # i mesi: ‹ e ›
        await pg11.click('[data-az="avanti"]'); await pg11.wait_for_timeout(100)
        mese_dopo=date(oggi_.year+(oggi_.month==12), oggi_.month%12+1, 1)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[mese_dopo.month-1]} {mese_dopo.year}" and await pg11.locator(".cal-cella").count()==42, "› va al mese dopo")
        ok(await pg11.get_attribute(".cal-cella[aria-pressed='true']","data-giorno")==iso(mese_dopo) and await pg11.inner_text("#cal-giorno-titolo")==bello(mese_dopo), "…e ne sceglie il primo giorno, con la sua agenda")
        await pg11.click('[data-az="indietro"]'); await pg11.wait_for_timeout(100)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[oggi_.month-1]} {oggi_.year}", "‹ torna indietro")
        idx=await posto_del_primo_novembre(pg11)
        ok(await pg11.inner_text("#cal-mese-titolo")=="novembre 2026" and idx==6, f"novembre 2026: l'1 è domenica, ultima colonna (casella n. {idx+1} su 42: la settima)")
        await pg11.click('[data-az="oggi"]'); await pg11.wait_for_timeout(100)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[oggi_.month-1]} {oggi_.year}" and await pg11.get_attribute(".cal-cella[aria-pressed='true']","data-giorno")==iso(oggi_), "«Oggi» riporta al mese di oggi, con oggi scelto")
        async def scorri_mese(dx):
            await pg11.evaluate("""dx=>{const z=document.querySelector('.cal-griglia');const T=(x,y)=>new Touch({identifier:1,target:z,clientX:x,clientY:y});
              z.dispatchEvent(new TouchEvent('touchstart',{touches:[T(300,400)],changedTouches:[T(300,400)],bubbles:true}));
              z.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[T(300+dx,408)],bubbles:true}));}""", dx)
            await pg11.wait_for_timeout(150)
        await scorri_mese(-150)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[mese_dopo.month-1]} {mese_dopo.year}" and await pg11.evaluate("document.body.dataset.scheda")=="calendario", "il dito a sinistra sul mese: il mese dopo (e la scheda non cambia)")
        await scorri_mese(150)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[oggi_.month-1]} {oggi_.year}", "il dito a destra: il mese prima")
        await scorri_mese(-20)
        ok(await pg11.inner_text("#cal-mese-titolo")==f"{MESI[oggi_.month-1]} {oggi_.year}", "un tocco corto del dito non cambia mese")
        # un impegno di dopodomani, toccato il giorno, «✓ Fatto»
        ok("la revisione" in await pg11.inner_text(cella(dopo_)), "un impegno di dopodomani ha la sua etichetta nella griglia")
        await pg11.click(cella(dopo_)); await pg11.wait_for_timeout(100)
        ok(await pg11.get_attribute(cella(dopo_),"aria-pressed")=="true" and await pg11.get_attribute(cella(oggi_),"aria-pressed")=="false" and await pg11.inner_text("#cal-giorno-titolo")==bello(dopo_), "toccato il giorno: si evidenzia e sotto c'è l'agenda di quel giorno")
        r_=pg11.locator('#cal-giorno-casa .cal-riga[data-id="i-dopo"]')
        ok("la revisione" in await r_.inner_text() and "09:00" in await r_.inner_text() and "✓ Fatto" in await r_.inner_text(), "nell'agenda c'è «la revisione», con l'ora e «✓ Fatto»")
        ok((await pg11.evaluate("document.querySelector('#cal-giorno-casa .cal-fatto').getBoundingClientRect().height"))>=44, "il bottone è grande")
        prima_=len(inviati)
        await r_.locator(".cal-fatto").click(); await pg11.wait_for_timeout(900)
        fatti_=[d for (r,d) in inviati[prima_:] if r=="fatto"]
        ok(len(fatti_)==1 and fatti_[0]=={"id":"i-dopo"} and len([1 for (r,d) in inviati[prima_:] if r in ("fatto","annulla")])==1, "UNA POST /assistente/fatto, con il suo id")
        ok("la revisione" not in await pg11.inner_text(cella(dopo_)) and "Niente in questo giorno" in await pg11.inner_text("#cal-giorno-casa"), "l'etichetta sparisce dalla griglia e il giorno è vuoto: «Niente in questo giorno»")
        ok(await pg11.is_visible("#cal-annulla") and "la revisione" in await pg11.inner_text("#cal-annulla"), "in basso compare «Annulla»")
        ok(await pg11.is_visible("#cal-fatti") and not await pg11.evaluate("document.getElementById('cal-fatti').open") and "Fatti negli ultimi 30 giorni" in await pg11.inner_text("#cal-fatti summary"), "«✓ Fatti negli ultimi 30 giorni» c'è, ma chiusa")
        await pg11.click("#cal-annulla-btn"); await pg11.wait_for_timeout(700)
        ann_=[d for (r,d) in inviati[prima_:] if r=="annulla"]
        ok(len(ann_)==1 and ann_[0]=={"id":"i-dopo"} and "la revisione" in await pg11.inner_text(cella(dopo_)) and await pg11.is_hidden("#cal-annulla"), "«Annulla»: UNA POST /assistente/annulla, l'etichetta torna, la barra se ne va")
        await pg11.click(cella(domani_)); await pg11.wait_for_timeout(100)
        ok("✓ Pagata" in await pg11.inner_text('#cal-giorno-casa .cal-riga[data-id="s-bollo"]') and "€ 180" in await pg11.inner_text('#cal-giorno-casa .cal-riga[data-id="s-bollo"]') and "€ bollo" in await pg11.inner_text(cella(domani_)), "una scadenza: «✓ Pagata», l'importo, e un'etichetta con «€» in griglia")
        await pg11.click('#cal-giorno-casa .cal-riga[data-id="s-bollo"] .cal-fatto'); await pg11.wait_for_timeout(900)
        ok(await pg11.is_visible("#cal-annulla"), "dopo «Pagata» la barra «Annulla» è lì")
        await pg11.wait_for_timeout(5300)
        ok(await pg11.is_hidden("#cal-annulla"), "e dopo 5 secondi se ne va")
        await pg11.click("#cal-fatti summary"); await pg11.wait_for_timeout(200)
        ok("bollo auto" in await pg11.inner_text("#cal-fatti-elenco"), "fra i fatti c'è la scadenza pagata")
        await pg11.click("#cal-fatti-elenco button"); await pg11.wait_for_timeout(700)
        ok(await pg11.locator('#cal-giorno-casa .cal-riga[data-id="s-bollo"]').count()==1, "…e da lì si può annullare")
        # rimasti indietro
        ok(await pg11.is_visible("#cal-indietro") and await pg11.inner_text("#cal-indietro-titolo")=="⚠️ Rimasti indietro (1)" and await pg11.evaluate("document.getElementById('cal-indietro').open"), "«⚠️ Rimasti indietro (1)»: c'è, aperta")
        ok("l'oculista" in await pg11.inner_text("#cal-indietro-elenco") and "✓ Fatto" in await pg11.inner_text("#cal-indietro-elenco"), "dentro c'è l'impegno di ieri, col suo «✓ Fatto»")
        ok(await pg11.is_hidden("#cal-fatti"), "e senza fatti la sezione «✓ Fatti negli ultimi 30 giorni» non c'è")
        await pg11.click("#cal-indietro summary"); await pg11.wait_for_timeout(1000)
        ok(not await pg11.evaluate("document.getElementById('cal-indietro').open"), "si può chiudere…")
        await pg11.click(cella(dopo_)); await pg11.wait_for_timeout(100)
        ok(not await pg11.evaluate("document.getElementById('cal-indietro').open"), "…e restare chiusa quando si cambia giorno")
        await pg11.click("#cal-indietro summary"); await pg11.wait_for_timeout(100)
        ok(await pg11.locator("#cal-indietro .cal-fatto").count()==1 and (await pg11.evaluate("document.querySelector('#cal-indietro summary').getBoundingClientRect().height"))>=44, "riaperta; il suo tasto è grande")

        print("── il calendario: aggiungere a mano")
        ok(await pg11.is_visible("#cal-piu") and (await pg11.evaluate("(()=>{const r=document.getElementById('cal-piu').getBoundingClientRect();return [r.width,r.height,innerWidth-r.right,innerHeight-r.bottom]})()"))[0]>=44, "il «＋» tondo c'è, in basso a destra")
        pos=await pg11.evaluate("(()=>{const r=document.getElementById('cal-piu').getBoundingClientRect();return [r.right>innerWidth-40, r.bottom>innerHeight-130, getComputedStyle(document.getElementById('cal-piu')).borderRadius]})()")
        ok(pos[0] and pos[1] and pos[2]=="50%", "…proprio in basso a destra e tondo")
        ok(await pg11.is_hidden("#cal-velo"), "il foglio è chiuso")
        await pg11.click(cella(domani_)); await pg11.wait_for_timeout(100)
        await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300)
        ok(await pg11.is_visible("#cal-velo") and await pg11.is_visible("#cal-f-cosa"), "«＋»: si apre il foglio dal basso")
        ok(await pg11.input_value("#cal-f-giorno")==iso(domani_), "il giorno è già quello scelto")
        ok(await pg11.get_attribute("#cal-t-impegno","aria-pressed")=="true" and await pg11.is_visible("#cal-f-ora") and not await pg11.is_visible("#cal-f-importo") and not await pg11.is_visible("#cal-f-ogni"), "«Impegno»: c'è l'ora; importo e «ogni mese» no")
        await pg11.click("#cal-t-scadenza")
        ok(await pg11.is_visible("#cal-f-importo") and await pg11.is_visible("#cal-f-ogni") and not await pg11.is_visible("#cal-f-ora"), "«Scadenza»: importo e «ogni mese», niente ora")
        await pg11.click("#cal-t-impegno")
        ok(await pg11.evaluate("document.activeElement.id")!="" and await pg11.is_visible("#cal-f-nota") and await pg11.is_visible("#cal-f-salva"), "c'è anche la nota, e «Salva»")
        await pg11.keyboard.press("Escape"); await pg11.wait_for_timeout(200)
        ok(await pg11.is_hidden("#cal-velo"), "Esc chiude il foglio")
        # errori della porta: il foglio resta com'è
        await pg11.click("#cal-aggiungi-giorno"); await pg11.wait_for_timeout(300)
        ok(await pg11.input_value("#cal-f-giorno")==iso(domani_), "anche «＋ Aggiungi» nell'agenda del giorno apre il foglio, col giorno scelto")
        prima_=len(inviati); CAL["rifiuta"]="la data non è valida"
        await pg11.fill("#cal-f-cosa","pratica"); await pg11.fill("#cal-f-nota","portare la ricevuta"); await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(500)
        ok(await pg11.is_visible("#cal-velo") and "la data non è valida" in await pg11.inner_text("#cal-f-errore"), "la porta dice no: l'errore è nel foglio")
        ok(await pg11.input_value("#cal-f-cosa")=="pratica" and await pg11.input_value("#cal-f-nota")=="portare la ricevuta" and not await pg11.is_disabled("#cal-f-salva"), "…e quello che si era scritto c'è ancora")
        CAL["rifiuta"]=None
        await pg11.fill("#cal-f-cosa",""); await pg11.click("#cal-f-salva")
        ok("Scrivi cosa" in await pg11.inner_text("#cal-f-errore") and len([1 for (r,d) in inviati[prima_:] if r=="aggiungi"])==1, "cosa vuota: lo dice il foglio, senza chiamare la porta")
        await pg11.keyboard.press("Escape"); await pg11.wait_for_timeout(200)
        # «dentista», domani, 10:00
        prima_=len(inviati)
        await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300)
        await pg11.fill("#cal-f-cosa","dentista"); await pg11.fill("#cal-f-giorno",iso(domani_)); await pg11.fill("#cal-f-ora","10:00")
        await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(900)
        nuovi_=[d for (r,d) in inviati[prima_:] if r=="aggiungi"]
        ok(len(nuovi_)==1 and nuovi_[0]=={"tipo":"impegno","cosa":"dentista","giorno":iso(domani_),"ora":"10:00"}, f"UNA POST /assistente/aggiungi con quei dati ({nuovi_})")
        ok(await pg11.is_hidden("#cal-velo"), "il foglio si chiude")
        ok("dentista" in await pg11.inner_text(cella(domani_)+" .cal-et.imp") and "dentista" in await pg11.inner_text("#cal-giorno-casa"), "la cosa compare subito sulla griglia (domani) e nell'agenda")
        idn=await pg11.get_attribute('#cal-giorno-casa .cal-riga:has-text("dentista")',"data-id")
        # una scadenza, dal «＋ Aggiungi»
        prima_=len(inviati)
        await pg11.click("#cal-aggiungi-giorno"); await pg11.wait_for_timeout(300); await pg11.click("#cal-t-scadenza")
        await pg11.fill("#cal-f-cosa","luce"); await pg11.fill("#cal-f-importo","€ 64,10"); await pg11.check("#cal-f-ogni"); await pg11.fill("#cal-f-nota","bolletta di ottobre")
        await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(900)
        nuovi_=[d for (r,d) in inviati[prima_:] if r=="aggiungi"]
        ok(len(nuovi_)==1 and nuovi_[0]=={"tipo":"scadenza","cosa":"luce","giorno":iso(domani_),"importo":"€ 64,10","ogni_mese":True,"nota":"bolletta di ottobre"}, f"una scadenza: UNA POST con importo, «ogni mese» e nota ({nuovi_})")
        ok("luce" in await pg11.inner_text("#cal-giorno-casa") and "€ 64,10" in await pg11.inner_text("#cal-giorno-casa") and "ogni mese" in await pg11.inner_text("#cal-giorno-casa"), "la scadenza è nell'agenda, con l'importo e «ogni mese»")
        # un altro giorno (scelto nel foglio): il calendario ci va
        await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300)
        await pg11.fill("#cal-f-cosa","corso"); await pg11.fill("#cal-f-giorno",iso(dopo_)); await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(900)
        ok(await pg11.inner_text("#cal-giorno-titolo")==bello(dopo_) and "corso" in await pg11.inner_text("#cal-giorno-casa") and "tutto il giorno" in await pg11.inner_text("#cal-giorno-casa"), "giorno diverso: il calendario lo mostra; senza ora è «tutto il giorno»")
        ok(await pg11.evaluate("(()=>{const t=[...document.querySelectorAll('#cal-giorno-casa .cal-ora')].map(e=>e.textContent);return t[0]==='tutto il giorno' && t[t.length-1]==='09:00'})()"), "e «tutto il giorno» sta in cima, prima di quello delle 09:00")

        print("── il calendario: «Salva» di un impegno manda l'invito per mail (27/10, JJ: «l'utente non deve impazzire»)")
        stato=lambda: pg11.inner_text("#cal-stato")
        async def salva_impegno(cosa):
            await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300)
            await pg11.fill("#cal-f-cosa",cosa); await pg11.fill("#cal-f-giorno",iso(dopo_)); await pg11.fill("#cal-f-ora","16:00")
            await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(900)
        INVITO_OK="✓ Salvato. 📩 Ti ho mandato l'invito per mail: aprila e tocca «Aggiungi al calendario»."
        await salva_impegno("invito mandato")
        ok(await stato()==INVITO_OK, f"la porta dice invito:\"mandato\" → l'avviso «{INVITO_OK}» (e la rilettura del calendario non lo cancella)")
        ok(await pg11.locator("#cal-stato .cal-riprova").count()==0 and not await pg11.locator("#cal-stato .cal-avviso.errore").count(), "…senza «Riprova» e senza il rosso dell'errore")
        CAL["invito"]="niente mail"; await salva_impegno("invito niente")
        ok(await stato()=="✓ Salvato." and await pg11.locator("#cal-stato .cal-riprova").count()==0, "invito:\"niente mail\" → solo «✓ Salvato.»")
        CAL["invito"]="errore: Brevo 503"; CAL["invito_errore"]="la mail non è partita: Brevo 503"; prima_=len(inviati)
        await salva_impegno("invito errore")
        idr=await pg11.get_attribute('#cal-giorno-casa .cal-riga:has-text("invito errore")',"data-id")
        ok(await pg11.inner_text("#cal-stato .cal-avviso p")=="✓ Salvato, ma l'invito per mail non è partito: Brevo 503" and await pg11.locator("#cal-stato .cal-avviso.errore").count()==1 and await pg11.locator("#cal-stato .cal-riprova").count()==1,
           "invito:\"errore: Brevo 503\" → «✓ Salvato, ma l'invito per mail non è partito: Brevo 503» e «Riprova»")
        ok("invito errore" in await pg11.inner_text("#cal-giorno-casa") and len([1 for (r,d) in inviati[prima_:] if r=="aggiungi"])==1, "l'impegno è salvato lo stesso (è nell'agenda), con UNA POST /assistente/aggiungi")
        prima_=len(inviati); await pg11.click("#cal-stato .cal-riprova"); await pg11.wait_for_timeout(700)
        inv_=[d for (r,d) in inviati[prima_:] if r=="invito"]
        ok(inv_==[{"id":idr}] and "non è partito" in await stato() and "Brevo 503" in await stato() and await pg11.locator("#cal-stato .cal-riprova").count()==1, f"«Riprova» → UNA POST /assistente/invito con l'id; se la porta dice ancora no, l'errore resta e si può riprovare ({inv_})")
        CAL["invito_errore"]=None; prima_=len(inviati); await pg11.click("#cal-stato .cal-riprova"); await pg11.wait_for_timeout(700)
        ok(len([1 for (r,d) in inviati[prima_:] if r=="invito"])==1 and await stato()==INVITO_OK and await pg11.locator("#cal-stato .cal-riprova").count()==0, "«Riprova» con la porta tornata: UNA POST e l'avviso «Ti ho mandato l'invito per mail…»")
        CAL["invito"]="mandato"
        prima_=len(inviati); CAL["invito"]="niente mail"
        await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300); await pg11.click("#cal-t-scadenza"); await pg11.fill("#cal-f-cosa","acqua"); await pg11.click("#cal-f-salva"); await pg11.wait_for_timeout(900)
        ok(not [1 for (r,d) in inviati[prima_:] if r=="invito"], "una scadenza non chiede nessun invito")
        CAL["invito"]="mandato"
        for x_ in list(CAL["impegni"]):
            if x_["cosa"].startswith("invito ") or x_["cosa"]=="acqua": CAL["impegni"].remove(x_)
        CAL["scadenze"]=[x_ for x_ in CAL["scadenze"] if x_["cosa"]!="acqua"]
        await riapri(pg11)

        print("── il calendario: aprire per esteso")
        await pg11.click(cella(domani_)); await pg11.wait_for_timeout(100)
        await pg11.click(f'#cal-giorno-casa .cal-riga[data-id="{idn}"] .cal-apri'); await pg11.wait_for_timeout(300)
        t_=await pg11.inner_text("#cal-foglio")
        ok(await pg11.is_visible("#cal-velo") and "dentista" in t_ and f"{bello(domani_,True)}, alle 10:00" in t_, f"toccata la riga: il dettaglio, «dentista» e «{bello(domani_,True)}, alle 10:00»")
        ok(all(x in t_ for x in ["✓ Fatto","📩 Mandami l'invito per mail","🗑 Elimina","Chiudi"]), "i bottoni: «✓ Fatto», «📩 Mandami l'invito per mail», «🗑 Elimina», «Chiudi»")
        ok("Metti nel calendario del telefono" not in t_ and "scarica l'invito" not in t_ and ".ics" not in t_ and await pg11.locator("#cal-d-google, #cal-d-ics, #cal-foglio a[href]").count()==0, "…e non c'è più «Metti nel calendario del telefono» né il link .ics (né altri link)")
        ok(await pg11.locator(".cal-foglio .cal-btn").count()>=4 and (await pg11.evaluate("[...document.querySelectorAll('.cal-foglio .cal-btn')].every(b=>b.getBoundingClientRect().height>=44)")), "i tasti del foglio sono alti almeno 44 px")
        # 27/10: sparite le prove di calLinkGoogle (il link di Google Calendar) e calIntentAndroid (l'intent «nuovo evento» di Android):
        # il tasto che apriva il calendario del telefono non c'è più, quindi non c'è più né il codice né niente da provare qui. L'ora giusta
        # (quella di Roma, d'estate e d'inverno) la dà ora l'invito che costruisce la porta (icsImpegno) e la prova è lì: collaudo/agenda.mjs
        prima_=len(inviati)
        await pg11.click("#cal-d-invito"); await pg11.wait_for_timeout(500)
        inv_=[d for (r,d) in inviati[prima_:] if r=="invito"]
        ok(inv_==[{"id":idn}] and await pg11.inner_text("#cal-d-invito")=="📩 Mandato: guarda la tua mail", f"toccato: UNA POST /assistente/invito con l'id, e il tasto dice «📩 Mandato: guarda la tua mail» ({inv_})")
        ok(await pg11.is_disabled("#cal-d-invito") and await pg11.inner_text("#cal-d-errore")=="", "…e non si ripete per sbaglio")
        prima_=len(inviati)
        await pg11.click("#cal-d-elimina"); await pg11.wait_for_timeout(200)
        ok(await pg11.is_visible("#cal-d-conferma") and not [1 for (r,d) in inviati[prima_:] if r=="elimina"], "«🗑 Elimina» chiede conferma, e non ha ancora eliminato niente")
        await pg11.click("#cal-d-elimina-no"); await pg11.wait_for_timeout(100)
        ok(await pg11.is_visible("#cal-d-elimina") and not await pg11.is_visible("#cal-d-conferma") and not [1 for (r,d) in inviati[prima_:] if r=="elimina"], "«No, lascia»: tutto com'era")
        await pg11.click("#cal-d-elimina"); await pg11.click("#cal-d-elimina-si"); await pg11.wait_for_timeout(900)
        el_=[d for (r,d) in inviati[prima_:] if r=="elimina"]
        ok(len(el_)==1 and el_[0]=={"id":idn}, "conferma → UNA POST /assistente/elimina con il suo id")
        ok(await pg11.is_hidden("#cal-velo") and "dentista" not in await pg11.inner_text(cella(domani_)) and "dentista" not in await pg11.inner_text("#cal-giorno-casa"), "il foglio si chiude e la cosa non c'è più, né in griglia né nell'agenda")
        # una scadenza, senza ora: evento di tutto il giorno; la nota; «Chiudi»; «✓ Pagata» dal dettaglio
        await pg11.click(f'#cal-giorno-casa .cal-riga[data-id="s-bollo"] .cal-apri'); await pg11.wait_for_timeout(300)
        t_=await pg11.inner_text("#cal-foglio")
        ok("bollo auto" in t_ and f"Scade {bello(domani_,True)}" in t_ and "€ 180" in t_ and "✓ Pagata" in t_, "scadenza: la cosa, «Scade …» per esteso, l'importo, «✓ Pagata»")
        ok(await pg11.locator("#cal-d-invito").count()==0, "una scadenza non ha il tasto dell'invito (la porta li manda solo per gli impegni)")
        await pg11.click("#cal-d-chiudi"); await pg11.wait_for_timeout(200)
        ok(await pg11.is_hidden("#cal-velo"), "«Chiudi» chiude il foglio")
        await pg11.click(cella(oggi_)); await pg11.wait_for_timeout(100); await pg11.click('#cal-giorno-casa .cal-riga[data-id="i-oggi"] .cal-apri'); await pg11.wait_for_timeout(300)
        ok("porta il badge" in await pg11.inner_text("#cal-foglio") and await pg11.evaluate("document.querySelector('.cal-dett-nota').innerText.includes('\\n')"), "la nota c'è per intero, anche a capo")
        prima_=len(inviati); await pg11.click("#cal-d-fatto"); await pg11.wait_for_timeout(900)
        ok(len([1 for (r,d) in inviati[prima_:] if r=="fatto"])==1 and await pg11.is_hidden("#cal-velo") and await pg11.locator('#cal-giorno-casa .cal-riga[data-id="i-oggi"]').count()==0, "«✓ Fatto» dal dettaglio: UNA POST /assistente/fatto, il foglio si chiude, la riga non c'è più")
        await pg11.click("#cal-annulla-btn"); await pg11.wait_for_timeout(700)

        print("── il calendario: testi lunghi")
        lungo="Lunghissimo"+"a"*109
        CAL["impegni"].append({"id":"i-lungo","cosa":lungo,"giorno":iso(oggi_),"ora":"08:00","nota":"n"*120})
        CAL["scadenze"].append({"id":"s-lunga","cosa":"Bolletta "+"b"*111,"giorno":iso(oggi_),"importo":"€ 1.234,56","ogni_mese":True})
        await riapri(pg11)
        ok(len(lungo)==120, "una cosa di 120 caratteri")
        dentro="""sel=>{const sec=document.querySelector('#p-calendario .etichetta').getBoundingClientRect(), r=document.querySelector(sel), rr=r.getBoundingClientRect(), c=r.querySelector('.cal-cosa'), cr=c.getBoundingClientRect(), s=c.querySelector('small');
          return {dentro: rr.left>=sec.left-1 && rr.right<=sec.right+1 && cr.right<=sec.right+1, tagliata: r.scrollHeight>r.clientHeight+1 || c.scrollWidth>c.clientWidth+1,
                  piccolo: s? (s.getBoundingClientRect().right<=sec.right+1 && s.getBoundingClientRect().height>0):null, pagina: document.documentElement.scrollWidth<=window.innerWidth}}"""
        v=await pg11.evaluate(dentro,'#cal-giorno-casa .cal-riga[data-id="i-lungo"]')
        ok(v["dentro"] and not v["tagliata"] and v["pagina"], f"la riga lunga va a capo dentro la scheda, senza tagli né scorrimento ({v})")
        v=await pg11.evaluate(dentro,'#cal-giorno-casa .cal-riga[data-id="s-lunga"]')
        ok(v["dentro"] and not v["tagliata"] and v["piccolo"] and "€ 1.234,56" in await pg11.inner_text('#cal-giorno-casa .cal-riga[data-id="s-lunga"]'), f"la scadenza lunga: l'importo resta leggibile, dentro la scheda ({v})")
        await pg11.click('#cal-giorno-casa .cal-riga[data-id="i-lungo"] .cal-apri'); await pg11.wait_for_timeout(300)
        v=await pg11.evaluate("""(()=>{const f=document.getElementById('cal-foglio'), fr=f.getBoundingClientRect(), h=f.querySelector('h3'), hr=h.getBoundingClientRect(), n=document.querySelector('.cal-dett-nota').getBoundingClientRect();
          return {intero:h.textContent.length===120, dentro:hr.left>=fr.left-1&&hr.right<=fr.right+1&&n.right<=fr.right+1, senzaScorrere:f.scrollWidth<=f.clientWidth+1, pagina:document.documentElement.scrollWidth<=innerWidth}})()""")
        ok(all(v.values()), f"il dettaglio della cosa lunga: per intero e dentro il foglio ({v})")
        await pg11.keyboard.press("Escape")
        ok(await pg11.evaluate("getComputedStyle(document.querySelector('#p-calendario .etichetta')).height")!="" and await pg11.evaluate("['#cal-giorno-casa','#p-calendario .etichetta','.cal-riga'].every(s=>{const m=getComputedStyle(document.querySelector(s)).maxHeight;return m==='none'})"), "la scheda non ha altezza fissa (né massima)")

        print("── il calendario: il tema, e il «＋» solo nel calendario")
        await pg11.evaluate("document.documentElement.dataset.tema='deciso'")
        ok(await pg11.evaluate("getComputedStyle(document.querySelector('.cal-cella.oggi .cal-num')).borderTopColor")=="rgb(255, 90, 31)" and await pg11.evaluate("getComputedStyle(document.getElementById('cal-piu')).backgroundColor")=="rgb(255, 90, 31)", "il tema della pagina arriva al calendario (deciso: arancio)")
        await pg11.evaluate("document.documentElement.dataset.tema='tech'")
        await pg11.click("#cal-piu"); await pg11.wait_for_timeout(300)
        await pg11.evaluate("location.hash='#profilo'"); await pg11.wait_for_timeout(500)
        ok(await pg11.evaluate("document.body.dataset.scheda")=="profilo" and await pg11.is_hidden("#cal-velo") and not await pg11.evaluate("document.body.classList.contains('cal-foglio-aperto')"), "cambiando scheda con il foglio aperto, il foglio si chiude")
        ok(not await pg11.is_visible("#cal-piu"), "fuori dal calendario il «＋» non c'è")

        print("── il calendario, a 360 px")
        c360,p360=await calendario_aperto(360,740)
        v=await p360.evaluate("({pagina:document.documentElement.scrollWidth<=360, corpo:document.body.scrollWidth<=360, celle:[...document.querySelectorAll('.cal-cella')].every(c=>c.scrollWidth<=c.clientWidth+1), larghe:Math.min(...[...document.querySelectorAll('.cal-cella')].map(c=>c.getBoundingClientRect().width))})")
        ok(v["pagina"] and v["corpo"] and v["celle"] and v["larghe"]>=40, f"360 px: niente scorrimento di lato, le caselle stanno nella griglia (la più stretta {round(v['larghe'])} px)")
        for n_ in range(4): CAL["impegni"].append({"id":f"i-p{n_}","cosa":f"cosa {n_}","giorno":iso(oggi_),"ora":f"1{n_}:00"})
        await riapri(p360)
        ok("+" in await p360.inner_text(cella(oggi_)+" .cal-piu-n") and await p360.locator(cella(oggi_)+" .cal-et").count()==2, "più di due cose in un giorno: due etichette e «+N»")
        v=await p360.evaluate("({pagina:document.documentElement.scrollWidth<=360, riga:(()=>{const sec=document.querySelector('#p-calendario .etichetta').getBoundingClientRect(), r=document.querySelector('#cal-giorno-casa .cal-riga[data-id=\"i-lungo\"]').getBoundingClientRect();return r.right<=sec.right+1})()})")
        ok(v["pagina"] and v["riga"], "con la cosa lunga, sempre a 360 px: nessuno scorrimento e la riga dentro")
        await p360.click("#cal-piu"); await p360.wait_for_timeout(300)
        v=await p360.evaluate("({pagina:document.documentElement.scrollWidth<=360, foglio:(()=>{const f=document.getElementById('cal-foglio');return f.scrollWidth<=f.clientWidth+1 && [...f.querySelectorAll('input,textarea')].every(i=>i.getBoundingClientRect().right<=f.getBoundingClientRect().right)})()})")
        ok(v["pagina"] and v["foglio"], "il foglio «aggiungi» a 360 px sta dentro, senza scorrere di lato")
        await c360.close()
        # il telefono è in Nuova Zelanda e vuole il movimento ridotto (le ore di Roma non dipendono più dalla pagina: l'invito lo costruisce la porta)
        cr_,pr_=await calendario_aperto(390,844,reduced_motion="reduce",timezone_id="Pacific/Auckland")
        await pr_.click("#cal-piu"); await pr_.wait_for_timeout(100)
        ok(await pr_.evaluate("getComputedStyle(document.getElementById('cal-foglio')).animationName")=="none", "con il movimento ridotto il foglio non si anima")
        await cr_.close()

        print("── il calendario, CONTROPROVA: con la griglia che parte dalla domenica, la prova di novembre è rossa")
        buona=PAGINA; riga_buona='-((new Date(primo+"T12:00:00Z").getUTCDay()+6)%7)'
        ok(riga_buona in buona, "(la riga della griglia è dove la controprova se l'aspetta)")
        PAGINA=buona.replace(riga_buona,'-(new Date(primo+"T12:00:00Z").getUTCDay())')
        cd_,pd_=await calendario_aperto()
        idx_d=await posto_del_primo_novembre(pd_)
        ok(not (await pd_.inner_text("#cal-mese-titolo")=="novembre 2026" and idx_d==6), f"da domenica l'1 novembre finisce in prima colonna (casella n. {idx_d+1}): «ultima colonna» non regge, la prova è rossa")
        await cd_.close(); PAGINA=buona

        print("── il calendario, porta giù")
        CAL["giu"]=True
        await pg11.click("#apri-conv"); await pg11.wait_for_timeout(450); await pg11.click("#menu-calendario"); await pg11.wait_for_timeout(700)
        t_=await pg11.inner_text("#p-calendario")
        ok("Non riesco a raggiungere" in t_ and await pg11.locator(".cal-riprova").count()==1 and "Niente in programma" not in t_ and await pg11.locator(".cal-riga").count()==0 and await pg11.locator(".cal-cella").count()==0 and not await pg11.is_visible("#cal-piu"), "senza rete: il motivo in chiaro e «Riprova», mai «niente in programma»; né griglia né «＋»")
        CAL["giu"]=False; await pg11.click(".cal-riprova"); await pg11.wait_for_timeout(700)
        ok(await pg11.locator(".cal-cella").count()==42 and await pg11.locator(".cal-avviso").count()==0 and await pg11.is_visible("#cal-piu"), "«Riprova» con la porta tornata: il calendario è di nuovo lì")
        print("── il calendario, vuoto")
        CAL.update(impegni=[], scadenze=[], fatti=[])
        await pg11.click("#apri-conv"); await pg11.wait_for_timeout(450); await pg11.click("#menu-calendario"); await pg11.wait_for_timeout(700)
        t_=await pg11.inner_text("#cal-giorno-casa")
        ok(await pg11.locator(".cal-cella").count()==42 and "Niente in questo giorno" in t_ and "Niente in programma. Per segnare una cosa dillo a Nova" in t_, "vuoto: la griglia c'è, «Niente in questo giorno» e «Niente in programma. Per segnare una cosa dillo a Nova»")
        ok(await pg11.is_hidden("#cal-indietro") and await pg11.is_hidden("#cal-fatti"), "senza arretrati né fatti: le due sezioni non ci sono")
        await pg11.click("#cal-alla-chat"); await pg11.wait_for_timeout(500)
        ok(await pg11.evaluate("document.body.dataset.scheda")=="inizia", "il tasto porta alla chat")
        await c11.close()
        print("── errori JavaScript:", errori or "nessuno")
        ok(not errori, "zero errori in tutta la prova")
        await b.close()
    print(f"\n{'VERDE' if not ok.errori else f'ROSSO: {ok.errori}'}")
asyncio.run(main())
