#!/usr/bin/env python3
"""import-icons.py — import Microsoft's official Azure Public Service Icons set
(https://learn.microsoft.com/azure/architecture/icons/) into this skill.

    python3 import-icons.py /path/to/Azure_Public_Service_Icons

Walks every *.svg under the given folder, normalises the official file names
(`00012-icon-service-Application-Insights.svg` -> `application-insights`) and copies
them into this skill's assets/icons/. Existing files are never overwritten, so the
curated icon ids that the docs and templates reference keep working. Duplicate
service names across category folders are imported once (first by sorted path).
"""
import re
import shutil
import sys
from pathlib import Path


def norm(stem):
    name = re.sub(r"^\d+-icon-service-", "", stem)
    nid = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return re.sub(r"-+", "-", nid).strip("-")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]).expanduser()
    if not src.is_dir():
        sys.exit(f"error: {src} is not a directory")
    dst = Path(__file__).resolve().parent.parent / "assets" / "icons"
    dst.mkdir(parents=True, exist_ok=True)

    added, kept, dups = 0, 0, 0
    seen = set()
    for f in sorted(src.rglob("*.svg")):
        nid = norm(f.stem)
        if not nid:
            continue
        if nid in seen:
            dups += 1
            continue
        seen.add(nid)
        tgt = dst / f"{nid}.svg"
        if tgt.exists():
            kept += 1
            continue
        shutil.copyfile(f, tgt)
        added += 1
    total = len(list(dst.glob("*.svg")))
    print(f"added {added} icons, kept {kept} existing, skipped {dups} duplicate names — {total} icons total in {dst}")


if __name__ == "__main__":
    main()
