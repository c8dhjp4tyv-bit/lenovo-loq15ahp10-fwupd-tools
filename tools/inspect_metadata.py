#!/usr/bin/env python3
"""Read-only inspection of a local fwupd remote's AppStream metadata.

Checks a CAB container hash if --cab is supplied; it does NOT verify digital
signatures, firmware payload contents, device compatibility or safe flashing.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True, help="fwupd firmware.xml.gz")
    parser.add_argument("--cab", type=Path, help="Optional local CAB for container hash comparison")
    args = parser.parse_args()
    try:
        with gzip.open(args.metadata, "rb") as handle:
            root = ET.fromstring(handle.read())
        component = root.find("component") if root.tag == "components" else root
        if component is None or component.tag != "component":
            raise ValueError("missing AppStream component")
        release = component.find("./releases/release")
        if release is None:
            raise ValueError("no release in metadata")
        app_id = component.findtext("id") or "(missing)"
        version = release.get("version") or "(missing)"
        guid = component.findtext("./provides/firmware") or "(missing)"
        location = release.findtext("location")
        print(f"Component: {app_id}")
        print(f"Version: {version}")
        print(f"Firmware GUID: {guid}")
        print(f"Location: {location or '(missing)'}")
        if args.cab:
            if location != args.cab.name:
                raise ValueError(f"location mismatch: {location!r} vs {args.cab.name!r}")
            checksum = next(
                (node.text.strip() for node in release.findall("checksum")
                 if node.get("target") == "container" and node.text), None
            )
            if checksum is None:
                raise ValueError("missing container checksum")
            observed = sha256(args.cab)
            if checksum.lower() != observed:
                raise ValueError("CAB container SHA-256 mismatch")
            print("CAB container SHA-256: matches remote metadata")
        print("Note: cryptographic signatures and payload bytes were NOT verified")
        return 0
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
