# Results

This section summarises what the project has actually achieved, what it has proven
in simulation and on the bench, and what remains open. Honesty first: the results
below are split into **verified** (we have logs, test runs or bench evidence) and
**open** (planned, blocked, or in progress) — nothing in the first list is aspirational.

!!! info "Status (2026-08-24)"
    The software pipeline is complete and verified in SITL. The flight controller
    hardware is **recovered** after the
    [2026-08-21 incident](../problems/incident-analysis-2026-08-21.md): the barometer
    that appeared "destroyed" was only unreachable behind a hung I2C bus. Bent
    GPS-connector pins were straightened, and on 2026-08-24 stock 4.6.3 detected the
    barometer again (see the
    [crash & recovery story](../problems/crash-2026-08-21.md)). The real-flight
    milestones are now **unblocked**, pending a parameter reload after the firmware
    flash — they have not yet been flown.

## What works (verified)

### End-to-end autonomous delivery in SITL — including GPS-denied

The complete indoor mission runs in the ArduCopter **4.6.3** SITL simulator, the same
firmware version as the real flight controller:

- Full state machine `IDLE → TAKEOFF → SEARCH → APPROACH → DROP → RECOVER`, driven
  by the companion over MAVLink in GUIDED mode.
- **GPS-denied navigation**: GPS truly off (`GPS1_TYPE 0`), EKF origin set *and read
  back* by the companion, position from simulated optical flow + rangefinder, all
  waypoints as local NED offsets. The drone searches for a pad whose position is not
  known in advance (expanding-square or lawnmower pattern), centres over it by
  visual servoing on the camera's `dx/dy`, and drops.
- Both search patterns and both detection cadences (stop-and-look, continuous) are
  exercised purely via configuration — no source edits between scenarios.
- Diagnostics and safety hardening built in and tested: autopilot `STATUSTEXT`
  mirrored into the mission log, companion heartbeat, verified (not assumed) origin
  and takeoff, mode monitoring, `LAND` instead of `RTL` indoors, and an FC safety
  envelope that is saved before every change and restored on every exit.

### Staged bring-up concept for real flights

Real flights are planned as **milestones 1–5**, each adding exactly one unknown
(hover → detector logging → search pattern → search + centre → full delivery),
selected with `--milestone N` on the command line so nothing is edited between
flights. A `--takeover` pilot-handover mode covers the takeoff phase where optical
flow cannot yet provide a position. The plan is laid out in the
[live-demo page](demo.md) and the Pi-Code roadmap.

### Sensor integration: MTF-01P verified streaming

The MicroAir MTF-01P (optical flow + LiDAR) was configured on the bench (it ships in
MSP mode and had to be switched to MAVLink) and is **proven working in flight logs**:
in all five dataflash logs from the 2026-08-20/21 test days the rangefinder reported
status *good* in 3441 of 3441 samples — truthfully tracking the crash climb from
0.02 m to 4.94 m — and optical-flow quality was 45–113. The sensor side of the
GPS-denied navigation task works.

### Companion platform verified on hardware

The Raspberry Pi Zero 2 WH image is reproducible and bench-verified: `mavlink-router`
forwards the FC's MAVLink stream (SERIAL4, 921 600 baud) to the mission script, a
ground station and a log simultaneously; the companion↔FC link (heartbeat, telemetry,
ArduCopter 4.6.3) is confirmed against the real flight controller; the drop-servo
stack (gpiozero + lgpio on GPIO18) runs on the Pi.

### The crash, fully understood — and fixed in code and parameters

The 2026-08-21 crash was reconstructed second-by-second from the flight controller's
own dataflash logs. All three causal links (a leftover 4 m always-land geofence, a
rangefinder-only EKF height source that diverged to −1070 m on the ground, and
disabled arming checks) are identified, and **every fix is already implemented**:
geofence off by default with crash-proof parameter restore, a ground-drift preflight
check with a DO-NOT-FLY verdict, restored arming checks, and a takeover gate that
trusts the rangefinder instead of the EKF altitude.

→ Full post-mortem: [Incident 2026-08-21](../problems/incident-analysis-2026-08-21.md)

The custom-firmware flash after the crash wiped all FC parameters; the complete
pre-crash state was recovered from the crash log's own parameter records and lives
in `Pi-Code/params/fc_baseline_463_20260821.parm`, with `fc_safe_overrides.parm`
overriding exactly the causal values.

## What is open

| Item | State |
|---|---|
| **Hardware repair** | **Resolved (2026-08-24).** The baro-not-detected + `Bad Compass Health` symptoms were a single-I2C-bus hang from bent GPS-connector pins, not dead chips. Pins straightened; stock 4.6.3 now detects the barometer again — no replacement hardware needed. The board's single shared I2C bus remains a permanent [design limitation](limitations.md). |
| **Parameter reload + compass recalibration** | Pending. The custom-firmware flash wiped all parameters; reload `fc_baseline_463_20260821.parm` then `fc_safe_overrides.parm` and reboot, then recalibrate the compass after the connector repair. |
| **Real-flight milestones 1–5** | Not yet flown — now unblocked (was blocked on the repair), pending the parameter reload above. SITL equivalents are green. |
| **AI-camera model (`.rpk`)** | The trained pad detector exists only as `pad_320_int8.tflite`; the IMX500 loads only Sony `.rpk` packages. Re-export (`yolo export format=imx` → `imx500-package`) is pending with a teammate. |
| **Frame mounts** | 3D-printed mounts for the MTF-01P, AI camera and drop servo still to be designed. |

## Read on

- [Live demo plan](demo.md) — what we can show today (SITL + bench) and what a
  flight demo depends on.
- [Limitations](limitations.md) — the limits of every subsystem, backed by our own
  log evidence.
- [Incident 2026-08-21](../problems/incident-analysis-2026-08-21.md) — the full crash post-mortem.
