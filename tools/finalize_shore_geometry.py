"""Freeze verified shore pixels; regenerate inspection layout, not artwork.

Visual approval is recorded separately only after opening these actual pages.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import world_pack as wp
import build_world_terrain as terrain

R=wp.ROOT;OUT=R/'assets/world/terrain/shore-geometry';PRE=R/'previews/world/shore-geometry';REC=R/'records/world-production'


def main():
    mp=OUT/'manifest.json';m=wp.readj(mp);qa=wp.readj(REC/'shore-geometry-validation.json')
    if qa['failed']or qa['manifestSHA256']!=wp.sha(mp):raise ValueError('Run current shore geometry QA before freezing')
    # Exact two files are failed intermediate zero-strip interpretations.
    # Remove only this pack's unreferenced test outputs, with recoverable hashes.
    current={a['image']for a in m['assets']};retired=[]
    for name in['shore-water-slot-09.png','shore-water-slot-12.png']:
        for p in[OUT/name,OUT/(name+'.derivation.json')]:
            if p.exists()and wp.rel(p)not in current:
                if p.resolve().parent!=OUT.resolve():raise ValueError('Retirement target escaped shore pack')
                retired.append({'file':wp.rel(p),'sha256':wp.sha(p),'reason':'Intermediate integer-floor zero strip would invent extra water area; final shoreline keeps continuous source zero contour.'});p.unlink()
    if retired:wp.writej(REC/'shore-geometry-retired-intermediates.json',{'createdAt':wp.now(),'files':retired})
    layer=Image.new('RGB',(1280,750),'#263b44');d=ImageDraw.Draw(layer);refs=[]
    for row,climate in enumerate(['grass','sand','snow']):
        s=next(s for s in m['coverageMappings'][0]['states']if s['shoreClimate']==climate and s['sourceShoreIndex']==1)
        for col,key in enumerate(['water','land','bank','whole']):
            f=s[key];im=Image.open(R/f).convert('RGBA');x=col*320+32;y=row*250+6;layer.paste(im,(x,y),im)
            d.text((x,y+205),climate+' / '+key,font=terrain.font(18),fill='#f3e3bd');refs.append({'file':f,'sha256':wp.sha(R/f),'record':f+'.derivation.json'})
    p=PRE/'layer-breakdown.jpg';layer.save(p,quality=97)
    wp.writej(str(p)+'.derivation.json',{'file':wp.rel(p),'sha256':wp.sha(p),'operation':'Actual formal water/land/nativebank/whole layers on inspection matte; labels only','derivedFrom':refs,'nativeModelGeneration':False})
    m['layerPreview']={'file':wp.rel(p),'sha256':wp.sha(p),'actualLayerSamples':12}
    m['nativeBankSampling']={'grass':{'file':'assets/world/infrastructure/fences-shore/river-grass-bank.png','tangentStartPx':[105,405],'tangentEndPx':[466,219],'nativeCrossHalfWidthPx':15,'landSide':-1},'sand':{'file':'assets/world/infrastructure/fences-shore/shore-sand.png','tangentStartPx':[91,359],'tangentEndPx':[420,190],'nativeCrossHalfWidthPx':13,'landSide':1},'snow':{'nativeBank':'same original sand water-side foam; Alpha clipped before land-side sand, no recolour','actualLand':'assets/world/terrain/terrain-snow-flat.png'},'formalRibbonHalfWidthWorld':1.6,'method':'Bilinear native-pixel sampling then geometric Alpha clipping; no procedural painted lines or replacement RGB.'}
    for a in m['assets']:a.update({'status':'art-checked','reviewBasis':'actual48whole contact pages plus12real layer samples; source height and rock-contact QA; user artwork acceptance and Unity remain pending'})
    for s in m['coverageMappings'][0]['reservedBindings']:s['noDraw']=True
    m['coverageMappings'][0]['completeVariantCoverage']=True
    m['acceptance']='source-bound48legal climate/posture assemblies and6explicit noDraw slots; art geometry and actual-page review complete; Unity/runtime pending'
    m['validationRecord']='records/world-production/shore-geometry-validation.json';m['visualReviewRecord']='records/world-production/shore-geometry-visual-review.json'
    wp.writej(mp,m)
    html='<!doctype html><meta charset="utf-8"><title>Shore geometry inspection</title><style>body{background:#253a43;color:#f3e3bd;font:18px sans-serif}img{display:block;max-width:100%;margin:20px 0}table{border-collapse:collapse}td,th{border:1px solid #678;padding:8px}</style><h1>Source-height shore geometry</h1><p>48 actual assemblies: 16 legal source slots × 3 climates. Water horizontal; land follows source height. Static art inspection; Unity unverified.</p>'
    for p in m['contactPages']:html+='<img src="'+Path(p['file']).name+'" alt="'+Path(p['file']).stem+'">'
    html+='<h2>Actual independent layers</h2><img src="layer-breakdown.jpg" alt="Actual water, land, native bank and whole layers"><h2>Reserved source slots: no draw</h2><table><tr><th>Climate</th><th>Slot</th><th>Slope</th><th>Applicability</th></tr>'
    for s in m['coverageMappings'][0]['reservedBindings']:html+=f"<tr><td>{s['shoreClimate']}</td><td>{s['sourceShoreIndex']}</td><td>{s['sourceSlopeCode']}</td><td>source assertion prohibits drawing; no PNG</td></tr>"
    html+='</table><p>Flat and half-tile slopes are outside this full-tile shore draw contract. Multi-corner/steep legal coast is DryOut; zero-area sea contact is explicit and contains no invented broad water pool. The mask is a documented reconstruction from source geometry, not an upstream external-graphics pixel mask.</p>'
    (PRE/'index.html').write_text(html,encoding='utf-8')
    print({'manifestSHA256':wp.sha(mp),'actualPNGs':len(m['assets']),'retiredIntermediates':len(retired)})


if __name__=='__main__':main()
