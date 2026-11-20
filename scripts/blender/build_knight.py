"""Build a mounted knight in tilting armour (seated pose) and export assets/knight.glb.

Run:  blender -b -P scripts/blender/build_knight.py -- <out_dir> [preview_dir]
Origin = the seat point on the saddle. Blender axes: +Y forward, +Z up, +X = rider's right.
Lance, shield and the hit proxy stay in the game code (gameplay needs them); this is the armour.
Lance grip (right hand) at (0.30, 0.10, 0.45); shield arm (left) reaches toward (-0.30, 0.08, 0.52).

Armour is made of plate *shells*: sphere/cone sections cut open, given real thickness (solidify) and
rounded by one subdivision level, so edges read as rolled plate rather than solid blobs.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = argv[0] if argv else os.path.join(os.path.dirname(__file__), "..", "..", "assets")
PREVIEW_DIR = argv[1] if len(argv) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
parts = []


def material(name, colour, metal, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    return m


STEEL = material("Steel", (0.8, 0.8, 0.82), 1.0, 0.24)
DARK = material("DarkSteel", (0.05, 0.05, 0.055), 0.9, 0.45)
BRASS = material("Brass", (0.85, 0.65, 0.3), 1.0, 0.3)
MAIL = material("Mail", (0.4, 0.4, 0.42), 1.0, 0.55)
LEATHER = material("Leather", (0.26, 0.14, 0.07), 0.0, 0.6)


def add_object(name, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), thick=0.0, subdiv=1):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    if thick:
        m = ob.modifiers.new("solid", "SOLIDIFY"); m.thickness = thick; m.offset = 0
    if subdiv:
        m = ob.modifiers.new("sub", "SUBSURF"); m.levels = m.render_levels = subdiv
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    parts.append(ob)
    return ob


def shell(name, loc, scale, keep, mat, thick=0.007, seg=32, rings=16, shape=None, rot=(0, 0, 0)):
    """Section of an ellipsoid: unit-sphere verts failing keep(co) are cut away; shape(co) may sculpt first."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1)
    if shape:
        for v in bm.verts: shape(v.co)
    bad = [v for v in bm.verts if not keep(v.co)]
    if bad: bmesh.ops.delete(bm, geom=bad, context="VERTS")
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return add_object(name, bm, mat, loc, rot, thick)


def band(name, loc, r_bot, r_top, h, mat, yscale=1.0, arc=None, rot=(0, 0, 0), thick=0.006, seg=40):
    """Open cone band (a lame). arc=(a0, a1) keeps only that angular range (radians, 0 = +X, pi/2 = +Y front)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=seg, radius1=r_bot, radius2=r_top, depth=h)
    if arc:
        a0, a1 = arc
        bad = [v for v in bm.verts if not (a0 <= math.atan2(v.co.y, v.co.x) <= a1)]
        bmesh.ops.delete(bm, geom=bad, context="VERTS")
    for v in bm.verts: v.co.y *= yscale
    return add_object(name, bm, mat, loc, rot, thick)


def tube(name, a, b, r0, r1, mat, seg=24, thick=0.006):
    a, b = Vector(a), Vector(b); d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=not thick, cap_tris=False, segments=seg, radius1=r0, radius2=r1, depth=d.length)
    ob = add_object(name, bm, mat, (a + b) / 2, (0, 0, 0), thick, 1)
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return ob


def ball(name, loc, scale, mat, seg=20, rings=10, rot=(0, 0, 0)):
    return shell(name, loc, scale, lambda c: True, mat, thick=0, seg=seg, rings=rings, rot=rot)


def rivets(points, r=0.007, mat=BRASS):
    for p in points:
        ball("rivet", p, (r, r, r * 0.6), mat, seg=8, rings=4)


def box(name, loc, size, mat, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = add_object(name, bm, mat, loc, rot, 0, 0)
    m = ob.modifiers.new("bev", "BEVEL"); m.width = min(size) * 0.3; m.segments = 2
    return ob


# ------------------------------------------------------------------ saddle (war saddle, high cantle)
box("saddle", (0, -0.02, -0.03), (0.36, 0.62, 0.08), LEATHER)
box("cantle", (0, -0.27, 0.12), (0.4, 0.07, 0.32), LEATHER, rot=(math.radians(-12), 0, 0))
box("pommel", (0, 0.25, 0.06), (0.3, 0.07, 0.18), LEATHER, rot=(math.radians(15), 0, 0))

# ------------------------------------------------------------------ torso
def keel(c):
    if c.y > 0: c.y += 0.12 * max(0.0, 1 - abs(c.x) * 3.5) * c.y   # gentle ridge down the centre of the breastplate


shell("breastplate", (0, 0.0, 0.56), (0.24, 0.18, 0.28), lambda c: c.y > -0.05 and -0.72 < c.z < 0.78, STEEL, 0.008, shape=keel)
shell("backplate", (0, -0.005, 0.56), (0.235, 0.165, 0.27), lambda c: c.y < 0.05 and -0.72 < c.z < 0.8, STEEL, 0.008)
band("neckRoll", (0, 0.005, 0.765), 0.13, 0.11, 0.03, STEEL, yscale=0.85, thick=0.012)       # rolled neck edge
rivets([(s * 0.12, 0.155, 0.4) for s in (-1, 1)] + [(0, 0.17, 0.36)])
# Fauld: overlapping lames flaring over the hips, tassets over the thighs, mail beneath
for i in range(3):
    z = 0.36 - i * 0.055
    band(f"fauld{i}", (0, 0.0, z), 0.2 + i * 0.012, 0.185 + i * 0.012, 0.07, STEEL, yscale=0.82)
    rivets([(0.0, (0.2 + i * 0.012) * 0.82 + 0.004, z - 0.025)])
for s in (-1, 1):
    for i in range(2):  # two-lame tassets
        band(f"tasset{s}{i}", (s * 0.11, 0.05, 0.17 - i * 0.07), 0.13, 0.12, 0.075, STEEL,
             arc=(math.radians(50), math.radians(130)), rot=(math.radians(-22), 0, s * math.radians(14)))
band("mailSkirt", (0, 0.0, 0.11), 0.27, 0.215, 0.16, MAIL, yscale=0.85, thick=0.01)

# ------------------------------------------------------------------ gorget and armet
band("gorget1", (0, 0.0, 0.82), 0.125, 0.1, 0.05, STEEL, yscale=0.9)
band("gorget2", (0, 0.0, 0.86), 0.1, 0.085, 0.045, STEEL, yscale=0.9)
HC = Vector((0, 0.0, 1.08))
shell("skull", HC, (0.13, 0.15, 0.15), lambda c: c.z > -0.4 and not (c.y > 0.5 and c.z < 0.12), STEEL, 0.006, seg=40, rings=20)
ball("comb", HC + Vector((0, -0.01, 0.138)), (0.011, 0.12, 0.035), STEEL)  # low ridge along the skull


def beak(c):
    if c.y > 0:  # stretch forward and pinch into a keel: the "sparrow-beak" visor
        y = c.y; c.y *= 1 + 0.35 * y; c.x *= 1 - 0.72 * y ** 1.2


shell("visor", HC + Vector((0, 0.06, -0.035)), (0.128, 0.16, 0.1), lambda c: c.y > -0.15 and c.z < 0.35, STEEL, 0.006, seg=40, rings=20, shape=beak)
shell("helmLining", HC, (0.115, 0.135, 0.135), lambda c: c.y > 0.2, DARK, 0)  # dark inside shows through the slit
shell("bevor", HC + Vector((0, 0.035, -0.115)), (0.122, 0.13, 0.07), lambda c: c.y > -0.3 and c.z < 0.6, STEEL, 0.006)
for s in (-1, 1):
    ball("visorPivot", HC + Vector((s * 0.132, 0.0, -0.02)), (0.012, 0.022, 0.022), BRASS)
for i in range(5):  # breaths on the right side of the visor
    box("breath", HC + Vector((0.07, 0.15 - i * 0.012, -0.06)), (0.012, 0.006, 0.03), DARK, rot=(0, 0, math.radians(25)))

# ------------------------------------------------------------------ shoulders
for s in (-1, 1):
    pc = Vector((s * 0.255, 0.0, 0.79))
    shell(f"pauldron{s}", pc, (0.13, 0.14, 0.11), lambda c: c.z > -0.45, STEEL, 0.008)
    for i in range(3):  # lames stepping down the upper arm
        band(f"pLame{s}{i}", pc + Vector((s * 0.01 * (i + 1), 0, -0.05 - i * 0.036)), 0.118 - i * 0.007, 0.126 - i * 0.007, 0.05,
             STEEL, yscale=1.1)
    rivets([pc + Vector((s * 0.06, 0.1, 0.03)), pc + Vector((s * 0.06, -0.1, 0.03))])
# Grand guard: big reinforcing plate over the left shoulder and breast (tilting armour)
shell("grandGuard", (-0.11, 0.05, 0.64), (0.21, 0.17, 0.26), lambda c: c.x < 0.25 and c.y > -0.2 and c.z > -0.55, STEEL, 0.01,
      rot=(0, math.radians(-8), math.radians(-12)))
rivets([(-0.05, 0.2, 0.52), (-0.18, 0.18, 0.5), (-0.2, 0.12, 0.8), (-0.04, 0.17, 0.8)])

# ------------------------------------------------------------------ arms: right couched under the lance, left forward to the shield
R_SH, R_EL, R_HAND = (0.27, -0.01, 0.7), (0.33, -0.12, 0.5), (0.3, 0.1, 0.45)
L_SH, L_EL, L_HAND = (-0.27, -0.01, 0.7), (-0.31, -0.02, 0.5), (-0.28, 0.12, 0.54)
for side, (sh, el, hand) in (("R", (R_SH, R_EL, R_HAND)), ("L", (L_SH, L_EL, L_HAND))):
    tube("rerebrace" + side, sh, el, 0.058, 0.052, STEEL)
    el_v, hand_v = Vector(el), Vector(hand)
    ball("couter" + side, el, (0.062, 0.062, 0.062), STEEL)
    out = Vector((1 if side == "R" else -1, 0, 0))
    ball("couterWing" + side, el_v + out * 0.05, (0.012, 0.075, 0.065), STEEL)   # fan-shaped wing
    tube("vambrace" + side, el, hand, 0.05, 0.043, STEEL)
    d = (hand_v - el_v).normalized()
    tube("gauntletCuff" + side, hand_v - d * 0.07, hand_v - d * 0.005, 0.048, 0.064, DARK, thick=0.006)
    ball("gauntlet" + side, hand_v + d * 0.025, (0.05, 0.065, 0.05), DARK)
    for k in range(3):  # finger lames
        ball("finger", hand_v + d * (0.06 + 0.012 * k) + Vector((0, 0, -0.01)), (0.046, 0.012, 0.04), DARK)

# ------------------------------------------------------------------ legs astride: cuisses, poleyns, greaves, pointed sabatons
for s in (-1, 1):
    hip, knee, ankle = Vector((s * 0.13, 0.03, 0.12)), Vector((s * 0.3, 0.3, -0.08)), Vector((s * 0.3, 0.12, -0.55))
    tube("cuisse", hip, knee, 0.088, 0.072, STEEL)
    shell("poleyn", knee + Vector((0, 0.02, 0)), (0.07, 0.075, 0.07), lambda c: c.y > -0.3, STEEL, 0.006)
    ball("poleynWing", knee + Vector((s * 0.06, 0.0, 0.0)), (0.012, 0.06, 0.07), STEEL)
    tube("greave", knee, ankle, 0.064, 0.047, STEEL)
    foot = ankle + Vector((0, 0.04, -0.07))
    for k in range(4):  # segmented sabaton narrowing to a point
        ball("sabaton", foot + Vector((0, 0.045 * k, -0.005 * k)), (0.055 - 0.009 * k, 0.04, 0.04 - 0.004 * k), STEEL)
    box("stirrup", ankle + Vector((0, 0.08, -0.115)), (0.1, 0.12, 0.015), DARK)

# ------------------------------------------------------------------ join (one draw call per material) and export
bpy.ops.object.select_all(action="DESELECT")
for ob in parts: ob.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.convert(target="MESH")   # apply solidify / subsurf / bevel
bpy.ops.object.join()
knight = bpy.context.active_object; knight.name = "Knight"
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)   # UVs for the scanned steel/leather textures
bpy.ops.object.mode_set(mode="OBJECT")
dec = knight.modifiers.new("dec", "DECIMATE"); dec.ratio = 0.5   # game budget: two knights on screen, phones too
bpy.ops.object.modifier_apply(modifier="dec")
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
glb = os.path.join(OUT_DIR, "knight.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_yup=True)
print("EXPORTED", glb, "faces", len(knight.data.polygons))

if PREVIEW_DIR:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
    scene.camera = cam; cam.data.lens = 50
    scene.world = bpy.data.worlds.new("w"); scene.world.color = (0.6, 0.65, 0.7)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_specular_highlight = True
    scene.render.resolution_x, scene.render.resolution_y = 480, 640
    for name, loc, look in (("front", (1.2, 2.3, 0.6), (0, 0, 0.35)), ("side", (2.6, 0.05, 0.45), (0, 0, 0.35)),
                            ("helm", (0.45, 0.7, 1.15), (0, 0.02, 1.05))):
        cam.location = loc
        cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(PREVIEW_DIR, f"knight_{name}.png")
        bpy.ops.render.render(write_still=True)
    print("PREVIEWS", PREVIEW_DIR)
