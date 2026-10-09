import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'source/modern_city_block.glb'))
# The Sketchfab FBX conversion stores centimetres as glTF units.
roots = [o for o in bpy.context.scene.objects if o.parent is None]
for obj in roots:
    obj.scale *= 0.01
bpy.context.view_layer.update()
# Separate material swatches placed beside the district are not map geometry.
for obj in list(bpy.context.scene.objects):
    if obj.name.startswith('Plane.061'):
        bpy.data.objects.remove(obj, do_unlink=True)
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
offset = Vector((-(lo.x+hi.x)/2, -(lo.y+hi.y)/2, 0))
for obj in roots:
    obj.location += offset
bpy.context.view_layer.update()
for obj in meshes:
    print('CITY_OBJECT', obj.name, tuple(round(x,2) for x in obj.matrix_world.translation))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender/modern_city_block.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT / 'godot/assets/modern_city_block.glb'), export_format='GLB')
stats = {'meshes':len(meshes), 'size_m':list(hi-lo), 'blender_offset':list(offset), 'textures':len(bpy.data.images)}
(ROOT / 'source/modern_city_stats.json').write_text(json.dumps(stats,indent=2))
print('CITY_STATS',stats)
