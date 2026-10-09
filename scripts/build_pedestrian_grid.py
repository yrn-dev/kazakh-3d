"""Sample textured pedestrian surfaces and static obstacle clearance from the city."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/modern_city_enclosed.blend'))
o=bpy.data.objects['terrain_5_0'];o.data.calc_loop_triangles();vs=[v.co.copy() for v in o.data.vertices];ts=list(o.data.loop_triangles);bvh=BVHTree.FromPolygons(vs,[t.vertices for t in ts],all_triangles=True)
im=bpy.data.images['Image_18'];pixels=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4);uv=o.data.uv_layers.active.data
uvs=[[Vector((*uv[l].uv,0)) for l in t.loops] for t in ts]
verts=[];faces=[]
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or not obj.name.startswith(('Plane','Cube','fences','dec.')):continue
 offset=len(verts);verts.extend(v.co.copy() for v in obj.data.vertices);faces.extend(tuple(offset+i for i in p.vertices) for p in obj.data.polygons)
obstacles=BVHTree.FromPolygons(verts,faces)
road=bpy.data.objects['roads_5_0'];roads=BVHTree.FromPolygons([v.co.copy() for v in road.data.vertices],[p.vertices[:] for p in road.data.polygons])
step=.65;x0=-263.;y0=-224.;nx=646;ny=628
safe=np.zeros((ny,nx),dtype=np.uint8);heights=np.zeros((ny,nx),dtype=np.float32)
for iy in range(ny):
 for ix in range(nx):
  x=x0+ix*step;y=y0+iy*step
  p,n,index,_=bvh.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),5)
  if p is None or abs(n.z)<.96 or p.z < -1.5:continue
  if roads.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),8)[0] is not None:continue
  tri=ts[index];tex=barycentric_transform(p,*[vs[i] for i in tri.vertices],*uvs[index]);c=pixels[int(tex.y%1*1024),int(tex.x%1*1024),:3]
  # The authored atlas dedicates its upper half to two paving patterns.
  # The lower half contains grass and asphalt, including parking surfaces.
  if not .52 < (tex.y % 1.0) < .98:continue
  hit=obstacles.find_nearest(p+Vector((0,0,.85)),.72)
  if hit[0] is not None:continue
  safe[iy,ix]=1;heights[iy,ix]=p.z
 if iy%100==0:print('NAV_GRID',iy,flush=True)
np.savez_compressed(str(ROOT/'research/pedestrian_grid.npz'),safe=safe,heights=heights,x0=x0,y0=y0,step=step)
print('PEDESTRIAN_GRID_READY',int(safe.sum()),flush=True)
