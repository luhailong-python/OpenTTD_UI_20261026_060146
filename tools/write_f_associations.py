"""Validate associations retained in this project; the former F: writer is retired.

Association text and historical evidence were migrated on 2026-10-26.
This compatibility entry point never rewrites source art READMEs or evidence.
"""
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_READMES = (
    'designs/attribute-panels/README.md',
    'designs/equipment-ui-20261008/README.md',
    'designs/gameplay-ui/README.md',
    'designs/mail-ui-v1/README.md',
    'designs/social-ui-v1/README.md',
    'designs/team-ui-v2/README.md',
    'designs/world-map-original-20260925/README.md',
)


def main(project_root: Path | None = None) -> int:
    document = (project_root if project_root is not None else ROOT) / "docs" / "image-reference-associations.md"
    try:
        text = document.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise SystemExit(f"Association document is unavailable: {document}: {error}") from error
    sources = re.findall(r"^原记录位置：\[([^\]]+)\]\([^\n]+\)$", text, re.MULTILINE)
    missing = sorted(set(EXPECTED_SOURCE_READMES) - set(sources))
    duplicates = sorted(source for source, count in Counter(sources).items() if count > 1)
    if missing or duplicates:
        raise SystemExit(f"Invalid association document {document}: missing={missing}; duplicate={duplicates}")
    print(f"Verified {len(EXPECTED_SOURCE_READMES)} project-local associations: {document}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
