"""Independent, read-only audit of production art; writes reports, never assets.

Run with the bundled Python/Pillow runtime.  It deliberately distinguishes a
fresh mechanical snapshot, upstream mapping, human art approval and Unity QA.
No files under the F: reference library are changed.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
from PIL import Image, ImageChops, ImageOps
from audit_manager_faces import audit as audit_manager_faces

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value)


class Audit:
    def __init__(self, root):
        self.root = root.resolve()
        self.started = datetime.now(timezone.utc).isoformat()
        self.counts = Counter()
        self.issues = []
        self.hashes = {}
        self.image_info = {}
        self.read_files = {}
        self.assets = defaultdict(list)
        self.master_records = []
        self.coverage = {}
        self.animation_specs = []

    def rel(self, path):
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def file(self, value):
        p = Path(value)
        return p if p.is_absolute() else self.root / p

    def sha(self, path):
        path = Path(path)
        if path not in self.hashes:
            self.hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return self.hashes[path]

    def read(self, path):
        path = Path(path)
        value = load(path)
        self.read_files[path] = self.sha(path)
        return value

    def check(self, condition, code, file=None, detail=None, level="FAIL"):
        self.counts["passed" if condition else level] += 1
        if not condition:
            row = {"level": level, "code": code}
            if file is not None:
                row["file"] = self.rel(file)
            if detail is not None:
                row["detail"] = detail
            self.issues.append(row)
        return bool(condition)

    def info(self, path):
        if path not in self.image_info:
            with Image.open(path) as im:
                alpha = im.getchannel("A") if "A" in im.getbands() else None
                self.image_info[path] = {
                    "size": list(im.size), "mode": im.mode,
                    "alphaExtrema": list(alpha.getextrema()) if alpha else None,
                    "alphaBBox": list(alpha.getbbox()) if alpha and alpha.getbbox() else None,
                }
        return self.image_info[path]

    def register(self, row, origin, inherited=None):
        if not isinstance(row, dict):
            return
        if row.get("authoritative") is False:
            return
        q = {**(inherited or {}), **row}
        name = q.get("image", q.get("file"))
        if isinstance(name, str) and name.lower().endswith(".png"):
            self.assets[self.rel(self.file(name))].append((q, origin))

    def collect(self):
        ui = self.read(self.root / "docs/ASSET_MASTER_MANIFEST.json")
        for row in ui["resources"] + ui["backgrounds"]:
            self.register(row, "docs/ASSET_MASTER_MANIFEST.json")
        portrait_packs = sorted((self.root / "assets/portraits").rglob("manifest.json"))
        central = self.root / "docs/MANAGER_FACE_ART_MANIFEST.json"
        if central.is_file():
            portrait_packs.append(central)
        for path in portrait_packs:
            q = self.read(path)
            for row in q.get("assets", []):
                self.register(row, self.rel(path))
        self.portrait_pack_paths = portrait_packs
        # Cursor and window-status packs were added after the original UI kit.
        # Register their formal PNGs as well as their source-timed animations.
        self.supplemental_pack_paths = []
        for folder in ("assets/common", "assets/icons", "assets/cargo"):
            for path in sorted((self.root / folder).rglob("manifest.json")):
                q = self.read(path)
                self.supplemental_pack_paths.append(path)
                for row in q.get("assets", []):
                    self.register(row, self.rel(path))
                for animation in q.get("animations", []):
                    self.animation_specs.append((animation, path))
        packs = sorted((self.root / "assets/world").rglob("manifest.json"))
        for path in packs:
            q = self.read(path)
            origin = self.rel(path)
            for item in q.get("qa", []):
                if isinstance(item, dict) and item.get("level") in ("WARN", "FAIL"):
                    self.check(False, "pack." + item.get("id", "reported-issue"), path, item, level=item["level"])
            for animation in q.get("animations", []):
                self.animation_specs.append((animation, path))
            for row in q.get("assets", []):
                self.register(row, origin)
            for row in q.get("frames", []):
                self.register(row, origin, {k: q[k] for k in ("pivot", "emitterPx") if k in q})
            for sprite in q.get("sprites", []):
                common = {k: sprite[k] for k in ("canvas", "pivot", "sources", "operations") if k in sprite}
                if sprite.get("body"):
                    self.register({**sprite, "file": sprite["body"]}, origin, common)
                for state in sprite.get("states", []):
                    self.register(state, origin, common)
        self.pack_paths = packs
        self.ui_resource_count = sum(not name.startswith("assets/world/") for name in self.assets)
        self.fonts = ui.get("fonts", [])

    def master_audit(self):
        paths = list((self.root / "source-art").rglob("*.generation.json"))
        paths += list((self.root / "assets").rglob("*.generation.json"))
        for path in sorted(paths):
            q = self.read(path)
            if q.get("tool") not in ("image_gen.imagegen", "image_gen"):
                continue
            image_path = self.file(q.get("file", "__missing__"))
            retired = q.get("taskLocalImageRetained") is False
            if not retired:
                self.check(image_path.is_file(), "master.png.exists", path, q.get("file"))
            else:
                self.check(bool(q.get("acceptance")), "master.retired-status-recorded", path)
            if image_path.is_file():
                self.check(self.sha(image_path) == q.get("sha256"), "master.png.sha256", path)
                size = self.info(image_path)["size"]
                self.check(size == [q.get("width"), q.get("height")], "master.native-size", path, size)
            submitted = q.get("submittedParameters", {})
            prompt = submitted.get("prompt")
            literal = isinstance(prompt, str) and len(prompt) > 80 and not re.fullmatch(r"[^\n]*\.txt", prompt.strip())
            self.check(literal, "master.literal-submitted-prompt", path)
            self.check(str(prompt).strip() == str(q.get("prompt")).strip(), "master.prompt-copies-match", path)
            prompt_file = q.get("promptFile")
            self.check(bool(prompt_file), "master.prompt-file-recorded", path)
            if prompt_file:
                p = self.file(prompt_file)
                self.check(p.is_file(), "master.prompt-file-exists", path, prompt_file)
                if p.is_file():
                    self.check(p.read_text(encoding="utf-8-sig").strip() == str(prompt).replace("\r\n", "\n").strip(), "master.prompt-file-matches", path)
            self.check("actualModel" in q and q["actualModel"] is None, "master.actual-model-undisclosed", path)
            self.check("actualQuality" in q and q["actualQuality"] is None, "master.actual-quality-undisclosed", path)
            self.check(submitted.get("model") is None and submitted.get("quality") is None, "master.selector-not-invented", path)
            self.check(bool(q.get("unverifiedReason")), "master.undisclosed-reason", path)
            self.check(bool(q.get("configSnapshot", {}).get("model")) and bool(q.get("configSnapshot", {}).get("quality")), "master.config-goal", path)
            self.check(bool(q.get("generatedAt")) and bool(q.get("generatedAtEvidence")), "master.time-and-evidence", path)
            self.check(bool(q.get("evidence", {}).get("returnedFields")), "master.returned-evidence", path)
            refs = q.get("references", [])
            submitted_refs = submitted.get("referenced_image_paths", [])
            ref_names = [str(x.get("path", "")).replace("\\", "/") for x in refs]
            for suffix in ("designs/mail-ui-v1/01-mail-event.png", "designs/team-ui-v2/team-ui-v2.png"):
                self.check(any(n.endswith(suffix) for n in ref_names) and any(str(n).replace("\\", "/").endswith(suffix) for n in submitted_refs), "master.actual-style-reference", path, suffix)
            for reference in refs:
                p = self.file(reference.get("path", "__missing__"))
                self.check(p.is_file(), "master.reference-exists", path, str(p))
                if p.is_file():
                    self.check(self.sha(p) == reference.get("sha256"), "master.reference-hash", path, str(p))
            self.master_records.append({"record": self.rel(path), "file": q.get("file"), "sha256": q.get("sha256"), "nativeSize": [q.get("width"), q.get("height")], "actualModel": q.get("actualModel"), "actualQuality": q.get("actualQuality"), "promptFile": prompt_file, "retained": not retired, "retirementReason": q.get("acceptance") if retired else None})

    def source_refs(self, value):
        if isinstance(value, dict):
            if isinstance(value.get("file"), str) and value.get("sha256"):
                yield value
            for child in value.values():
                yield from self.source_refs(child)
        elif isinstance(value, list):
            for child in value:
                yield from self.source_refs(child)

    def formal_audit(self):
        for name, candidates in sorted(self.assets.items()):
            path = self.file(name)
            if not self.check(path.is_file(), "formal.exists", path):
                continue
            info = self.info(path)
            actual_hash = self.sha(path)
            sizes = []
            hashes = set()
            anchors = []
            provenance = []
            for q, origin in candidates:
                expected = q.get("canvas", q.get("nativeSize"))
                if "width" in q and "height" in q:
                    expected = [q["width"], q["height"]]
                if expected:
                    sizes.append(expected)
                if q.get("sha256"):
                    hashes.add(q["sha256"])
                if q.get("anchorPx") is not None:
                    anchors.append(q["anchorPx"])
                elif q.get("pivot") is not None:
                    p = q["pivot"]
                    anchors.append([p[0] * info["size"][0], (1 - p[1]) * info["size"][1]])
                for key in ("derivedFrom", "sources"):
                    if q.get(key):
                        provenance.append(q[key])
                if q.get("source") and isinstance(q.get("source"), str):
                    provenance.append({"file": q["source"], "sha256": q.get("sourceSha256")})
                border = q.get("border")
                if border is not None:
                    w, h = info["size"]
                    self.check(len(border) == 4 and min(border) >= 0 and border[0] + border[2] < w and border[1] + border[3] < h, "formal.nine-slice-border", path, border)
            # Native backgrounds have a generation record as their formal source evidence.
            for suffix in (".derivation.json", ".generation.json"):
                sidecar = Path(str(path) + suffix)
                if sidecar.is_file():
                    q = self.read(sidecar)
                    if q.get("sha256"):
                        hashes.add(q["sha256"])
                    if q.get("width") and q.get("height"):
                        sizes.append([q["width"], q["height"]])
                    for key in ("derivedFrom", "sources"):
                        if q.get(key):
                            provenance.append(q[key])
                    if q.get("tool") == "image_gen.imagegen":
                        provenance.append({"nativeGenerationRecord": self.rel(sidecar)})
            self.check(bool(sizes), "formal.declared-size", path)
            self.check(all(list(s) == info["size"] for s in sizes), "formal.size", path, {"actual": info["size"], "declared": sizes})
            self.check(bool(hashes), "formal.declared-hash", path)
            self.check(hashes == {actual_hash}, "formal.sha256", path, list(hashes))
            world = name.startswith("assets/world/")
            if world:
                self.check(info["mode"] == "RGBA" and info["alphaExtrema"] and info["alphaExtrema"][0] == 0 and info["alphaExtrema"][1] > 0, "formal.real-transparent-alpha", path, info)
                self.check(bool(anchors), "formal.declared-anchor", path)
            else:
                # Some paper textures and the two backgrounds are deliberately opaque.
                declared_min = [q.get("alphaMin") for q, _ in candidates if "alphaMin" in q]
                if declared_min and min(declared_min) == 0:
                    self.check(bool(info["alphaExtrema"]) and info["alphaExtrema"][0] == 0, "formal.ui-alpha", path)
            w, h = info["size"]
            self.check(all(len(a) == 2 and 0 <= a[0] <= w and 0 <= a[1] <= h for a in anchors), "formal.anchor-in-canvas", path, anchors)
            if anchors:
                self.check(all(abs(a[0] - anchors[0][0]) < 0.01 and abs(a[1] - anchors[0][1]) < 0.01 for a in anchors), "formal.consistent-declared-anchor", path, anchors)
            self.check(bool(provenance), "formal.provenance-present", path)
            for source in self.source_refs(provenance):
                p = self.file(source["file"])
                self.check(p.is_file(), "formal.source-file-exists", path, source["file"])
                if p.is_file():
                    self.check(self.sha(p) == source["sha256"], "formal.source-sha256", path, source["file"])

    def ui_audit(self):
        q = self.read(self.root / "docs/UI_MASTER_MANIFEST.json")
        screens = q["screens"]
        self.screen_count = len(screens)
        self.state_count = sum(len(s.get("states", [])) for s in screens)
        self.feature_count = len({f for s in screens for f in s.get("upstreamFeatureIds", [])})
        catalog = self.read(self.root / "docs/screen-catalog.json")
        expected = {s["id"]: {x["id"] for x in s.get("states", [])} for s in catalog}
        observed = {s["id"]: {x["id"] for x in s.get("states", [])} for s in screens}
        self.check(observed == expected, "ui.current-catalog-screen-state-coverage")
        self.check(len(screens) >= 149 and self.state_count >= 227, "ui.baseline-149-screens-227-states-retained")
        for s in screens:
            for key, expected in (("designPath", [1920, 1080]), ("thumbnailPath", None)):
                p = self.file(s[key])
                self.check(p.is_file(), "ui.image-exists", p)
                if p.is_file() and expected:
                    self.check(self.info(p)["size"] == expected, "ui.screen-size", p)
                    self.ui_image_record(p)
            for state in s.get("states", []):
                p = self.file(state["previewPath"])
                self.check(p.is_file(), "ui.state-exists", p)
                if p.is_file():
                    self.check(self.info(p)["size"] == [960, 600], "ui.state-size", p)
                    self.ui_image_record(p)
        legacy = self.read(self.root / "records/final-validation.json")
        self.check(legacy.get("checkCount") == 4279 and legacy.get("passed") is True and legacy.get("failures") == [], "ui.existing-4279-checks")

    def ui_image_record(self, path):
        record = Path(str(path) + ".generation.json")
        if self.check(record.is_file(), "ui.composite-record", path):
            q = self.read(record)
            self.check(self.sha(path) == q.get("sha256"), "ui.composite-current-hash", path)
            self.check(q.get("nativeModelGeneration") is False and q.get("route") == "deterministic-composite", "ui.composite-not-native-generation", path)
            for source in self.source_refs(q.get("derivedFrom", [])):
                p = self.file(source["file"])
                self.check(p.is_file(), "ui.composite-source-exists", path, source["file"])
                if p.is_file():
                    self.check(self.sha(p) == source["sha256"], "ui.composite-source-hash", path, source["file"])

    def navigation_audit(self):
        for name in ("index.html", "previews/world/index.html", "previews/vehicles/index.html", "previews/world/industry-assembly/index.html", "previews/pointers/index.html", "previews/manager-customization/index.html", "previews/micro-ui/index.html", "previews/road-oneway/index.html", "previews/airport-ui/index.html", "previews/roadside/index.html", "previews/rail-reservation/index.html", "previews/fence-adapter/index.html", "previews/world/field-stages/index.html", "previews/world/bridge-railtypes/index.html", "previews/world/shore-geometry/index.html", "previews/world/rocks-overlay/index.html"):
            path = self.file(name)
            if not self.check(path.is_file(), "preview.entry-exists", path):
                continue
            parser = Links()
            self.read_files[path] = self.sha(path)
            parser.feed(path.read_text(encoding="utf-8"))
            for value in parser.links:
                url = urlsplit(value)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = path.parent / unquote(url.path)
                self.check(target.exists(), "preview.local-link-exists", path, value)
        for name in ("README.md", "docs/ACCEPTANCE.md", "docs/UNITY_IMPORT.md", "docs/SOURCES.md", "docs/PROJECT_ASSOCIATIONS.md", "docs/FULL_GAME_ART_DELIVERY.md", "docs/image-reference-associations.md"):
            p = self.file(name)
            if not self.check(p.is_file(), "delivery.document-exists", p):
                continue
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
                target = target.strip("<>").split("#")[0]
                if not target or urlsplit(target).scheme:
                    continue
                self.check((p.parent / unquote(target)).exists(), "delivery.document-local-link", p, target)

    def special_audit(self):
        for clip, manifest in self.animation_specs:
            frames = clip.get("frames", [])
            dims = []
            for frame in frames:
                name = frame if isinstance(frame, str) else frame.get("file", frame.get("image"))
                if not name:
                    self.check(False, "animation.explicit-frame-path", manifest, clip.get("id"))
                    continue
                p = self.file(name)
                if not p.is_file() and (manifest.parent / name).is_file():
                    p = manifest.parent / name
                if self.check(p.is_file(), "animation.frame-exists", manifest, name):
                    size = self.info(p)["size"]
                    dims.append(size)
                    if clip.get("frameSize"):
                        self.check(size == clip["frameSize"], "animation.declared-frame-size", p, clip.get("id"))
                    fixed = clip.get("fixedAnchorPx")
                    if fixed:
                        row = self.assets.get(self.rel(p), [])
                        known = [a.get("anchorPx") for a, _ in row if a.get("anchorPx")]
                        self.check(bool(known) and all(all(abs(x - y) < 0.01 for x, y in zip(a, fixed)) for a in known), "animation.fixed-anchor", p, clip.get("id"))
            self.check(bool(dims) and all(d == dims[0] for d in dims), "animation.shared-canvas", manifest, clip.get("id"))
            duration = clip.get("durationsMs")
            if duration is not None:
                self.check(len(duration) == len(frames) and all(v > 0 for v in duration), "animation.explicit-timing", manifest, clip.get("id"))
        for font in self.fonts:
            p = self.file(font["file"])
            self.check(p.is_file(), "font.file-exists", p)
            if p.is_file():
                self.check(self.sha(p) == font["sha256"], "font.sha256", p)
            self.check(self.file(font["licenseFile"]).is_file(), "font.license-bundled", p)
        snapshots = self.root / "records/reference-rules-snapshot.json"
        if snapshots.is_file():
            for row in self.read(snapshots).get("files", []):
                p = self.file(row.get("snapshot", "__missing__"))
                self.check(p.is_file(), "reference.rule-snapshot-exists", p)
                if p.is_file():
                    self.check(self.sha(p) == row["sha256"], "reference.rule-snapshot-hash", p)
        for name in ("01-mail-event.png", "team-ui-v2.png"):
            p = self.root / "docs/reference-images" / name
            self.check(p.is_file(), "reference.primary-image-bundled", p)
        self.reassembly_groups = 0
        for name in ("assets/world/houses/manifest.json", "assets/world/infrastructure/object-states/manifest.json"):
            path = self.root / name
            if not path.is_file():
                continue
            q = self.read(path)
            by_id = {a["id"]: a for a in q["assets"]}
            groups = defaultdict(list)
            for a in q["assets"]:
                if a.get("sourceWholeAssetId"):
                    groups[a["sourceWholeAssetId"]].append(a)
            for whole_id, pieces in groups.items():
                self.check(whole_id in by_id, "fragment.parent-exists", path, whole_id)
                if whole_id not in by_id:
                    continue
                whole = by_id[whole_id]
                with Image.open(self.file(whole["image"])) as original:
                    merged = Image.new("RGBA", original.size)
                    for a in pieces:
                        with Image.open(self.file(a["image"])) as piece:
                            merged.alpha_composite(piece)
                        x, y = a["tileOffsetXY"]
                        sx, sy = whole["footprintTiles"]
                        dx, dy = x - (sx - 1) / 2, y - (sy - 1) / 2
                        expected = [whole["anchorPx"][0] + (dy - dx) * 128, whole["anchorPx"][1] + (dy + dx) * 64]
                        self.check(all(abs(v - e) < 0.01 for v, e in zip(a["anchorPx"], expected)), "fragment.world-tile-anchor", self.file(a["image"]), expected)
                    self.check(merged.tobytes() == original.convert("RGBA").tobytes(), "fragment.exported-exact-RGBA-reassembly", self.file(whole["image"]), {"pieces": len(pieces)})
                self.reassembly_groups += 1
            if "houses/manifest" in name:
                mappings = q.get("coverageMappings", [])
                self.check(len(mappings) == 110 and len({a["sourceHouseTileId"] for a in mappings}) == 110, "house.110-source-tile-mappings", path)
                expected = {(v, stage) for v in range(4) for stage in range(4)}
                for a in mappings:
                    pairs = {(s["locationVariant"], s["constructionStage"]) for s in a["states"]}
                    self.check(pairs == expected and len(a["states"]) == 16, "house.4-random-by-4-construction", path, a["sourceHouseTileId"])
                    self.check(all(s["assetId"] in by_id and by_id[s["assetId"]]["image"] == s["image"] for s in a["states"]), "house.mapped-state-images", path, a["sourceHouseTileId"])
        vehicles = self.read(self.root / "docs/VEHICLE_RUNTIME_MANIFEST.json")
        self.check({m["id"] for m in vehicles["models"]} == set(range(256)), "vehicle.256-source-models")
        for model in vehicles["models"]:
            self.check({s["direction"] for s in model["sprites"]} == {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}, "vehicle.eight-logical-directions", detail=model["id"])
        effects = self.read(self.root / "docs/EFFECT_RUNTIME_MANIFEST.json")
        disasters = self.read(self.root / "docs/DISASTER_RUNTIME_MANIFEST.json")
        self.check(len(effects.get("effects", [])) == 12, "effects.12-source-types")
        self.check(len(disasters.get("subtypes", [])) == 15, "disasters.15-source-subtypes")

    def independent_visual_audit(self):
        path = self.root / "records/full-game-independent-visual-review.json"
        self.visual_review = {"record": self.rel(path), "reviewedContacts": 0, "openFindings": []}
        if not path.is_file():
            self.check(False, "independent-visual.review-record-missing", path, level="WARN")
            return
        q = self.read(path)
        for row in q.get("items", []):
            p = self.file(row["file"])
            unchanged = p.is_file() and self.sha(p) == row["sha256"]
            if row.get("status") == "passed-local" and unchanged:
                self.visual_review["reviewedContacts"] += 1
                continue
            finding = {**row, "imageChangedSinceReview": not unchanged}
            self.visual_review["openFindings"].append(finding)
            self.check(False, "independent-visual.needs-recheck" if not unchanged else "independent-visual.needs-repair", p, finding, level="WARN")

    def manager_art_audit(self):
        self.manager_customization = audit_manager_faces(self.root)
        report = self.root / "records/manager-customization-audit.json"
        write(report, self.manager_customization)
        source = self.file(self.manager_customization["sourceSpec"]["source"])
        self.sha(source)
        if self.manager_customization.get("artManifest"):
            self.read(self.file(self.manager_customization["artManifest"]))
        self.check(self.manager_customization["complete"], "manager.parameterized-art-and-advanced-state-coverage", report,
                   {"requiredBindings":self.manager_customization["requiredBindings"],"suppliedBindings":self.manager_customization["suppliedBindings"],"gaps":self.manager_customization["gaps"]}, level="WARN")

    def assembly_audit(self):
        """Recompose exported layers from current PNGs, independently of pack QA."""
        self.layer_reassembly_groups = 0
        seen = set()

        def group(whole_name, members, origin):
            key = (whole_name, tuple(members))
            if key in seen:
                return
            seen.add(key)
            paths = [self.file(n) for n in [whole_name] + members]
            if not all(p.is_file() for p in paths):
                self.check(False, "layers.exported-files-exist", origin, key)
                return
            with Image.open(paths[0]) as raw:
                original = raw.convert("RGBA")
            transparent = original.getchannel("A").point(lambda a: 255 if a == 0 else 0)
            original.paste((0, 0, 0, 0), mask=transparent)
            merged = Image.new("RGBA", original.size)
            same_canvas = True
            for p in paths[1:]:
                with Image.open(p) as raw:
                    part = raw.convert("RGBA")
                if part.size != original.size:
                    same_canvas = False
                    continue
                merged.alpha_composite(part)
            self.check(same_canvas, "layers.shared-canvas", paths[0], members)
            self.check(same_canvas and merged.tobytes() == original.tobytes(), "layers.exported-exact-visible-RGBA-reassembly", paths[0], members)
            self.layer_reassembly_groups += 1

        def walk(value, origin):
            if isinstance(value, dict):
                layers = value.get("layers", {})
                whole = value.get("image", value.get("whole"))
                if whole and isinstance(layers, dict) and value.get("layerOrder"):
                    order = value["layerOrder"]
                    self.check(isinstance(order,list) and bool(order) and all(key in layers for key in order),
                               "layers.explicit-draw-order", origin, order)
                    group(whole,[layers[key] for key in order if layers.get(key)],origin)
                elif whole and isinstance(layers, dict) and layers.get("rear") and layers.get("front"):
                    # Current bridges and visible tunnel mouths include an
                    # independent painted lane/floor between the two shells.
                    # Masks, piers and occluder aliases are not body layers.
                    order = value.get("layerOrder", ["rear", "front"])
                    self.check(isinstance(order, list) and order[0] == "rear" and order[-1] == "front",
                               "layers.explicit-draw-order", origin, order)
                    group(whole, [layers[key] for key in order if layers.get(key)], origin)
                elif value.get("whole") and value.get("ground"):
                    group(value["whole"], [value["ground"]]+([value["overlay"]]if value.get("overlay")else[]), origin)
                if value.get("whole") and value.get("sectionOrder"):
                    members = [n for n in value.get("files", []) if n != value["whole"]]
                    if members:
                        group(value["whole"], members, origin)
                for child in value.values():
                    walk(child, origin)
            elif isinstance(value, list):
                for child in value:
                    walk(child, origin)

        for pack in self.pack_paths:
            walk(self.read(pack).get("coverageMappings", []), pack)

        self.industry_bound_clips = 0
        self.industry_assembled_frames = 0
        for clip, manifest in self.animation_specs:
            if "industries" not in manifest.parts:
                continue
            binding = clip.get("binding", {})
            if not self.check(bool(binding), "industry.parent-animation-binding", manifest, clip.get("id")):
                continue
            self.industry_bound_clips += 1
            parent = self.file(binding.get("parentImage", "__missing__"))
            base_path = self.file(binding.get("cleanBaseImage", "__missing__"))
            mask_path = self.file(binding.get("ownershipMask", "__missing__"))
            self.check(parent.is_file() and self.sha(parent) == binding.get("parentSha256"), "industry.bound-parent-sha256", manifest, clip["id"])
            self.check(mask_path.is_file() and self.sha(mask_path) == binding.get("ownershipMaskSha256"), "industry.ownership-mask-sha256", manifest, clip["id"])
            self.check(binding.get("mustReplaceParentStaticArt") is True and binding.get("drawParentOriginalSimultaneously") is False, "industry.no-double-parent-render-rule", manifest, clip["id"])
            self.check(binding.get("attachmentOffsetPx") == [0, 0] and binding.get("attachmentScale") == 1, "industry.explicit-parent-pixel-coordinate-binding", manifest, clip["id"])
            if not all(p.is_file() for p in (parent, base_path, mask_path)):
                continue
            with Image.open(parent) as raw:
                original = raw.convert("RGBA")
            with Image.open(base_path) as raw:
                base = raw.convert("RGBA")
            with Image.open(mask_path) as raw:
                mask = raw.convert("L")
            self.check(list(original.size) == binding.get("frameCanvasPx") and base.size == mask.size == original.size, "industry.parent-base-mask-shared-canvas", manifest, clip["id"])
            previews = binding.get("assemblyPreviewFrames", [])
            self.check(len(previews) == len(clip.get("frames", [])) == 12, "industry.12-installed-preview-frames", manifest, clip["id"])
            frame_hashes = []
            for frame, preview_name in zip(clip.get("frames", []), previews):
                frame_path, preview = self.file(frame), self.file(preview_name)
                if not self.check(frame_path.is_file() and preview.is_file(), "industry.moving-and-installed-frame-exist", manifest, frame):
                    continue
                with Image.open(frame_path) as raw:
                    moving = raw.convert("RGBA")
                with Image.open(preview) as raw:
                    installed = raw.convert("RGBA")
                if moving.size != base.size or installed.size != base.size:
                    self.check(False, "industry.installed-frame-canvas", manifest, preview_name)
                    continue
                merged = base.copy()
                merged.alpha_composite(moving)
                self.check(merged.tobytes() == installed.tobytes(), "industry.actual-parent-plus-moving-equals-installed-preview", preview)
                unchanged_mask = ImageOps.invert(mask).point(lambda v: 255 if v == 255 else 0)
                alpha_difference = ImageChops.difference(merged.getchannel("A"), original.getchannel("A"))
                self.check(ImageChops.multiply(alpha_difference, unchanged_mask).getbbox() is None, "industry.fixed-support-alpha-outside-ownership", preview)
                diff = ImageChops.difference(merged.convert("RGB"), original.convert("RGB"))
                channels = diff.split()
                maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
                outside = ImageChops.multiply(maximum, unchanged_mask)
                self.check(outside.getbbox() is None, "industry.static-support-unchanged-outside-ownership", preview)
                frame_hashes.append(self.sha(frame_path))
                self.industry_assembled_frames += 1
            self.check(len(set(frame_hashes)) > 1, "industry.real-changing-moving-frames", manifest, clip["id"])

        self.check(self.industry_bound_clips == 8 and self.industry_assembled_frames == 96, "industry.eight-clips-96-installed-frames")

        for name in ("previews/world/assembled-transport-town.png", "previews/full-game-overview.jpg"):
            image = self.file(name)
            sidecar = Path(str(image) + ".derivation.json")
            if not self.check(image.is_file() and sidecar.is_file(), "assembly.preview-and-record-exist", image):
                continue
            record = self.read(sidecar)
            self.check(self.sha(image) == record.get("sha256"), "assembly.preview-current-sha256", sidecar)
            self.check(self.info(image)["size"] == [record.get("width"), record.get("height")], "assembly.preview-declared-size", sidecar)
            self.check(bool(record.get("operation")) and bool(record.get("derivedFrom")), "assembly.preview-derived-operation", sidecar)
            for source in self.source_refs(record.get("derivedFrom", [])):
                p = self.file(source["file"])
                self.check(p.is_file() and self.sha(p) == source["sha256"], "assembly.preview-source-sha256", sidecar, source["file"])

        bridge = self.root / "records/world-production/bridge-joins-geometry.json"
        if self.check(bridge.is_file(), "bridge.join-record-exists", bridge):
            q = self.read(bridge)
            runtime = self.root / "assets/world/infrastructure/transport-runtime/manifest.json"
            current = q.get("runtimeManifestSha256") == self.sha(runtime)
            self.check(current, "bridge.join-report-current-runtime", bridge, level="WARN")
            qa = q.get("mechanicalJoinQA", {})
            self.check(qa.get("assemblies") == 52 and qa.get("interfaces") == 104, "bridge.all-source-cases-axes-end-slopes", bridge)
            self.check(qa.get("exactPortAlignment") is True and qa.get("noTransparentDeckGap") is True, "bridge.exact-port-and-real-alpha-joins", bridge)
            for row in q.get("cases", []):
                p = self.file(row["preview"])
                self.check(p.is_file() and self.sha(p) == row.get("sha256"), "bridge.join-preview-current-sha256", bridge, row["preview"])
        aqueduct = self.root / "records/world-production/aqueduct-joins-geometry.json"
        if self.check(aqueduct.is_file(), "aqueduct.join-record-exists", aqueduct):
            q = self.read(aqueduct)
            runtime = self.root / "assets/world/infrastructure/transport-runtime/manifest.json"
            self.check(q.get("runtimeManifestSha256") == self.sha(runtime), "aqueduct.join-report-current-runtime", aqueduct, level="WARN")
            self.check(q.get("assemblies") == 16 and q.get("interfaces") == 32 and q.get("exactPortAlignment") is True and q.get("noTransparentDeckGap") is True and q.get("allWaterSurfacesLevel") is True, "aqueduct.all-source-roles-real-alpha-level-water", aqueduct)
            for row in q.get("cases", []):
                p = self.file(row["image"])
                self.check(p.is_file() and self.sha(p) == row.get("sha256"), "aqueduct.join-current-image", aqueduct, row["image"])
        cleanup = self.root / "records/world-production/bridge-cleanup.json"
        if cleanup.is_file():
            q = self.read(cleanup)
            self.check(q.get("deletionConfirmed") is True, "cleanup.bridge-working-candidates-retained-after-policy-block", cleanup, q.get("returnedReason"), level="WARN")

    def coverage_audit(self):
        path = self.root / "docs/WORLD_DELIVERY_COVERAGE.json"
        q = self.read(path)
        rows = q.get("items", [])
        missing = [r["id"] for r in rows if not r.get("artFiles")]
        unaccepted = [r["id"] for r in rows if not str(r.get("acceptanceStatus", "")).startswith(("passed", "local-art-check-passed", "local-static-check-passed"))]
        aggregate = self.read(self.root / "docs/WORLD_ASSET_MANIFEST.json")
        recorded = {x.get("file"): x.get("sha256") for x in aggregate.get("packSources", [])}
        stale = [self.rel(p) for p in self.pack_paths if recorded.get(self.rel(p)) != self.sha(p)]
        inventory = self.read(self.root / "docs/WORLD_ASSET_COVERAGE.json")
        expected_ids = {row["id"] for row in inventory["items"]}
        self.check({row["id"] for row in rows} == expected_ids, "world.current-source-inventory-exact-coverage", path, {"expected":len(expected_ids),"actual":len(rows)})
        self.check(not stale, "world.aggregate-current", path, stale, level="WARN")
        self.check(not missing, "world.requirements-mapped", path, missing, level="WARN")
        self.check(not unaccepted, "world.final-variant-art-review", path, {"count": len(unaccepted), "ids": unaccepted}, level="WARN")
        self.coverage = {"sourceRequirements": len(rows), "mappedRows": len(rows) - len(missing), "missingOrUnmappedRows": len(missing), "missingOrUnmappedIds": missing, "rowsWithoutFinalLocalAcceptance": len(unaccepted), "unacceptedIds": unaccepted, "aggregateStale": bool(stale), "staleOrUnaggregatedPacks": stale, "aggregateAssetCount": len(aggregate.get("assets", [])), "aggregateAnimations": len(aggregate.get("animations", []))}

    def browser_audit(self):
        self.browser_current = True
        self.browser_reports = []
        pairs = [("records/browser-validation.json", "index.html"), ("records/vehicle-fx-browser-validation.json", "previews/vehicles/index.html"), ("records/world-production/browser-validation.json", "previews/world/index.html"), ("records/world-production/industry-binding-browser-validation.json", "previews/world/industry-assembly/index.html")]
        for name, preview_name in pairs:
            p, preview = self.file(name), self.file(preview_name)
            if not p.is_file():
                self.browser_current = False
                self.check(False, "browser.report-missing", p, level="WARN")
                continue
            q = self.read(p)
            checks = q.get("checks", [])
            good = bool(q.get("passed")) and not q.get("failed") and not q.get("errors") and not q.get("pageErrors") and not q.get("failedRequests")
            if isinstance(checks, list):
                good = good and all(c.get("passed") for c in checks)
            fresh = preview.is_file() and p.stat().st_mtime >= preview.stat().st_mtime
            if name == "records/world-production/browser-validation.json":
                observed = next((c.get("count") for c in checks if c.get("name") == "world manifest embedded"), None)
                fresh = fresh and observed == self.coverage["aggregateAssetCount"]
            self.browser_reports.append({"record": name, "preview": preview_name, "passed": good, "currentForPreview": fresh})
            self.browser_current = self.browser_current and good and fresh
            self.check(good, "browser.recorded-checks-passed", p)
            self.check(fresh, "browser.current-preview-checked", p, preview_name, level="WARN")

    def run(self):
        self.collect()
        self.master_audit()
        self.formal_audit()
        self.ui_audit()
        self.navigation_audit()
        self.special_audit()
        self.assembly_audit()
        self.manager_art_audit()
        from audit_supplemental_art import audit as audit_supplemental_art
        self.supplemental_art = audit_supplemental_art(self)
        self.independent_visual_audit()
        self.coverage_audit()
        self.browser_audit()
        # Re-hash both metadata and actual image/font inputs. A producer can
        # replace a PNG before writing its new manifest, so JSON stability alone
        # is insufficient evidence that this snapshot stayed unchanged.
        changed = [self.rel(p) for p, digest in self.hashes.items() if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest]
        self.check(not changed, "audit.inputs-stable-during-read", detail=changed, level="WARN")
        local_ready = not self.counts["FAIL"] and not self.counts["WARN"] and not changed and not self.coverage["aggregateStale"] and not self.coverage["missingOrUnmappedRows"] and not self.coverage["rowsWithoutFinalLocalAcceptance"] and not self.visual_review["openFindings"] and self.browser_current and self.manager_customization["complete"] and self.supplemental_art["allCurrentLocalChecksPassed"]
        categories = Counter()
        for name in self.assets:
            parts = Path(name).parts
            categories[parts[2] if name.startswith("assets/world/") else "ui"] += 1
        world_count = sum(n.startswith("assets/world/") for n in self.assets)
        report = {"schema": "cloud-route.final-art-audit.v1", "startedAt": self.started, "finishedAt": datetime.now(timezone.utc).isoformat(), "root": str(self.root), "scope": "Independent PNG/hash/dimensions/Alpha/anchor/provenance/generation-evidence/path audit. Does not certify visual appearance, semantic game completeness or Unity runtime.", "summary": {"passedChecks": self.counts["passed"], "failures": self.counts["FAIL"], "warnings": self.counts["WARN"], "formalPNGs": len(self.assets), "uiFormalPNGs": self.ui_resource_count, "worldFormalPNGsInCurrentPackManifests": world_count, "screens": self.screen_count, "states": self.state_count, "upstreamUIFeatures": self.feature_count, "nativeImageGenMasters": sum(m["retained"] for m in self.master_records), "nativeGenerationRecords": len(self.master_records), "retiredImageRecords": sum(not m["retained"] for m in self.master_records), "exportedFragmentReassemblyGroups": self.reassembly_groups, "exportedLayerReassemblyGroups": self.layer_reassembly_groups, "industryBoundClips": self.industry_bound_clips, "industryAssembledFrames": self.industry_assembled_frames, "formalPNGByDirectory": dict(categories)}, "coverage": self.coverage, "inputsStable": not changed, "issues": self.issues, "generationRecords": self.master_records, "sourceManifestSnapshots": [{"file": self.rel(p), "sha256": self.read_files[p]} for p in self.pack_paths], "unityValidated": False, "userArtAccepted": False, "gitSubmitted": False}
        write(self.root / "records/full-game-art-audit.json", report)
        status = {"schema": "cloud-route.full-game-acceptance.v1", "checkedAt": report["finishedAt"], "status": "production-or-final-review-pending", "mechanicalSnapshotPassed": self.counts["FAIL"] == 0, "fullGameLocalArtAccepted": False, "userArtAccepted": False, "unityValidated": False, "gitSubmitted": False, "counts": report["summary"], "worldCoverage": self.coverage, "audit": "records/full-game-art-audit.json", "remaining": [{"level": x["level"], "code": x["code"], "file": x.get("file"), "detail": x.get("detail")} for x in self.issues], "acceptanceRule": "No whole-game acceptance claim while an upstream requirement, required state, stale aggregate, failed check or local visual review remains unresolved. User art approval and Unity runtime approval are separate."}
        report["independentVisualReview"] = self.visual_review
        report["supplementalArt"] = self.supplemental_art
        status["supplementalArt"] = self.supplemental_art
        report["managerCustomization"] = {k:self.manager_customization[k] for k in ["complete","artManifest","spriteValueSlots","uniqueSourceSpriteIds","requiredBindings","suppliedBindings","existingPresetCount","gaps"]}
        report["browserReports"] = self.browser_reports
        status["independentVisualReview"] = self.visual_review
        status["managerCustomization"] = report["managerCustomization"]
        status["browserReports"] = self.browser_reports
        status["fullGameLocalArtAccepted"] = local_ready
        status["status"] = "local-art-checks-passed; user-art-review-pending" if local_ready else "production-or-final-review-pending"
        write(self.root / "records/full-game-art-audit.json", report)
        write(self.root / "docs/FULL_GAME_ACCEPTANCE_STATUS.json", status)
        delivery_path = self.root / "DELIVERY.json"
        if delivery_path.is_file():
            delivery = load(delivery_path)
            delivery["status"] = status["status"]
            delivery["counts"].update({"formalPNG": len(self.assets), "uiFormalPNG": self.ui_resource_count, "worldFormalPNG": world_count, "retainedBuiltinMasters": report["summary"]["nativeImageGenMasters"], "worldSourceRequirements": self.coverage["sourceRequirements"]})
            delivery["auditSnapshotAt"] = report["finishedAt"]
            write(delivery_path, delivery)
        document = self.root / "docs/FULL_GAME_ART_DELIVERY.md"
        if document.is_file():
            summary = report["summary"]
            snapshot = (
                f"核查时间（UTC）：`{report['finishedAt']}`。当前分包清单列出 **{summary['formalPNGs']}** 个正式PNG，"
                f"其中UI **{summary['uiFormalPNGs']}**、世界/载具 **{world_count}**；保留的原生AI母图 **{summary['nativeImageGenMasters']}** 张，"
                f"逐图记录 **{summary['nativeGenerationRecords']}** 份（含 **{summary['retiredImageRecords']}** 份明确废弃图文字证据）。\n\n"
                f"本次机械检查 **{summary['passedChecks']}** 项通过、**{summary['failures']}** 项失败、**{summary['warnings']}** 项警告。"
                f"世界 **{self.coverage['sourceRequirements']}** 项需求中，总覆盖表当前映射 **{self.coverage['mappedRows']}** 项，"
                f"仍缺资源或映射 **{self.coverage['missingOrUnmappedRows']}** 项；未有最终本地验收记录 **{self.coverage['rowsWithoutFinalLocalAcceptance']}** 项。"
                f"世界总聚合{'已过期，需先刷新' if self.coverage['aggregateStale'] else '与当前分包记录一致'}。\n\n"
                "具体缺口、警告和输入版本见[完整验收状态](FULL_GAME_ACCEPTANCE_STATUS.json)与[终检证据](../records/full-game-art-audit.json)。"
            )
            text = document.read_text(encoding="utf-8")
            text = re.sub(r"<!-- audit-snapshot:begin -->.*?<!-- audit-snapshot:end -->", "<!-- audit-snapshot:begin -->\n" + snapshot + "\n<!-- audit-snapshot:end -->", text, flags=re.S)
            manager = self.manager_customization
            manager_text = (f"经理参数化头像专项：{manager['suppliedBindings']}/{manager['requiredBindings']}项source值/状态绑定，"
                            f"{'资源与必要状态的本地专项检查通过，仍待用户与Unity验收' if manager['complete'] else '仍有部件或高级流程预览缺口，整套不得提前验收'}。"
                            "原8张完整preset与参数化五官/服饰层分开统计，详见[专项结果](../records/manager-customization-audit.json)。")
            text = re.sub(r"<!-- manager-snapshot:begin -->.*?<!-- manager-snapshot:end -->", "<!-- manager-snapshot:begin -->\n" + manager_text + "\n<!-- manager-snapshot:end -->", text, flags=re.S)
            document.write_text(text, encoding="utf-8")
        print(json.dumps({"summary": report["summary"], "coverage": {k: v for k, v in self.coverage.items() if not isinstance(v, list)}, "reports": ["records/full-game-art-audit.json", "docs/FULL_GAME_ACCEPTANCE_STATUS.json"]}, ensure_ascii=False))
        return 1 if self.counts["FAIL"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    raise SystemExit(Audit(args.root).run())
