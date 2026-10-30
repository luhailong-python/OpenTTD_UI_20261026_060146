"""Brand checks consumed by the full art audit and compact resource index.

The canonical artwork remains in branding/yuntu-wanli.  This module never
rewrites artwork, provenance, layout records or historical production labels.
"""
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from io import BytesIO
import hashlib, json, re, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BRAND_FOLDER = "branding/yuntu-wanli"
BRAND_MANIFEST = BRAND_FOLDER + "/manifest.json"
RESOURCE_MANIFEST = "docs/asset-branding-manifest.json"
TITLE = "云途万里"
EXPECTED_FILES = {
    "logo-main.png", "logo-symbol.png", "logo-main-1024w.png",
    "logo-main-512w.png", "logo-symbol-512.png", "logo-symbol-256.png",
    "logo-symbol-128.png", "logo-symbol-64.png",
}
# Read before branding integration from the previously accepted resource index
# and actual PNGs. The digest includes relative paths as well as byte hashes.
WORLD_PIXEL_BASELINE = {
    "sourceIndex": "docs/ART_RESOURCE_INDEX.json",
    "sourceIndexSHA256BeforeBranding": "c59bb35f443833c01254374f3e440179f2d5a332f5d461feadda04c8f3e5e484",
    "formalCount": 11555,
    "formalPathAndSHA256Digest": "cf200aed97b73bcf1526f079bb031db029fdb939e90949f55c7352636e6712dc",
    "allWorldPNGCount": 11656,
    "allWorldPathAndSHA256Digest": "38efcfe673592125a5ecdef1bfd5451fb5b1d49f239fcd0f85535f35ac644bd7",
    "scope": "All existing assets/world PNGs, including vehicles and non-authoritative retained references; no source pack metadata rename required.",
}


def resolve_path(root, value, base):
    p = Path(value)
    if p.is_absolute():
        return p
    direct = root / p
    return direct if direct.exists() else base / p


def relative(root, path):
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def normalize_refs(root, value, base):
    if isinstance(value, list):
        return [normalize_refs(root, v, base) for v in value]
    if not isinstance(value, dict):
        return value
    out = {k: normalize_refs(root, v, base) for k, v in value.items()}
    for key in ("file", "record", "generationRecord"):
        if isinstance(value.get(key), str):
            out[key] = relative(root, resolve_path(root, value[key], base))
    return out


def normalize_row(root, row):
    out = normalize_refs(root, row, root / BRAND_FOLDER)
    if isinstance(out.get("image"), str):
        out["image"] = relative(root, resolve_path(root, out["image"], root / BRAND_FOLDER))
    out.setdefault("category", "branding")
    out.setdefault("border", [0, 0, 0, 0])
    out.setdefault("pivotUnity", [.5, .5])
    return out


def collect(a):
    """Register brand PNGs in Audit.assets, alongside all pre-existing packs."""
    a.brand_pack_paths = []
    path = a.root / BRAND_MANIFEST
    if not a.check(path.is_file(), "brand.canonical-manifest-exists", path):
        return
    package = a.read(path)
    a.brand_pack_paths.append(path)
    for field, native in (("nativeAssets", True), ("derivedExports", False)):
        for row in package.get(field, []):
            q = normalize_row(a.root, row)
            q["nativeModelGeneration"] = native
            a.register(q, BRAND_MANIFEST)
    central = a.root / RESOURCE_MANIFEST
    if a.check(central.is_file(), "brand.formal-resource-list-exists", central):
        rows = a.read(central)
        a.brand_pack_paths.append(central)
        if a.check(isinstance(rows, list), "brand.resource-schema-is-list", central):
            for row in rows:
                a.register(normalize_row(a.root, row), RESOURCE_MANIFEST)


def digest_rows(rows):
    return hashlib.sha256(json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored = 0
        self.text = []
        self.images = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))
        if tag in ("a", "link"):
            self.links.append(dict(attrs))
        if tag in ("script", "style"):
            self.ignored += 1
        elif not self.ignored:
            self.text.extend(value for key, value in attrs if key in ("title", "alt", "aria-label") and value)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.ignored:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.text.append(data)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def browser_evidence(a, name, required_inputs):
    path = a.file(name)
    if not a.check(path.is_file(), "brand.browser-report-exists", path):
        return {"record":name,"passed":False,"requiredInputs":sorted(required_inputs)}
    q = a.read(path)
    checks = q.get("checks", [])
    good = q.get("passed") is True and bool(checks) and not any(q.get(k) for k in ("failed","failures","errors","pageErrors","failedRequests"))
    good = good and all(c.get("passed") is True or c.get("level") == "OK" for c in checks)
    a.check(good, "brand.browser-all-recorded-checks-passed", path)
    snapshots = q.get("inputSnapshots", [])
    covered = set()
    for item in snapshots:
        file = item.get("file")
        if not a.check(bool(file) and bool(item.get("sha256")), "brand.browser-input-SHA256-recorded", path, item):
            good = False
            continue
        p = a.file(file)
        current = p.is_file() and a.sha(p) == item["sha256"]
        a.check(current, "brand.browser-current-input-SHA256", path, file)
        good = good and current
        covered.add(a.rel(p))
    complete = set(required_inputs) <= covered
    a.check(complete, "brand.browser-required-current-inputs-covered", path, {"missing":sorted(set(required_inputs)-covered)})
    return {"record":name,"sha256":a.sha(path),"passed":bool(good and complete),"requiredInputs":sorted(required_inputs),"snapshotCount":len(snapshots)}


def ui_visual_evidence(a, screens):
    """Require current, actual artwork review after the UI was re-rendered."""
    name="records/ui-branding-visual-review.json"
    path=a.file(name)
    required_ids={"01-main-menu","02-bootstrap","09-main-hud","123-about"}
    by_id={s["id"]:s for s in screens}
    a.check(required_ids<=set(by_id),"brand.UI-visual-four-primary-screens-exist",path,sorted(required_ids-set(by_id)))
    primary={by_id[i]["designPath"]for i in required_ids if i in by_id}
    screen_contacts=sorted((a.root/"previews").glob("screens-contact-*.jpg"))
    state_contacts=sorted((a.root/"previews").glob("states-contact-*.jpg"))
    a.check(len(screen_contacts)==13 and len(state_contacts)==12,"brand.UI-visual-all-current-contact-pages-exist",path,
            {"screenPages":len(screen_contacts),"statePages":len(state_contacts)})
    required=primary|{a.rel(p)for p in screen_contacts+state_contacts}|{"previews/overview.jpg"}
    if not a.check(path.is_file(),"brand.UI-actual-local-visual-record-exists",path):
        return {"record":name,"passed":False,"requiredCurrentFiles":sorted(required)}
    q=a.read(path)
    good=q.get("complete")is True and str(q.get("status","")).startswith("passed-local") and not q.get("openFindings")
    a.check(good,"brand.UI-actual-local-visual-passed-with-no-open-findings",path)
    rows=q.get("reviewedFiles",q.get("pages",q.get("items",[])))
    seen=set()
    a.check(bool(rows),"brand.UI-actual-reviewed-files-recorded",path)
    good=good and bool(rows)
    for item in rows:
        file=item.get("file",item.get("image"))
        declared=bool(file)and bool(item.get("sha256"))and str(item.get("status","")).startswith(("passed-local","locally-reviewed"))and bool(item.get("finding"))
        a.check(declared,"brand.UI-reviewed-file-status-SHA-and-finding",path,item)
        if not declared:
            good=False
            continue
        p=a.file(file)
        inside=p.resolve().is_relative_to(a.root)
        current=inside and p.is_file()and a.sha(p)==item["sha256"]
        a.check(current,"brand.UI-actual-reviewed-current-pixels",path,file)
        good=good and current
        seen.add(a.rel(p))
    complete=required<=seen
    a.check(complete,"brand.UI-visual-primary-screens-all-contacts-and-overview-covered",path,
            {"required":len(required),"reviewed":len(seen),"missing":sorted(required-seen)})
    return {"record":name,"sha256":a.sha(path),"passed":bool(good and complete),"reviewedCurrentFiles":len(seen),
            "requiredCurrentFiles":sorted(required),"openFindings":q.get("openFindings",[]),
            "scope":"Actual local review of current menu/bootstrap/HUD/about and all13screen/12state contacts plus overview; mechanical logo matching does not replace this review."}


def preview_contracts(a, screens, canonical):
    """Compare the current overview pixels and parse active flow/index content."""
    root = a.root
    by_id = {s["id"]:s for s in screens}
    selected = ["01-main-menu","09-main-hud","11-rail-build","43-buy-train","53-timetable","60-finances","69-small-map","93-servers","127-scenario-editor"]
    overview = root/"previews/overview.jpg"
    evidence = {"overview":None,"flow":None,"index":None}
    if a.check(overview.is_file(), "brand.current-overview-exists", overview):
        # An independent in-memory composition of the agreed presentation.
        # The actual JPEG must match; an old title or stale thumbnail cannot
        # pass merely because a current source manifest mentions the new name.
        expected = Image.new("RGB", (1920,1290), "#F1ECD8")
        d = ImageDraw.Draw(expected)
        fp = root/"assets/fonts/NotoSansSC-Variable.ttf"
        a.sha(fp)
        logo_path = root/BRAND_FOLDER/"logo-main.png"
        with Image.open(logo_path) as im:
            logo = im.convert("RGBA")
        logo.thumbnail((360,164), Image.Resampling.LANCZOS)
        expected.paste(logo, (24,0), logo)
        d.text((420,45), "整套 UI 美术总览", font=ImageFont.truetype(str(fp),35), fill="#164F45")
        sources = []
        for i, identifier in enumerate(selected):
            s = by_id[identifier]
            p = a.file(s["designPath"])
            with Image.open(p) as im:
                picture = im.copy()
            picture.thumbnail((615,346))
            x=(i%3)*640+12;y=(i//3)*370+175
            expected.paste(picture,(x,y))
            d.text((x,y+347),s["title"],font=ImageFont.truetype(str(fp),19),fill="#164F45")
            sources.append({"file":a.rel(p),"sha256":a.sha(p)})
        encoded=BytesIO();expected.save(encoded,format="JPEG",quality=93)
        expected_sha=hashlib.sha256(encoded.getvalue()).hexdigest()
        a.check(a.sha(overview)==expected_sha, "brand.actual-overview-formal-logo-current-screens-and-no-provisional-title", overview,
                {"expectedSHA256":expected_sha,"actualSHA256":a.sha(overview),"referenceSize":[1920,1290]})
        evidence["overview"]={"file":a.rel(overview),"sha256":a.sha(overview),"expectedSHA256":expected_sha,"sourceScreens":sources,
                              "title":"整套 UI 美术总览","logo":{"file":a.rel(logo_path),"sha256":a.sha(logo_path),"box":[24,0,360,164]},
                              "claim":"Actual full JPEG compared with an in-memory formal-title composition; no acceptance inferred from a file count."}
    flow=root/"previews/flow-map.svg"
    if a.check(flow.is_file(), "brand.current-flow-map-exists", flow):
        a.read_files[flow]=a.sha(flow)
        try:
            svg=ET.fromstring(flow.read_text(encoding="utf-8-sig"))
            text=["".join(n.itertext())for n in svg.iter()if n.tag.rsplit("}",1)[-1]=="text"]
            links=[n.get("href",n.get("{http://www.w3.org/1999/xlink}href"))for n in svg.iter()if n.tag.rsplit("}",1)[-1]=="a"]
            a.check(any(TITLE in t for t in text)and not any("暂名"in t for t in text), "brand.current-flow-formal-title-no-provisional-copy", flow)
            targets=[]
            for href in links:
                url=urlsplit(href or "");target=flow.parent/unquote(url.path)
                good=not url.scheme and target.resolve()==(root/"index.html").resolve()and url.fragment in by_id
                a.check(good,"brand.current-flow-valid-formal-gallery-node",flow,href);targets.append(url.fragment)
            a.check(len(links)==12 and len(set(targets))==12,"brand.current-flow-twelve-existing-screen-nodes",flow)
            evidence["flow"]={"file":a.rel(flow),"sha256":a.sha(flow),"visibleText":text,"screenNodes":targets}
        except ET.ParseError as error:
            a.check(False,"brand.current-flow-valid-SVG",flow,str(error))
    index=root/"index.html"
    if a.check(index.is_file(),"brand.main-index-exists",index):
        parser=VisibleHTML();parser.feed(index.read_text(encoding="utf-8-sig"));a.read_files[index]=a.sha(index)
        images=[]
        for row in parser.images:
            url=urlsplit(row.get("src",""))
            if not url.scheme:
                images.append(a.rel(index.parent/unquote(url.path)))
        main_files={BRAND_FOLDER+"/"+n for n in EXPECTED_FILES if n.startswith("logo-main")}
        a.check(bool(set(images)&main_files),"brand.main-index-actual-title-logo-img-reference",index,images)
        a.check(any(unquote(urlsplit(row.get("href","")).path)=="previews/branding/index.html"for row in parser.links),
                "brand.main-index-links-formal-brand-gallery",index)
        evidence["index"]={"file":a.rel(index),"sha256":a.sha(index),"actualLogoImages":sorted(set(images)&canonical)}
    return evidence


def audit(a):
    before_fail = a.counts["FAIL"]
    path = a.root / BRAND_MANIFEST
    if not path.is_file():
        a.check(False, "brand.required-for-full-game-delivery", path)
        return {"complete": False}
    package = a.read(path)
    a.check(package.get("name") == TITLE, "brand.exact-selected-title", path)
    native = package.get("nativeAssets", [])
    derived = package.get("derivedExports", [])
    names = [r.get("file") for r in native + derived]
    a.check(set(names) == EXPECTED_FILES and len(names) == 8 and len(native) == 2 and len(derived) == 6,
            "brand.two-native-six-derived-files", path, names)
    canonical = {BRAND_FOLDER + "/" + n for n in EXPECTED_FILES}
    a.check({n for n in a.assets if n.startswith(BRAND_FOLDER + "/")} == canonical,
            "brand.included-in-complete-formal-assets", path)
    central_path = a.root / RESOURCE_MANIFEST
    rows = a.read(central_path) if central_path.is_file() else []
    a.check(isinstance(rows, list) and len(rows) == 8, "brand.eight-central-formal-resources", central_path)
    registry = {}
    for raw in rows if isinstance(rows, list) else []:
        q = normalize_row(a.root, raw)
        name = q.get("file", q.get("image"))
        registry[q.get("id", name)] = q
        a.check(name in canonical and q.get("role") and raw.get("border") == [0, 0, 0, 0]
                and len(raw.get("pivotUnity", [])) == 2 and all(isinstance(n,(int,float))and 0<=n<=1 for n in raw.get("pivotUnity", []))
                and isinstance(raw.get("width"),int) and raw["width"]>0 and isinstance(raw.get("height"),int) and raw["height"]>0
                and bool(raw.get("generationRecord")),
                "brand.explicit-import-role-pivot-border-generation", central_path, q.get("id"))
        if name:
            a.check(any(origin == RESOURCE_MANIFEST for _, origin in a.assets.get(name, [])),
                    "brand.central-resource-registered", central_path, name)
    native_names = {r["file"] for r in native}
    for row in native + derived:
        p = a.root / BRAND_FOLDER / row["file"]
        if not a.check(p.is_file(), "brand.png-exists", path, row["file"]):
            continue
        info = a.info(p)
        a.check(info["mode"] == "RGBA" and info["alphaExtrema"] == [0, 255], "brand.real-transparent-native-or-export", p, info)
        a.check(a.sha(p) == row.get("sha256"), "brand.canonical-current-SHA256", p)
        if row["file"] in native_names:
            gp = resolve_path(a.root, row["generationRecord"], p.parent)
            if not a.check(gp.is_file(), "brand.actual-generation-record", p):
                continue
            generation = a.read(gp)
            call_name = generation.get("evidence", {}).get("callRecord")
            cp = resolve_path(a.root, call_name, p.parent) if call_name else p.parent / "__missing__"
            if a.check(cp.is_file(), "brand.actual-call-record", gp):
                call = a.read(cp)
                a.check(call.get("submittedParameters") == generation.get("submittedParameters"), "brand.actual-submission-matches-call", gp)
                a.check(call.get("finishedAt") == generation.get("generatedAt") and bool(call.get("startedAt")), "brand.actual-generation-time-from-call", gp)
                a.check(call.get("returnedFields") == generation.get("evidence", {}).get("returnedFields")
                        and call.get("returnedPath") == generation.get("evidence", {}).get("returnedPath"),
                        "brand.actual-returned-evidence-matches-call", gp)
                a.check(call.get("actualModel") is None and call.get("actualQuality") is None
                        and generation.get("actualModel") is None and generation.get("actualQuality") is None,
                        "brand.no-invented-actual-model-or-quality", gp)
            submitted = generation.get("submittedParameters", {})
            references = generation.get("references", [])
            a.check([r.get("path") for r in references] == submitted.get("referenced_image_paths"), "brand.actual-reference-order-and-paths", gp)
        else:
            refs = row.get("derivedFrom", [])
            a.check(len(refs) == 1 and refs[0].get("file") in native_names, "brand.export-from-native-parent", p)
            if len(refs) == 1 and refs[0].get("file") in native_names:
                source_path = p.parent / refs[0]["file"]
                with Image.open(source_path) as im:
                    source_size = im.size
                    expected = im.convert("RGBA").resize((row["width"], row["height"]), Image.Resampling.LANCZOS)
                with Image.open(p) as im:
                    a.check(im.convert("RGBA").tobytes() == expected.tobytes(), "brand.exact-downsample-no-repaint", p)
                a.check(row["width"] <= source_size[0] and row["height"] <= source_size[1], "brand.export-no-native-upscale", p)
    brand_generations = [r for r in a.master_records if r["record"].startswith(BRAND_FOLDER + "/")]
    a.check(len(brand_generations) == 2 and {r["file"] for r in brand_generations} == {BRAND_FOLDER+"/"+n for n in native_names},
            "brand.two-native-records-in-complete-generation-audit", path)
    a.check(len(a.master_records) == 91 and sum(r["retained"] for r in a.master_records) == 90,
            "brand.complete-generation-record-count-adds-two", detail={"records":len(a.master_records),"retained":sum(r["retained"] for r in a.master_records)})
    a.check(len(a.assets) == 12212 and a.ui_resource_count == 657, "brand.full-index-adds-exactly-eight-PNGs", detail={"formal":len(a.assets), "uiIncludingBrand":a.ui_resource_count})
    formal_world = [(name, a.sha(a.file(name))) for name in a.assets if name.startswith("assets/world/")]
    all_world = [(a.rel(p), a.sha(p)) for p in sorted((a.root / "assets/world").rglob("*.png"))]
    a.check(len(formal_world) == WORLD_PIXEL_BASELINE["formalCount"] and digest_rows(formal_world) == WORLD_PIXEL_BASELINE["formalPathAndSHA256Digest"],
            "brand.all-existing-formal-world-vehicle-PNGs-unchanged", detail={"count":len(formal_world), "digest":digest_rows(formal_world)})
    a.check(len(all_world) == WORLD_PIXEL_BASELINE["allWorldPNGCount"] and digest_rows(all_world) == WORLD_PIXEL_BASELINE["allWorldPathAndSHA256Digest"],
            "brand.all-existing-world-PNGs-including-legacy-unchanged", detail={"count":len(all_world), "digest":digest_rows(all_world)})
    active_metadata = ["docs/UI_MASTER_MANIFEST.json", "docs/screen-catalog.json", "docs/ASSET_MASTER_MANIFEST.json",
                       "docs/WORLD_ASSET_COVERAGE.json", "docs/WORLD_ASSET_MANIFEST.json", "docs/WORLD_DELIVERY_COVERAGE.json",
                       "docs/VEHICLE_PRODUCTION_CONTRACT.json", "DELIVERY.json"]
    for name in active_metadata:
        p = a.file(name)
        if not a.check(p.is_file(), "brand.current-delivery-metadata-exists", p):
            continue
        q = a.read(p)
        if isinstance(q, dict) and "project" in q:
            a.check(q["project"] == TITLE, "brand.active-project-title", p, q["project"])
    ui = a.read(a.root / "docs/UI_MASTER_MANIFEST.json")
    screens = ui.get("screens", [])
    a.check(len(screens) == 149 and sum(len(s.get("states", [])) for s in screens) == 227,
            "brand.exact149-screens227-states-retained")
    a.check(len(a.read(a.root / "docs/WORLD_ASSET_COVERAGE.json").get("items", [])) == 550, "brand.world550-requirements-retained")
    placement_evidence = []
    for s in screens:
        display = {k:s.get(k) for k in ("title", "subtitle", "tabs", "columns", "rows", "details", "actions", "states")}
        a.check(not any("暂名" in t for t in strings(display)), "brand.no-provisional-visible-screen-copy", detail=s.get("id"))
        variants = [(s["id"], "docs/layouts/" + s["id"] + ".json", s.get("designPath"))]
        variants += [(s["id"]+"--"+st["id"], "docs/layouts/states/"+s["id"]+"--"+st["id"]+".json", st.get("previewPath")) for st in s.get("states", [])]
        for identifier, layout_name, image_name in variants:
            lp = a.file(layout_name)
            if not a.check(lp.is_file(), "brand.actual-layout-record-exists", lp):
                continue
            layout = a.read(lp)
            a.check(not any("暂名" in str(t.get("text", "")) for t in layout.get("textRegions", [])), "brand.no-provisional-rendered-copy", lp)
            for placement in layout.get("spritePlacements", []):
                key = placement.get("asset", placement.get("resourceId", placement.get("file")))
                row = registry.get(key)
                if row is None and isinstance(key, str) and key.startswith(BRAND_FOLDER + "/"):
                    row = next((q for q in registry.values() if q.get("file") == key), None)
                if row is None:
                    continue
                file = row.get("file", row.get("image"));rect = placement.get("rectTopLeftXYWH", [])
                if not a.check(len(rect) == 4 and all(isinstance(n, (int,float)) for n in rect) and min(rect[2:]) > 0, "brand.actual-layout-logo-rect", lp, placement):
                    continue
                x,y,w,h = map(int, rect);canvas=layout.get("referenceResolution", [])
                source = a.file(file);size=a.info(source)["size"]
                a.check(len(canvas)==2 and min(x,y)>=0 and x+w<=canvas[0] and y+h<=canvas[1], "brand.logo-placement-in-canvas", lp, rect)
                a.check(abs((w/h)/(size[0]/size[1])-1)<.015, "brand.logo-placement-uniform-scale", lp, rect)
                ip = a.file(image_name) if image_name else lp.parent/"__missing__"
                match = 0.;sample_count = 0
                if a.check(ip.is_file(), "brand.actual-composite-for-logo-placement", lp, image_name):
                    with Image.open(source)as im:logo=np.asarray(im.convert("RGBA").resize((w,h), Image.Resampling.LANCZOS))
                    with Image.open(ip)as im:crop=np.asarray(im.convert("RGB").crop((x,y,x+w,y+h)))
                    opaque=logo[...,3]>=250;sample_count=int(opaque.sum())
                    if sample_count:
                        delta=np.max(np.abs(crop.astype(int)-logo[...,:3].astype(int)),axis=2)
                        match=float(np.mean(delta[opaque]<=8))
                    a.check(sample_count>=8 and match>=.995, "brand.actual-PNG-has-placed-native-logo-pixels", ip, {"layout":layout_name,"asset":key,"opaqueSamples":sample_count,"matchingFraction":match})
                    gp=Path(str(ip)+".generation.json")
                    if a.check(gp.is_file(), "brand.composite-provenance-record-exists", ip):
                        generation=a.read(gp);parents=list(a.source_refs(generation.get("derivedFrom", [])))
                        a.check(any(p.get("file") in (file,RESOURCE_MANIFEST) for p in parents), "brand.composite-record-references-brand-input", gp, file)
                placement_evidence.append({"layout":layout_name,"screen":identifier,"role":row.get("role"),"file":file,"rectTopLeftXYWH":rect,"opaqueSamples":sample_count,"matchingFraction":match})
    a.check(any(p["screen"]=="01-main-menu" and p["role"]=="main-title" and p["rectTopLeftXYWH"][2]>=480 for p in placement_evidence),
            "brand.main-menu-actual-full-title-logo")
    a.check(any(p["role"]=="symbol" and p["screen"]!="01-main-menu" for p in placement_evidence), "brand.related-page-actual-symbol")
    presentation = preview_contracts(a, screens, canonical)
    html_files = [a.root/"index.html"] + sorted((a.root/"previews").rglob("*.html"))
    for hp in html_files:
        if not hp.is_file():
            continue
        parser=VisibleHTML();parser.feed(hp.read_text(encoding="utf-8-sig"));a.read_files[hp]=a.sha(hp)
        a.check(not any("暂名" in t for t in parser.text), "brand.no-provisional-active-HTML-visible-copy", hp)
    index_path = a.root / "docs/ART_RESOURCE_INDEX.json"
    if a.check(index_path.is_file(), "brand.complete-resource-index-exists", index_path):
        index = a.read(index_path);assets = index.get("assets", [])
        a.check(index.get("project") == TITLE and index.get("formalPNGCount") == 12212
                and len(assets) == 12212 and {r.get("file") for r in assets} == set(a.assets),
                "brand.complete-index-current-all-formal-PNGs", index_path)
        indexed = [r for r in assets if r.get("file") in canonical]
        a.check(len(indexed) == 8 and sum(r.get("nativeModelGeneration") is True for r in indexed) == 2,
                "brand.complete-index-eight-with-two-native", index_path)
        for r in indexed:
            f = r["file"]
            a.check(r.get("sha256") == a.sha(a.file(f)) and r.get("role") and r.get("generationRecord")
                    and "actualModel" in r and r["actualModel"] is None and "actualQuality" in r and r["actualQuality"] is None,
                    "brand.complete-index-current-brand-import-and-evidence", index_path, f)
        evidence = index.get("brandGenerationEvidence", [])
        a.check({r.get("record") for r in evidence} == {r["record"] for r in brand_generations}
                and len(evidence) == 2, "brand.complete-index-actual-native-generation-records", index_path)
        for r in evidence:
            original = next((q for q in brand_generations if q["record"] == r.get("record")), None)
            a.check(original is not None and r == original, "brand.complete-index-literal-prompt-reference-SHA-and-generation-fields", index_path, r.get("record"))
    historical=[]
    for pp in a.pack_paths:
        q=a.read(pp)
        if isinstance(q.get("project"),str) and "暂名" in q["project"]:
            historical.append({"file":a.rel(pp),"project":q["project"],"classification":"historical production label; source pack preserved unchanged"})
    review = package.get("localVisualReview", {})
    rp=resolve_path(a.root,review.get("record","__missing__"),path.parent)
    if a.check(rp.is_file(), "brand.current-native-local-visual-record", path):
        v=a.read(rp)
        a.check(review.get("passed") is True and a.sha(rp)==review.get("sha256") and str(v.get("status", "")).startswith("passed-local"), "brand.native-local-visual-passed-current", rp)
        for item in v.get("reviewedFiles", []):
            ip=resolve_path(a.root,item["file"],path.parent)
            a.check(ip.is_file()and a.sha(ip)==item.get("sha256"), "brand.native-reviewed-current-pixels", rp,item["file"])
    browser = [browser_evidence(a,"records/browser-validation.json",{"index.html"}),
               browser_evidence(a,"records/brand-gallery-browser-validation.json",canonical|{BRAND_MANIFEST,RESOURCE_MANIFEST,"previews/branding/index.html"})]
    ui_visual=ui_visual_evidence(a,screens)
    upstream_failures=[issue for issue in a.issues if issue.get("level")=="FAIL"and issue.get("file","").startswith(BRAND_FOLDER+"/")and not issue.get("code","").startswith("brand.")]
    brand_checks=getattr(a,"brand_checks",[])
    complete=a.counts["FAIL"]==before_fail and not upstream_failures and all(c["passed"]for c in brand_checks)and all(b["passed"]for b in browser)and ui_visual["passed"]
    inputs={BRAND_MANIFEST,RESOURCE_MANIFEST,"docs/UI_MASTER_MANIFEST.json","docs/ASSET_MASTER_MANIFEST.json","docs/ART_RESOURCE_INDEX.json",
            "docs/screen-catalog.json","index.html","previews/overview.jpg","previews/flow-map.svg","previews/branding/index.html",
            "records/ui-branding-visual-review.json"}|canonical
    snapshots=[{"file":n,"sha256":a.sha(a.file(n))}for n in sorted(inputs)if a.file(n).is_file()]
    return {"schema":"cloud-route.brand-integration-validation.v1","checkedAt":datetime.now(timezone.utc).isoformat(),
            "complete":complete,"passed":complete,"passedChecks":sum(c["passed"]for c in brand_checks),
            "failed":sum(not c["passed"]for c in brand_checks)+len(upstream_failures),"checks":brand_checks,"upstreamBrandFailures":upstream_failures,
            "canonicalManifest":BRAND_MANIFEST,"formalResourceManifest":RESOURCE_MANIFEST,
            "title":TITLE,"formalPNGs":len(canonical & set(a.assets)),"nativePNGs":len(native),"derivedPNGs":len(derived),
            "currentPresentation":presentation,"browserEvidence":browser,"uiBrandingVisualReview":ui_visual,"inputSnapshots":snapshots,
            "actualLayoutLogoPlacements":placement_evidence,"worldPixelPreservationBaseline":WORLD_PIXEL_BASELINE,
            "nativeGenerationRecords":[{"file":r["record"],"sha256":r["recordSHA256"]}for r in brand_generations],
            "currentWorldPixelDigest":digest_rows(all_world),"historicalSourcePackLabelsAllowed":historical,
            "historicalLabelRule":"Active delivery titles/contracts and visible previews use the formal name. Historical provenance, actual submitted prompts and source pack production labels remain intact.",
            "userArtAccepted":False,"unityValidated":False}
