from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage
R=Path(r'E:\work\image\OpenTTD_UI_20261026_060146')
for name in ['station-kit','depot-kit','bridge-families']:
 im=Image.open(R/'source-art/world'/f'{name}.png').convert('RGBA');a=np.asarray(im)[:,:,3];lab,n=ndimage.label(a>32);sz=np.bincount(lab.ravel())
 big=[i for i in range(1,n+1) if sz[i]>8000]
 rows=[]
 for i in big:
  yy,xx=np.where(lab==i);rows.append({'label':i,'count':int(sz[i]),'box':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'center':[float(xx.mean()),float(yy.mean())]})
 print(name,im.size,'alpha',im.getchannel('A').getextrema(),'components',rows)
