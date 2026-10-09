"""Bake Jane's walk to clean, textured game rigs; retain all original files."""
from pathlib import Path
import bpy, math, re, json
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'blender/characters/walking'; OUT.mkdir(exist_ok=True)
GLB=ROOT/'godot/assets/characters'; GLB.mkdir(exist_ok=True,parents=True)
ROLES=['hips','spine','spine1','chest','neck','head']
for s in ['Left','Right']: ROLES += [s+k for k in ['Shoulder','Arm','ForeArm','Hand','UpLeg','Leg','Foot','Toe']]
PARENT={'hips':None,'spine':'hips','spine1':'spine','chest':'spine1','neck':'chest','head':'neck'}
for s in ['Left','Right']:
 for a,b in [('Shoulder','chest'),('Arm',s+'Shoulder'),('ForeArm',s+'Arm'),('Hand',s+'ForeArm'),('UpLeg','hips'),('Leg',s+'UpLeg'),('Foot',s+'Leg'),('Toe',s+'Foot')]:PARENT[s+a]=b

def find(rig,prefix):
 matches=[b.name for b in rig.data.bones if re.fullmatch(re.escape(prefix)+r'_\d+',b.name)]
 if len(matches)!=1:raise ValueError((prefix,matches))
 return matches[0]

def mapping(rig,kind):
 if kind=='jane':
  m=dict(zip(ROLES[:6],['Hips','Spine02','Spine01','Spine','neck','Head']))
  for s in ['Left','Right']:
   for k in ['Shoulder','Arm','ForeArm','Hand','UpLeg','Leg','Foot','Toe']:m[s+k]=s+('ToeBase' if k=='Toe' else k)
 elif kind=='teen':
  m=dict(zip(ROLES[:6],['Hips','Spine','Spine1','Spine2','Neck','Head']))
  for s in ['Left','Right']:
   for k in ['Shoulder','Arm','ForeArm','Hand','UpLeg','Leg','Foot','Toe']:m[s+k]=s+('ToeBase' if k=='Toe' else k)
  m={k:'mixamorig:'+v for k,v in m.items()}
 elif kind=='asian':
  m=dict(zip(ROLES[:6],['root.x','spine_01.x','spine_02.x','spine_03.x','neck.x','head.x']))
  for s,t in [('Left','l'),('Right','r')]:
   for k,v in zip(['Shoulder','Arm','ForeArm','Hand','UpLeg','Leg','Foot','Toe'],['shoulder','arm','forearm','hand','thigh','leg','foot','toes_01']):m[s+k]=v+'.'+t
 else:
  m=dict(zip(ROLES[:6],['Hip','Waist','Spine01','Spine02','NeckTwist01','Head']))
  for s,t in [('Left','L'),('Right','R')]:
   for k,v in zip(['Shoulder','Arm','ForeArm','Hand','UpLeg','Leg','Foot','Toe'],['Clavicle','Upperarm','Forearm','Hand','Thigh','Calf','Foot','ToeBase']):m[s+k]=t+'_'+v
  m={k:'CC_Base_'+v for k,v in m.items()}
 return {k:find(rig,v) for k,v in m.items()}

def rotation(m):return m.to_quaternion().to_matrix().to_4x4()
def rigid(m):
 r=rotation(m);r.translation=m.translation;return r

def open_model(stem):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/characters'/f'{stem}.blend'))
 bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 return next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')

# Sample the actual donor clip in world space. Its bind pose uses Y-up, while
# the authored clip uses Z-up. Convert only the bind reference to Z-up.
JANE='everyday_jane_casual_modern_woman_rigged'
src=open_model(JANE);sm=mapping(src,'jane'); duration=31/30
fix=Matrix.Rotation(math.pi/2,4,'X')
srest={k:rigid(fix@src.matrix_world@src.data.bones[n].matrix_local) for k,n in sm.items()}
samples=[]
for i in range(32):
 f=i/31*24.799999237060547;bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
 samples.append({k:rigid(src.matrix_world@src.pose.bones[n].matrix) for k,n in sm.items()})
# The source seam already matches; use identical samples to eliminate float drift.
samples[-1]={k:v.copy() for k,v in samples[0].items()}

TASKS=[('teen-boy','teen',1.68),('cartoon_asian__boy','asian',1.25),('free_stylized_cartoon_girl_rigged_character','cc',1.70),('free_cartoon_game_man_character_rigged','cc',1.80)]
reports=[]
for stem,kind,height in TASKS:
 rig=open_model(stem);mp=mapping(rig,kind);invmap={v:k for k,v in mp.items()}
 original_bones={b.name:{'parent':b.parent.name if b.parent else None,'matrix':rigid(rig.matrix_world@rig.pose.bones[b.name].matrix)} for b in rig.data.bones}
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.vertices)>0 and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
 # Freeze the displayed original bind pose into mesh data. This removes imported
 # scale-compensation/helper transforms without changing visible geometry/weights.
 dg=bpy.context.evaluated_depsgraph_get();weights=set();baked=[]
 for o in meshes:
  world=o.matrix_world.copy();data=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
  data.transform(world)
  groups=[g.name for g in o.vertex_groups]
  for v in data.vertices:
   for g in v.groups:
    if g.weight>0.00001:weights.add(groups[g.group])
  baked.append((o,data))
 coords=[v.co for o,d in baked for v in d.vertices];bottom=min(v.z for v in coords);top=max(v.z for v in coords)
 scale=height/(top-bottom);hip=original_bones[mp['hips']]['matrix'].translation
 norm=Matrix.Scale(scale,4)@Matrix.Translation(Vector((-hip.x,-hip.y,-bottom)))
 rest={n:rigid(norm@b['matrix']) for n,b in original_bones.items()}
 main={k:rest[n] for k,n in mp.items()}
 keep=weights|set(mp.values())
 def owner(n):
  if n in invmap:return invmap[n]
  low=n.lower();side=('Left' if ('.l_' in n or '_L_' in n) else 'Right' if ('.r_' in n or '_R_' in n) else '')
  if side:
   if any(t in low for t in ['thigh']):return side+'UpLeg'
   if any(t in low for t in ['calf','knee','leg_stretch','leg_twist']):return side+'Leg'
   if 'forearm' in low or 'elbow' in low:return side+'ForeArm'
   if 'upperarm' in low or 'arm_stretch' in low or 'arm_twist' in low:return side+'Arm'
   if 'toe' in low:return side+'Toe'
   if any(t in low for t in ['pinky','thumb','index','middle','ring','hand','_mid']):return side+'Hand'
  if n.startswith('CC_Base_BoneRoot'):return 'hips'
  current=original_bones[n]['parent']
  while current:
   if current in invmap:return invmap[current]
   current=original_bones[current]['parent']
  if any(t in low for t in ['head','eye','teeth','jaw','brow','lid','lip','cheek','nose','chin','tongue','forehead','temple']):return 'head'
  return 'hips'
 owners={n:owner(n) for n in keep}
 # Independent deform bones preserve original weight groups. All motion is baked;
 # original authoring rigs are retained in the untouched parent directory.
 bpy.ops.object.select_all(action='DESELECT')
 arm=bpy.data.armatures.new('WalkSkeleton');new=bpy.data.objects.new('CharacterRig',arm);bpy.context.collection.objects.link(new)
 bpy.context.view_layer.objects.active=new;new.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for n in sorted(keep):
  b=arm.edit_bones.new(n);b.matrix=rest[n];b.length=0.04;b.use_deform=True
 bpy.ops.object.mode_set(mode='OBJECT')
 for o,data in baked:
  o.animation_data_clear();o.parent=None;o.matrix_world=Matrix.Identity(4);data.transform(norm);o.data=data
  for mod in list(o.modifiers):o.modifiers.remove(mod)
  mod=o.modifiers.new('Skin','ARMATURE');mod.object=new;o.parent=new
 for o in list(bpy.context.scene.objects):
  if o!=new and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 bpy.context.view_layer.update()
 rest={b.name:b.matrix_local.copy() for b in new.data.bones};main={k:rest[n] for k,n in mp.items()}
 # Align each limb's bind direction to the donor's bind direction (A/T pose fix).
 align={k:Matrix.Identity(4) for k in ROLES}
 for s in ['Left','Right']:
  for k,child in [('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','Toe')]:
   role=s+k;end=s+child;t=(main[end].translation-main[role].translation).normalized();v=(srest[end].translation-srest[role].translation).normalized()
   align[role]=t.rotation_difference(v).to_matrix().to_4x4()
  align[s+'Hand']=align[s+'ForeArm'];align[s+'Toe']=align[s+'Foot']
 ratio=(main['hips'].translation.z-main['LeftFoot'].translation.z)/(srest['hips'].translation.z-srest['LeftFoot'].translation.z)
 scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=1;scene.frame_end=32
 new.animation_data_create();act=bpy.data.actions.new('Walk');new.animation_data.action=act
 metrics=[];prev={}
 for i,sample in enumerate(samples):
  scene.frame_set(i+1);pose={}
  for k in ROLES:
   delta=rotation(sample[k])@rotation(srest[k]).inverted()
   m=delta@align[k]@rotation(main[k]);parent=PARENT[k]
   if parent is None:m.translation=main[k].translation+(sample[k].translation-srest[k].translation)*ratio
   else:m.translation=pose[parent]@main[parent].inverted()@main[k].translation
   pose[k]=m
  matrices={n:pose[owners[n]]@main[owners[n]].inverted()@rest[n] for n in keep}
  for n,m in matrices.items():new.pose.bones[n].matrix_basis=rest[n].inverted()@m
  bpy.context.view_layer.update()
  # Ground the lowest deformed sole on each sampled frame; no sinking/floating.
  dg=bpy.context.evaluated_depsgraph_get();low=1e9;high=-1e9
  for o in meshes:
   ev=o.evaluated_get(dg);mesh=ev.to_mesh()
   low=min(low,min(v.co.z for v in mesh.vertices));high=max(high,max(v.co.z for v in mesh.vertices));ev.to_mesh_clear()
  for n,m in matrices.items():
   m.translation.z-=low;pb=new.pose.bones[n];pb.matrix_basis=rest[n].inverted()@m;pb.rotation_mode='QUATERNION'
   if n in prev and pb.rotation_quaternion.dot(prev[n])<0:pb.rotation_quaternion.negate()
   prev[n]=pb.rotation_quaternion.copy()
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=i+1,group=n)
  metrics.append({'frame':i+1,'ground_correction':-low,'height':high-low})
  if i%10==0:print('BAKE',stem,i,flush=True)
 scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.file.pack_all()
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{stem}_walk.blend'))
 bpy.ops.export_scene.gltf(filepath=str(GLB/f'{stem}_walk.glb'),export_format='GLB',export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=False)
 report={'model':stem,'bones':len(keep),'clip':'Walk','frames':32,'duration_seconds':duration,'height_m':height,'owners':owners,'metrics':metrics}
 reports.append(report);print('WALK_DONE',stem,flush=True)
(ROOT/'research/walk_retarget_report.json').write_text(json.dumps(reports,indent=2)+'\n')
