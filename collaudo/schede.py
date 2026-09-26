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
conta_risposte=[]
async def instrada(route):
    u=route.request.url
    if u.startswith(BASE) and (u==BASE or "#" in u or u.endswith("index.html")):
        return await route.fulfill(body=PAGINA, content_type="text/html")
    if u.endswith("conto.json"): return await route.fulfill(body=open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])),"conto.json")).read(), content_type="application/json")
    if u.endswith("sostieni.json"): return await route.fulfill(body=json.dumps(SOST), content_type="application/json")
    if u.startswith(PORTA):
        if route.request.method=="POST":
            inviati.append((u.split("/")[-1], json.loads(route.request.post_data)))
            return await route.fulfill(status=201, body='{"ok":true,"id":"abc12345"}', content_type="application/json", headers={"Access-Control-Allow-Origin":"https://jjoeboy93.github.io"})
        if u.endswith("/vetrina"): return await route.fulfill(body='{"canzoni":5747,"attrezzi":41}', content_type="application/json")
        if "/risposte" in u:
            conta_risposte.append(1)
            return await route.fulfill(body=json.dumps({"risposte":RISPOSTE}), content_type="application/json")
        return await route.fulfill(body='[]', content_type="application/json")
    await route.fulfill(status=404, body="")
SOST={"pronto":False,"modi":[]}
RISPOSTE=[]
def ok(c,m):
    print(("  ✅ " if c else "  ❌ ")+m); 
    if not c: ok.errori+=1
ok.errori=0
async def main():
    global SOST
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        ctx=await b.new_context(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True)
        await ctx.route("**/*", instrada)
        pg=await ctx.new_page(); errori=[]
        pg.on("pageerror", lambda e: errori.append(str(e)))
        print("── primo arrivo")
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        ok(await pg.is_visible("#o1"), "si apre su Inizia, «Come vuoi chiamarmi?»")
        ok(await pg.inner_text("#et-inizia")=="Inizia", "la prima scheda si chiama Inizia")
        ok(not await pg.is_visible("#p-chi-sono"), "le altre schede sono chiuse")
        await pg.click("#s-chi-sono"); await pg.wait_for_timeout(300)
        ok(await pg.is_visible("#tcs") and "#chi-sono" in pg.url, "tocco «Chi sono»: pannello e indirizzo")
        ok(await pg.inner_text("#n-canzoni")=="5.747", "i numeri della vetrina arrivano")
        ok(await pg.is_visible("#conto"), "Quanto costo c'è")
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
        await scorri(-150); ok(await pg.evaluate("document.body.dataset.scheda")=="profilo", "ancora: Profilo")
        await scorri(150); ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "a destra: torna")
        await scorri(-30); ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "un tocco corto non cambia scheda")
        await pg.click("#s-inizia"); await scorri(150); ok(await pg.evaluate("document.body.dataset.scheda")=="inizia", "dalla prima non si va oltre")
        print("── la prima conversazione")
        await pg.click('#nomi .scelta:has-text("Atlas")'); await pg.click("#avanti-o1"); await pg.wait_for_timeout(300)
        await pg.click("#avanti-o2"); await pg.fill("#tuo-nome","Marco"); await pg.click("#avanti-o3"); await pg.wait_for_timeout(300)
        ok(await pg.inner_text("#et-inizia")=="Atlas", "la scheda prende il nome dato: Atlas")
        ok(await pg.is_visible("#d1") and await pg.is_visible("#parla"), "domande e chat sotto il benvenuto")
        await pg.click('#d1 .scelta:has-text("Corriere")'); await pg.wait_for_timeout(200)
        await pg.click('a[href="#chi-sono"]'); await pg.wait_for_timeout(300)
        ok(await pg.evaluate("document.body.dataset.scheda")=="chi-sono", "«Cosa so fare →» porta a Chi sono")
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
        await pg.click("#s-chi-sono"); await pg.wait_for_timeout(200)
        ok(await pg.is_visible("#costruisci"), "la sezione commissioni è in Chi sono")
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
        d1=await pg3.evaluate("document.getElementById('conosci-domanda').textContent"); ok("ora comincia" in d1, "prima domanda: "+d1)
        await pg3.click('#conosci-scelte .scelta:has-text("Cambia ogni giorno")'); await pg3.wait_for_timeout(1200)
        d2=await pg3.evaluate("document.getElementById('conosci-domanda').textContent"); ok(d2!=d1 and d2, "dopo un secondo, senza ricaricare: "+d2)
        for _ in range(8):
            if not await pg3.is_visible("#conosci-scelte .scelta:not([disabled])"): break
            await pg3.click("#conosci-scelte .scelta:not([disabled]) >> nth=0"); await pg3.wait_for_timeout(1100)
        ok(await pg3.is_visible("#conosci-fine") and not await pg3.is_visible("#conosci"), "finite le domande: «di te so già parecchio»")
        await pg3.close()
        print("── le risposte arrivano da sole")
        pg4=await ctx.new_page(); pg4.on("pageerror", lambda e: errori.append(str(e)))
        await pg4.clock.install()
        await pg4.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'a1b2c3d4e5f60718',nome:'Nova',inviato:true,mestiere:'Ufficio'}))")
        await pg4.goto(BASE+"#parla"); await pg4.wait_for_timeout(300)
        await pg4.fill("#scrivi","Mi faresti il sito della mia azienda?"); await pg4.click("#manda-chat"); await pg4.wait_for_timeout(300)
        prima=len(conta_risposte)
        await pg4.click("#s-chi-sono")
        RISPOSTE.append({"id":"abc12345","domanda":"Mi faresti il sito della mia azienda?","risposta":"Sì, si può fare: lasciami la mail.","quando":"2026-09-26T10:00:00Z"})
        await pg4.clock.fast_forward(21000); await pg4.wait_for_timeout(400)
        ok(len(conta_risposte)>prima, "dopo 20 secondi chiede da sola")
        ok("si può fare" in await pg4.inner_text("#chat"), "la risposta è nella chat senza ricaricare")
        ok(await pg4.evaluate("document.getElementById('s-inizia').classList.contains('nuovo')"), "il puntino sulla prima scheda, perché sei altrove")
        await pg4.click("#s-inizia"); await pg4.wait_for_timeout(200)
        ok(not await pg4.evaluate("document.getElementById('s-inizia').classList.contains('nuovo')"), "tornando, il puntino si spegne")
        dopo=len(conta_risposte); await pg4.clock.fast_forward(180000); await pg4.wait_for_timeout(300)
        ok(len(conta_risposte)==dopo, "niente più in attesa: smette di chiedere")
        RISPOSTE.clear(); await pg4.close()
        print("── Clio, per le guide")
        pg5=await ctx.new_page(); pg5.on("pageerror", lambda e: errori.append(str(e)))
        await pg5.add_init_script("localStorage.setItem('jjavis-io', JSON.stringify({id:'b1b2c3d4e5f60718',nome:'Nova'}))")
        await pg5.goto(BASE+"#clio"); await pg5.wait_for_timeout(300)
        ok(await pg5.evaluate("document.body.dataset.scheda")=="chi-sono" and await pg5.is_visible("#cl-manda"), "#clio apre Chi sono sulla sezione Clio")
        await pg5.fill("#cl-lingue","italiano, inglese"); await pg5.fill("#cl-mail","giulia@guide.it"); await pg5.fill("#cl-nome","Giulia")
        await pg5.click("#cl-manda"); ok("spunta" in await pg5.inner_text("#cl-esito"), "senza consenso non parte")
        await pg5.check("#cl-ok"); await pg5.click("#cl-manda"); await pg5.wait_for_timeout(300)
        cl=[d for (r,d) in inviati if r=="parla" and d.get("da_dove")=="clio"]
        ok(len(cl)==1 and cl[0]["testo"].startswith("🏛 Clio — lingue: italiano, inglese") and "giulia@" not in cl[0]["testo"] and cl[0]["contatto"]["mail"]=="giulia@guide.it", "parte come clio, mail nel contatto e non nel testo")
        ok("invito" in await pg5.inner_text("#cl-esito"), "dice che l'invito arriva per mail")
        await pg5.goto(BASE+"#d1"); await pg5.wait_for_timeout(200)
        await pg5.click('#d1 .scelta:has-text("Guida turistica")'); await pg5.wait_for_timeout(200)
        ok(await pg5.locator('#r1 a[href="#clio"]').count()==1, "chi sceglie Guida turistica si sente dire di Clio, col link")
        ok("Ripetere lo stesso tour" in await pg5.inner_text('.scelte[data-campo="tempo"]'), "e le domande dopo sono da guida")
        await pg5.close()
        print("── Creator o gamer")
        await pg2.goto(BASE+"#d1"); await pg2.wait_for_timeout(200)
        ok(await pg2.locator('#d1 .scelta:has-text("Creator o gamer")').count()==1, "c'è il mestiere Creator o gamer")
        print("── errori JavaScript:", errori or "nessuno")
        ok(not errori, "zero errori in tutta la prova")
        await b.close()
    print(f"\n{'VERDE' if not ok.errori else f'ROSSO: {ok.errori}'}")
asyncio.run(main())
