"""Current-input gates for the post-baseline portrait/cursor/window art packs.

These checks consume separate production QA and actual visual review records.
They never turn a PNG count or a mechanical-only result into visual approval.
"""
from pathlib import Path


def audit(a):
    result = {}

    def report(name):
        path = a.file(name)
        if not a.check(path.is_file(), "supplement.report-exists", path):
            return {}
        q = a.read(path)
        # Explicit hashes prevent a previous successful run from certifying
        # newly edited manifests, contacts or state images.
        if q.get("manifest") and q.get("manifestSHA256"):
            current(q["manifest"], q["manifestSHA256"], path)
        if q.get("bindings") and q.get("bindingsSHA256"):
            current(q["bindings"], q["bindingsSHA256"], path)
        for key in ("sourceManifests", "reviewedPages", "reviewedSources", "reviewedAssets", "reviewedFormalAssets"):
            for item in q.get(key, []):
                filename = item.get("file", item.get("image"))
                if filename and item.get("sha256"):
                    current(filename, item["sha256"], path)
        for key in ("mechanicalValidation", "browserValidation", "previewAssembly"):
            item = q.get(key, {})
            if item.get("file") and item.get("sha256"):
                current(item["file"], item["sha256"], path)
        return q

    def current(name, digest, origin):
        path = a.file(name)
        ok = path.is_file() and a.sha(path) == digest
        a.check(ok, "supplement.current-input-sha256", origin, name)
        return ok

    def visual(name, flag=None):
        q = report(name)
        items = q.get("reviewedPages", q.get("items", []))
        ok = bool(q) and bool(items)
        if flag:
            ok = ok and q.get(flag) is True
        ok = ok and not q.get("staleEvidence") and not q.get("unresolvedBlockingVisualIssues")
        for item in items:
            filename = item.get("file", item.get("image"))
            ok = bool(filename and item.get("sha256")) and ok
            if filename and item.get("sha256"):
                ok = current(filename, item["sha256"], name) and ok
            ok = str(item.get("status", "")).startswith(("passed", "locally-reviewed")) and ok
        a.check(ok, "supplement.actual-current-visual-review", a.file(name))
        return ok

    def browser(name, hash_fields):
        q = report(name)
        ok = bool(q) and bool(q.get("checks")) and not any(q.get(k) for k in ("failed", "failures", "errors", "pageErrors", "failedRequests"))
        for check in q.get("checks", []):
            ok = (check.get("passed") is True or check.get("level") == "OK") and ok
        for field, filename in hash_fields.items():
            ok = bool(q.get(field)) and current(filename, q.get(field), name) and ok
        a.check(ok, "supplement.browser-current-preview", a.file(name))
        return ok

    before = a.counts["FAIL"]
    manager = report("records/manager-customization-validation.json")
    a.check(manager.get("mechanicalPassed") is True and not manager.get("failures"), "manager.current-mechanical-validation", a.file("records/manager-customization-validation.json"))
    mv = visual("records/manager-customization-visual-review.json", "localVisualPassed")
    mb = browser("records/manager-gallery-browser-validation.json", {
        "advancedGallerySHA256": "previews/manager-customization/index.html",
        "combinationGallerySHA256": "previews/manager-customization/part-combination-gallery.html"})
    result["manager"] = {"currentLocalChecksPassed": mv and mb and a.counts["FAIL"] == before,
        "mechanicalRecord": "records/manager-customization-validation.json", "visualRecord": "records/manager-customization-visual-review.json"}

    before = a.counts["FAIL"]
    pointer = report("records/pointer-art-validation.json")
    a.check(bool(pointer.get("passed")) and not pointer.get("failures"), "pointer.current-mechanical-validation", a.file("records/pointer-art-validation.json"))
    coverage = report("records/pointer-overlay-validation.json")
    a.check(bool(coverage.get("passed")) and coverage.get("remaining") == 0, "pointer.source-contract-coverage", a.file("records/pointer-overlay-validation.json"))
    for field, filename in {"sourceInventorySHA256": "docs/POINTER_OVERLAY_REQUIREMENTS.json", "bindingSHA256": "docs/POINTER_OVERLAY_BINDINGS.json"}.items():
        current(filename, coverage.get(field), "records/pointer-overlay-validation.json")
    pv = visual("records/pointer-visual-review.json")
    pb = browser("records/pointer-browser-validation.json", {
        "htmlSha256": "previews/pointers/index.html", "bindingSha256": "docs/POINTER_OVERLAY_BINDINGS.json"})
    result["pointers"] = {"currentLocalChecksPassed": pv and pb and a.counts["FAIL"] == before,
        "sourceRequirements": coverage.get("counts", {}).get("requirementRows"), "mechanicalRecord": "records/pointer-art-validation.json", "visualRecord": "records/pointer-visual-review.json"}

    # The final window/status icon pack uses the same explicit gate contract.
    before = a.counts["FAIL"]
    micro = report("records/micro-ui-validation.json")
    a.check(micro.get("complete") is True and not micro.get("failures"), "micro-ui.source-and-current-PNG-coverage", a.file("records/micro-ui-validation.json"))
    iv = visual("records/micro-ui-visual-review.json", "localVisualPassed")
    ib = browser("records/micro-ui-browser-validation.json", {"htmlSha256": "previews/micro-ui/index.html"})
    result["microUI"] = {"currentLocalChecksPassed": iv and ib and a.counts["FAIL"] == before,
        "mechanicalRecord": "records/micro-ui-validation.json", "visualRecord": "records/micro-ui-visual-review.json"}
    for key, stem, preview in (("roadOneWay", "road-oneway", "previews/road-oneway/index.html"), ("airportUI", "airport-ui", "previews/airport-ui/index.html"), ("roadside", "roadside", "previews/roadside/index.html"), ("railReservation", "rail-reservation", "previews/rail-reservation/index.html"), ("fenceAdapter", "fence-adapter", "previews/fence-adapter/index.html")):
        before = a.counts["FAIL"]
        q = report("records/"+stem+"-validation.json")
        a.check(q.get("complete") is True and not q.get("failures"), "supplement.explicit-source-and-state-coverage", a.file("records/"+stem+"-validation.json"))
        checked_visual = visual("records/"+stem+"-visual-review.json", "localVisualPassed")
        checked_browser = browser("records/"+stem+"-browser-validation.json", {"htmlSha256": preview})
        result[key] = {"currentLocalChecksPassed": checked_visual and checked_browser and a.counts["FAIL"] == before,
                       "sourceRequirements": q.get("sourceRequirements"), "mechanicalRecord": "records/"+stem+"-validation.json", "visualRecord": "records/"+stem+"-visual-review.json"}
    from additional_world_acceptance import SPECS, checked_evidence
    for key,qa_name,visual_name,_ in SPECS:
        before = a.counts["FAIL"]
        try:
            qa_evidence, visual_evidence = checked_evidence(qa_name,visual_name)
            report(qa_name);report(visual_name)
            for item in a.read(a.file(visual_name)).get("pages",[]):
                current(item["file"],item["sha256"],visual_name)
            ok = True
        except (ValueError,FileNotFoundError,KeyError) as error:
            ok = False
            a.check(False,"supplement.dedicated-world-package-evidence",a.file(visual_name),str(error))
        result[key] = {"currentLocalChecksPassed":ok and a.counts["FAIL"]==before,"mechanicalRecord":qa_name,"visualRecord":visual_name}
    before=a.counts["FAIL"]
    gallery_name="records/supplemental-gallery-browser-validation.json"
    galleries=report(gallery_name)
    gallery_ok=galleries.get("complete") is True and not galleries.get("failed") and not galleries.get("failures") and not galleries.get("pendingPages") and galleries.get("screenshotVisualReview",{}).get("localPassed") is True
    for page in galleries.get("pages",[]):
        gallery_ok=current(page["html"],page["htmlSha256"],gallery_name) and gallery_ok
        gallery_ok=current(page["manifest"],page["manifestSHA256"],gallery_name) and gallery_ok
        for viewport in page.get("viewports",[]):
            for item in viewport.get("images",[]):
                if item.get("local"):
                    gallery_ok=current(item["resolved"],item["sha256"],gallery_name) and gallery_ok
    a.check(gallery_ok,"supplement.four-specialist-galleries-current-browser-and-visual-review",a.file(gallery_name))
    result["supplementalGalleries"]={"currentLocalChecksPassed":gallery_ok and a.counts["FAIL"]==before,"browserRecord":gallery_name}
    result["allCurrentLocalChecksPassed"] = all(q["currentLocalChecksPassed"] for q in result.values())
    result["userArtAccepted"] = False
    result["unityValidated"] = False
    return result
