import os
import json
import random
import bpy
import bmesh
from math import pi, sin, cos, radians
from mathutils import Vector, Matrix, noise

# ─── CONFIGURATION ──────────────────────────────────────────────
# Set up project directories and ensure output folders exist
# Important: Change this to the project path!
# Example: SEMINARSKA_DIR      = r"C:\Users\Asus\Documents\FRI\4. godina\2. semestar\Napredna računarska grafika\Seminarska"

SEMINARSKA_DIR      = r""
TEXTURES_DIR        = os.path.join(SEMINARSKA_DIR, "textures")
PARAM_DIR           = os.path.join(SEMINARSKA_DIR, "parameters")
OUTPUT_BLEND_FOLDER = os.path.join(SEMINARSKA_DIR, "blends")
OUTPUT_GLB_FOLDER   = os.path.join(SEMINARSKA_DIR, "glbs")
TEXTURE_SETS        = [os.path.join(TEXTURES_DIR, f"{i}") for i in ("1","2","3","4","5","6")]

os.makedirs(OUTPUT_BLEND_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_GLB_FOLDER, exist_ok=True)

# ─── SCENE MANAGEMENT ───────────────────────────────────────────
def clear_scene():
    """Remove all objects from the current Blender scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

# ─── TEXTURE SELECTION ──────────────────────────────────────────
def pick_random_textures():
    """Pick one of the numbered texture folders at random."""
    base = random.choice(TEXTURE_SETS)
    return base, {
        'color'       : os.path.join(base, "Color.jpg"),
        'normal'      : os.path.join(base, "Normal.jpg"),
        'roughness'   : os.path.join(base, "Roughness.jpg"),
        'displacement': os.path.join(base, "Displacement.jpg"),
    }

def pick_specific_textures(idx):
    """Pick textures by index (1–6), allowing user choice in JSON."""
    base = TEXTURE_SETS[int(idx)-1]
    return base, {
        'color'       : os.path.join(base, "Color.jpg"),
        'normal'      : os.path.join(base, "Normal.jpg"),
        'roughness'   : os.path.join(base, "Roughness.jpg"),
        'displacement': os.path.join(base, "Displacement.jpg"),
    }

# ─── MATERIAL BUILDERS ──────────────────────────────────────────
def create_image_pbr_bark_material(mat_name,
                                   base_color_path,
                                   normal_map_path,
                                   roughness_map_path,
                                   displacement_path=None,
                                   hue=0.0,
                                   saturation=1.0,
                                   value=1.0,
                                   bump_strength=1.0,
                                   disp_strength=0.1):
    """
    Construct a PBR bark material:
      - Color / Normal / Roughness / optional Displacement
      - Hue/Saturation/Value adjustments
      - Normal‐map and displacement strengths
    """
    # Remove existing material of same name
    if bpy.data.materials.get(mat_name):
        bpy.data.materials.remove(bpy.data.materials[mat_name])
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Create nodes
    texCoord, mapping = nodes.new("ShaderNodeTexCoord"), nodes.new("ShaderNodeMapping")
    imgColor, hsv     = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeHueSaturation")
    imgNorm, normMap  = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeNormalMap")
    imgRough          = nodes.new("ShaderNodeTexImage")
    principled        = nodes.new("ShaderNodeBsdfPrincipled")
    output            = nodes.new("ShaderNodeOutputMaterial")
    if displacement_path:
        imgDisp  = nodes.new("ShaderNodeTexImage")
        dispNode = nodes.new("ShaderNodeDisplacement")

    # Position nodes (for clarity in Shader Editor)
    texCoord.location = (-800, 300)
    mapping.location  = (-600, 300)
    imgColor.location = (-400, 400)
    hsv.location      = (-200, 400)
    imgNorm.location  = (-400, 200)
    normMap.location  = (-200, 200)
    imgRough.location = (-400,   0)
    principled.location = (0, 200)
    output.location     = (200, 200)
    if displacement_path:
        imgDisp.location  = (-400, -200)
        dispNode.location = (-200, -200)

    # Load images into the texture nodes
    imgColor.image = bpy.data.images.load(base_color_path)
    imgNorm.image  = bpy.data.images.load(normal_map_path)
    imgNorm.image.colorspace_settings.name = 'Non-Color'
    imgRough.image = bpy.data.images.load(roughness_map_path)
    imgRough.image.colorspace_settings.name = 'Non-Color'
    if displacement_path:
        imgDisp.image = bpy.data.images.load(displacement_path)
        imgDisp.image.colorspace_settings.name = 'Non-Color'

    # Adjust HSV and bump/displacement strengths
    hsv.inputs['Hue'].default_value        = hue
    hsv.inputs['Saturation'].default_value = saturation
    hsv.inputs['Value'].default_value      = value
    hsv.inputs['Fac'].default_value        = 0
    normMap.inputs['Strength'].default_value = bump_strength
    if displacement_path:
        dispNode.inputs['Scale'].default_value = disp_strength

    # Wire up the node tree
    links.new(texCoord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], imgColor.inputs['Vector'])
    links.new(imgColor.outputs['Color'], hsv.inputs['Color'])
    links.new(hsv.outputs['Color'], principled.inputs['Base Color'])
    links.new(mapping.outputs['Vector'], imgNorm.inputs['Vector'])
    links.new(imgNorm.outputs['Color'], normMap.inputs['Color'])
    links.new(normMap.outputs['Normal'], principled.inputs['Normal'])
    links.new(mapping.outputs['Vector'], imgRough.inputs['Vector'])
    links.new(imgRough.outputs['Color'], principled.inputs['Roughness'])
    if displacement_path:
        links.new(mapping.outputs['Vector'], imgDisp.inputs['Vector'])
        links.new(imgDisp.outputs['Color'], dispNode.inputs['Height'])
        links.new(dispNode.outputs['Displacement'], output.inputs['Displacement'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat

def create_image_pbr_cap_material(mat_name,
                                  base_color_path,
                                  roughness_map_path,
                                  displacement_path=None,
                                  disp_strength=0.05):
    """
    Similar to bark material but simpler: only color, roughness, and optional displacement
    for the end‐cap cross‐section texture.
    """
    if bpy.data.materials.get(mat_name):
        bpy.data.materials.remove(bpy.data.materials[mat_name])
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    texCoord = nodes.new("ShaderNodeTexCoord")
    mapping  = nodes.new("ShaderNodeMapping")
    imgColor = nodes.new("ShaderNodeTexImage")
    imgRough = nodes.new("ShaderNodeTexImage")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    output     = nodes.new("ShaderNodeOutputMaterial")
    if displacement_path:
        imgDisp  = nodes.new("ShaderNodeTexImage")
        dispNode = nodes.new("ShaderNodeDisplacement")

    # Position nodes
    mapping.location    = (-600, 300)
    imgColor.location   = (-400, 400)
    imgRough.location   = (-400,   0)
    principled.location = (   0, 200)
    output.location     = ( 200, 200)
    if displacement_path:
        imgDisp.location  = (-400, -200)
        dispNode.location = (-200, -200)

    # Load and mark non-color for maps
    imgColor.image = bpy.data.images.load(base_color_path)
    imgRough.image = bpy.data.images.load(roughness_map_path)
    imgRough.image.colorspace_settings.name = 'Non-Color'
    if displacement_path:
        imgDisp.image = bpy.data.images.load(displacement_path)
        imgDisp.image.colorspace_settings.name = 'Non-Color'
        dispNode.inputs['Scale'].default_value = disp_strength

    # Link nodes
    links.new(texCoord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], imgColor.inputs['Vector'])
    links.new(imgColor.outputs['Color'], principled.inputs['Base Color'])
    links.new(mapping.outputs['Vector'], imgRough.inputs['Vector'])
    links.new(imgRough.outputs['Color'], principled.inputs['Roughness'])
    if displacement_path:
        links.new(mapping.outputs['Vector'], imgDisp.inputs['Vector'])
        links.new(imgDisp.outputs['Color'], dispNode.inputs['Height'])
        links.new(dispNode.outputs['Displacement'], output.inputs['Displacement'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat

# ─── GEOMETRY GENERATOR ─────────────────────────────────────────
def generate_proc_log(name, params, location=(0,0,0)):
    """
    Create a procedural log mesh:
      - ring‐by‐ring interpolation of radius (taper)
      - optional ellipse, grooves, noise, flanges
      - centerline curve, eccentric offset, twist
    Returns the new object.
    """
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj  = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location

    bm = bmesh.new()
    rings_verts = []

    # Unpack parameters for readability
    length              = params['length']
    radius_start        = params['radius_start']
    radius_center       = params['radius_center']
    radius_end          = params['radius_end']
    rings               = params['rings']
    verts_per_ring      = params['verts_per_ring']
    taper_shape         = params['taper_shape']
    taper_rate          = params['taper_rate']
    curve_count         = params['curve_count']
    curve_strength      = params['curve_strength']
    twist_angle         = params['twist_angle']
    twist_direction     = params['twist_direction']
    ellipse_ratio       = params['ellipse_ratio']
    oval_region_fraction= params['oval_region_fraction']
    eccentricity_offset = params['eccentricity_offset']
    eccentricity_angle  = params['eccentricity_angle']
    groove_count        = params['groove_count']
    groove_width        = params['groove_width']
    groove_depth        = params['groove_depth']
    noise_scale         = params['noise_scale']
    bark_roughness_depth= params['bark_roughness_depth']
    bark_roughness_level= params['bark_roughness_level']
    flange_count        = params['flange_count']
    flange_width        = params['flange_width']

    # Build each cross‐section ring
    for i in range(rings + 1):
        t = i / rings

        # Compute tapered radius (linear / exponential / quadratic)
        if taper_shape == 'linear':
            radius = radius_start + (radius_end - radius_start) * t
        elif taper_shape == 'exponential':
            radius = radius_start + (radius_end - radius_start) * (t ** taper_rate)
        else:
            radius = ((1-t)**2 * radius_start
                      + 2*(1-t)*t * radius_center
                      + t**2 * radius_end)

        # Apply ellipse or circle
        if t < oval_region_fraction:
            rx, ry = radius*ellipse_ratio, radius/ellipse_ratio
        else:
            rx = ry = radius

        # Add flange bumps at regular intervals
        if flange_count and (i % max(1, rings//flange_count)) == 0:
            rx += flange_width
            ry += flange_width

        # Centerline sinusoidal curve offset
        cx = curve_strength * sin(2*pi*curve_count*t)
        cy = curve_strength * cos(2*pi*curve_count*t)
        cz = length * t
        center = Vector((cx, cy, cz))

        # Eccentric offset in the XY plane
        ea = radians(eccentricity_angle)
        center += Vector((eccentricity_offset * cos(ea),
                          eccentricity_offset * sin(ea), 0))

        # Twist rotation matrix per ring
        angle = radians(twist_angle) * t
        rot = Matrix.Rotation(angle, 4, twist_direction.upper())

        # Generate vertices around the ring
        ring = []
        for j in range(verts_per_ring):
            theta = 2*pi*j/verts_per_ring

            # Groove pattern: notch out the radius
            ang_per = 2*pi/groove_count
            off     = (theta - ang_per/2) % ang_per - ang_per/2
            groove  = -groove_depth if abs(off) < (groove_width/2) else 0

            # Perlin noise for bark roughness
            n     = noise.noise(Vector((t*noise_scale, theta*noise_scale, 0)))
            rough = n * bark_roughness_depth * bark_roughness_level

            r_x, r_y = rx + rough + groove, ry + rough + groove
            loc_v    = Vector((r_x*cos(theta), r_y*sin(theta), 0))
            ring.append(bm.verts.new(rot @ loc_v + center))

        rings_verts.append(ring)

    # Connect rings into quads
    for i in range(rings):
        A, B = rings_verts[i], rings_verts[i+1]
        for j in range(verts_per_ring):
            bm.faces.new([
                A[j],
                A[(j+1)%verts_per_ring],
                B[(j+1)%verts_per_ring],
                B[j]
            ])

    bm.to_mesh(mesh)
    bm.free()

    # Enable smooth shading
    for poly in obj.data.polygons:
        poly.use_smooth = True

    return obj

def uv_unwrap(obj):
    """
    Apply Smart UV Project
    Clears old UV layers, unwraps, then returns to Object mode.
    """
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Remove existing UVs
    for _ in obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])

    # Perform UV unwrap
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

# ─── MAIN PROCESS LOOP ────────────────────────────────────────
json_files = [fn for fn in os.listdir(PARAM_DIR) if fn.lower().endswith(".json")]
if not json_files:
    raise FileNotFoundError(f"No JSON found in:\n{PARAM_DIR}")

for js in json_files:
    # Load parameters
    with open(os.path.join(PARAM_DIR, js), "r") as f:
        cfg = json.load(f)

    clear_scene()
    log_obj = generate_proc_log(cfg['name'], cfg)

    # Choose bark textures (random or specific)
    if cfg.get('texture','random') == 'random':
        base, tex = pick_random_textures()
    else:
        base, tex = pick_specific_textures(cfg['texture'])

    # Assign materials and caps
    bark_mat = create_image_pbr_bark_material(
        mat_name=f"BarkImagePBR_{cfg['name']}",
        base_color_path=tex['color'],
        normal_map_path=tex['normal'],
        roughness_map_path=tex['roughness'],
        displacement_path=tex['displacement'],
        hue=cfg.get('hue', 0.0),
        saturation=cfg.get('saturation', 1.0),
        value=cfg.get('value', 1.0),
        bump_strength=cfg.get('bump_strength', 1.0),
        disp_strength=cfg.get('disp_strength', 0.1)
    )
    log_obj.data.materials.clear()
    log_obj.data.materials.append(bark_mat)

    cs_tex = os.path.join(base, "CS.png")
    cap_mat = create_image_pbr_cap_material(
        mat_name=f"CapMat_{cfg['name']}",
        base_color_path=cs_tex,
        roughness_map_path=cs_tex,
        displacement_path=cs_tex,
        disp_strength=cfg.get('cap_disp_strength', 0.03)
    )

    # Generate and UV‐unwrap end‐caps
    verts = log_obj.data.vertices
    n     = cfg['verts_per_ring']
    start_coords = [v.co.copy() for v in verts[:n]]
    end_coords   = [v.co.copy() for v in verts[-n:]]

    def make_cap(name, coords, material, flip=False):
        mesh = bpy.data.meshes.new(f"{name}Mesh")
        obj  = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        bm = bmesh.new()
        bm_verts = [bm.verts.new(c) for c in coords]
        loop = bm_verts[::-1] if flip else bm_verts
        bm.faces.new(loop)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(material)
        return obj

    cap_start = make_cap(f"{cfg['name']}_cap_start", start_coords, cap_mat, flip=True)
    cap_end   = make_cap(f"{cfg['name']}_cap_end",   end_coords,   cap_mat, flip=False)

    # UV unwrap all pieces
    uv_unwrap(log_obj)
    uv_unwrap(cap_start)
    uv_unwrap(cap_end)

    # Save .blend and .glb exports
    blend_path = os.path.join(OUTPUT_BLEND_FOLDER, f"{cfg['name']}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"✔ Saved: {blend_path}")

    glb_path = os.path.join(OUTPUT_GLB_FOLDER, f"{cfg['name']}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True
    )
    print(f"✔ Saved: {glb_path}")
