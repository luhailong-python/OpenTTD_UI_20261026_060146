"""Source-backed omissions found by the continuation's independent review."""
from pathlib import Path
import json

R = Path(__file__).resolve().parents[1]
SLOPES = list(range(15)) + [23, 27, 29, 30]
MACHINERY = ["mine-head", "oil-well-pump", "power-sparks", "toy-factory", "plastic-fountain", "bubble-generator", "toffee-quarry", "sugar-mine-sieve"]

def source(file, symbol, fallback=None):
    lines = (R / "reference/OpenTTD" / file).read_text(encoding="utf-8-sig").splitlines()
    line = next((i for i, text in enumerate(lines, 1) if symbol in text), fallback)
    return {"file": file, "line": line, "symbol": symbol}

def apply(items):
    by = {item["id"]: item for item in items}
    rocks = by["terrain-rocks"]
    rocks["neededVariants"].update({"densityStages": None, "overlayStates": ["dry", "snow-quarter", "snow-half", "snow-three-quarter", "snow-full", "water-coast"], "dryLayouts": [0,1], "layoutsByState": {"dry":[0,1], "snow-quarter":[0], "snow-half":[0], "snow-three-quarter":[0], "snow-full":[0], "water-coast":[0]}, "slopeCodes": SLOPES, "stoneBodiesSeparateFromGround": True, "snowCoverageFractions": [0.25, 0.5, 0.75, 1.0], "waterClassAndCoastSeparate": True})
    rocks["neededVariants"].pop("overlayLayouts",None)
    rocks["source"] = [source("src/clear_cmd.cpp", "SPR_OVERLAY_ROCKS"), source("src/water_cmd.cpp", "CoastRocks"), source("src/table/sprites.h", "SPR_OVERLAY_ROCKS")]
    rocks["scopeCorrection"] = "The former rough/bare density blend is gravel ground, not a stone overlay. It cannot satisfy this requirement."
    for name in ("snow", "desert"):
        by["terrain-" + name]["neededVariants"]["coverageFractions"] = [0.25, 0.5, 0.75, 1.0]
    by["terrain-field"]["neededVariants"].update({"sourceRandomVariants": None, "fieldStages": list(range(9)), "stage8HarvestHayBales": True})
    by["terrain-field"]["source"] = [source("src/table/clear_land.h", "_clear_land_sprites_farmland"), source("src/clear_cmd.cpp", "field_type < 8")]
    by["terrain-fence"]["neededVariants"].update({"styles": 6, "sourceStyleIds": list(range(1,7)), "noneSourceType": 0, "storedArrayCapacity": 7, "sourceSlopeOffsets": list(range(6)), "slopeCodes": SLOPES})
    by["water-shore"]["neededVariants"].update({"validSlopeCodes":[1,2,3,4,6,7,8,9,11,12,13,14,23,27,29,30], "reservedSourceSlots":[16,17], "noDrawSlopeCodes":[0,5,10], "waterSurfaceMustRemainLevel":True, "sourceShoreSprites":18})
    for item in items:
        if item["category"] == "bridge":
            item["neededVariants"]["railTypes"] = ["rail", "electric", "monorail", "maglev"]
        if item["id"].startswith("rail-") and item["neededVariants"].get("compositionMasks"):
            item["neededVariants"].update({"pathReservationState": True, "railFenceRoles": 8, "railFenceOffsets": 16})
        if item["id"] in ("road-road", "road-tram"):
            item["neededVariants"].update({"roadsideDetailSourceMasks": 16, "roadsideTypes": ["StreetLights", "Trees"], "roadsideLowBridgeAndTransparencyContracts": True})
    by["animation-industry-machinery"]["neededVariants"]["types"] = MACHINERY
    if "road-oneway-markings" not in by:
        items.append({"id": "road-oneway-markings", "category": "road", "name": "道路单行/禁行地面标记", "source": [source("src/table/sprites.h", "SPR_ONEWAY_BASE"), source("src/road_cmd.cpp", "SPR_ONEWAY_BASE")], "neededVariants": {"sourceSpriteSlots": 18, "axes": ["X", "Y"], "disallowedRoadDirections": [1, 2, 3], "sourceSlopeGroups": [0, 6, 12], "originalSlopeCodes": SLOPES, "postFoundationBindings": 114}, "animation": {"required": False}, "entryKind": "source-drawing-path-overlay", "artStatus": "missing-not-yet-produced", "artFiles": [], "acceptanceStatus": "not-checked", "nativeGenerationClaim": False})
    return items

if __name__ == "__main__":
    p = R / "docs/WORLD_ASSET_COVERAGE.json"
    q = json.loads(p.read_text(encoding="utf-8-sig"))
    apply(q["items"])
    q["counts"]["inventoryRows"] = len(q["items"])
    from collections import Counter
    q["counts"]["categoryRows"] = dict(Counter(row["category"] for row in q["items"]))
    q["continuationScopeCorrections"] = "Source drawing paths: road restrictions, independent climate/coast rock overlays, and all eight installed industry machinery/particle types."
    p.write_text(json.dumps(q, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"sourceRequirements": len(q["items"])})
