"""
PRIMA PROVA (4/10): la catena funziona (bpy 5.0.1 → .glb con scheletro), ma le forme vengono a palloncini: la suddivisione
arrotonda ogni pezzo staccato. La prossima strada: un corpo solo col modificatore Skin di Blender (uno scheletro di punti
con un raggio, che diventa una pelle continua), poi la suddivisione. I .glb non sono nel repo finché non sono buoni.

Genera l'avatar della città in Blender (bpy 5.0), e lo esporta in glTF (.glb).

    python modelli/genera_avatar.py uomo   -> modelli/avatar-uomo.glb
    python modelli/genera_avatar.py donna  -> modelli/avatar-donna.glb

Serve bpy (Blender come libreria Python): pip install bpy  (vuole Python 3.11).
JJ, 4/10: «partirei proprio da Blender, che mi sblocca anche parte dei progetti 3D da realizzare con Jarvis».

IL CONTRATTO con la città (citta.html), lo stesso degli omini fatti nel codice:
  - in piedi sull'origine, guarda verso +Z di three.js (in Blender: -Y), alto ~2,1 m
  - giunture: anca a 0,90 m (ossa gamba_s, gamba_d), spalle a 1,55 m (ossa braccio_s, braccio_d), testa
  - materiali coi nomi che la città ricolora: maglia, pantaloni, pelle, capelli, scarpe, occhi
Ogni pezzo è legato per intero a un osso (pelle rigida): si piega come gli omini di adesso, ma ha forme morbide
(suddivisione) invece di scatole.
"""
import sys, math, os, bpy
from mathutils import Vector

CORPO = (sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else "uomo"))
DONNA = CORPO == "donna"
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.path.join(QUI, f"avatar-{CORPO}.glb")

# misure (metri). In Blender Z è l'alto e -Y è davanti
M = dict(gx=0.12 if DONNA else 0.14, gr=0.088 if DONNA else 0.095, bx=0.31 if DONNA else 0.34, br=0.064 if DONNA else 0.07,
         top=0.25 if DONNA else 0.28, vita=0.2 if DONNA else 0.23, bacino=0.225 if DONNA else 0.235, testa=0.21 if DONNA else 0.22)
ANCA, SPALLA = 0.90, 1.55

bpy.ops.wm.read_factory_settings(use_empty=True)

def materiale(nome, colore):
    m = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*colore, 1)
    b.inputs["Roughness"].default_value = 0.7
    return m

MAT = dict(maglia=materiale("maglia", (0.05, 0.05, 0.07)), pantaloni=materiale("pantaloni", (0.03, 0.04, 0.08)),
           pelle=materiale("pelle", (0.76, 0.52, 0.38)), capelli=materiale("capelli", (0.08, 0.05, 0.03)),
           scarpe=materiale("scarpe", (0.06, 0.06, 0.07)), occhi=materiale("occhi", (0.02, 0.02, 0.02)))

def morbido(o, livelli=2):
    s = o.modifiers.new("morbido", "SUBSURF"); s.levels = livelli; s.render_levels = livelli
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="morbido")
    bpy.ops.object.shade_smooth()

def pezzo(nome, tipo, loc, scala, mat, livelli=2, rot=(0, 0, 0)):
    if tipo == "cubo": bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    elif tipo == "sfera": bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=loc, rotation=rot, segments=24, ring_count=16)
    elif tipo == "cilindro": bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=loc, rotation=rot, vertices=20)
    o = bpy.context.active_object; o.name = nome; o.scale = scala
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(MAT[mat])
    if livelli: morbido(o, livelli)
    return o

pezzi = {}   # nome dell'osso -> pezzi legati a lui
def lega(osso, o): pezzi.setdefault(osso, []).append(o)

# il corpo: bacino, busto che si stringe in vita, spalle, collo, testa
lega("busto", pezzo("bacino", "cubo", (0, 0, 0.95), (M["bacino"] * 2, M["bacino"] * 1.25, 0.2), "pantaloni"))
busto = pezzo("busto", "cubo", (0, 0, 1.30), (M["top"] * 2, M["top"] * 1.15, 0.66), "maglia")
# il busto più stretto in basso: si avvicinano i vertici sotto la metà
for v in busto.data.vertices:
    if v.co.z < 1.30:
        k = 1 - (1.30 - v.co.z) / 0.33 * (1 - M["vita"] / M["top"])
        v.co.x *= k; v.co.y *= k
lega("busto", busto)
lega("busto", pezzo("collo", "cilindro", (0, 0, 1.67), (0.15, 0.15, 0.14), "pelle", 1))
lega("testa", pezzo("testa", "sfera", (0, 0, 1.90), (M["testa"] * 1.9, M["testa"] * 2.0, M["testa"] * 2.2), "pelle", 1))
for s in (-1, 1):
    lega("testa", pezzo(f"occhio_{s}", "sfera", (0.072 * s, -M["testa"] * 0.92, 1.92), (0.05, 0.03, 0.06), "occhi", 0))
    lega("testa", pezzo(f"orecchio_{s}", "sfera", (M["testa"] * 0.95 * s, 0, 1.89), (0.05, 0.08, 0.09), "pelle", 0))
lega("testa", pezzo("naso", "sfera", (0, -M["testa"] * 0.98, 1.87), (0.05, 0.05, 0.06), "pelle", 0))
# i capelli: una calotta inclinata indietro, sopra le sopracciglia
cap = pezzo("capelli", "sfera", (0, 0.02, 1.98), (M["testa"] * 2.08, M["testa"] * 2.12, M["testa"] * 1.7), "capelli", 1)
for v in cap.data.vertices:
    if v.co.z < 1.93 - 0.06 * (v.co.y / M["testa"]): v.co.z = 1.93 - 0.06 * (v.co.y / M["testa"])
lega("testa", cap)
if DONNA:
    lega("testa", pezzo("capelli_dietro", "cubo", (0, 0.17, 1.74), (0.42, 0.12, 0.5), "capelli"))
# gambe e braccia
for s, lato in ((-1, "s"), (1, "d")):
    lega(f"gamba_{lato}", pezzo(f"gamba_{lato}", "cilindro", (M["gx"] * s, 0, ANCA - 0.42), (M["gr"] * 2, M["gr"] * 2.1, 0.8), "pantaloni"))
    lega(f"gamba_{lato}", pezzo(f"scarpa_{lato}", "cubo", (M["gx"] * s, -0.05, 0.05), (M["gr"] * 2.1, 0.3, 0.11), "scarpe"))
    lega(f"braccio_{lato}", pezzo(f"spalla_{lato}", "sfera", ((M["top"] - 0.04) * s, 0, 1.56), (0.2, 0.18, 0.16), "maglia", 1))
    lega(f"braccio_{lato}", pezzo(f"braccio_{lato}", "cilindro", (M["bx"] * s, 0, SPALLA - 0.3), (M["br"] * 2, M["br"] * 2, 0.56), "maglia"))
    lega(f"braccio_{lato}", pezzo(f"mano_{lato}", "sfera", (M["bx"] * s, 0, SPALLA - 0.63), (M["br"] * 2.3, M["br"] * 2.2, M["br"] * 2.4), "pelle", 1))

# lo scheletro: le giunture del contratto
bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = "scheletro"
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones; eb.remove(eb[0])
def osso(nome, testa, coda, padre=None):
    b = eb.new(nome); b.head = testa; b.tail = coda
    if padre: b.parent = eb[padre]
osso("busto", (0, 0, ANCA), (0, 0, 1.6))
osso("testa", (0, 0, 1.68), (0, 0, 2.1), "busto")
for s, lato in ((-1, "s"), (1, "d")):
    osso(f"gamba_{lato}", (M["gx"] * s, 0, ANCA), (M["gx"] * s, 0, 0.05), "busto")
    osso(f"braccio_{lato}", (M["bx"] * s, 0, SPALLA), (M["bx"] * s, 0, SPALLA - 0.6), "busto")
bpy.ops.object.mode_set(mode="OBJECT")

# un'unica forma, ogni pezzo pesato al 100% sul suo osso
oggetti = []
for nome_osso, lista in pezzi.items():
    for o in lista:
        vg = o.vertex_groups.new(name=nome_osso); vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE"); oggetti.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in oggetti: o.select_set(True)
bpy.context.view_layer.objects.active = oggetti[0]
bpy.ops.object.join(); corpo = bpy.context.active_object; corpo.name = f"avatar_{CORPO}"
mod = corpo.modifiers.new("scheletro", "ARMATURE"); mod.object = arm; corpo.parent = arm

bpy.ops.export_scene.gltf(filepath=FUORI, export_format="GLB", export_yup=True, export_apply=False, export_skins=True,
                          export_animations=False, export_materials="EXPORT")
print("scritto", FUORI, round(os.path.getsize(FUORI) / 1024), "kB", "vertici", len(corpo.data.vertices))
