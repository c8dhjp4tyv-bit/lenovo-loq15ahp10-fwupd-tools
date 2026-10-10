# Lenovo LOQ 15AHP10 (83JG): fwupd research and tooling

**Unofficial, community-maintained research. Not affiliated with Lenovo, not a Lenovo-approved update channel, and not an LVFS firmware release.**

This public repository shares source-only tools, an example AppStream metadata manifest, and **sanitized evidence** from a real Lenovo LOQ 15AHP10 (machine type **83JG**) system firmware update via `fwupd`. The goal is to assist technical review and advocate for **official vendor-supported LVFS updates** through the normal `fwupdmgr update` workflow.

## Hardware test

On **2026-09-13**, the machine owner intentionally reinstalled the already-current Lenovo BIOS **R8CN26WW** via a local `fwupd` UEFI capsule workflow. The device reported successful completion (`UpdateState: 2`, `LastAttemptStatus: 0x0`) and booted afterward. The relevant firmware GUID is `115cbe64-b198-4519-8022-5250690f65ac`.

**This is one successful same-version reinstall, NOT a tested upgrade between different versions, Lenovo QA approval, or evidence of an official LVFS download.** See [TESTING.md](TESTING.md) for a compact report, environment details, and limitations.

## What is public here?

- `TESTING.md` — sanitized test summary (no serial number, private keys, full `fwupdmgr` JSON, TPM event log, or firmware image)
- `tools/build_signed_remote.py` — source-only experimental packaging/signing helper for a **separately and lawfully obtained** vendor CAB; it does not perform an update
- `tools/init_signing_keys.sh` — local key generation for testing; never upload generated private keys
- `tools/inspect_metadata.py` — read-only metadata inspection and optional container SHA-256 check
- `examples/firmware.metainfo.xml.template` — non-installable, illustrative metadata with an intentionally missing payload digest

**Not included:** Lenovo's proprietary `.cab`, `.ROM`, `.bin`, `.fd` or other firmware images; generated catalogs or signed firmware bundles; certificates, signing keys, trust roots, machine identifiers, or private-repository Git history.

## Using the source tools (no firmware flashing)

These tools are for developers evaluating packaging and metadata only. They do not enable a firmware remote or invoke an installation on a device.

```sh
python3 tools/build_signed_remote.py --help
python3 tools/inspect_metadata.py --help
```

The experimental builder requires `python3`, `bsdtar`, `fwupdtool`, your own locally generated signing credentials and an independently obtained vendor CAB containing a firmware member plus AppStream metadata. Generated output must stay local unless redistribution permission has been secured.

All example manifests require validation and completion before use; the sample is **not** an LVFS submission or update-ready artifact. Firmware compatibility, vendor signatures, Secure Boot behavior, recovery and cross-version upgrades are **not validated** by this repository.

## Upstream discussions

- [Lenovo LOQ series LVFS request — fwupd/firmware-lenovo#461](https://github.com/fwupd/firmware-lenovo/issues/461)
- [fwupd discussion #10989](https://github.com/fwupd/fwupd/discussions/10989)
- [LVFS project](https://fwupd.org/)

**Official LVFS distribution of Lenovo BIOS images requires Lenovo or another properly authorized publisher and vendor QA.** A local signed JCat is not a Lenovo authorization or a substitute for firmware-platform signatures.

## Licensing

Original source and documentation in this repository are provided under the [MIT license](LICENSE); that license does **not** apply to Lenovo/Insyde firmware or other third-party materials. Do not mirror the private repository or copy its history to this public repository.
