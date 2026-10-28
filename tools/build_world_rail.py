"""Project actual painted track textures to the source game's six track bits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,math,numpy as np
import world_pack as wp
import build_world_terrain as terrain
from build_world_network import tram_segment,UV
ROOT=wp.ROOT;OUT=ROOT/'assets/world/infrastructure/rail'
TRACKS=[('X',1,3),('Y',0,2),('Upper',0,1),('Lower',2,3),('Left',0,3),('Right',1,2)]
SLOPES=[(3,'sw'),(6,'se'),(9,'nw'),(12,'ne')]

def source_strip(im,box,uv_height):
    strip=im.crop(box).transpose(Image.Transpose.ROTATE_90)
    # Native track spans at least195px along its length; export UV192.
    # The formal2:1 projection shrinks that axis again.
    if strip.width<UV or strip.height<uv_height:raise ValueError('refuse native upscaling '+str(box))
    strip=strip.resize((UV,uv_height),Image.Resampling.LANCZOS)
    uv=Image.new('RGBA',(UV,UV));uv.alpha_composite(strip,(0,(UV-uv_height)//2))
    return uv

def save(ident,im,srcs,operation,extra=None,anchor=None):
    p=OUT/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    a=wp.base_asset(ident,p.relative_to(ROOT).as_posix(),im,srcs[0],operation,'infrastructure',anchor or[128,64]);a.update(extra or{});a['derivedFrom']=srcs;a['sha256']=wp.sha(p)
    wp.writej(str(p)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'route':'deterministic-derivative','generatedAt':wp.now(),'width':im.width,'height':im.height,'operation':operation,'derivedFrom':srcs,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'unverifiedReason':'Source native generation did not expose actual model/quality; geometric and layered exports do not add native detail.'})
    return a

def catenary(im):
    pieces=[]
    data=[('rail-catenary-post-left',[100,643,196,810],[(0,0),(96,0),(96,56),(28,56),(28,167),(0,167)],[14,161]),('rail-catenary-post-right',[201,643,288,810],[(0,0),(87,0),(87,167),(58,167),(58,56),(0,56)],[69,161])]
    for ident,box,polygon,anchor in data:
        crop=im.crop(box).convert('RGBA');m=Image.new('L',crop.size);ImageDraw.Draw(m).polygon(polygon,fill=255);crop.putalpha(ImageChops.multiply(crop.getchannel('A'),m))
        canvas=Image.new('RGBA',(128,192));at=(48-anchor[0],176-anchor[1]);canvas.alpha_composite(crop,at)
        pieces.append((ident,canvas))
    return pieces

def build():
    OUT.mkdir(parents=True,exist_ok=True);src=ROOT/'source-art/world/rail-topology.png';im=Image.open(src).convert('RGBA');sources=[wp.source_record(src)]
    if im.size!=(1536,1024):raise ValueError('native crop contract changed')
    raw={'rail':source_strip(im,[148,89,231,284],60),'monorail':source_strip(im,[548,695,603,897],48),'maglev':source_strip(im,[900,700,1020,910],72)}
    raw['electric']=raw['rail']
    entries=[];qa=[];segments={};comp={}
    operation='actual hand-painted rail/beam/slab strip crop -> UV coordinate normalization -> true symmetric transpose or annular curve remap -> exact2:1 diamond projection; no code-painted rails or newly generated details'
    poles=catenary(im)
    for ident,pole in poles:entries.append(save(ident,pole,sources,'native painted catenary pole/arm crop -> authored Alpha polygon excluding adjacent track -> fixed canvas; no new perspective',{'sourceRequirementIds':['rail-catenary'],'anchorMeaning':'actual pole-base contact','layer':'overhead','status':'produced-needs-visual-review'},[48,176]))
    # The same genuinely painted copper wire span repeats to the required
    # length; repeating existing pixels is not a new painted stroke.
    wire_piece=im.crop((118,663,174,672));wire_long=Image.new('RGBA',(224,9))
    for x in range(0,224,56):wire_long.alpha_composite(wire_piece,(x,0))
    wire_long=wire_long.resize((UV,4),Image.Resampling.LANCZOS);wire_uv=Image.new('RGBA',(UV,UV));wire_uv.alpha_composite(wire_long,(0,UV//2-2));wire_segments=[]
    for bit,(name,a,b)in enumerate(TRACKS):
        wire=terrain.project(tram_segment(wire_uv,a,b));wire_segments.append(wire)
        entries.append(save('rail-catenary-wire-'+name.lower(),wire,sources,'actual native copper-wire span crop -> four repeats -> downscale -> UV direction/curve remap ->2:1 projection; no code-painted wire',{'sourceRequirementIds':['rail-catenary'],'trackBit':bit,'heightAboveRailPx':136,'layer':'overhead-wire','status':'produced-needs-connection-review'},[128,64]))
    for kind,texture in raw.items():
        variants=[]
        for bit,(name,a,b)in enumerate(TRACKS):
            u=tram_segment(texture,a,b);tile=terrain.project(u)
            ident='rail-'+kind+'-segment-'+name.lower();entry=save(ident,tile,sources,operation,{'trackBit':bit,'trackName':name,'connectedPorts':[a,b],'sourceRequirementIds':['rail-'+kind],'layer':'track-overlay','status':'produced-needs-connection-review'});entries.append(entry);variants.append(tile)
            for code,slope in SLOPES:
                sl,points,heights=wp.projected_slope(tile,code)
                entries.append(save(ident+'-slope-'+slope,sl,sources,operation+'; piecewise-affine slope geometry',{'trackBit':bit,'slopeCode':code,'cornerHeights':heights,'layer':'track-overlay','sourceRequirementIds':['rail-'+kind],'status':'produced-needs-connection-review'},[128,128]))
        segments[kind]=variants;comp[kind]={}
        for mask in range(1,64):
            overlay=Image.new('RGBA',(256,128))
            for bit in range(6):
                if mask&(1<<bit):overlay.alpha_composite(variants[bit])
            comp[kind][mask]=overlay
            for climate,base in [('normal','grass'),('snow','snow'),('desert','desert')]:
                groundpath=ROOT/'assets/world/terrain'/('terrain-'+base+'-flat.png');ground=Image.open(groundpath).convert('RGBA');ground.alpha_composite(overlay)
                srcs=sources+[{'file':groundpath.relative_to(ROOT).as_posix(),'sha256':wp.sha(groundpath),'record':groundpath.relative_to(ROOT).as_posix()+'.derivation.json'}]
                ident='rail-'+kind+'-mask-'+format(mask,'02d')+'-'+climate
                if kind=='electric':
                    # Overhead props remain upright; only the ground track is projected.
                    tall=Image.new('RGBA',(320,320));tall.alpha_composite(ground,(32,192))
                    for bit in range(6):
                        if mask&(1<<bit):tall.alpha_composite(wire_segments[bit],(32,56))
                    tall.alpha_composite(poles[0][1],(64-48,256-176));tall.alpha_composite(poles[1][1],(256-48,256-176));ground=tall;anchor=[160,256]
                else:anchor=[128,64]
                entries.append(save(ident,ground,srcs,operation+'; six track-bit overlays composed on actual painted '+climate+' ground'+('; upright native catenary props layered separately'if kind=='electric'else''),{'compositionMask':mask,'trackBits':[TRACKS[k][0]for k in range(6)if mask&(1<<k)],'climate':climate,'sourceRequirementIds':['rail-'+kind],'logicalFootprint':[1,1],'layer':'track-and-ground'if kind!='electric'else'track-and-overhead-preview','overheadSeparateAssets':[p[0]for p in poles]if kind=='electric'else[],'status':'produced-needs-connection-review','nativeVariantClaim':False},anchor))
        for code,slope in SLOPES:
            # Six independent overlays cover all graph compositions without
            # duplicating every impossible track-mask/slope runtime combination.
            qa.append({'id':'rail-'+kind+'-slope-'+slope,'level':'OK','value':'6 track-bit overlays produced','runtimeLegalCombinations':'must be filtered by source foundation/track build rules during Unity implementation'})
    manifest={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'batchId':'rail-network','assets':entries,'animations':[],'qa':qa,'sourceTrackBitOrder':[t[0]for t in TRACKS],'nativeStripCrops':{'rail':[148,89,231,284],'monorail':[548,695,603,897],'maglev':[900,700,1020,910]},'sourceRequirementIds':['rail-rail','rail-electric','rail-monorail','rail-maglev','rail-catenary'],'acceptance':'not yet accepted; route/port and Alpha review pending','claim':'4 technologies ×6 reusable track segments;63 graph masks per technology and3 climates are explicit composites, not756 native paintings.','limitations':['Catenary ground sprites and upright poles/wires must remain separate runtime layers.','Only valid game-rule combinations may be assembled on inclined terrain; not every graph mask is buildable on every slope.','Mono/maglev textures are geometric remaps of actual painted strips, not additional native viewpoints.','Unity renderer, collisions, route legality and platform compression remain unverified.']}
    wp.writej(OUT/'manifest.json',manifest)
    samples=[a for a in entries if('segment-'in a['id']and'slope'not in a['id'])or a.get('compositionMask')in[3,5,9,17,33,63]and a.get('climate')=='normal']
    terrain.contact(samples,'rail-contact.jpg',6,160)
    print(json.dumps({'assets':len(entries),'segments':24,'topologyMasks':252,'climateComposites':756,'catenaryProps':2,'slopeOverlays':96},ensure_ascii=False))
if __name__=='__main__':build()
