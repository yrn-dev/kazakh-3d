import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];reports=[]
for path in (root/'blender/characters/walking').glob('*_walk.blend'):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');scene=bpy.context.scene
 meshes=[o for o in scene.objects if o.type=='MESH'];snapshots=[]
 for frame in [1,9,17,25,32]:
  scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();points=[]
  for o in meshes:
   ev=o.evaluated_get(dg);m=ev.to_mesh();points.extend(v.co.copy() for v in m.vertices);ev.to_mesh_clear()
  assert all(math.isfinite(c) for v in points for c in v)
  low=min(v.z for v in points);high=max(v.z for v in points);width=max(v.x for v in points)-min(v.x for v in points)
  assert abs(low)<0.002,(path.name,frame,low)
  assert width<1.5,(path.name,frame,width)
  assert high<2.05,(path.name,frame,high)
  snapshots.append(points)
 seam=max((a-b).length for a,b in zip(snapshots[0],snapshots[-1]));motion=max((a-b).length for a,b in zip(snapshots[1],snapshots[3]));assert seam<0.002;assert motion>0.1
 r={'model':path.stem,'loop_vertex_error_m':seam,'motion_displacement_m':motion,'sampled_frames':[1,9,17,25,32],'grounded':True};reports.append(r);print('WALK_CHECK_OK',r,flush=True)
(root/'research/walk_validation.json').write_text(json.dumps(reports,indent=2)+'\n')
