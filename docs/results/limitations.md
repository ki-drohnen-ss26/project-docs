# Limitations

Every system in this project has hard limits, and most of them we did not read about
— we hit them. This page is the catalogue, grouped by subsystem. Each entry states
what the limit is and what it costs (or how we mitigate it). Numbers marked with a
log reference come from our own dataflash logs; the crash-related ones are analysed
in full on the [incident page](../problems/incident-analysis-2026-08-21.md).

!!! danger "The expensive combination"
    Individually, most of these limits are survivable. The
    [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md) happened because three of them
    lined up: a barometer-referenced fence sized inside the baro's own downwash
    noise band, a rangefinder configured as the *only* EKF height source, and
    disabled arming checks. Read the limits below with combinations in mind.

## Flight controller (Flywoo GOKU GN745 AIO)

| Limit | Consequence / mitigation |
|---|---|
| **Exactly one I2C bus** (FlywooF745 hwdef), shared by the onboard barometer and the external GPS-module compass. *(Permanent design limitation — kept listed.)* | One damaged device can take down the whole bus: after the crash tore off the GPS connector, the baro stopped being detected *and* the compass reported unhealthy — two symptoms, one bus. This is exactly what happened on 2026-08-21, and it was **resolved on 2026-08-24 at zero cost**: the fault was bent GPS-connector pins holding the bus down, not dead chips — straightening them brought the compass back, and re-flashing stock 4.6.3 detected the barometer again (the chip was never dead). Mitigation: treat every external I2C device as a risk to the baro; the zero-cost diagnosis is to inspect/unplug the external device and reboot. See the [crash & recovery story](../problems/crash-2026-08-21.md). |
| **No SD-card slot** — logging goes to 16 MB of onboard SPI flash. | The flash fills within a few sessions, and `LOG_DISARMED` eats it while the aircraft just sits there. Mitigation: keep `LOG_DISARMED` off except when hunting a ground-side problem, download and erase logs after every test day. |
| **1 MB-flash MCU (STM32F745)** — the stock firmware build cannot fit every feature. | Extra features require a custom build, and flashing a different firmware **wiped all parameters to defaults** (including accel calibration and the MTF-01P serial setup). Mitigation: a full parameter baseline is kept in the repo (`Pi-Code/params/fc_baseline_463_20260821.parm` + `fc_safe_overrides.parm`) and reloaded after any flash. |
| **FC parameters are persistent** across power cycles and outlive the process that wrote them. | A companion-written geofence survived for days and ambushed a purely manual flight. Mitigation: the companion now saves every parameter before changing it, restores on every exit, and mirrors the originals to disk so even a killed run is cleaned up by the next one. |

## Sensors

| Limit | Consequence / mitigation |
|---|---|
| **Barometer is unusable near the ground.** Propeller downwash raises local pressure: our five logs show baro altitude spiking to 4.05–6.73 m at ~15 % throttle while the aircraft was centimetres off the floor. | Any barometer-referenced threshold inside that band (our 4 m fence) fires on *every* takeoff. Mitigation: no baro-referenced fence indoors; trust the rangefinder for near-ground truth. |
| **MTF-01P optical flow needs floor texture, light and some height** — it delivers no position estimate while the aircraft is on the ground. | Chicken-and-egg at takeoff: position-controlled modes need a position the sensor cannot give yet. Mitigation: the `--takeover` pilot handover flies the takeoff manually until flow is healthy. |
| **The LiDAR is the EKF's only height source, as the assignment mandates (`EK3_SRC1_POSZ = 2`) — and on the ground EKF3 fused no height at all.** It correctly reads its own ~0.02 m mounting height, but a constant reading carries no absolute height, so the filter never corrected its vertical integrator. | The vertical estimate diverged quadratically to **−1070 m while parked on the floor**; every altitude-controlled mode then chases that estimate. The barometer is not permitted as the EKF source, so the mitigation is a safety protocol, not a source switch: `preflight.py` ground-drift GO/NO-GO before every arming, a bench hand-lift test, a rangefinder-gated takeover, an in-flight EKF-vs-rangefinder cross-check (`EKF_ALT_DIVERGED` → LAND), and `RNGFND1_GNDCLEAR = 2` aligned to the true mounting height. Why fusion never engaged is still open — a parameter diff against a team flying the same sensor with `POSZ = 2` is pending. |
| **A sensor being "healthy" is not the same as being "fused".** The rangefinder reported *good* in 3441/3441 samples while the EKF ignored it completely. | A perfect sensor proved nothing about the estimate. Mitigation: monitor the EKF *output*, not just sensor status. |

## Indoor / GPS-denied flight

| Limit | Consequence / mitigation |
|---|---|
| **No GPS means no RTL.** RTL first climbs to `RTL_ALT` — which indoors is the ceiling. | An RTL-style failsafe is actively dangerous in a hall. Mitigation: every companion abort path uses `LAND` instead. |
| **The geofence is altitude-only at best.** Without a position estimate at boot, a polygon/circle fence has nothing to reference — and the altitude reference is the barometer (see above). | An indoor-sized altitude fence sits inside the baro's downwash noise band and breaches on every takeoff, and `FENCE_ACTION` turns that into an uncommanded mode change. Mitigation: fence **disabled by default** indoors; horizontal containment comes from the companion's own position-radius guard and the safety pilot. |
| **The EKF needs an explicitly set origin.** Without GPS, `LOCAL_POSITION_NED` and local waypoints only work after the companion sends `SET_GPS_GLOBAL_ORIGIN` — and ArduPilot **silently drops** the message when an origin already exists. | A "green" test run turned out to be flying on the simulator's origin, not ours. Mitigation: `set_origin()` reads the origin back and fails loudly on mismatch. |

## Companion computer (Raspberry Pi Zero 2 W)

| Limit | Consequence / mitigation |
|---|---|
| **The CPU cannot run YOLO inference alongside MAVLink handling.** A CPU build of the pad detector exists (`pad_320_int8.tflite`) but was never put on the aircraft — a Zero 2 W cannot sustain that next to the mission loop (the CPU path needs `SKIP_FRAMES = 2` to keep up). | Detection must run *on the camera sensor* (Sony IMX500), which loads **only** `.rpk` packages. That re-export is **done** as of 2026-08-19, its quantisation loss is measured (mAP50 and recall unchanged), and the `.rpk` is on the Pi; what remains is the flight-code configuration and a bench check of the decoded offsets — see [Landing Pad Detection](../landing-pad/integration.md#the-settings-that-still-have-to-change). |
| **The IMX500 holds exactly one network on the sensor**, and swapping costs a camera restart. | The Pi CPU path could run a pad detector *and* a person detector per frame; the AI Camera cannot. Detecting people on the pad as well would require a single two-class model, which measurably costs pad recall in the hard cases — [measured here](../landing-pad/training.md#a-short-detour-spotting-people-too). |
| **One UART to the flight controller, many consumers.** The mission script, a ground station and a log all need the same MAVLink stream. | Mitigation: `mavlink-router` fans the single serial link (SERIAL4, 921 600 baud) out to the mission script, a ground station and a logfile simultaneously. |

## Power (4S Li-Ion)

| Limit | Consequence / mitigation |
|---|---|
| **Narrow usable window with sag:** 16.4 V full to 11.2 V empty, and Li-Ion sags noticeably under load. | A voltage threshold read under throttle can look like an empty pack that recovers at idle. Mitigation: conservative `BATT_LOW_VOLT=12.8` on the FC plus the companion's own battery failsafe, both acting well above the true floor. |

## Firmware (ArduCopter 4.6.3)

| Limit | Consequence / mitigation |
|---|---|
| **Parameter names differ between 4.6.3 and 4.7 — and unknown names are silently ignored.** No error, no warning; the write just does nothing. | A safety limit you believe you set may not exist on the vehicle. Mitigation: the companion writes version-fallback names and verifies every parameter by reading it back. |
| **Failsafe outcomes masquerade as other faults.** After a fence-triggered LAND, re-arming is refused with `Arm: LAND mode not armable` — which we misread as a battery problem for two test days. | Mitigation: read the refusal text literally and check the current mode first; the companion now mirrors every autopilot `STATUSTEXT` into the mission log so the reason is on record. |
| **Disabled pre-arm checks remove the last line of defence.** `ARMING_CHECK=0` let the aircraft arm with a 1000 m vertical estimate error. | Every disabled check is a failure mode volunteered for discovery in the air. Mitigation: `ARMING_CHECK=786390` (everything except GPS lock, which indoors can never pass). |

## RC / FPV

| Limit | Consequence / mitigation |
|---|---|
| **Analog 5.8 GHz video is low-resolution and noisy.** | Fine for pilot situational awareness, useless as an AI input — which is one reason detection runs on a separate digital AI camera, not the FPV feed. |
| **Channel discipline is required when several teams fly.** Analog VTXs on overlapping channels wipe out each other's video. | Mitigation: agree channel assignments before anyone powers a VTX, and power up one aircraft at a time. |
| **German regulations limit transmit power** — generically, analog 5.8 GHz video is restricted to a low-milliwatt class, and the 868 MHz RC band has its own power and duty-cycle rules. | Mitigation: keep the TX800 on its lowest power setting indoors (which is also all a hall needs) and operate the ELRS link within band rules; verify the current legal values against official sources before flying, rather than folklore. |

## Read on

- [Incident 2026-08-21](../problems/incident-analysis-2026-08-21.md) — the crash in which several of
  these limits combined, second by second.
- [Results overview](index.md) — what works despite the limits.
- [Live demo plan](demo.md) — what can be demonstrated within them.
