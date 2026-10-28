"""Aiuti comuni ai collaudi di index.html.

Dal 28/10 ogni sezione dei pannelli (chat e Calendario esclusi) è un <details> chiuso finché non lo si apre (JJ: «se clicchi ad esempio su
I tuoi dati si apre espanso tutto intero, altrimenti resta chiuso»). I collaudi che toccano cose DENTRO le sezioni (campi, elenchi, testi)
le trovano chiuse, quindi nascoste: `sezioni_aperte()` le apre tutte all'apertura di ogni pagina, in un punto solo, invece di una riga per prova.
Il collaudo che prova le sezioni chiuse è collaudo/sezioni.py, e quello NON la chiama.

    import aiuti; aiuti.sezioni_aperte()     # in cima al collaudo, dopo gli import di playwright
"""
from playwright.async_api import Browser

APRI_TUTTE = "document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('details.sezione').forEach(d=>{d.open=true;delete d.dataset.auto}))"


def sezioni_aperte():
    """Ogni contesto del browser (new_context e new_page), e quindi ogni pagina, apre le sezioni appena la pagina è pronta."""
    if getattr(Browser, "_sezioni_aperte", False):
        return
    nuovo, nuova = Browser.new_context, Browser.new_page

    async def new_context(self, *a, **k):
        ctx = await nuovo(self, *a, **k)
        await ctx.add_init_script(APRI_TUTTE)
        return ctx

    async def new_page(self, *a, **k):   # Browser.new_page non passa da questo new_context: ha il suo
        pg = await nuova(self, *a, **k)
        await pg.context.add_init_script(APRI_TUTTE)
        return pg

    Browser.new_context, Browser.new_page = new_context, new_page
    Browser._sezioni_aperte = True


async def apri(pg, selettore):
    """Apre la sezione che contiene `selettore` (se è chiusa), come farebbe una persona toccandola."""
    return await pg.evaluate("s=>{let n=0;for(let d=document.querySelector(s)&&document.querySelector(s).closest('details');d;d=d.parentElement&&d.parentElement.closest('details'))if(!d.open){d.querySelector(':scope>summary').click();n++}return n}", selettore)
