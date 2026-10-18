"""I biglietti da visita di JJA-VIS, da stampare e tagliare (19 ottobre 2026, Athena).

    python3 strumenti/biglietti.py [uscita.pdf]        (pip install reportlab qrcode)

JJ, 19/10: «biglietti da visita con link e QR code, che poi li stampo li taglio e
potrei fare una sorta di volantinaggio ... nel mio paese».
A4, dieci biglietti 85x55 mm che si toccano: un taglio solo separa due biglietti,
e il fondo scuro non lascia righe bianche se il taglio esce di un millimetro.
I segni di taglio stanno fuori dalla griglia. Stampa al 100% («dimensioni
effettive»), non «adatta alla pagina»: altrimenti i 85 mm non sono più 85.
Il QR porta alla pagina con ?da=biglietto: oggi la pagina lo ignora, domani si
possono contare quelli arrivati dal biglietto.
"""
import io, os, sys
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

CASA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = "https://jjoeboy93.github.io/JJA-VIS/?da=biglietto"
SCRITTO = "jjoeboy93.github.io/JJA-VIS"
FONDO, CIANO, GIALLO, BIANCO, GRIGIO = "#020B18", "#00B4D8", "#FFD60A", "#E8F7FF", "#7FDBFF"
W, H = 85 * mm, 55 * mm
COLONNE, RIGHE = 2, 5
X0 = (A4[0] - COLONNE * W) / 2
Y0 = (A4[1] - RIGHE * H) / 2


def qr_png():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
    q.add_data(LINK); q.make(fit=True)
    b = io.BytesIO(); q.make_image(fill_color="black", back_color="white").save(b, "PNG"); b.seek(0)
    return ImageReader(b)


def biglietto(c, x, y, qr, icona):
    c.setFillColor(FONDO); c.rect(x, y, W, H, stroke=0, fill=1)
    # la riga ciano in alto, come la testata della pagina
    c.setFillColor(CIANO); c.rect(x, y + H - 1.2 * mm, W, 1.2 * mm, stroke=0, fill=1)
    # l'icona e il nome
    c.drawImage(icona, x + 4 * mm, y + H - 19 * mm, 14 * mm, 14 * mm, mask="auto")
    c.setFillColor(BIANCO); c.setFont("Helvetica-Bold", 17)
    c.drawString(x + 20.5 * mm, y + H - 11.5 * mm, "JJA-VIS")
    c.setFillColor(GRIGIO); c.setFont("Helvetica", 6.6)
    c.drawString(x + 20.7 * mm, y + H - 16 * mm, "il tuo assistente personale")
    # cosa fa, in tre righe
    c.setFillColor(BIANCO); c.setFont("Helvetica-Bold", 8.6)
    c.drawString(x + 4 * mm, y + 24 * mm, "Gli dai un nome.")
    c.drawString(x + 4 * mm, y + 19.6 * mm, "Lui impara il tuo lavoro.")
    c.setFillColor(GIALLO); c.setFont("Helvetica-Bold", 7.6)
    c.drawString(x + 4 * mm, y + 13.6 * mm, "Entra gratis nella sua città 3D")
    c.setFillColor(GRIGIO); c.setFont("Helvetica", 6.2)
    c.drawString(x + 4 * mm, y + 5.2 * mm, SCRITTO)
    # il QR: nero su bianco, con la sua cornice bianca (i telefoni lo leggono meglio)
    lato = 27 * mm
    qx, qy = x + W - lato - 4 * mm, y + (H - lato) / 2 - 2.5 * mm
    c.setFillColor("#FFFFFF"); c.roundRect(qx - 0.8 * mm, qy - 0.8 * mm, lato + 1.6 * mm, lato + 1.6 * mm, 1.5 * mm, stroke=0, fill=1)
    c.drawImage(qr, qx, qy, lato, lato)
    c.setFillColor(CIANO); c.setFont("Helvetica-Bold", 6.4)
    c.drawCentredString(qx + lato / 2, qy + lato + 2.6 * mm, "INQUADRAMI")


def segni_di_taglio(c):
    c.setStrokeColor("#000000"); c.setLineWidth(0.25)
    lungo, stacco = 5 * mm, 1.5 * mm
    xs = [X0 + i * W for i in range(COLONNE + 1)]
    ys = [Y0 + j * H for j in range(RIGHE + 1)]
    for x in xs:
        c.line(x, Y0 - stacco, x, Y0 - stacco - lungo)
        c.line(x, Y0 + RIGHE * H + stacco, x, Y0 + RIGHE * H + stacco + lungo)
    for y in ys:
        c.line(X0 - stacco, y, X0 - stacco - lungo, y)
        c.line(X0 + COLONNE * W + stacco, y, X0 + COLONNE * W + stacco + lungo, y)


def main(uscita):
    c = canvas.Canvas(uscita, pagesize=A4)
    c.setTitle("JJA-VIS — biglietti da visita"); c.setAuthor("JJA-VIS")
    qr = qr_png(); icona = ImageReader(os.path.join(CASA, "immagini", "app", "icona-512.png"))
    for i in range(COLONNE):
        for j in range(RIGHE):
            biglietto(c, X0 + i * W, Y0 + j * H, qr, icona)
    segni_di_taglio(c)
    c.setFillColor("#666666"); c.setFont("Helvetica", 7)
    c.drawCentredString(A4[0] / 2, 4 * mm, "Stampa al 100% (dimensioni effettive), su cartoncino. Taglia sui segni: 10 biglietti 85 x 55 mm.")
    c.showPage(); c.save()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "biglietti-jjavis.pdf")
