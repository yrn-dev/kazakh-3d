"""Add an editable residential perimeter to the supplied city asset."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/modern_city_block.blend'))
original = [o for o in bpy.context.scene.objects if o.type == 'MESH']
# Bake the imported FBX hierarchy to metre-scale meshes for reliable physics.
for o in original:
    world = o.matrix_world.copy()
    o.data = o.data.copy()
    o.data.transform(world)
    o.parent = None
    o.matrix_world = Matrix.Identity(4)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)

def hull(points):
    points = sorted(set(points))
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def half(seq):
        out=[]
        for p in seq:
            while len(out)>1 and cross(out[-2],out[-1],p)<=0: out.pop()
            out.append(p)
        return out
    return [Vector(p) for p in half(points)[:-1]+half(reversed(points))[:-1]]

terrain=[o for o in original if o.name.startswith('terrain')]
boundary=hull([(round(v.co.x,3),round(v.co.y,3)) for o in terrain for v in o.data.vertices])
# Discard collinear/nearly-collinear detail from the exterior boundary.
while len(boundary)>4:
    distances=[]
    for i,p in enumerate(boundary):
        a=boundary[i-1]; b=boundary[(i+1)%len(boundary)]; ab=b-a
        distances.append(abs(ab.x*(p-a).y-ab.y*(p-a).x)/ab.length)
    i=min(range(len(distances)),key=distances.__getitem__)
    if distances[i]>2: break
    boundary.pop(i)

def offset(poly,d):
    result=[]
    for i,p in enumerate(poly):
        before=(p-poly[i-1]).normalized(); after=(poly[(i+1)%len(poly)]-p).normalized()
        n1=Vector((before.y,-before.x)); n2=Vector((after.y,-after.x))
        bis=(n1+n2).normalized()
        result.append(p+bis*d/max(.1,bis.dot(n1)))
    return result

def simple_mat(name,color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF'); shader.inputs['Base Color'].default_value=(*color,1); shader.inputs['Roughness'].default_value=.9
    return m

concrete=simple_mat('Perimeter concrete',(.38,.39,.36))
metal=simple_mat('Perimeter steel',(.13,.17,.16))
grass=simple_mat('Outer grass',(.19,.25,.12))
road=bpy.data.objects['roads_5_0'].data.materials[0]
def face(name,points,material):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(points,[],[list(range(len(points)))]); mesh.materials.append(material)
    uv=mesh.uv_layers.new()
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co; uv.data[li].uv=(v.x/8,v.y/8)
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj); return obj
def box(name,center,size,mat,angle=0):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh.materials.append(mat)
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    o.matrix_world=Matrix.Translation(Vector(center)) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Diagonal((*size,1.0))
    return o

outer=offset(boundary,95)
print('BOUNDARY', [list(p) for p in boundary],flush=True)
face('Outer_Ground',[(p.x,p.y,-1.7) for p in offset(boundary,1200)],grass)
inner=offset(boundary,1)
road_outer=offset(boundary,16)
for i,a in enumerate(inner):
    j=(i+1)%len(inner); b=inner[j]; c=road_outer[j]; d=road_outer[i]
    face('Outer_Access_Road_%02d'%i,[(p.x,p.y,-1.3) for p in [a,b,c,d]],road)

# Reuse two complete apartment buildings, with their original texture sets.
templates=[]
for prefix in ['Plane.036_', 'Plane.001_']:
    parts=[o for o in original if o.name.startswith(prefix)]
    pts=[v.co for o in parts for v in o.data.vertices]
    center=Vector((sum(p.x for p in pts)/len(pts),sum(p.y for p in pts)/len(pts),0))
    xx=sum((p.x-center.x)**2 for p in pts); yy=sum((p.y-center.y)**2 for p in pts); xy=sum((p.x-center.x)*(p.y-center.y) for p in pts)
    angle=.5*math.atan2(2*xy,xx-yy)
    axis=Vector((math.cos(angle),math.sin(angle),0))
    along=[(p-center).dot(axis) for p in pts]
    templates.append((parts,center,angle,max(along)-min(along)))

housing=offset(boundary,49)
buildings=0
for i,a in enumerate(housing):
    b=housing[(i+1)%len(housing)]; edge=b-a; length=edge.length
    count=max(1,round(length/88))
    for n in range(count):
        parts,center,old_angle,width=templates[(i+n)%len(templates)]
        p=a+edge*((n+.5)/count)
        angle=math.atan2(edge.y,edge.x)
        stretch=min(1.12,(length/count-7)/width)
        transform=Matrix.Translation(Vector((p.x,p.y,-.8))) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Diagonal((stretch,1.0,[.8,1.0,.92][(i+n)%3],1.0)) @ Matrix.Rotation(-old_angle,4,'Z') @ Matrix.Translation(-center)
        for src in parts:
            o=bpy.data.objects.new('Perimeter_%02d_%s'%(buildings,src.name),src.data)
            bpy.context.collection.objects.link(o); o.matrix_world=transform
        buildings+=1

# Continuous physical border behind the apartment ring: low concrete base,
# closely spaced steel bars. Every edge joins at the polygon corners.
for i,a in enumerate(outer):
    b=outer[(i+1)%len(outer)]; edge=b-a; mid=(a+b)*.5; angle=math.atan2(edge.y,edge.x)
    box('Boundary_Base_%02d'%i,(mid.x,mid.y,-.2),(edge.length+.4,.55,3.0),concrete,angle)
    box('Boundary_Rail_%02d'%i,(mid.x,mid.y,2.65),(edge.length+.4,.12,.12),metal,angle)
    for n in range(math.ceil(edge.length/2)+1):
        p=a+edge*(n/math.ceil(edge.length/2))
        box('Boundary_Post_%02d_%03d'%(i,n),(p.x,p.y,1.7),(.1,.1,2.0),metal)

# Bake all final object transforms. Keep the 3D building parts editable.
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    if o.matrix_world != Matrix.Identity(4):
        o.data=o.data.copy(); o.data.transform(o.matrix_world); o.matrix_world=Matrix.Identity(4)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/modern_city_enclosed.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'godot/assets/modern_city_enclosed.glb'),export_format='GLB')
stats={'added_buildings':buildings,'boundary_blender_xy':[list(p) for p in outer], 'base_boundary':[list(p) for p in boundary]}
(ROOT/'source/enclosure_stats.json').write_text(json.dumps(stats,indent=2))
print('ENCLOSURE_READY',json.dumps(stats))
