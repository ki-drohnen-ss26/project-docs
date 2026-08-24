# MicroAir MTF-01P

The MTF-01P is the sensor that makes indoor position hold possible on this
drone. It combines **two sensors in one small module**:

- an **optical flow camera** that tracks how the ground texture moves under the
  drone (horizontal velocity), and
- a **TOF LiDAR rangefinder** that measures the distance straight down
  (height above ground).

Indoors there is no GPS, so this pair replaces it: flow supplies the EKF's
horizontal velocity, the LiDAR supplies the height reference the flow scaling
needs. How exactly the data feeds the EKF is covered in the
[sensors section](../sensors/index.md); this page is about the module as a
piece of hardware.

The [MicoAir MTF-01P](https://micoair.com/optical_range_sensor_mtf-01p/) is sold as a compact 2-in-1 optical-flow range sensor for drones and autonomous aircraft; the module officially supports ArduPilot, PX4, INAV and FMT.

## Interfaces: MSP by default, MAVLink for ArduPilot

The module has a single UART. It can speak two protocols:

| Protocol | Used by | Notes |
|---|---|---|
| MSP (MultiWii Serial Protocol) | Betaflight/INAV | **Factory default** |
| MAVLink | ArduPilot | What we need — sends `OPTICAL_FLOW` and `DISTANCE_SENSOR` messages |

!!! warning "The module ships in MSP mode"
    Out of the box the MTF-01P talks MSP and ArduPilot will see nothing on the
    port. It must be switched to **MAVLink at 115200 baud** once, using the
    MicroAir assistant software over a **CP2102 USB-UART adapter** (included in
    the team toolkit). The full procedure — wiring of the adapter, assistant
    settings, and every FC parameter — is in
    [MTF-01P Configuration](../sensors/mtf-01p-configuration.md).

On the flight controller side the module is wired to **SERIAL5**
(MAVLink1, 115200 baud) and registered as `FLOW_TYPE = 5` (MAVLink) and
`RNGFND1_TYPE = 10` (MAVLink) — see the
[configuration page](../sensors/mtf-01p-configuration.md) for the complete
parameter set on ArduCopter 4.6.3.

## Mounting requirements

Both sensors look through the bottom of the module, so mounting is not
optional detail — it decides whether the sensor works at all:

- **Facing straight down.** The rangefinder orientation is configured as
  downward (`RNGFND1_ORIENT = 25`); a tilted mount skews both the height
  reading and the flow scaling.
- **Completely free optical path.** Nothing may protrude into the field of
  view — no zip ties, wires, prop-guard edges or landing-gear parts. The flow
  camera also needs *visible floor texture and light* to produce anything
  useful.
- **Low over the ground when landed.** On our airframe the lens sits roughly
  2 cm above the floor with the drone at rest.

!!! info "A reading of 0.02 m on the ground is CORRECT"
    Do not "fix" a 2 cm reading while the drone stands on the floor — that is
    the true lens-to-floor distance, and it matters: the rangefinder minimum
    must be configured *below* it (`RNGFND1_MIN_CM = 1` on 4.6.3, not the
    20 cm default). With a higher minimum the driver reports "out of range low"
    on the ground, the EKF gets no terrain height, optical flow cannot be
    scaled and arming fails with *"Need Position Estimate"*. In our crash
    analysis the sensor itself performed flawlessly — status good on 3441 of
    3441 samples, tracking the climb from 0.02 m to 4.94 m
    ([incident report](../problems/incident-analysis-2026-08-21.md)).

!!! note "Status: final mount still to be designed"
    The mechanical mount that fixes the MTF-01P under the frame (together with
    the AI-camera and servo mounts) is still open as of 2026-08-22 — the sensor
    has so far been configured and bench-tested, and validated in the
    2026-08-21 flight logs.

## Known limitations

- **No position estimate while grounded.** At 2 cm height the flow camera sees
  almost no usable texture, so a position estimate only becomes available once
  airborne — a chicken-and-egg problem for autonomous takeoff that we solve
  with a pilot handover (`--takeover`) in the companion code.
- **Floor dependent.** Featureless, dark or glossy floors degrade flow quality;
  our logs show flow quality between 45 and 113 on the hall floor.
- **Range limits.** Configured usable rangefinder window is 1 cm to 8 m
  (`RNGFND1_MIN_CM`/`RNGFND1_MAX_CM`).
- **Height *reference*, not sole height *source*.** Using the LiDAR as the
  EKF's only altitude source (`EK3_SRC1_POSZ = 2`) caused our crash — keep the
  barometer primary and let the rangefinder assist near the ground. Details in
  the [incident report](../problems/incident-analysis-2026-08-21.md) and the
  [sensors section](../sensors/index.md).

## Related pages

- [MTF-01P Configuration](../sensors/mtf-01p-configuration.md) — CP2102 wiring,
  assistant software, all FC parameters
- [Sensors overview](../sensors/index.md) — how flow and LiDAR feed EKF3
- [Optical flow](../sensors/optical-flow.md) and [LiDAR](../sensors/lidar.md)
  — the two measurement principles in detail
