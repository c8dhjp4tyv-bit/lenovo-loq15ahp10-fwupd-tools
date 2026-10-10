# Firmware validation evidence — LOQ 15AHP10 / 83JG

## Summary

**Result: fwupd/UEFI reported success for a same-version reinstall on one real machine.**

On **2026-09-13 10:20:54** (timestamp as printed by fwupd), the owner deliberately reinstalled Lenovo BIOS **R8CN26WW**, which was already installed, using a locally packaged firmware update. The Linux fwupd history and UEFI capsule result record success. The machine booted following the update, as evidenced by later device output.

This is a **single-device smoke test**, not a manufacturer QA certification or proof of compatibility with every firmware revision. No firmware binaries, machine serial numbers, device-specific TPM measurements, or complete logs are included here. This public repository contains only the deliberately sanitized fields below.

## Evidence (selected, sanitized fields)

| Property | Observation |
| --- | --- |
| Device | Lenovo LOQ 15AHP10, machine type **83JG** |
| Firmware GUID (model update target) | `115cbe64-b198-4519-8022-5250690f65ac` |
| Firmware release | `R8CN26WW` |
| User-visible firmware version | `114.119.24614` |
| Raw/history firmware version | `1920426022` (same before and after; intentionally reinstalled) |
| Update mechanism | `uefi_capsule`, `org.uefi.capsule`, capsule-on-disk |
| fwupd version recorded | `2.1.7` |
| Test environment | Fedora Linux 46 prerelease, x86_64 |
| fwupd history | `UpdateState: 2` / `Success` |
| UEFI last attempt | `LastAttemptStatus: 0x0` |
| UEFI last attempt version | `0x72776026` |
| AppStream ID recorded in history | `org.loq15ahp10.community.bios.firmware` |
| Secure Boot | Disabled during this recorded test |

The `fwupdmgr get-history --json` record identifies the custom AppStream ID and UEFI capsule protocol; `fwupdmgr get-results` reports `Success`. The device record later identifies the BIOS as R8CN26WW. The operator confirms that the same version was intentionally installed again because it was already the latest on the machine.

**Interpretation:** The combined evidence is strong for an actual local fwupd capsule update attempt completed successfully, not merely a CAB file that can be parsed. It does not, by itself, prove that different-version upgrades work, or demonstrate which bytes the firmware reprogrammed during a same-version reinstall. The remote name was not recorded in the shared history excerpt; do not describe this test as a successful download from LVFS.

## Limits and remaining validation work

- Only one physical LOQ 15AHP10/83JG has been tested; this does not cover other LOQ models or machine types.
- Previous and new BIOS versions were identical, so upgrade-path and rollback behavior remain untested.
- Secure Boot was disabled for the recorded operation.
- There is no Lenovo-authorized production rollout, manufacturer QA approval, or explicit redistribution license in this project.
- The signed CAB and its embedded metadata remain in a **separate private research repository**. This public source-only repository does not ship that CAB or any signed catalogs; this report must not be read as validation of the illustrative metadata template.
- Do not publish unredacted fwupd `--json` output: it can contain host identifiers, machine serials, security state and large TPM/UEFI measurements.

## Intended upstream pathway

The requested user experience is **standard LVFS delivery**, where a supported LOQ device receives approved updates with ordinary `fwupdmgr refresh` and `fwupdmgr update`, without opting into a community remote.

This requires Lenovo (or a party explicitly authorized by the firmware rights holder) to take responsibility for legal permission, platform QA and the LVFS release. The local proof of concept and this evidence are offered only to help the vendor evaluate feasibility.

Related upstream discussion: https://github.com/fwupd/firmware-lenovo/issues/461

LVFS vendor eligibility and legal requirements: https://lvfs.readthedocs.io/en/latest/apply.html
