"""Runs INSIDE Blender (background mode). Builds a cinematic scene from scene.json + the style preset, then renders frames.

Called by engines/blender/render.py:
  blender -b --factory-startup --python-exit-code 1 -P build_scene.py -- ARGS.json
ARGS.json: {scene, style_json, out, width, height, fmt, engine (EEVEE|CYCLES), samples, frames: [..], gpu, save_blend}
Coordinates: Blender's own (metres, Z is UP). Camera lens = mm on a 24 mm-high sensor (vertical fit), so every
format keeps the same vertical view and wider formats see more at the sides (like the Toon 3D engine).
"""
import json, math, os, sys, time

import bpy
from mathutils import Vector

ARGS = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
SC = json.load(open(ARGS["scene"], encoding="utf-8"))
ST = ARGS["style"]
FPS = SC.get("fps", 30)


def hex2lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


# ---------------- reset ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS


# ---------------- materials (procedural, from the style preset) ----------------
_MATS = {}


def material(name):
    if name in _MATS:
        return _MATS[name]
    spec = ST.get("materials", {}).get(name) or {"color": name if str(name).startswith("#") else "#888888", "roughness": 0.8}
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex2lin(spec["color"])
    bsdf.inputs["Roughness"].default_value = spec.get("roughness", 0.8)
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if spec.get("sheen"):
        bsdf.inputs["Sheen Weight"].default_value = spec["sheen"]
    if spec.get("subsurface"):
        bsdf.inputs["Subsurface Weight"].default_value = spec["subsurface"]
    if spec.get("noise"):                       # colour variation + bump from one noise texture (no image files)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = spec["noise"]
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        v = spec.get("var", 0.15)
        base = hex2lin(spec["color"])
        ramp.color_ramp.elements[0].color = [c * (1 - v) for c in base[:3]] + [1]
        ramp.color_ramp.elements[1].color = [min(1, c * (1 + v)) for c in base[:3]] + [1]
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        if spec.get("bump"):
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = spec["bump"]
            nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    _MATS[name] = m
    return m


def assign(obj, mat_name):
    obj.data.materials.clear()
    obj.data.materials.append(material(mat_name))


def displace(obj, strength, size=1.5, seed=0, subdiv=3, simple=True, basis=None):
    if subdiv:
        s = obj.modifiers.new("subdiv", "SUBSURF")
        s.subdivision_type = "SIMPLE" if simple else "CATMULL_CLARK"
        s.levels = s.render_levels = subdiv
    tex = bpy.data.textures.new(f"clouds{seed}", "CLOUDS")
    tex.noise_scale = size
    tex.noise_depth = 3
    if basis:
        try:
            tex.noise_basis = basis                      # e.g. VORONOI_F2F1 = cracked, blocky rock
        except Exception:
            pass
    d = obj.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.mid_level = 0.5
    d.texture_coords = "GLOBAL"
    return d


def place(obj, el):
    obj.location = el.get("pos", [0, 0, 0])
    r = el.get("rot", [0, 0, 0])
    obj.rotation_euler = [math.radians(a) for a in r]
    return obj


def smooth_shade(obj, flat_axis=None):
    """Smooth shading; with flat_axis="Z" the faces facing along local Z (cylinder caps) stay flat (no radial streaks)."""
    for p in obj.data.polygons:
        p.use_smooth = not (flat_axis == "Z" and abs(p.normal.z) > 0.7)


# ---------------- elements ----------------
def el_ground(el):
    n = el.get("detail", 80)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=el.get("size", 200))
    o = bpy.context.object
    place(o, el)
    displace(o, el.get("bumps", 0.4), size=el.get("bump_size", 6), seed=1, subdiv=0)
    smooth_shade(o)
    assign(o, el.get("material", "ground"))
    return o


def el_cliff(el):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = place(bpy.context.object, el)
    o.scale = el.get("size", [12, 6, 6])
    bpy.ops.object.transform_apply(scale=True)
    assign(o, el.get("material", "rock"))
    bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.8; bev.segments = 3
    displace(o, el.get("rough", 0.9), size=el.get("rough_size", 1.6), seed=2, subdiv=el.get("detail", 4), basis="VORONOI_F2F1")
    displace(o, el.get("rough", 0.9) * 0.35, size=0.45, seed=8, subdiv=0, basis="BLENDER_ORIGINAL")
    # doorways are cut LAST so their edge stays clean (subdivision level 4 keeps the exact boolean light on RAM)
    for h in el.get("openings", []):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=h.get("radius", 1.0), depth=h.get("depth", 4))
        cut = bpy.context.object
        cut.location = h["pos"]
        cut.rotation_euler = [math.radians(a) for a in h.get("rot", [90, 0, 0])]
        cut.scale = h.get("scale", [1, 1.25, 1])
        cut.hide_render = True; cut.display_type = "WIRE"
        cut.data.materials.append(material("dark"))                   # the inside of the doorway is a dark void
        b = o.modifiers.new("door", "BOOLEAN"); b.object = cut; b.operation = "DIFFERENCE"; b.solver = "EXACT"
        try:
            b.material_mode = "TRANSFER"
        except Exception:
            pass
    smooth_shade(o)
    return o


def el_disc(el):                                         # a rolling stone, a millstone, a wheel
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=el.get("radius", 1.4), depth=el.get("thickness", 0.45))
    o = place(bpy.context.object, el)
    bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.08; bev.segments = 3
    smooth_shade(o, flat_axis="Z")                       # texture comes from the bump material (displacing the caps streaks them)
    assign(o, el.get("material", "rock_light"))
    return o


def el_rock(el):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
    o = place(bpy.context.object, el)
    o.scale = el.get("size", [1, 1, 0.7])
    displace(o, el.get("rough", 0.35), size=0.7, seed=el.get("seed", 4), subdiv=1)
    smooth_shade(o)
    assign(o, el.get("material", "rock"))
    return o


def el_tree(el):                                         # olive-like: twisted trunk + clumpy canopy
    h = el.get("height", 4.0)
    x, y, z = el.get("pos", [0, 0, 0])
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.28 * h / 4, radius2=0.12 * h / 4, depth=h * 0.6, location=(x, y, z + h * 0.3))
    t = bpy.context.object
    t.rotation_euler = (0.08, 0.12, 0)
    displace(t, 0.06, size=0.3, seed=5, subdiv=2)
    smooth_shade(t); assign(t, "bark")
    import random
    r = random.Random(el.get("seed", 7))
    for k in range(6):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=h * r.uniform(0.18, 0.28),
                                              location=(x + r.uniform(-0.35, 0.35) * h, y + r.uniform(-0.35, 0.35) * h, z + h * r.uniform(0.6, 0.85)))
        c = bpy.context.object
        c.scale = (1, 1, 0.7)
        displace(c, h * 0.08, size=0.25, seed=6 + k, subdiv=1)
        smooth_shade(c); assign(c, "foliage")
    return t


def el_prim(el):
    kind = el["type"]
    if kind == "box":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif kind == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=48)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24)
    o = place(bpy.context.object, el)
    o.scale = el.get("size", [1, 1, 1])
    if el.get("bevel"):
        b = o.modifiers.new("bevel", "BEVEL"); b.width = el["bevel"]; b.segments = 3
    if kind != "box":
        smooth_shade(o)
    assign(o, el.get("material", "plaster"))
    return o


DRAW = {"ground": el_ground, "cliff": el_cliff, "disc": el_disc, "rock": el_rock, "tree": el_tree, "box": el_prim, "cylinder": el_prim, "sphere": el_prim}
for el in SC.get("elements", []):
    DRAW[el["type"]](el)


# ---------------- light + world ----------------
L = {**ST["lights"].get(SC.get("light", "day"), {}), **SC.get("light_override", {})}
world = bpy.data.worlds.new("world"); scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
bg = wn.get("Background")
elev, azim = math.radians(L.get("sun_elev", 30)), math.radians(L.get("sun_azim", 120))
try:
    sky = wn.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    for attr, val in (("sun_elevation", max(elev, math.radians(0.5))), ("sun_rotation", azim), ("altitude", 100.0), ("air_density", 1.0), ("dust_density", 2.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
except Exception as e:                                   # older/newer Blender without this sky type: simple gradient colour
    print("sky texture fallback:", e)
    bg.inputs["Color"].default_value = hex2lin(L.get("haze_color", "#c8d4e0"))
bg.inputs["Strength"].default_value = L.get("sky_strength", 1.0)
if L.get("haze", 0) > 0 and ARGS["engine"] == "CYCLES":  # atmospheric haze: Cycles only (an Eevee world volume can black out the frame on some GPUs)
    vs = wn.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = L["haze"]
    vs.inputs["Color"].default_value = hex2lin(L.get("haze_color", "#ffffff"))
    world.node_tree.links.new(vs.outputs["Volume"], wn.get("World Output").inputs["Volume"])
sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = L.get("sun_strength", 4.0)
sun_data.color = hex2lin(L.get("sun_color", "#ffffff"))[:3]
sun_data.angle = math.radians(1.5)
sun = bpy.data.objects.new("sun", sun_data); scene.collection.objects.link(sun)
d = Vector((math.cos(elev) * math.sin(azim), -math.cos(elev) * math.cos(azim), math.sin(elev)))   # direction TO the sun
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
if L.get("moon"):
    md = bpy.data.lights.new("moon", "SUN"); md.energy = L["moon"]; md.color = (0.7, 0.78, 1.0)
    mo = bpy.data.objects.new("moon", md); scene.collection.objects.link(mo); mo.rotation_euler = (math.radians(50), 0, math.radians(30))

# ---------------- camera ----------------
cam_data = bpy.data.cameras.new("cam")
cam_data.sensor_fit = "VERTICAL"; cam_data.sensor_height = 24.0
cam_data.clip_end = 2000
cam = bpy.data.objects.new("cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
KEYS = SC.get(f"camera_{ARGS['fmt']}") or SC["camera"]
DOF = SC.get("dof")
if DOF:
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = DOF.get("fstop", 2.8)


def cam_at(t):
    if t <= KEYS[0]["t"]:
        a = b = KEYS[0]; u = 0
    elif t >= KEYS[-1]["t"]:
        a = b = KEYS[-1]; u = 0
    else:
        for a, b in zip(KEYS, KEYS[1:]):
            if a["t"] <= t <= b["t"]:
                break
        u = smooth((t - a["t"]) / (b["t"] - a["t"]))
    lerp = lambda p, q: [x + (y - x) * u for x, y in zip(p, q)]
    return lerp(a["pos"], b["pos"]), lerp(a["look"], b["look"]), a.get("lens", 35) + (b.get("lens", 35) - a.get("lens", 35)) * u


def set_camera(t):
    pos, look, lens = cam_at(t)
    cam.location = pos
    cam.rotation_euler = (Vector(look) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    if DOF:
        cam_data.dof.focus_distance = (Vector(DOF.get("focus", look)) - Vector(pos)).length


# ---------------- render settings ----------------
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = ARGS["width"], ARGS["height"], 100
r.image_settings.file_format = "JPEG"; r.image_settings.quality = 92
if ARGS["engine"] == "CYCLES":
    r.engine = "CYCLES"
    scene.cycles.samples = ARGS["samples"]
    scene.cycles.use_denoising = True
    if ARGS.get("gpu"):
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                if any(dv.type == kind for dv in prefs.devices):
                    for dv in prefs.devices:
                        dv.use = dv.type == kind
                    scene.cycles.device = "GPU"
                    print("cycles device:", kind)
                    break
            except Exception:
                continue
else:
    r.engine = "BLENDER_EEVEE"
    ee = scene.eevee
    ee.taa_render_samples = ARGS["samples"]
    for attr, val in (("shadow_pool_size", "512" if ARGS["samples"] >= 32 else "128"),   # integrated GPUs share system RAM
                      ("shadow_resolution_scale", 1.0 if ARGS["samples"] >= 32 else 0.5), ("use_raytracing", ARGS["samples"] >= 32), ("volumetric_tile_size", "8" if ARGS["samples"] >= 32 else "16"),
                      ("volumetric_samples", 32 if ARGS["samples"] >= 32 else 16), ("use_volumetric_shadows", True), ("shadow_ray_count", 1)):
        try:
            setattr(ee, attr, val)
        except Exception as e:
            print("eevee setting skipped:", attr, e)
grade = ST.get("grade", {})
try:
    scene.view_settings.view_transform = grade.get("view", "AgX")
    scene.view_settings.look = grade.get("look", "None")
except Exception as e:
    print("colour management fallback:", e)
scene.view_settings.exposure = L.get("exposure", 0.0)

if ARGS.get("save_blend"):
    bpy.ops.wm.save_as_mainfile(filepath=ARGS["save_blend"])

# ---------------- render the requested frames ----------------
out = ARGS["out"]
t_all = time.time()
for i, f in enumerate(ARGS["frames"]):
    scene.frame_set(f)
    set_camera(f / FPS)
    dst = os.path.join(out, f"f{f:04d}.jpg")
    tmp = os.path.join(out, f"_tmp_f{f:04d}")
    r.filepath = tmp
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    os.replace(tmp + ".jpg", dst)                        # atomic: a frame is complete or absent (safe resume)
    print(f"FRAME {f} {time.time() - t0:.2f}s", flush=True)
print(f"ALLDONE {len(ARGS['frames'])} frames {time.time() - t_all:.1f}s", flush=True)
