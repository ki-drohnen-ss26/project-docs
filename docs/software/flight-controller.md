# Flight Controller Firmware

The Flywoo GOKU GN745 AIO ships as a racing/FPV board, and boards of this class are
usually flown with Betaflight. We flashed it with **ArduPilot (ArduCopter) 4.6.3**
instead — this page explains that choice, why the exact version is pinned, and which
firmware build features the mission depends on. The hands-on flashing and initial
configuration is documented step by step in
[Initial Setup](../hardware/drone/InitialSetup.md).

## Why ArduPilot, not Betaflight or INAV

The mission is autonomous: a companion computer must command takeoff, waypoints,
visual-servoing nudges and a landing over MAVLink, and the autopilot must maintain a
position estimate indoors from optical flow + rangefinder. That requirement decides the
firmware:

| | **Betaflight** | **INAV** | **ArduPilot (our choice)** |
|---|---|---|---|
| Primary purpose | manual FPV / racing performance | navigation-capable FPV (GPS hold, RTH, waypoints) | full autopilot for autonomous vehicles |
| State estimation | none needed for its mission (rate/attitude control) | simpler position estimator | **EKF3** with selectable sources (GPS, optical flow, rangefinder) — exactly what GPS-denied indoor flight needs |
| Companion-computer control | no GUIDED-style external control | limited MAVLink support | **GUIDED mode**: an external computer streams position/velocity targets over MAVLink — the foundation of the whole Pi-Code state machine |
| MAVLink | telemetry-oriented | partial | first-class, including parameter protocol, `STATUSTEXT`, dataflash logs |
| SITL | no | yes, less mature | **mature SITL** — we rehearse every mission in simulation first ([Setup Simulation](SetupSimulation.md)) |

Betaflight is the right tool for flying this frame *manually* — but it has no concept of
an external computer flying the aircraft. INAV would be the lighter-weight alternative
if we only needed GPS waypoints outdoors; its indoor/flow support and companion-control
surface are far thinner. ArduPilot is the only one of the three where "Raspberry Pi
commands the drone in GUIDED, EKF fuses optical flow because GPS does not exist" is a
documented, supported configuration.

## The version is pinned: 4.6.3

The flight controller, the SITL simulator and every parameter file in the project are
pinned to the **same release**, ArduCopter **4.6.3** (`git checkout Copter-4.6.3` for
SITL builds). This is not pedantry — it prevents a failure mode that produces no error
message:

!!! warning "Unknown parameter names are ignored silently"
    Parameter names change between ArduPilot releases. On 4.5/4.6 the rangefinder
    limits are `RNGFND1_MIN_CM` / `RNGFND1_MAX_CM` (centimetres); from 4.7 they are
    `RNGFND1_MIN` / `RNGFND1_MAX` (metres). Likewise `RTL_ALT` (cm) became `RTL_ALT_M`
    (m), and `SYSID_MYGCS` became `MAV_GCS_SYSID`. Loading a `.parm` file written for
    the wrong version does **not** fail — the unknown lines are simply skipped, the
    parameters keep their defaults, and you get a subtly misconfigured vehicle instead
    of an error. Our companion code even has to try both `RTL_ALT` spellings for this
    reason.

Testing against SITL built from `master` (a moving development version) would mean
validating the mission against a *different autopilot* than the one that flies. So:
whatever version the firmware banner in Mission Planner shows is the version everything
else must use.

We also learned the cost of leaving the pinned version the hard way: during the
[2026-08-21 incident](../problems/incident-analysis-2026-08-21.md) debugging, a custom
**4.8.0-dev** build was flashed onto the FC — which **wiped every parameter to
defaults**. The recovered baseline now lives in the Pi-Code repository
(`params/fc_baseline_463_20260821.parm` plus `fc_safe_overrides.parm`), so the known-good
4.6.3 state can be restored after any re-flash.

## Firmware features the mission needs

ArduPilot's stock builds for small AIO boards are feature-trimmed to fit the flash. The
[ArduPilot Custom Firmware Builder](https://custom.ardupilot.org) lets you build a
chosen release for a chosen board (`FlywooF745`) with an explicit feature list. The
features this project cannot fly without:

| Feature (custom build option) | Why we need it |
|---|---|
| **MAVLink optical flow** | The MicroAir MTF-01P delivers its flow data as MAVLink messages on a serial port (`FLOW_TYPE = 5`) — without this driver the sensor is invisible |
| **EKF3 optical-flow fusion** | The EKF must be able to *fuse* the flow into a velocity/position estimate; indoors this is the only horizontal position source |
| **Guided / Guided-NoGPS** | The companion flies the aircraft in GUIDED via position targets; the NoGPS variant is the fallback for attitude-level external control without any position estimate |

Before flashing any build — stock or custom — verify these are present for your board
and release; a missing driver fails silently (the sensor just never appears), not with
an error.

!!! info "Status"
    The FC currently runs stock ArduCopter 4.6.3 with the recovered parameter baseline.
    The aircraft is grounded pending the barometer/I2C repair from the
    [2026-08-21 incident](../problems/incident-analysis-2026-08-21.md); all firmware-level
    validation since then has run against SITL at the same 4.6.3 tag.

## Where to go next

- [Initial Setup](../hardware/drone/InitialSetup.md) — flashing the board and the full
  first-time configuration
- [Autopilot section](../autopilot/index.md) — flight modes, EKF sources and parameters
  for GPS-denied flight
- [Setup Simulation](SetupSimulation.md) — building SITL at the matching version tag
