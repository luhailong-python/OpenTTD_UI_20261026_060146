"""Export complete current import metadata and actual brand generation evidence.

The canonical brand folder is indexed directly. Requested configuration goals
are never relabelled as returned actual model/quality values.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json
from final_art_audit import Audit, DEFAULT_ROOT
from audit_brand_integration import BRAND_FOLDER, BRAND_MANIFEST, RESOURCE_MANIFEST, TITLE


def build_index(a):
    a.collect()
    a.master_audit()
    if a.counts["FAIL"]:
        raise ValueError("Current collection/generation evidence failed; refusing resource index: " + json.dumps(a.issues, ensure_ascii=False))
    brand_native = {r["file"] for r in a.master_records if r["record"].startswith(BRAND_FOLDER + "/")}
    generation_by_file = {r["file"]:r for r in a.master_records}
    rows = []
    for file, candidates in sorted(a.assets.items()):
        ordered = sorted(candidates, key=lambda item: item[1] != RESOURCE_MANIFEST)
        q, origin = ordered[0]
        canvas = q.get("canvas", q.get("nativeSize"))
        if q.get("width") and q.get("height"):
            canvas = [q["width"], q["height"]]
        anchor = q.get("anchorPx")
        pivot = q.get("pivotUnity", q.get("pivot"))
        if anchor is None and canvas and pivot:
            anchor = [pivot[0]*canvas[0], (1-pivot[1])*canvas[1]]
        is_brand = file.startswith(BRAND_FOLDER + "/")
        evidence = generation_by_file.get(file)
        generation = q.get("generationRecord") or (evidence["record"] if evidence else None)
        row = {
            "id":q.get("id", Path(file).stem), "file":file,
            "sha256":q.get("sha256") or a.sha(a.file(file)), "canvasPx":canvas,
            "anchorFromTopLeftPx":anchor, "pivotUnity":pivot,
            "borderLeftBottomRightTop":q.get("border", [0,0,0,0]),
            "sourceManifest":origin,
            "additionalManifestReferences":sorted({o for _,o in candidates if o != origin}),
            "sourceRequirementIds":sorted({v for item,_ in candidates for v in item.get("sourceRequirementIds", [])}),
            "category":"branding" if is_brand else q.get("category", "ui"),
            "state":q.get("state"), "direction":q.get("direction"),
            "nativeModelGeneration":file in brand_native if is_brand else bool(q.get("nativeModelGeneration", False)),
            "operation":q.get("operation", "Native image generation; see actual generation record" if file in brand_native else "See source manifest and current derivation sidecar"),
            "userArtAccepted":False, "unityValidated":False,
        }
        if is_brand:
            row.update({
                "role":q.get("role"), "derivedFrom":q.get("derivedFrom", []),
                "generationRecord":generation,
                "generationRecordSHA256":a.sha(a.file(generation)) if generation and a.file(generation).is_file() else None,
                "actualModel":None, "actualQuality":None,
                "modelDisclosure":"Actual model/quality were not returned; requested configuration remains separately recorded in native generation evidence.",
            })
        rows.append(row)
    paths = a.pack_paths + a.portrait_pack_paths + a.supplemental_pack_paths + a.brand_pack_paths
    paths += [a.root/"docs/ASSET_MASTER_MANIFEST.json"]
    snapshots = [{"file":a.rel(p), "sha256":a.sha(p)} for p in sorted(set(paths))]
    brand_evidence = [r for r in a.master_records if r["record"].startswith(BRAND_FOLDER + "/")]
    branding = [r for r in rows if r["category"] == "branding"]
    if len(rows) != 12212 or sum(r["file"].startswith("assets/world/") for r in rows) != 11555:
        raise ValueError("Expected12212formal PNGs including unchanged11555world/vehicle PNGs")
    if len(branding) != 8 or len(brand_evidence) != 2 or any(not r.get("role") or not r.get("generationRecord") for r in branding):
        raise ValueError("Formal brand metadata requires8PNG/2native generation records with roles and provenance")
    return {
        "schema":"cloud-route.compact-art-import-index.v1", "project":TITLE,
        "createdAt":datetime.now(timezone.utc).isoformat(), "formalPNGCount":len(rows),
        "scope":"Complete formal PNG/import index, including two native brand PNGs and six size exports at canonical branding/yuntu-wanli paths. Includes formal mask/data PNGs; PNG counts are not native painting counts. Superseded non-authoritative shoreline references excluded. Full state/source composition contracts remain in source manifests.",
        "assetManifests":snapshots, "generationEvidenceIndex":"records/full-game-art-audit.json",
        "brandGenerationEvidence":brand_evidence,
        "brandSummary":{"formalPNGs":8,"nativePNGs":2,"derivedPNGs":6,"canonicalManifest":BRAND_MANIFEST,"formalResourceManifest":RESOURCE_MANIFEST},
        "worldSourceCoverage":"docs/WORLD_DELIVERY_COVERAGE.json", "sourceUIFeatures":"docs/UI_MASTER_MANIFEST.json",
        "historicalSourceLabelPolicy":"Current presentation uses the formal title. Historical source pack project labels and original submitted prompts are provenance and remain unchanged.",
        "userArtAccepted":False, "unityValidated":False, "assets":rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    a = Audit(args.root)
    result = build_index(a)
    out = a.root/"docs/ART_RESOURCE_INDEX.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps({"file":a.rel(out),"formalPNGs":result["formalPNGCount"],"brandFormalPNGs":8,"brandNativeRecords":2,"sourceManifests":len(result["assetManifests"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
