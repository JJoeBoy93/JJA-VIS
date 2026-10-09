"""
Prepara le skin della Sartoria in modelli/skin/*.glb (JJ, 4/10: «le nostre in Blender come base quando inizi; quelle della
2 e la 3 le puoi sbloccare con i gettoni nella Sartoria, e costano come nel negozio di Fortnite, dalle 800 alle 2000 monete»).

    /home/claude/blenderenv/bin/python modelli/prepara_skin.py <quale>
      base-uomo | base-donna            : genera_avatar.py (fatte da noi, gratis)
      realista-uomo | realista-donna    : MPFB2 (genera_mpfb.py) con le braccia abbassate
      persona-<mestiere>-<uomo|donna>   : la skin base, una persona di MakeHuman vestita da lavoro (genera_persona.py,
                                          JJ 9/10: «non voglio omini finti»), con le braccia abbassate
      avventuriera | cavaliere          : KayKit Adventurers (CC0, github.com/KayKit-Game-Assets), senza armi né animazioni

Ogni skin è alta circa 1,9 m, guarda verso +Z di three.js e ha uno scheletro; la città muove gambe e braccia dagli ossi
scritti in SKIN (citta.html).
"""
import sys, os, bpy, math, importlib, runpy
QUI = os.path.dirname(os.path.abspath(__file__)); FUORI = os.path.join(QUI, "skin"); os.makedirs(FUORI, exist_ok=True)
quale = sys.argv[1]
KAYKIT = "/home/claude/kaykit/addons/kaykit_character_pack_adventures/Characters/gltf"

def braccia_giu(corpi, arm, nome, lati, gradi):
    """abbassa le braccia: si posa l'osso del braccio, si applica la posa alla pelle e diventa la posa di riposo"""
    from mathutils import Matrix
    corpi = corpi if isinstance(corpi, list) else [corpi]
    bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for lato, s in zip(lati, (1, -1)):
        pb = arm.pose.bones[nome.format(lato)]
        R = Matrix.Rotation(math.radians(gradi) * s, 4, "Y")   # attorno all'asse avanti-dietro
        m = pb.matrix.copy(); t = m.to_translation()
        pb.matrix = Matrix.Translation(t) @ R @ Matrix.Translation(-t) @ m
    bpy.context.view_layer.update(); bpy.ops.object.mode_set(mode="OBJECT")
    for h in corpi:
        mods = [m for m in h.modifiers if m.type == "ARMATURE"]
        if not mods: continue
        bpy.ops.object.select_all(action="DESELECT"); h.select_set(True); bpy.context.view_layer.objects.active = h
        bpy.ops.object.modifier_copy(modifier=mods[0].name); bpy.ops.object.modifier_apply(modifier=mods[0].name)
    bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode="OBJECT")

def esporta(nome, oggetti, **piu):
    bpy.ops.object.select_all(action="DESELECT")
    for o in oggetti: o.select_set(True)
    out = os.path.join(FUORI, nome + ".glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, export_skins=True, export_animations=False, use_selection=True, **piu)
    print("scritto", out, round(os.path.getsize(out) / 1024), "kB")

if quale.startswith("base-"):
    sys.argv = [sys.argv[0], quale.split("-")[1]]
    runpy.run_path(os.path.join(QUI, "genera_avatar.py"))
    os.replace(os.path.join(QUI, f"avatar-{sys.argv[1]}.glb"), os.path.join(FUORI, quale + ".glb")); print("scritto", quale)

elif quale.startswith("realista-"):
    sys.argv = [sys.argv[0], quale.split("-")[1]]
    g = runpy.run_path(os.path.join(QUI, "genera_mpfb.py"))
    h, arm = g["h"], g["arm"]
    braccia_giu(h, arm, "upperarm_{}", ("l", "r"), 30)
    esporta(quale, [h, arm])

elif quale.startswith("persona-"):
    _, mestiere, corpo = quale.split("-")
    sys.argv = [sys.argv[0], mestiere, corpo]
    g = runpy.run_path(os.path.join(QUI, "genera_persona.py"))
    corpi = [g["corpo"]] + g["pezzi"]
    braccia_giu(corpi, g["arm"], "upperarm_{}", ("l", "r"), 30)
    esporta(quale, [g["arm"]] + corpi, export_image_format="JPEG", export_jpeg_quality=80)   # texture già a 512

else:
    nome = {"avventuriera": "Rogue", "cavaliere": "Knight"}[quale]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KAYKIT, nome + ".glb"))
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    tieni = []
    for o in list(bpy.data.objects):
        if o.type == "ARMATURE": tieni.append(o); o.animation_data_clear()
        elif o.type == "MESH" and o.name.startswith(nome + "_"): tieni.append(o)
        else: bpy.data.objects.remove(o)
    arm = [o for o in tieni if o.type == "ARMATURE"][0]
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    braccia_giu([o for o in tieni if o.type == "MESH"], arm, "upperarm.{}", ("l", "r"), 70)
    alto = max((o.matrix_world @ v.co).z for o in tieni if o.type == "MESH" for v in o.data.vertices)
    arm.scale = [x * 1.9 / alto for x in arm.scale]
    esporta(quale, tieni)
