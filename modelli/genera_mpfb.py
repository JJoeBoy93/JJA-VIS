"""
Persona con MPFB2 (MakeHuman per Blender): corpo vero (CC0), scheletro «game_engine» (53 ossi, come Unreal),
vestiti a zone secondo l'osso (testa/mani pelle, piedi scarpe, gambe pantaloni, il resto maglia), alleggerita.

    /home/claude/blenderenv/bin/python modelli/genera_mpfb.py uomo|donna   -> /home/claude/mpfb-<corpo>.glb

Prima: MPFB2 da GitHub (makehumancommunity/mpfb2) copiato fra le estensioni di Blender come «mpfb»
(bpy.utils.user_resource('EXTENSIONS', path='user_default')). Vestiti e capelli veri di MakeHuman non sono nel suo
repository: si scaricano dal sito della comunità, che dalla sandbox non si raggiunge. PROVA (4/10), non usata dalla città.
"""
import sys, bpy, os, importlib, math
CORPO = sys.argv[1] if len(sys.argv) > 1 else "uomo"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
HS = importlib.import_module("bl_ext.user_default.mpfb.services.humanservice").HumanService
TS = importlib.import_module("bl_ext.user_default.mpfb.services.targetservice").TargetService
donna = CORPO == "donna"
h = HS.create_human(scale=0.1, macro_detail_dict={"gender": 0.0 if donna else 1.0, "age": 0.5, "muscle": 0.55, "weight": 0.5, "height": 0.6, "proportions": 0.7,
    "cupsize": 0.5, "firmness": 0.5, "race": {"african": 0.33, "asian": 0.33, "caucasian": 0.34}})
TS.bake_targets(h)
arm = HS.add_builtin_rig(h, "game_engine")   # prima lo scheletro: le giunture si leggono dalle geometrie d'aiuto
# poi via le geometrie d'aiuto (la maschera), lasciando l'armatura
bpy.ops.object.select_all(action="DESELECT"); h.select_set(True); bpy.context.view_layer.objects.active = h
for m in list(h.modifiers):
    if m.type == "MASK":
        bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0); bpy.ops.object.modifier_apply(modifier=m.name)
print("ossi", len(arm.data.bones), [b.name for b in arm.data.bones][:12])
# materiali per osso dominante: testa/collo/mani pelle, piedi scarpe, gambe e bacino pantaloni, il resto maglia
def mat(n, c):
    m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*c, 1); return m
mats = {"maglia": mat("maglia", (0.05, 0.05, 0.07)), "pantaloni": mat("pantaloni", (0.03, 0.04, 0.08)), "pelle": mat("pelle", (0.76, 0.52, 0.38)), "scarpe": mat("scarpe", (0.06, 0.06, 0.07))}
h.data.materials.clear()
for n in ("maglia", "pantaloni", "pelle", "scarpe"): h.data.materials.append(mats[n])
gn = {g.index: g.name.lower() for g in h.vertex_groups}
ossi = {b.name.lower() for b in arm.data.bones}   # solo i gruppi che sono ossi (MPFB aggiunge anche «body» e altri)
def zona(nome):
    if any(k in nome for k in ("head", "neck", "hand", "thumb", "index", "middle", "ring", "pinky", "jaw", "eye")): return 2
    if any(k in nome for k in ("foot", "ball", "toe")): return 3
    if any(k in nome for k in ("thigh", "calf", "pelvis")): return 1
    return 0
vz = []
for v in h.data.vertices:
    best = max((g for g in v.groups if gn.get(g.group, "") in ossi), key=lambda g: g.weight, default=None)
    vz.append(zona(gn.get(best.group, "")) if best else 0)
for f in h.data.polygons:
    zs = [vz[i] for i in f.vertices]; f.material_index = max(set(zs), key=zs.count)
bpy.ops.object.shade_smooth()
# più leggero
dec = h.modifiers.new("leggero", "DECIMATE"); dec.ratio = 0.25
bpy.ops.object.select_all(action="DESELECT"); h.select_set(True); bpy.context.view_layer.objects.active = h
bpy.ops.object.modifier_move_to_index(modifier="leggero", index=0); bpy.ops.object.modifier_apply(modifier="leggero")
out = f"/home/claude/mpfb-{CORPO}.glb"
if __name__ != "<run_path>":
  bpy.ops.object.select_all(action="DESELECT"); h.select_set(True); arm.select_set(True)
  bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, export_skins=True, export_animations=False, use_selection=True)
  print("scritto", out, round(os.path.getsize(out) / 1024), "kB", len(h.data.vertices), "punti", h.dimensions)
