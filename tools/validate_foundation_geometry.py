"""Independent continuous-source geometry checks and actual terrain assemblies."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math
import world_pack as wp

R = wp.ROOT
UV = {'n': (0., 0.), 'e': (0., 1.), 's': (1., 1.), 'w': (1., 0.)}
OPP = {'w': 'e', 's': 'n', 'e': 'w', 'n': 's'}
BITS = {'w': 1, 's': 2, 'e': 4, 'n': 8}


def source_z(code, x, y):
    # Continuous equivalent of landscape.cpp GetPartialPixelZ, before source
    # integer pixel rounding. Independent of producer triangulation/functions.
    return {
        0: lambda: 0., 1: lambda: max(x-y, 0), 2: lambda: max(x+y-1, 0),
        3: lambda: x, 4: lambda: max(y-x, 0), 5: lambda: abs(x-y),
        6: lambda: y, 7: lambda: 1-max(1-x-y, 0),
        8: lambda: max(1-x-y, 0), 9: lambda: 1-y, 10: lambda: abs(1-x-y),
        11: lambda: 1-max(y-x, 0), 12: lambda: 1-x,
        13: lambda: 1-max(x+y-1, 0), 14: lambda: 1-max(x-y, 0),
        27: lambda: 1+x-y, 23: lambda: x+y, 30: lambda: 1+y-x, 29: lambda: 2-x-y,
    }[code]()


def in_half(c, x, y):
    return {'w': x > y, 's': x+y >= 1, 'e': x <= y, 'n': x+y < 1}[c]


def expected(c, x, y):
    code, mode = c['slopeCode'], c['mode']
    high = {1: 'w', 2: 's', 4: 'e', 8: 'n', 27: 'w', 23: 's', 30: 'e', 29: 'n'}.get(code)
    dz = int(code > 16)
    if mode == 'Leveled':
        return 1+dz
    if mode == 'InclinedX':
        return dz + (x if high in {'w', 's'} else 1-x)
    if mode == 'InclinedY':
        return dz + (y if high in {'e', 's'} else 1-y)
    if mode == 'SteepLower':
        return 1+source_z(BITS[high], x, y)
    if mode == 'SteepBoth':
        return 2. if in_half(high, x, y) else 1.
    if mode.startswith('HalfTile'):
        return (1+dz) if in_half(mode[-1].lower(), x, y) else source_z(code, x, y)
    if mode.startswith('Rail'):
        return source_z(15 ^ BITS[OPP[mode[-1].lower()]], x, y)
    raise ValueError(mode)


def patch_z(patch, x, y):
    for tri in patch['triangles']:
        p0, p1, p2 = [UV[k] for k in tri]
        det = (p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
        a = ((p1[1]-p2[1])*(x-p2[0])+(p2[0]-p1[0])*(y-p2[1]))/det
        b = ((p2[1]-p0[1])*(x-p2[0])+(p0[0]-p2[0])*(y-p2[1]))/det
        if min(a, b, 1-a-b) >= -1e-7:
            return sum(w*patch['heights'][k] for w, k in zip((a, b, 1-a-b), tri))
    return None


def main():
    mp = R/'assets/world/infrastructure/foundations/manifest.json'
    pack = wp.readj(mp)
    cases = [c for c in pack['coverageMappings'][0]['caseBindings'] if c.get('whole')]
    checks, sampling = [], []
    def check(name, passed, **data):
        checks.append({'id': name, 'level': 'OK' if passed else 'FAIL', **data})
    for a in pack['assets']:
        p = R/a['image']
        im = Image.open(p)
        check(a['id']+'.png', im.mode == 'RGBA' and im.size == (512,384)
              and a['anchorPx'] == [256,224] and wp.sha(p) == a['sha256']
              and im.getchannel('A').getextrema() == (0,255), image=a['image'])
    for c in cases:
        failures, count = [], 0
        for ix in range(33):
            for iy in range(33):
                x, y = ix/32, iy/32
                if (c['mode'].startswith('HalfTile') or c['mode']=='SteepBoth') and (
                        abs(x-y)<1e-6 or abs(x+y-1)<1e-6):
                    continue  # Discontinuity has two boundary heights; test interiors.
                z = None
                for patch in c['targetPatches']:
                    z = patch_z(patch, x, y)
                    if z is not None:
                        break
                if z is None:
                    z = source_z(c['slopeCode'], x, y) # Half's untouched natural remainder.
                ref = expected(c, x, y)
                if abs(z-ref)>1e-6 or z < source_z(c['slopeCode'], x, y)-1e-6:
                    failures.append({'uv':[x,y], 'actual':z, 'expected':ref})
                count += 1
        tag = c['mode']+'-'+str(c['slopeCode'])
        check(tag+'.source-height', not failures, sampleCount=count, issues=failures[:5])
        sampling.append({'mode':c['mode'],'slopeCode':c['slopeCode'],'samples':count})
        for p in c['targetPatches']:
            if c['mode'].startswith('HalfTile'):
                check(tag+'.half-area', len(p['corners']) == 3 and abs(p['footprintArea']-.5)<1e-8,
                      corners=p['corners'],area=p['footprintArea'])
        if c['mode']=='SteepBoth':
            whole = Image.open(R/c['whole']).convert('RGBA')
            parts = Image.new('RGBA',whole.size)
            for part in c['orderedPartLayers']:
                parts.alpha_composite(Image.open(R/part['image']).convert('RGBA'))
            check(tag+'.two-part-reassembly', parts.tobytes()==whole.tobytes())
        for face in c['supportFaces']:
            check(tag+'.support', all(z>=-1e-7 for z in face['heightPixels']), face=face['edgeCorners'])
    check('four-half-corners', {c['mode'] for c in cases if c['mode'].startswith('HalfTile')}
          == {'HalfTileW','HalfTileS','HalfTileE','HalfTileN'})
    check('all14-modes', len({c['mode'] for c in pack['coverageMappings'][0]['caseBindings']})==14)
    # Every source-valid case is actually assembled with the matching current slope PNG.
    previews = []
    fontpath = 'C:/Windows/Fonts/arial.ttf'
    font = ImageFont.truetype(fontpath, 17)
    bycode = dict(wp.SLOPES)
    for start in range(0,len(cases),24):
        pagecases = cases[start:start+24]
        canvas = Image.new('RGB',(1200,math.ceil(len(pagecases)/4)*220),(30,58,50))
        d = ImageDraw.Draw(canvas)
        for n,c in enumerate(pagecases):
            tile = Image.new('RGBA',(512,384))
            ground = R/('assets/world/terrain/terrain-grass-slope-'+bycode[c['slopeCode']]+'.png')
            tile.alpha_composite(Image.open(ground).convert('RGBA'),(128,96))
            tile.alpha_composite(Image.open(R/c['whole']).convert('RGBA'))
            thumb = tile.resize((288,216),Image.Resampling.LANCZOS)
            xx,yy = (n%4)*300,(n//4)*220
            canvas.paste(thumb,(xx,yy-8),thumb)
            d.text((xx+10,yy+193),c['mode']+' / '+bycode[c['slopeCode']],font=font,fill=(239,232,210))
        p = R/('previews/world/foundation-terrain-assembly-'+str(start//24+1)+'.jpg')
        canvas.save(p,quality=94)
        previews.append({'file':wp.rel(p),'sha256':wp.sha(p),'cases':len(pagecases)})
    report = {'createdAt':wp.now(),'scope':'source piecewise height functions, triangular half area, real PNG/Alpha/anchor/SHA, two-part reassembly, all66 valid terrain assemblies',
        'sourceGeometry':['src/landscape.cpp:182-225','src/landscape.cpp:240-300','src/rail_cmd.cpp:310-381'],
        'manifest':{'file':wp.rel(mp),'sha256':wp.sha(mp)},'checks':checks,
        'passed':sum(c['level']=='OK' for c in checks),'failures':sum(c['level']=='FAIL' for c in checks),
        'samples':sum(c['samples'] for c in sampling),'sourceValidCases':len(cases),
        'sourceInvalidOrNoneCases':len(pack['coverageMappings'][0]['caseBindings'])-len(cases),
        'formalPNGCount':len(pack['assets']),'assemblyPreviews':previews,
        'visualReview':'pending actual preview inspection','userArtAcceptance':'pending','unityValidated':False,
        'continuousReferenceNote':'Reference evaluates exact source planes before integer pixel rounding; strict half boundaries have upper/lower values and are excluded from interiors test.'}
    reviewp = R/'records/world-production/foundation-visual-review.json'
    if reviewp.exists():
        review = wp.readj(reviewp)
        if review.get('manifestSHA256') == wp.sha(mp) and all(
                (R/a['file']).is_file() and wp.sha(R/a['file']) == a['sha256'] for a in review.get('pages',[])):
            report['visualReview'] = 'passed-local: actual family contact and all66 terrain assemblies inspected; current hashes match'
            report['visualReviewRecord'] = {'file':wp.rel(reviewp),'sha256':wp.sha(reviewp)}
    report['sourceScripts'] = [{'file':x,'sha256':wp.sha(R/x)} for x in
        ['tools/foundation_geometry_v2.py','tools/build_foundation_geometry.py','tools/validate_foundation_geometry.py']]
    wp.writej(R/'records/world-production/foundation-geometry-validation.json',report)
    print(json.dumps({k:report[k] for k in ['passed','failures','samples','sourceValidCases','formalPNGCount']}))


if __name__=='__main__':
    main()
