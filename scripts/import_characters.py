"""Import the five selected source GLBs into standalone, packed Blender files."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'blender' / 'characters'
OUT.mkdir(parents=True, exist_ok=True)
audit = json.loads((ROOT / 'research/character_file_audit.json').read_text())
results = []
for entry in audit:
    source = ROOT / 'source/characters' / entry['file']
    destination = OUT / (source.stem + '.blend')
    if destination.exists():
        raise FileExistsError(destination)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    assert meshes and rigs, f'Missing mesh or skeleton: {source.name}'
    assert any(m.type == 'ARMATURE' for o in meshes for m in o.modifiers)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    result = dict(file=source.name, blend=str(destination), meshes=len(meshes),
                  bones=[len(o.data.bones) for o in rigs],
                  images=len(bpy.data.images),
                  actions=[dict(name=a.name, frames=list(a.frame_range)) for a in bpy.data.actions])
    results.append(result)
    print('CHARACTER_IMPORTED ' + json.dumps(result), flush=True)
(ROOT / 'research/character_blender_audit.json').write_text(json.dumps(results, indent=2) + '\n')
