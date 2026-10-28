"""Read upstream face fields and check art bindings; never builds production art."""
from pathlib import Path
from datetime import datetime, timezone
import json, re, hashlib

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def extract(root):
    source = root / 'reference/OpenTTD/src/table/company_face.h'
    text = source.read_text(encoding='utf-8')
    styles, requirements, sprite_ids = [], [], set()
    for number, body in re.findall(r'static constexpr FaceVar _face_style_(\d+)\[\] = \{(.*?)\n\};', text, re.S):
        style, fields = int(number) - 1, []
        for line in body.splitlines():
            m = re.search(r'FaceVarType::(\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(.*)', line)
            if not m:
                continue
            kind, position, offset, bits, count, data = m.groups()
            name = re.search(r'STR_FACE_\w+', data)
            field = dict(kind=kind, sourceVarIndex=len(fields), uiPosition=int(position), bitOffset=int(offset), bitLength=int(bits), validValues=int(count), name=name.group() if name else 'fixed-base')
            if kind == 'Sprite':
                start = int(re.search(r'0x[0-9A-Fa-f]+', data).group(), 16)
                field['sourceSpriteIds'] = list(range(start, start + int(count)))
                sprite_ids.update(field['sourceSpriteIds'])
            elif kind == 'Toggle':
                expression = re.search(r'std::pair\{(.*?)\}', data).group(1)
                masks = []
                for half in expression.split(','):
                    masks.append([int(n) for n in re.findall(r'1ULL\s*<<\s*(\d+)', half)])
                field['hiddenWhenValue0'], field['hiddenWhenValue1'] = masks
            else:
                field['affectedSourceVarIndices'] = [int(n) for n in re.findall(r'1ULL\s*<<\s*(\d+)', data)]
                field['paletteNames'] = ['brown', 'blue', 'green']
            fields.append(field)
            for value in range(int(count)):
                row = dict(requirementId=f'manager-style-{style}-var-{field["sourceVarIndex"]}-value-{value}', sourceStyle=style, sourceStyleLabel='default/face'+number, sourceVarIndex=field['sourceVarIndex'], kind=kind, sourceValue=value, fieldName=field['name'])
                if kind == 'Sprite': row['sourceSpriteId'] = field['sourceSpriteIds'][value]
                if kind == 'Toggle': row['hiddenSourceVarIndices'] = field['hiddenWhenValue'+str(value)]
                if kind == 'Palette':
                    row['paletteName'] = field['paletteNames'][value]
                    row['affectedSourceVarIndices'] = field['affectedSourceVarIndices']
                requirements.append(row)
        styles.append(dict(sourceStyle=style, sourceStyleLabel='default/face'+number, fields=fields, spriteValueSlots=sum(f['validValues'] for f in fields if f['kind']=='Sprite')))
    return {'referenceCommit':'cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8','source':source.relative_to(root).as_posix(),'sourceSha256':sha(source),'styles':styles,'requirements':requirements,'spriteValueSlots':sum(s['spriteValueSlots'] for s in styles),'uniqueSourceSpriteIds':len(sprite_ids)}

def audit(root):
    root = Path(root).resolve()
    spec = extract(root)
    candidates = [root/'docs/MANAGER_FACE_ART_MANIFEST.json',root/'assets/portraits/customization/manifest.json',root/'assets/portraits/face-parts/manifest.json']
    manifest = next((p for p in candidates if p.is_file()), None)
    art = load(manifest) if manifest else {}
    assets = {a['id']:a for a in art.get('assets',[])}
    bindings = {a['requirementId']:a for a in art.get('bindings',[])}
    gaps = []
    missing = []
    for requirement in spec['requirements']:
        name = requirement['requirementId']
        binding = bindings.get(name)
        if not binding:
            missing.append(name)
            continue
        if requirement['kind']=='Sprite':
            ids = binding.get('assetIds',[])
            if not ids or any(a not in assets or not (root/assets[a].get('image',assets[a].get('file','__missing__'))).is_file() for a in ids):
                gaps.append({'requirementId':name,'gap':'No actual registered composable PNG for this sprite value'})
            if binding.get('sourceSpriteId')!=requirement['sourceSpriteId']:
                gaps.append({'requirementId':name,'gap':'Binding does not identify the actual source SpriteID value'})
            if requirement['fieldName']!='fixed-base' and any(re.fullmatch(r'assets/portraits/manager-\d\d\.png',assets[a].get('image',assets[a].get('file',''))) for a in ids if a in assets):
                gaps.append({'requirementId':name,'gap':'A complete existing preset bust cannot stand in for a replaceable facial/clothing component'})
        elif requirement['kind']=='Toggle':
            if binding.get('hiddenSourceVarIndices')!=requirement['hiddenSourceVarIndices']:
                gaps.append({'requirementId':name,'gap':'Toggle must preserve the exact active/hidden source variable relationship'})
        else:
            if binding.get('affectedSourceVarIndices')!=requirement['affectedSourceVarIndices'] or not binding.get('paletteRule'):
                gaps.append({'requirementId':name,'gap':'Eye palette needs isolated ownership and a concrete3-colour art rule'})
    if missing: gaps.append({'gap':'Missing source value/state bindings','count':len(missing),'requirementIds':missing})
    names = {s.get('id') for s in art.get('previewStates',[])}
    expected = {'advanced','moustache-on','glasses-off','earring-off','eye-colours','facecode-load','facecode-save','facecode-invalid','cancel-restores-original'}
    missing_states = sorted(expected-names)
    if missing_states: gaps.append({'gap':'Missing manager advanced/control-flow art previews','ids':missing_states})
    for state in art.get('previewStates',[]):
        image = state.get('image',state.get('file'))
        if not image or not (root/image).is_file(): gaps.append({'gap':'Preview state has no existing design image','state':state.get('id')})
    if not art.get('compositionSamples'):
        gaps.append({'gap':'No real layered portrait composition samples; complete preset busts do not prove parameter support'})
    report = {'schema':'manager-face-independent-art-audit.v1','checkedAt':datetime.now(timezone.utc).isoformat(),'sourceSpec':spec,'artManifest':manifest.relative_to(root).as_posix() if manifest else None,'artManifestSha256':sha(manifest) if manifest else None,'existingPresetCount':len(list((root/'assets/portraits').glob('manager-??.png'))),'presetScope':'Complete illustrated busts only; no independent eye/nose/mouth/hair/clothing ownership layers in the eight preset files.','spriteValueSlots':spec['spriteValueSlots'],'uniqueSourceSpriteIds':spec['uniqueSourceSpriteIds'],'requiredBindings':len(spec['requirements']),'suppliedBindings':len(bindings),'complete':not gaps,'gaps':gaps,'unityValidated':False,'userArtAccepted':False}
    return report

def main():
    root=Path(__file__).resolve().parents[1]
    report=audit(root)
    for name,value in [('docs/MANAGER_FACE_REQUIREMENTS.json',report['sourceSpec']),('records/manager-customization-audit.json',report)]:
        (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k]for k in ['spriteValueSlots','uniqueSourceSpriteIds','requiredBindings','suppliedBindings','complete']}))

if __name__=='__main__':main()
