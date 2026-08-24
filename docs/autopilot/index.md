# Autopilot

The autopilot is the flight-control firmware running on the Flywoo GOKU GN745 flight
controller. For this project it has to do far more than keep a quadcopter level: it must
hold a position **indoors without GPS**, accept navigation commands from a companion
computer, and record enough data to reconstruct what happened when a flight goes wrong.
This section explains why we chose **ArduPilot (ArduCopter)** and how it is configured
for autonomous indoor delivery.

## Why ArduPilot and not Betaflight / INAV?

Our flight controller ships as an FPV racing board, and the "native" firmware choice for
it would be Betaflight. Betaflight is excellent at what it is built for — a human pilot
with fast reflexes — but it is the wrong tool for an autonomous delivery drone:

| Requirement | Betaflight | INAV | **ArduPilot** |
|---|---|---|---|
| Autonomous flight commanded by a companion computer | No GUIDED-style mode; MAVLink support is telemetry-oriented | Limited waypoint autonomy, weak external-control API | **GUIDED / Guided-NoGPS mode**: an onboard computer streams position/velocity targets over MAVLink and the autopilot flies them |
| Indoor position hold without GPS | No position estimator for flow-only flight | GPS-centric navigation | **EKF3 sensor fusion** with selectable sources — optical flow for horizontal velocity, barometer/rangefinder for height, per-axis (`EK3_SRC1_*`) |
| Post-flight analysis | Blackbox (rates/PID-focused) | Limited | **Dataflash logging** of every sensor, EKF state and parameter — our [crash analysis](../problems/incident-analysis-2026-08-21.md) was possible only because of it |
| Configurable failsafes & pre-arm checks | Basic | Basic | Fine-grained (`ARMING_CHECK` bitmask, per-failsafe actions, geofence) |
| Custom firmware builds | Fixed feature set | Fixed feature set | **[custom.ardupilot.org](https://custom.ardupilot.org/)** — pick exactly the features the 1 MB flash target needs |

The decisive point is the first row: the whole delivery mission is flown by a Raspberry
Pi companion computer that talks MAVLink to the autopilot and commands it in **GUIDED**
mode. ArduPilot is the only one of the three where that is a first-class, documented
workflow. The EKF3's ability to swap GPS out for optical flow per axis is what makes the
same firmware fly indoors at all, and the dataflash logs are what let us diagnose
failures down to individual sensor samples.

The trade-off: ArduPilot is not tuned out of the box for a 3.5" CineWhoop, and its
defaults assume open sky (high speeds, RTL failsafes, GPS checks). A significant part of
the setup work is walking those defaults back to values that are safe in a hall — see
the pages below.

## Version pinned: ArduCopter 4.6.3

Everything in this documentation is written for and verified against **ArduCopter
4.6.3**. This is not pedantry: parameter names move between releases
(`RNGFND1_MIN_CM` → `RNGFND1_MIN`, `RTL_ALT` → `RTL_ALT_M` in 4.7), and ArduPilot
**silently ignores parameter names it does not know**. A configuration that "loaded
fine" on the wrong version can leave a sensor unusable with no error shown. Do not
install "latest" — install 4.6.3 and verify the version banner before changing anything.

## Pages in this section

- **[ArduPilot Setup](ardupilot-setup.md)** — firmware selection (custom build with
  optical-flow and Guided-NoGPS support), flashing via DFU, the mandatory-hardware
  configuration, and parameter hygiene (including our recovered baseline files).
- **[Position & Altitude Hold](position-altitude-hold.md)** — how the EKF fuses sensors
  into a position estimate, the indoor `EK3_SRC1_*` source configuration, and why one
  wrong source value crashed the aircraft.
- **[Mission Planning](mission-planning.md)** — how missions are "planned" in this
  project: not waypoint files, but a companion-computer state machine flying GUIDED,
  rehearsed in SITL first.

The full step-by-step bring-up of the aircraft — calibration, motor order, serial
ports, failsafes, first hover — is in the hardware section:
**[Drone Initial Setup](../hardware/drone/InitialSetup.md)**.
