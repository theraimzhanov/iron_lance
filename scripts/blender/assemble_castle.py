"""Assemble a castle and a curtain wall from Poly Haven's photoscanned modular fort kit (CC0).

Run:  blender -b -P scripts/blender/assemble_castle.py -- <kit_gltf_dir> <out_dir> [preview_dir]
Writes castle.glb (four corner towers, curtain walls, gated front, tall keep) and curtain.glb (a straight wall
with a central gatehouse tower). Kit pieces: walls run along local -Y from y=0, thickness along +X from x=0.
"""
import bpy, sys, os, glob, math
from mathutils import Vector, Matrix

kit_dir, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
preview = sys.argv[sys.argv.index("--") + 3] if len(sys.argv) > sys.argv.index("--") + 3 else None
os.makedirs(out_dir, exist_ok=True)


def load_kit():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glob.glob(os.path.join(kit_dir, "*.gltf"))[0])
    kit = {}
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH":
            o.parent = None
            kit[o.name.replace("modular_fort_01_", "")] = o
    return kit


def local_center(o):
    vs = [Vector(c) for c in o.bound_box]
    return Vector([(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)]), min(v[2] for v in vs)


placed = []


def place(kit, name, cx, cy, angle_deg=0.0, sz=1.0, base=0.0):
    """Put a linked copy of a kit piece with its footprint centred on (cx, cy), standing on z=base."""
    src = kit[name]
    o = src.copy(); bpy.context.scene.collection.objects.link(o)
    c, zmin = local_center(src)
    R = Matrix.Rotation(math.radians(angle_deg), 3, "Z")
    off = R @ Vector((c.x, c.y, 0))
    o.rotation_mode = "XYZ"  # the glTF importer leaves objects in quaternion mode, which ignores rotation_euler
    o.rotation_euler = (0, 0, math.radians(angle_deg)); o.scale = (1, 1, sz)
    o.location = (cx - off.x, cy - off.y, base - zmin * sz)
    placed.append(o)
    return o


def finish(path):
    kit_objs = set(o for o in bpy.context.scene.objects if o.type == "MESH") - set(placed)
    for o in kit_objs: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in placed: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_image_format="JPEG")
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in placed)
    print("EXPORTED", path, "pieces", len(placed), "tris", tris)


# ------------------------------------------------------------------ castle on the hill
kit = load_kit()
D = 22.0                                      # half-size of the courtyard, tower centres at the corners
for sx in (-1, 1):
    for sy in (-1, 1):
        place(kit, "tower_round", sx * D, sy * D)
for i, y in enumerate((D - 7.0 - 7.28, D - 7.0 - 7.28 - 14.56)):   # east and west walls (two sections each)
    place(kit, "wall_thick_straight_0%d" % (1 + i % 2), D, y)
    place(kit, "wall_thick_straight_0%d" % (2 - i % 2), -D, y)
for i, x in enumerate((D - 7.0 - 7.28, D - 7.0 - 7.28 - 14.56)):   # north (back) wall
    place(kit, "wall_thick_straight_0%d" % (1 + i % 2), x, D, 90)
# south (front) wall: thin sections either side of the gate
for name, x in (("wall_thin_straight_03", -11.0), ("wall_thin_straight_04", -6.0), ("wall_thin_gate_01", 0.0),
                ("wall_thin_straight_04", 6.0), ("wall_thin_straight_03", 11.0)):   # overlapping, so no gaps
    place(kit, name, x, -D, 90)
place(kit, "tower_round", 0, 4, sz=1.9)        # the keep: a taller tower inside the courtyard
finish(os.path.join(out_dir, "castle.glb"))

# ------------------------------------------------------------------ curtain wall closing the far end of the field
placed.clear()
kit = load_kit()
for k in range(-3, 4):
    if k == 0: continue
    place(kit, "wall_thick_straight_0%d" % (1 + (k % 2)), k * 14.56 - math.copysign(7.0, k) * 0.0, 0, 90)
place(kit, "tower_round", 0, 0, sz=1.3)        # gatehouse tower in the middle
for sx in (-1, 1):
    place(kit, "tower_round", sx * 3.5 * 14.56, 0, sz=0.9)
finish(os.path.join(out_dir, "curtain.glb"))

if preview:
    for name in ("castle", "curtain"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"))
        sc = bpy.context.scene
        cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
        cam.location = (60, -95, 45) if name == "castle" else (30, -110, 25)
        cam.rotation_euler = (Vector((0, 0, 6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
        sc.render.resolution_x, sc.render.resolution_y = 800, 450
        sc.render.filepath = os.path.join(preview, name + ".png"); bpy.ops.render.render(write_still=True)
