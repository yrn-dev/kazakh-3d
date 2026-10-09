"""Build separated out-and-back sidewalk lanes; never use car surfaces."""
import json,heapq,math
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt,label,gaussian_filter1d
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];data=np.load(ROOT/'research/pedestrian_grid.npz');raw=data['safe'];heights=data['heights'];step=float(data['step']);origin=np.array([float(data['x0']),float(data['y0'])]);clear=distance_transform_edt(raw)*step;mask=clear>1.5;labels,_=label(mask)
coords=np.argwhere(mask);xy=origin+coords[:,::-1]*step;tree=cKDTree(xy)
requests=[('Central sidewalk',(-44,20),(-15,-18)),('West promenade',(-185,-45),(-145,-10)),('West courtyard',(-100,-14),(-85,-60)),('Park promenade',(65,90),(135,88)),('East courtyard',(63,-86),(86,-62)),('South courtyard',(-64,-198),(-33,-174)),('Northwest sidewalk',(-170,25),(-135,56)),('East sidewalk',(60,51),(112,53))]
directions=[(dy,dx) for dy in [-1,0,1] for dx in [-1,0,1] if dy or dx]
def pathfind(a,b):
 q=[(0.,0.,a)];cost={a:0.};prev={}
 while q:
  _,g,p=heapq.heappop(q)
  if p==b:
   out=[b]
   while out[-1]!=a:out.append(prev[out[-1]])
   return out[::-1]
  if g>cost[p]+1e-8:continue
  for dy,dx in directions:
   n=(p[0]+dy,p[1]+dx)
   if not(0<=n[0]<mask.shape[0] and 0<=n[1]<mask.shape[1]) or not mask[n]:continue
   if dy and dx and (not mask[p[0]+dy,p[1]] or not mask[p[0],p[1]+dx]):continue
   ng=g+math.hypot(dx,dy)*(1+.9/max(clear[n],.1))
   if ng<cost.get(n,1e20):cost[n]=ng;prev[n]=p;heapq.heappush(q,(ng+math.dist(n,b),ng,n))
 raise RuntimeError('Disconnected path')
def sample(points,spacing=.4):
 out=[]
 for a,b in zip(points[:-1],points[1:]):
  for f in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(b-a)/spacing)),endpoint=False):out.append(a+(b-a)*f)
 return np.array(out+[points[-1]])
def lookup(p):return tuple(np.rint((p-origin)[::-1]/step).astype(int))
routes=[]
for name,a,b in requests:
 _,idx=tree.query(a);start=tuple(coords[idx]);component=labels[start];cc=np.argwhere(labels==component);world=origin+cc[:,::-1]*step;_,j=cKDTree(world).query(b);end=tuple(cc[j]);cells=pathfind(start,end);center=origin+np.array(cells)[:,::-1]*step
 if len(center)<12: print('SKIP_SHORT',name);continue
 center=sample(center,.35);center=gaussian_filter1d(center,2,axis=0,mode='nearest')
 tangent=np.gradient(center,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.column_stack([-tangent[:,1],tangent[:,0]])
 lane=.62;left=center+normal*lane;right=center-normal*lane
 # Round end caps keep walkers on their own side of the promenade.
 endcap=[center[-1]+lane*(normal[-1]*math.cos(t)+tangent[-1]*math.sin(t)) for t in np.linspace(0,math.pi,12)]
 startcap=[center[0]+lane*(-normal[0]*math.cos(t)-tangent[0]*math.sin(t)) for t in np.linspace(0,math.pi,12)]
 points=np.concatenate([left,endcap,right[::-1],startcap,left[:1]])
 points=sample(points,.3)
 safe=True;minclear=100
 for p in points:
  c=lookup(p);minclear=min(minclear,float(clear[c]))
  if clear[c]<.65:safe=False;break
 if not safe:print('SKIP_CLEARANCE',name,minclear);continue
 out=[]
 for p in points:
  c=lookup(p);out.append([round(float(p[0]),4),round(float(heights[c])+.025,4),round(float(-p[1]),4)])
 length=sum(math.dist(a,b) for a,b in zip(out[:-1],out[1:]));routes.append(dict(name=name,points=out,length=length,minimum_clearance=minclear,pedestrians=4))
 print('ROUTE',name,round(length,1),'m',round(minclear,2),'clearance')
assert len(routes)>=4,'Not enough safe routes'
# The camera starts on the first path, facing its approaching pedestrians.
a=np.array(routes[0]['points'][0]);b=np.array(routes[0]['points'][20]);direction=(b-a);direction[1]=0;direction/=np.linalg.norm(direction)
result={'ground_source':'terrain_5_0 paving atlas only; roads and parking excluded','grid_step':step,'routes':routes,'camera_start':(a+np.array([0,1.8,0])).tolist(),'camera_yaw':math.atan2(-direction[0],-direction[2])}
(ROOT/'godot/pedestrian_routes.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
# Diagnostic geometry plot: roads are blank, routes are colored lines.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,10));ax.imshow(raw,origin='lower',cmap='Greys',alpha=.25,extent=[origin[0],origin[0]+raw.shape[1]*step,origin[1],origin[1]+raw.shape[0]*step])
for i,r in enumerate(routes):
 p=np.array(r['points']);ax.plot(p[:,0],-p[:,2],label=r['name']);ax.text(p[0,0],-p[0,2],str(i+1))
ax.legend(loc='upper left');ax.set_aspect('equal');fig.savefig(ROOT/'previews/npc_routes.png',dpi=140)
