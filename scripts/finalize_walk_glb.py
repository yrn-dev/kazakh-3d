"""Name the baked clip and shift its time origin to zero without resampling."""
from pathlib import Path
import json,struct
ROOT=Path(__file__).resolve().parents[1]
def finalize(path):
 raw=path.read_bytes();size,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+size]);binary=bytearray(raw[28+size:]);assert kind==0x4E4F534A
 for clip in doc.get('animations',[]):
  clip['name']='Walk';inputs={s['input'] for s in clip['samplers']};offset=min(doc['accessors'][i]['min'][0] for i in inputs)
  if abs(offset)<1e-7:continue
  for i in inputs:
   a=doc['accessors'][i];assert a['componentType']==5126 and a['type']=='SCALAR';view=doc['bufferViews'][a['bufferView']];start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',4)
   for j in range(a['count']):
    pos=start+j*stride;v=struct.unpack_from('<f',binary,pos)[0];struct.pack_into('<f',binary,pos,v-offset)
   a['min']=[a['min'][0]-offset];a['max']=[a['max'][0]-offset]
 data=json.dumps(doc,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4E4F534A)+data+struct.pack('<II',len(binary),0x004E4942)+binary)
if __name__=='__main__':
 for p in (ROOT/'godot/assets/characters').glob('*_walk.glb'):finalize(p);print('FINALIZED',p.name)
