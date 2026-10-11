"""La natura della città dai demo CC0 di Blender (JJ, 11/10: «usa anche le altre librerie per fare gli alberi, il prato, il fondo
del laghetto fallo con i ciottoli e il pavimento della piazza con i sanpietrini che ci sono nei Blender già a disposizione»).

    /home/claude/blenderenv/bin/python modelli/prepara_natura.py <cartella dei demo>

I demo stanno nella bozza «Modelli-1» di JJA-VIS-Voci (caricati da JJ il 9/10 dalla pagina «demo files» di blender.org, solo
quelli CC0): tree_leaves_moss_geo-nodes-demo.blend (la quercia) e pebble_scattering.blend (i sassi). Escono:
  modelli/natura/quercia.glb       la quercia dei parchi: legno ridotto + ciuffi di foglie su carte ritagliate (~5.000 triangoli)

  modelli/natura/ciottoli.glb      sette ciottoli del demo, ognuno una mesh, per il fondo del laghetto
  modelli/natura/foglie.png        la carta delle foglie: foglie di quercia del demo fotografate dall'alto, con lo sfondo trasparente
"""
import bpy, bmesh, random, math, sys, os
from mathutils import Matrix, Vector
DEMO = sys.argv[-1]; QUI = os.path.dirname(os.path.abspath(__file__)); FUORI = os.path.join(QUI, "natura"); os.makedirs(FUORI, exist_ok=True)
random.seed(7)

# ── 1. la quercia: il legno (tronco e rami medi, senza suddivisione) e le punte dei rami piccoli, dove vanno le foglie ──
bpy.ops.wm.open_mainfile(filepath=os.path.join(DEMO, "tree_leaves_moss_geo-nodes-demo.blend"))
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type == "SUBSURF": m.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
legno = bmesh.new(); punte = []
for inst in dg.object_instances:
    o = inst.object; n = o.original.name
    if o.type != "MESH": continue
    M = inst.matrix_world.copy()
    if (n.startswith("GEO-oak.1_trunk") and "moss" not in n) or n.startswith("GEO-tree_branch_medium"):
        me = o.to_mesh(); me.transform(M); legno.from_mesh(me); o.to_mesh_clear()
    elif n.startswith("GEO-tree_branch_small") or n.startswith("GEO-tree_branch_twig"):
        me = o.to_mesh(); vs = [M @ v.co for v in me.vertices]; o.to_mesh_clear()
        c = sum(vs, Vector()) / len(vs); punte.append((c, max((v - c).length for v in vs)))
foglia = bpy.data.objects["GEO-leaves-oak.004"]
_f = foglia.evaluated_get(dg).to_mesh()
FOGLIA = ([v.co.copy() for v in _f.vertices], [tuple(q.vertices) for q in _f.polygons])   # i dati, non la mesh: aprire un file nuovo la cancella

# ── 2. la carta delle foglie: 60 foglie del demo sparse in un quadrato, fotografate dall'alto su sfondo trasparente ──
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
fme = bpy.data.meshes.new("foglia"); fme.from_pydata(*FOGLIA[:1], [], FOGLIA[1]) if False else fme.from_pydata(FOGLIA[0], [], FOGLIA[1])
verdi = [(0.16, 0.36, 0.10), (0.22, 0.45, 0.13), (0.12, 0.30, 0.09), (0.28, 0.50, 0.16)]
for k in range(70):
    o = bpy.data.objects.new(f"f{k}", fme); sc.collection.objects.link(o)
    a = random.uniform(0, 2 * math.pi); r = 0.42 * math.sqrt(random.random())
    o.location = (math.cos(a) * r, math.sin(a) * r, random.uniform(0, 0.05)); o.scale = (2.2, 2.2, 2.2)
    o.rotation_euler = (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 2 * math.pi))
    o.color = (*verdi[k % 4], 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.15; cam.location = (0, 0, 3)
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 256
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
carta = os.path.join(FUORI, "foglie.png"); sc.render.filepath = carta; bpy.ops.render.render(write_still=True)

def quercia(nome, legno_tris, ciuffi, lato):
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    me = bpy.data.meshes.new("legno"); legno.to_mesh(me)
    ol = bpy.data.objects.new("legno", me); sc.collection.objects.link(ol)
    bpy.context.view_layer.objects.active = ol
    d = ol.modifiers.new("leggero", "DECIMATE"); d.ratio = legno_tris / max(1, len(me.polygons) * 2); bpy.ops.object.modifier_apply(modifier="leggero")
    mlg = bpy.data.materials.new("corteccia"); mlg.use_nodes = True
    mlg.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.16, 0.11, 1)
    me.materials.append(mlg)
    # i ciuffi: le punte si raggruppano a griglia (lato = metri) e ogni gruppo ha tre carte incrociate
    gruppi = {}
    for c, r in punte:
        k = (round(c.x / lato), round(c.y / lato), round(c.z / lato)); gruppi.setdefault(k, []).append(c)
    centri = sorted(gruppi.values(), key=len, reverse=True)[:ciuffi]
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    for g in centri:
        c = sum(g, Vector()) / len(g); s = lato * 1.35 + random.uniform(-0.1, 0.1)
        rot = random.uniform(0, math.pi)
        for asse in range(3):
            if asse == 0: R = Matrix.Rotation(rot, 3, "Z") @ Matrix.Rotation(math.pi / 2, 3, "X")
            elif asse == 1: R = Matrix.Rotation(rot + math.pi / 2, 3, "Z") @ Matrix.Rotation(math.pi / 2, 3, "X")
            else: R = Matrix.Rotation(rot, 3, "Z")
            vs = [bm.verts.new(c + R @ Vector((x * s / 2, y * s / 2, 0))) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            f = bm.faces.new(vs)
            for l, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = (u, v)
    mf = bpy.data.meshes.new("foglie"); bm.to_mesh(mf)
    of = bpy.data.objects.new("foglie", mf); sc.collection.objects.link(of)
    mfo = bpy.data.materials.new("foglie"); mfo.use_nodes = True; nt = mfo.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(carta)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"])
    mfo.blend_method = "CLIP" if hasattr(mfo, "blend_method") else None; mfo.use_backface_culling = False
    mf.materials.append(mfo)
    # in piedi su y, alta 8 m (la quercia del demo è alta ~6,4): la città la scala ancora per albero
    alto = max(v.co.z for v in me.vertices); k = 8.0 / alto
    for o in (ol, of): o.scale = (k, k, k)
    bpy.ops.object.select_all(action="DESELECT"); ol.select_set(True); of.select_set(True)
    out = os.path.join(FUORI, nome + ".glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, use_selection=True, export_apply=True)
    print("scritto", out, os.path.getsize(out) // 1024, "kB · legno", len(me.polygons), "facce · carte", len(mf.polygons))

quercia("quercia", 500, 70, 1.2)
# (la quercia-lontana per il bosco: tolta l'11/10, il bosco resta di coni sotto la nebbia)

# ── 3. i ciottoli del laghetto: i sette sassi del demo dei sassi ──
bpy.ops.wm.open_mainfile(filepath=os.path.join(DEMO, "pebble_scattering.blend"))
sassi = [o for o in bpy.data.objects if o.name.startswith("GEO-pebble")]
for o in list(bpy.data.objects):
    if o not in sassi: bpy.data.objects.remove(o)
for i, o in enumerate(sassi):
    for c in list(o.users_collection): c.objects.unlink(o)   # nel demo stanno in una raccolta esclusa dalla scena: non si esporterebbero
    bpy.context.scene.collection.objects.link(o)
    o.location = (i * 0.3, 0, 0); o.name = f"ciottolo{i}"
    m = bpy.data.materials.new("ciottolo"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.6, 0.58, 0.54, 1)
    o.data.materials.clear(); o.data.materials.append(m)
bpy.ops.object.select_all(action="DESELECT")
for o in sassi: o.select_set(True)
out = os.path.join(FUORI, "ciottoli.glb")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_yup=True, use_selection=True, export_apply=True)
print("scritto", out, os.path.getsize(out) // 1024, "kB · sassi", len(sassi), [round(max(o.dimensions), 3) for o in sassi])
