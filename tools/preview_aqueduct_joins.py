"""Inspect current exported aqueduct pieces; never changes production art."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
from PIL import Image, ImageDraw, ImageFont
from preview_bridge_joins import panel, inspect_joins

R = Path(__file__).resolve().parents[1]

def main():
    manifest = R / 'assets/world/infrastructure/transport-runtime/manifest.json'
    data = json.loads(manifest.read_text(encoding='utf-8'))
    assets = {a['id']: a for a in data['assets']}
    font = ImageFont.truetype(str(R / 'assets/fonts/NotoSansSC-Variable.ttf'), 22)
    image = Image.new('RGB', (1880, 600), '#ebe6d8')
    draw = ImageDraw.Draw(image)
    cases = []
    for c, axis in enumerate(['X', 'Y']):
        for n in range(8):
            a = assets[f'aqueduct-{axis}-piece-{n}']
            sprite = Image.open(R / a['image']).convert('RGBA')
            part = (sprite, a['projection'])
            checks = inspect_joins([part] * 3, axis)
            cases.append({'axis': axis, 'sourceRole': n, 'image': a['image'],
                          'sha256': hashlib.sha256((R / a['image']).read_bytes()).hexdigest(),
                          'waterSurfaceRisePx': a['projection']['rampRisePx'], **checks})
            if n == 4:
                preview = panel([part] * 3, axis)
                preview = preview.resize((preview.width * 2, preview.height * 2), Image.Resampling.NEAREST)
                preview.thumbnail((910, 500), Image.Resampling.NEAREST)
                image.paste(preview.convert('RGB'), (c * 940 + 12, 65))
                draw.text((c * 940 + 12, 15), axis + ' / 3 actual level-water spans / source-pixel geometry', font=font, fill='#204337')
    preview_path = R / 'previews/world/aqueduct-joins.jpg'
    image.save(preview_path, quality=96)
    report = {'createdAt': datetime.now(timezone.utc).isoformat(),
              'runtimeManifestSha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
              'preview': preview_path.relative_to(R).as_posix(),
              'previewSha256': hashlib.sha256(preview_path.read_bytes()).hexdigest(),
              'cases': cases, 'assemblies': 16, 'interfaces': 32,
              'exactPortAlignment': all(a['exactPortAlignment'] for a in cases),
              'noTransparentDeckGap': all(a['noTransparentDeckGap'] for a in cases),
              'allWaterSurfacesLevel': all(a['waterSurfaceRisePx'] == 0 for a in cases),
              'rule': 'Eight source roles share the declared native canal module. Water stays level; four head land slopes require matching foundation support. PNG stitching is not Unity clearance or terrain acceptance.',
              'unityValidated': False}
    (R / 'records/world-production/aqueduct-joins-geometry.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['assemblies', 'interfaces', 'exactPortAlignment', 'noTransparentDeckGap', 'allWaterSurfacesLevel']}))

if __name__ == '__main__':
    main()
