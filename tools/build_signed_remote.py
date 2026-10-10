#!/usr/bin/env python3
"""Build a signed local fwupd test package from an independently obtained CAB.

Does not install firmware, deploy a remote, or authorize redistribution.

The firmware payload is never modified.  The input CAB is expected to contain
the raw firmware member and its AppStream metainfo.  The signing certificate
and private key must be supplied explicitly and should live outside Git.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_remote_metadata(metainfo: Path, cab: Path) -> bytes:
    tree = ET.parse(metainfo)
    component = tree.getroot()
    releases = component.find("releases")
    if component.tag != "component" or releases is None:
        raise ValueError("metainfo must contain one <component>/<releases> tree")
    release = releases.find("release")
    if release is None:
        raise ValueError("metainfo has no <release>")

    for child in list(release):
        if child.tag == "location":
            release.remove(child)
        elif child.tag == "checksum" and child.attrib.get("target") == "container":
            release.remove(child)

    location = ET.Element("location")
    location.text = cab.name
    release.insert(0, location)

    size = ET.Element("size", {"type": "download"})
    size.text = str(cab.stat().st_size)
    release.insert(1, size)

    checksum = ET.Element(
        "checksum",
        {"type": "sha256", "filename": cab.name, "target": "container"},
    )
    checksum.text = sha256(cab)
    release.append(checksum)

    wrapper = ET.Element("components", {"version": "1.0"})
    wrapper.append(component)
    ET.indent(wrapper, space="  ")
    return ET.tostring(wrapper, encoding="utf-8", xml_declaration=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cab", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ca-cert", type=Path, required=True)
    parser.add_argument("--signer-cert", type=Path, required=True)
    parser.add_argument("--signer-key", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument(
        "--expected-source-sha256",
        help="Optional SHA-256 for an independently acquired vendor ROM",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cab = args.cab.resolve()
    output_dir = args.output_dir.resolve()
    for path in (cab, args.ca_cert, args.signer_cert, args.signer_key):
        if not path.resolve().is_file():
            print(f"error: file does not exist: {path}", file=sys.stderr)
            return 2
    if args.source and not args.source.resolve().is_file():
        print(f"error: source does not exist: {args.source}", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="loq-signed-remote-") as temp_name:
        work = Path(temp_name)
        extracted = work / "extracted"
        extracted.mkdir()
        run("bsdtar", "-xf", str(cab), "-C", str(extracted))

        metainfo = extracted / "firmware.metainfo.xml"
        if not metainfo.is_file():
            print("error: CAB has no firmware.metainfo.xml", file=sys.stderr)
            return 2
        firmware_members = [
            path
            for path in extracted.iterdir()
            if path.is_file() and path.name not in {"firmware.metainfo.xml", "firmware.jcat"}
        ]
        if len(firmware_members) != 1:
            print(
                "error: expected exactly one firmware member, found "
                + ", ".join(path.name for path in firmware_members),
                file=sys.stderr,
            )
            return 2
        firmware = firmware_members[0]
        if args.source:
            source_hash = sha256(args.source.resolve())
            if args.expected_source_sha256 and source_hash.lower() != args.expected_source_sha256.lower():
                print(
                    f"error: source SHA-256 mismatch: {source_hash} != "
                    f"{args.expected_source_sha256}",
                    file=sys.stderr,
                )
                return 2
            if sha256(firmware) != source_hash:
                print("error: CAB firmware does not match --source", file=sys.stderr)
                return 2

        jcat = work / "firmware.jcat"
        # Sign both archive members and also embed SHA-256 checksums.  The
        # PKCS#7 signatures are validated against the installed root CA.
        run("fwupdtool", "jcat-sign", str(jcat), str(firmware), str(args.signer_cert), str(args.signer_key))
        run("fwupdtool", "jcat-self-sign", str(jcat), str(firmware), "sha256")
        run("fwupdtool", "jcat-sign", str(jcat), str(metainfo), str(args.signer_cert), str(args.signer_key))
        run("fwupdtool", "jcat-self-sign", str(jcat), str(metainfo), "sha256")

        signed_cab = work / cab.name
        run(
            "fwupdtool",
            "build-cabinet",
            str(signed_cab),
            str(firmware),
            str(metainfo),
            str(jcat),
        )

        remote_xml = build_remote_metadata(metainfo, signed_cab)
        remote_xml_gz = work / "firmware.xml.gz"
        with remote_xml_gz.open("wb") as stream:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=stream, mtime=0, compresslevel=9
            ) as compressed:
                compressed.write(remote_xml)

        remote_jcat = work / "firmware.xml.gz.jcat"
        run(
            "fwupdtool",
            "jcat-sign",
            str(remote_jcat),
            str(remote_xml_gz),
            str(args.signer_cert),
            str(args.signer_key),
        )
        run("fwupdtool", "jcat-self-sign", str(remote_jcat), str(remote_xml_gz), "sha256")

        for source in (signed_cab, remote_xml_gz, remote_jcat, metainfo):
            shutil.copyfile(source, output_dir / source.name)
        shutil.copyfile(args.ca_cert, output_dir / "community-root-ca.pem")

    sums = output_dir / "SHA256SUMS"
    names = [
        cab.name,
        "firmware.xml.gz",
        "firmware.xml.gz.jcat",
        "firmware.metainfo.xml",
        "community-root-ca.pem",
    ]
    with sums.open("w", encoding="utf-8") as stream:
        for name in names:
            stream.write(f"{sha256(output_dir / name)}  {name}\n")

    print(f"signed remote written to {output_dir}")
    print(f"CAB sha256: {sha256(output_dir / names[0])}")
    print(f"metadata sha256: {sha256(output_dir / names[1])}")
    print("private signing key was not copied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
