# MissionSoftware — Mission Software Engineering (concise English summary)

The Chinese [README.md](README.md) is the authoritative and complete guide; this page is a short summary.

**What this is.** Code, data and documents of the *Mission Software Engineering* project: a **mission shell** on seL4 Microkit (two protection domains: a passive `gatekeeper`, priority 100, and a `client`, priority 99, on one channel), a **controlled-experiment pipeline** comparing a traditional-process gate (B), a domain-rule-hardened baseline (B+) and a mission-layer gate (M, plus 4 ablations), and the project's reports, lifecycle documents, experiment design, literature survey and a graduation-project specification.

**Core claim.** An action is "within mission" only if *explicit entrustment ∧ the current action is still aligned with that entrustment ∧ the check is falsifiable*; and **delivery ≠ achievement** (`ALLOW_SIM` means "may be delivered in simulation", never "mission achieved").

**Evidence status — environment self-check, not confirmatory.** All experiment numbers come from an author-written corpus with draft oracle labels and only show that the apparatus works (pre-registered hypothesis H1′). Reproduction of the corpus matrix on Windows Docker and an independently labelled hold-out evaluation are **pending**. The original demo (`DEMO_PROFILE=full`) was accepted on the author's Windows + Docker machine on 2026-10-08 with `GATE|CHAIN|tip=80488a97|len=10`. On 2026-10-10 the repository scripts were re-run on the author's Linux sandbox (native cross-compiler + QEMU, no Docker): demo and all 43 matrix logs matched the committed reference results ([verification record](docs/verification/box-verification-2026-10-10.md)).

**Hard boundaries.** Non-clinical simulation only; no beam or vendor write-enable path. Formal kernel guarantees (K) are cited, not claimed. Microkit 2.3.1 uses the MCS kernel configuration whose verification is in progress, so *a build is not a verified kernel*. Cosign is a demo stand-in. The FNV-1a32 evidence chain is teaching-grade. `ALLOW_SIM` ≠ achievement.

## Quick start (run from the repository root)

```bash
git clone https://github.com/KOS-TL/MissionSoftware.git && cd MissionSoftware
bash scripts/setup_sdk.sh            # downloads Microkit SDK 2.3.1, verifies SHA-256 b1b285b8…c424
bash scripts/run_demo.sh full        # A: demo; expect 10 EVIDENCE events, tip=80488a97 len=10, final rc=124 (timeout, expected)
bash scripts/run_experiment.sh full  # B: 43-log matrix (use "quick" for a smoke run)
bash scripts/analyze.sh              #    -> mission-shell/experiment/reports/<docker|local>/report.md
bash scripts/check_host.sh           # C: host-only: corpus --check, 84 unit tests, 18 hostsim logs (no Docker/QEMU/SDK)
```

Windows (cmd): `scripts\windows\setup_sdk.bat`, `run_demo.bat full`, `run_experiment.bat full`, `analyze.bat`, `check_host.bat` (same order; untested on Windows so far). The underlying Docker command, accepted by the author on Windows, is:

```bat
docker run --rm -e DEMO_PROFILE=full -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

Scripts use Docker when available, otherwise a native `aarch64-linux-gnu-gcc` + `qemu-system-aarch64` (`MODE=docker|native`). macOS on Apple silicon is untested.

**Reference results on the author's sandbox** (`mission-shell/experiment/reports/box-qemu/report.md`; self-check, not confirmatory): MUST_DENY miss rate B 800/1000 (80.0%), B+ 128/200 (64.0%), M 0/1000 (0.0%); ablations M-cosign 20/200, M-align 93/200, M-prov 20/200, M-U 20/200; false rejection 0 in every condition; 12/12 determinism groups identical.

**Docs:** [docs/INDEX.md](docs/INDEX.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [REPRODUCE](docs/REPRODUCE.md) · [EXTENDING](docs/EXTENDING.md) · [STATUS-AND-LIMITATIONS](docs/STATUS-AND-LIMITATIONS.md) · [CONTRIBUTING](CONTRIBUTING.md) (pre-registration discipline) · [CITATION.cff](CITATION.cff).

**License:** not yet chosen — see [LICENSE-PENDING.md](LICENSE-PENDING.md). The Microkit SDK, seL4 and the Docker image are not redistributed here.
