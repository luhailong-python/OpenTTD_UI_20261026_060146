"""Read real Alpha component bounds for authored atlas crop review."""
from collections import deque
from PIL import Image
from pathlib import Path
import json,argparse
ROOT=Path(__file__).resolve().parents[1]
def components(path,threshold=128,min_area=1000):
 im=Image.open(path);w,h=im.size;a=bytearray(im.getchannel('A').point(lambda x:255 if x>threshold else 0).tobytes());groups=[]
 for pos in range(w*h):
  if not a[pos]:continue
  a[pos]=0;q=deque([pos]);area=0;l=w;r=0;t=h;b=0
  while q:
   at=q.popleft();area+=1;x=at%w;y=at//w;l=min(l,x);r=max(r,x);t=min(t,y);b=max(b,y)
   for yy in range(max(0,y-1),min(h,y+2)):
    rr=yy*w
    for xx in range(max(0,x-1),min(w,x+2)):
     k=rr+xx
     if a[k]:a[k]=0;q.append(k)
  if area>=min_area:groups.append({'area':area,'bbox':[l,t,r+1,b+1]})
 return sorted(groups,key=lambda x:x['area'],reverse=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('names',nargs='+');a=p.parse_args();out={}
 for name in a.names:
  out[name]=components(ROOT/('source-art/world/'+name+'.png'));print(name,[(g['area'],g['bbox'])for g in out[name]],flush=True)
 (ROOT/'records/world-production/service-native-components.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
