# Problems

This project documents its problems in the open, on purpose. The brief's **Task 1**
explicitly grades *understanding the limits of the systems we use* — and nothing
demonstrates those limits more sharply than the moments they bit us. Almost every
non-obvious thing we learned about indoor GPS-denied flight, this flight controller,
and this sensor stack, we learned by hitting a wall first. So the failures are not
hidden in a lab notebook; they are collected here as first-class documentation,
because they are the most instructive part of the whole project.

Each problem below is written up where it is most relevant (the sensor page, the
simulation guide, the incident analysis, …). This page is the catalogue that links
them together. Every entry lists the **symptom** as it actually appeared, the
**resolution or current status**, and a link to the **full write-up** — and every
link target is a page that exists in this site.

## The catalogue

| Problem | Symptom as it appeared | Resolution / status | Documented in |
|---|---|---|---|
| **Full-throttle climb into the ceiling (2026-08-21)** | Manual Stabilize flight went to 100 % throttle at ~1 m and hit the ceiling at 4.8 g; a leftover fence forced LAND while the EKF altitude read −1070 m on the floor. | **Resolved in software & parameters.** All three causal links identified from the logs; each got a fix (fence off by default with crash-proof restore, ground-drift preflight check, arming checks restored, rangefinder-trusting takeover gate). | [Crash & recovery](crash-2026-08-21.md), [full incident analysis](incident-analysis-2026-08-21.md) |
| **"Destroyed" barometer / bad compass after the crash** | Stock 4.6.3 halted at boot with `Config Error: Baro`; a custom no-baro build then showed `Bad Compass Health`; all telemetry read zero. | **Resolved, zero-cost.** The FlywooF745's single I2C bus was hung by bent GPS-connector pins — every device unreachable, no dead chips. Pins straightened (2026-08-23); stock 4.6.3 re-flashed (2026-08-24) → barometer detected and working again. | [Crash & recovery](crash-2026-08-21.md) |
| **Leftover geofence / parameter persistence** | A `FENCE_ALT_MAX = 4 m`, `FENCE_ACTION = 2` (always-LAND) fence from a days-old companion run breached on every takeoff (baro downwash spikes to 4–6.7 m) and forced LAND. | **Resolved.** FC parameters outlive the process that wrote them; the companion now saves every parameter before changing it, restores on every exit, and mirrors originals to disk so even a killed run is cleaned up. Fence off by default indoors. | [Full incident analysis](incident-analysis-2026-08-21.md) |
| **EKF height fusion never engaged on the ground (`POSZ = 2`)** | With the assignment-mandated `EK3_SRC1_POSZ = 2` (rangefinder as the EKF height source), EKF3 fused no height while parked, so the vertical estimate diverged quadratically to −1070 m on the floor; altitude-controlled modes then chased it. | **Under investigation — parameter diff with a working team pending.** The barometer is not permitted as the EKF source, so we fly `POSZ = 2` under a safety protocol (ground-drift preflight GO/NO-GO, bench hand-lift test, rangefinder-gated takeover, in-flight EKF-vs-rangefinder cross-check, `RNGFND1_GNDCLEAR = 2`) while diffing parameters against a colleague team that flies the same sensor with `POSZ = 2` successfully. | [Full incident analysis](incident-analysis-2026-08-21.md) |
| **Disabled arming checks masked everything** | `ARMING_CHECK = 0` let the aircraft arm with a 1000 m vertical estimate error and a stale fence — nothing refused. | **Resolved.** `ARMING_CHECK = 786390` (everything except the GPS lock that can never pass indoors), documented with its reason. | [Full incident analysis](incident-analysis-2026-08-21.md) |
| **Firmware flash wiped all parameters** | Flashing the custom 4.8.0-dev build reset every parameter to defaults, including accel calibration and the MTF-01P serial setup. | **Mitigated.** The full pre-crash state was recovered from the crash log's own parameter records into `fc_baseline_463_20260821.parm` (+ `fc_safe_overrides.parm`), kept under version control and reloaded after any flash. | [Full incident analysis](incident-analysis-2026-08-21.md) |
| **`Arm: LAND mode not armable` confusion** | After a fence-forced landing the vehicle stayed in LAND mode; re-arming was refused with `Arm: LAND mode not armable`, which was misread as a flat battery for two test days. | **Resolved (understanding).** The refusal was literally true — read the mode first. The companion now mirrors every autopilot `STATUSTEXT` into the mission log so the reason is on record. | [Firmware limitations](../results/limitations.md) |
| **Optical-flow bootstrap deadlock on the ground** | `main.py --milestone 1` hung forever waiting for `EKF_POS_HORIZ_REL`: flow needs height, height needs takeoff, takeoff needs a position estimate. | **Resolved by design.** The `--takeover` mode lets a safety pilot fly the first metre by hand (Stabilize needs no position); the companion takes over once the EKF converges in the air. | [Optical flow](../sensors/optical-flow.md) |
| **MTF-01P shipped in MSP mode, never configured** | On first bring-up the FC saw nothing: no `OPTICAL_FLOW`, no `RANGEFINDER`, no error — the sensor speaks MSP out of the box, the FC listens for MAVLink. | **Resolved.** Switch the sensor to MAVLink in the MicroAir assistant (once per sensor), then configure the FC serial/flow/rangefinder parameters. | [MTF-01P configuration](../sensors/mtf-01p-configuration.md) |
| **4.6 vs 4.7 parameter rename, silently ignored** | `RNGFND1_MIN_CM`/`_MAX_CM` (cm) became `RNGFND1_MIN`/`_MAX` (m) in 4.7; ArduPilot **silently ignores** unknown parameter names, so the wrong-version name "sets" without error and changes nothing. | **Mitigated.** Check the firmware banner first, use the `_CM` names on 4.6.3, and read every value back after writing it; the companion writes version-fallback names and verifies by read-back. | [MTF-01P configuration](../sensors/mtf-01p-configuration.md) |
| **SITL `SIM_TERRAIN` makes the rangefinder read 0.00 m** | With `--custom-location` and terrain enabled (the default), SITL measures the rangefinder against a terrain model far below the modelled ground, so it reports a constant 0.00 m at every altitude. | **Resolved.** Set `SIM_TERRAIN 0` for indoor tests; a rangefinder that reads 0.00 m at every altitude is this bug, not the driver. | [SITL setup](../software/SetupSimulation.md) |
| **pigpio removed in Debian 13 (trixie)** | Older servo guides say `apt install pigpio`; on the trixie-based Pi OS this fails with *"has no installation candidate"*, and forcing the pigpio pin factory breaks the drop servo. | **Resolved.** Use the `gpiozero` + `lgpio` stack instead of pigpio for the drop mechanism. | [Servo mechanism](../delivery-system/servo-mechanism.md) |

## Read on

- [Crash & barometer recovery](crash-2026-08-21.md) — the chronological story of the
  crash and the four-day hardware recovery.
- [Full incident analysis](incident-analysis-2026-08-21.md) — the second-by-second,
  log-level post-mortem of the crash.
- [Limitations](../results/limitations.md) — the permanent limits of every subsystem,
  many of which produced the problems above.
