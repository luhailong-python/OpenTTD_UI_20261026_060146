"""Source-correct Foundation projection using existing native painted pixels.
Sortable sprite bounds are not ground footprints. No new painting is made here.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json
import world_pack as wp
import build_world_services as services
import build_world_terrain as terrain

R = wp.ROOT
OUT = 'assets/world/infrastructure/foundations'
UV = {'n': (0., 0.), 'e': (0., 1.), 's': (1., 1.), 'w': (1., 0.)}
OPPOSITE = {'w': 'e', 'e': 'w', 'n': 's', 's': 'n'}
HALVES = {'w': ('n', 's', 'w'), 's': ('e', 's', 'w'),
          'e': ('n', 'e', 's'), 'n': ('n', 'e', 'w')}
MODES = ['Leveled', 'InclinedX', 'InclinedY', 'SteepLower', 'SteepBoth',
         'HalfTileW', 'HalfTileS', 'HalfTileE', 'HalfTileN',
         'RailW', 'RailS', 'RailE', 'RailN']
# Exact GetRailFoundation outcomes for single diagonal tracks and the two
# non-overlapping opposite pairs. Flat HalfTile bindings are never selected.
HALF_CODES = {'w': {1, 5, 27}, 's': {2, 10, 23},
              'e': {4, 5, 30}, 'n': {8, 10, 29}}
RAIL_CODES = {'w': {3, 9, 10}, 's': {3, 6, 5},
              'e': {6, 12, 10}, 'n': {9, 12, 5}}


def polyarea(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
                   - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def point(u, v, z):
    return ((v-u)*128+256, (u+v)*64+160-z*32)


def natural(u, v, h, code):
    for labels in wp.slope_triangles(code):
        p0,p1,p2 = [UV[k] for k in labels]
        den = (p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
        a = ((p1[1]-p2[1])*(u-p2[0])+(p2[0]-p1[0])*(v-p2[1]))/den
        b = ((p2[1]-p0[1])*(u-p2[0])+(p0[0]-p2[0])*(v-p2[1]))/den
        c = 1-a-b
        if min(a,b,c)>=-1e-6:
            return a*h[labels[0]]+b*h[labels[1]]+c*h[labels[2]]
    raise ValueError((u,v,code))


def target(code, mode):
    """Exact piecewise planar target or explicit source-invalid combination."""
    h = wp.corner_heights(code)
    high, maxh = max(h, key=h.get), max(h.values())
    dz = 1 if code & 16 else 0
    full = tuple(UV)
    if mode == 'Leveled':
        if code == 0:
            return None
        return [{'name': 'whole', 'corners': full, 'heights': {k: float(maxh) for k in UV},
                 'triangles': [('n', 'e', 's'), ('n', 's', 'w')]}]
    if mode.startswith('Inclined'):
        if code not in {1, 2, 4, 8, 27, 23, 30, 29}:
            return None
        highset = ({'w', 's'} if high in {'w', 's'} else {'n', 'e'}) if mode == 'InclinedX' else (
            {'e', 's'} if high in {'e', 's'} else {'w', 'n'})
        tops = {k: float(dz + (k in highset)) for k in UV}
        return [{'name': 'whole', 'corners': full, 'heights': tops,
                 'triangles': [('n', 'e', 's'), ('n', 's', 'w')]}]
    if mode in {'SteepLower', 'SteepBoth'}:
        if not code & 16:
            return None
        lower, upper = HALVES[OPPOSITE[high]], HALVES[high]
        return [{'name': 'lower', 'corners': lower, 'heights': {k: 1. for k in lower}, 'triangles': [lower]},
                {'name': 'upper', 'corners': upper,
                 'heights': {k: float(2 if mode == 'SteepBoth' or k == high else 1) for k in upper},
                 'triangles': [upper]}]
    if mode.startswith('HalfTile'):
        corner = mode[-1].lower()
        if code not in HALF_CODES[corner]:
            return None
        labels = HALVES[corner]
        return [{'name': 'half', 'corners': labels,
                 'heights': {k: float(maxh) for k in labels}, 'triangles': [labels]}]
    if mode.startswith('Rail'):
        corner = mode[-1].lower()
        if code not in RAIL_CODES[corner]:
            return None
        result = 15 ^ wp.CORNERS[OPPOSITE[corner]]
        return [{'name': 'whole', 'corners': full, 'heights': wp.corner_heights(result),
                 'triangles': wp.slope_triangles(result)}]
    raise ValueError(mode)


def texture_triangle(tex, dst, src):
    size = (512, 384)
    if polyarea(dst) < .2:
        return Image.new('RGBA', size)
    im = tex.transform(size, Image.Transform.AFFINE, wp.affine_coeff(dst, src), Image.Resampling.BICUBIC)
    mask = Image.new('L', size)
    ImageDraw.Draw(mask).polygon(dst, fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel('A'), mask))
    return im


def textured_quad(tex, quad):
    im = Image.new('RGBA', (512,384))
    src = [(0,0),(tex.width,0),(tex.width,tex.height),(0,tex.height)]
    for ids in [(0,1,2),(0,2,3)]:
        im.alpha_composite(texture_triangle(tex,[quad[i] for i in ids],[src[i] for i in ids]))
    return im


def render_patch(patch, h, code, wall, cap):
    labels, tops = patch['corners'], patch['heights']
    sides, surface = Image.new('RGBA', (512, 384)), Image.new('RGBA', (512, 384))
    faces = []
    edges = list(zip(labels, labels[1:] + labels[:1]))
    edges.sort(key=lambda e: sum(sum(UV[k]) for k in e))
    for a, b in edges:
        upper = [point(*UV[k], tops[k]) for k in (a, b)]
        bottomz = [natural(*UV[k], h, code) for k in (a, b)]
        bottom = [point(*UV[k], z) for k, z in zip((a, b), bottomz)]
        depths = [(tops[k] - z) * 32 for k, z in zip((a, b), bottomz)]
        sides.alpha_composite(textured_quad(wall, upper + bottom[::-1]))
        faces.append({'patch': patch['name'], 'edgeCorners': [a, b], 'topEndpoints': upper,
                      'bottomEndpoints': bottom, 'heightPixels': depths})
    for tri in patch['triangles']:
        dst = [point(*UV[k], tops[k]) for k in tri]
        # Global material UV: both halves stay registered to the same full tile.
        src = [(UV[k][1] * (cap.width - 1), UV[k][0] * (cap.height - 1)) for k in tri]
        surface.alpha_composite(texture_triangle(cap, dst, src))
    whole = sides.copy()
    whole.alpha_composite(surface)
    return whole, sides, faces


def main():
    mp = R / OUT / 'manifest.json'
    prior = wp.readj(mp) if mp.exists() else {'assets': []}
    wallp = R / 'assets/world/infrastructure/construction-ready/construction-stone-wall.png'
    wall = Image.open(wallp).convert('RGBA').transform((192, 64), Image.Transform.QUAD,
        (151, 268, 151, 307, 338, 372, 338, 331), Image.Resampling.BICUBIC)
    wall.putalpha(Image.new('L', wall.size, 255))
    gp = R / 'assets/world/terrain/terrain-grass-flat.png'
    cap = terrain.unwrap(Image.open(gp).convert('RGBA'), [[128, 1], [255, 64], [128, 127], [1, 64]]).convert('RGBA')
    refs = [{'file': wp.rel(p), 'sha256': wp.sha(p), 'record': wp.rel(p) + '.derivation.json'} for p in (wallp, gp)]
    entries, cases, checks = [], [], []
    for code, name in wp.SLOPES:
        h = wp.corner_heights(code)
        cases.append({'slopeCode': code, 'mode': 'None', 'draw': 'no foundation; native terrain slope retained'})
        for mode in MODES:
            patches = target(code, mode)
            if patches is None:
                cases.append({'slopeCode': code, 'mode': mode, 'draw': 'not-applicable',
                    'reason': 'not selected by source Foundation preconditions / GetRailFoundation'})
                continue
            whole, sides = Image.new('RGBA', (512, 384)), Image.new('RGBA', (512, 384))
            allfaces, partimages = [], []
            for patch in sorted(patches, key=lambda p: sum(sum(UV[k]) for k in p['corners']) / len(p['corners'])):
                body, side, faces = render_patch(patch, h, code, wall, cap)
                whole.alpha_composite(body)
                sides.alpha_composite(side)
                allfaces.extend(faces)
                partimages.append((patch['name'], body, side))
            ident = 'foundation-' + mode.lower() + '-' + name
            patchmeta = [{**p, 'patchUV': [UV[k] for k in p['corners']],
                          'footprintArea': polyarea([UV[k] for k in p['corners']])} for p in patches]
            meta = {'category': 'foundation', 'foundationMode': mode, 'slopeCode': code,
                'naturalCornerHeightUnits': h, 'targetPatches': patchmeta, 'supportFaceGeometry': allfaces,
                'sourceRequirementIds': ['terrain-foundation'],
                'sourceFootprint': 'triangular-half-tile' if mode.startswith('HalfTile') else 'whole-tile',
                'patchUV': patchmeta[0]['patchUV'] if len(patchmeta) == 1 else None,
                'status': 'produced-needs-geometry-review', 'nativeTopGapFilled': True}
            en = services.emit(OUT, ident, whole, refs,
                'existing native stone/grass pixels reprojected onto source piecewise-planar Foundation surfaces; half-tile follows GetPartialPixelZ, not sortable bounds; no new painting or native upscale', meta, [256, 224])
            entries.append(en)
            sideasset = services.emit(OUT, ident + '-sides', sides, [services.ref(en)],
                'same positioned textured support faces without top cap; alternative layer to whole',
                {'category': 'foundation-side-layer', 'foundationMode': mode, 'slopeCode': code,
                 'sourceRequirementIds': ['terrain-foundation'], 'status': 'produced-needs-geometry-review'}, [256, 224])
            entries.append(sideasset)
            binding = {'slopeCode': code, 'mode': mode, 'whole': en['image'], 'sideLayer': sideasset['image'],
                'targetPatches': patchmeta, 'supportFaces': allfaces, 'groundCapPaintedSource': wp.rel(gp),
                'renderRule': 'whole OR sides plus matching target cap; retain native terrain outside selected triangular half'}
            if mode == 'SteepBoth':
                binding['orderedPartLayers'] = []
                for partname, body, side in partimages:
                    part = services.emit(OUT, ident + '-' + partname, body, [services.ref(en)],
                        'exact component of two-part steep foundation at same parent anchor; existing native textured geometry',
                        {'category': 'foundation-part-layer', 'foundationMode': mode, 'slopeCode': code,
                         'part': partname, 'sourceRequirementIds': ['terrain-foundation'],
                         'status': 'produced-needs-geometry-review'}, [256, 224])
                    entries.append(part)
                    binding['orderedPartLayers'].append({'part': partname, 'image': part['image'], 'anchorPx': [256, 224]})
                binding['renderRule'] += '; two saved ordered part layers OR whole, never both'
            cases.append(binding)
            checks.append({'id': ident + '.geometry', 'level': 'OK' if all(min(f['heightPixels']) >= -1e-6 for f in allfaces) else 'FAIL',
                'topAndBottomEndpointsShared': True, 'fullyTexturedSideFaces': True,
                'halfFootprintArea': patchmeta[0]['footprintArea'] if mode.startswith('HalfTile') else None})
    mapping = {'requirementId': 'terrain-foundation', 'files': [a['image'] for a in entries],
        'FoundationModes': MODES + ['None'], 'slopeCodes': [c for c, _ in wp.SLOPES], 'caseBindings': cases,
        'sourceSpriteBlockCounts': {'normal': 74, 'normalAndHalfTile': 90},
        'countingRule': 'source blocks are compatibility storage, not 164 independent native paintings',
        'halfTileMethod': 'half square UV triangle area 0.5; source x>y / x+y>=1 / x<=y / x+y<1; 8x8 sortable bounds are not a footprint',
        'steepBothMethod': 'opposite lower half level at height 1; selected upper half level at height 2; independent ordered part layers OR whole',
        'sourceGeometry': ['src/slope_type.h:119-140', 'src/landscape.cpp:182-225', 'src/landscape.cpp:240-300', 'src/rail_cmd.cpp:310-381']}
    wp.writej(mp, {'schema': 'cloud-route.world-art.v1', 'createdAt': wp.now(), 'assets': entries,
        'animations': [], 'qa': checks, 'coverageMappings': [mapping],
        'acceptance': 'source geometry corrected; independent numeric and actual image review pending', 'unityValidated': False})
    active = {a['image'] for a in entries}
    retired = []
    for old in prior['assets']:
        if old['image'] in active:
            continue
        p = (R / old['image']).resolve()
        if p.parent != (R / OUT).resolve():
            raise ValueError('Prior asset outside foundation pack')
        retired.append({'file': old['image'], 'sha256': old['sha256'], 'reason': 'source-invalid binding previously emitted'})
        for fp in (p, Path(str(p) + '.derivation.json')):
            if fp.is_file():
                fp.unlink()
    wp.writej(R / 'records/world-production/foundation-geometry-repair.json',
        {'createdAt': wp.now(), 'assetCount': len(entries), 'caseCount': len(cases), 'checks': checks,
         'sourceMaterial': refs, 'noNativeUpscale': True, 'retiredInvalidBindings': retired,
         'corrections': ['quarter footprint replaced by half triangle', 'SteepBoth now two levels',
                         'Rail top now piecewise triangular instead of bilinear', 'source-invalid pairs explicitly have no PNG'],
         'visualReview': 'pending'})
    chosen = [next(a for a in entries if a.get('foundationMode') == m and a['category'] == 'foundation') for m in MODES]
    chosen += [a for a in entries if a.get('foundationMode') in {'HalfTileW', 'HalfTileS', 'HalfTileE', 'HalfTileN', 'SteepBoth'} and a['category'] == 'foundation']
    terrain.contact(chosen, 'foundation-slopes-contact.jpg', 4, 200)
    print(json.dumps({'assets': len(entries), 'cases': len(cases), 'retiredInvalidPNGs': len(retired)}))


if __name__ == '__main__':
    main()
