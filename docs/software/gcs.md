# Ground Control Station

A ground control station (GCS) is not part of the autonomous loop — the mission is
flown by the companion computer — but it is indispensable for everything *around* the
loop: configuring the flight controller, finding out why an arm was refused, and
downloading the dataflash logs that every one of our post-flight (and post-crash)
analyses was built on.

## The two we use

| | **Mission Planner** (our main tool) | **QGroundControl** |
|---|---|---|
| Platforms | Windows | macOS, Linux, Windows, Android/iOS |
| Full parameter list | yes — including **load/save/compare** of `.param` files | yes, with search; no compare view as convenient as MP's |
| Messages / `STATUSTEXT` | dedicated *Messages* tab under the HUD | notification dropdown + MAVLink Inspector |
| Dataflash logs | download over MAVLink + built-in log browser with graphing | download supported; analysis weaker |
| Where it shines | deep ArduPilot configuration and log review | quick telemetry check from a Mac or phone |

Mission Planner is ArduPilot's de-facto reference GCS and the one this documentation
assumes for setup tasks ([Initial Setup](../hardware/drone/InitialSetup.md)). QGC is
the convenient second screen — in the SITL workflow we use its MAVLink Inspector to
watch `DISTANCE_SENSOR` while validating the rangefinder
([Setup Simulation](SetupSimulation.md)).

## Connecting

**Via USB.** Plug the FC into the laptop; Mission Planner connects on the USB COM port
(115200). This is the way for firmware flashing, parameter sessions and dataflash log
downloads — it works with the aircraft otherwise powered down and does not depend on
any companion software.

**Via the Pi's mavlink-router over Wi-Fi.** The router on the Pi
([Raspberry Pi OS](raspberry-pi-os.md)) can be given an extra UDP endpoint with the
laptop's IP address. The GCS then sees the live aircraft on the *same* FC stream the
mission script uses — telemetry, mode changes and `STATUSTEXT` in real time while the
companion flies. The same trick works in simulation: SITL outputs on UDP 14550 and a
GCS connects automatically, so the rehearsal looks identical to the real thing.

!!! note "One stream, many consumers"
    The GCS never talks to the FC's UART directly in the Wi-Fi setup — mavlink-router
    owns the serial port and every consumer (mission, recorder, GCS) gets its own UDP
    endpoint. Adding a GCS therefore never disturbs the running mission.

## The three habits that saved us

**1. When something is refused, read the Messages tab — always.**
A rejected command comes back over MAVLink as a bare `result=4` (failed). The *reason*
is sent separately as a `STATUSTEXT` message, and the Messages tab is where it appears
verbatim: `PreArm: Check mag field (z diff:976>200)`, `Arm: LAND mode not armable`,
fence breaches, EKF failsafes. Guessing at a refusal without reading it wastes hours;
reading it usually solves the problem in one line. (The companion mirrors these
messages into its own log for the same reason, and `preflight.py` in Pi-Code streams
them live while you try to arm.)

**2. Download the dataflash logs after every session.**
The FC's onboard dataflash log is the authoritative record — it captures far more than
the telemetry stream carries. The complete analysis of the
[2026-08-21 incident](../problems/incident-analysis-2026-08-21.md) — the diverging EKF altitude,
the baro downwash spikes, the fence breach on every takeoff — was reconstructed
entirely from downloaded dataflash logs. Two practical notes for our board: the Flywoo
GN745 logs to a **16 MB SPI flash** (no SD slot), which fills quickly — download and
clear it regularly, especially with `LOG_DISARMED = 1` set. And set `LOG_DISARMED = 1`
when chasing pre-arm problems, because by default the FC only logs while armed, which
excludes exactly the failures you are hunting.

**3. Save parameters before changing them.**
Mission Planner's *Full Parameter List* can save the complete parameter set to a file
and *compare* a file against the live FC. Save before every configuration session. Our
FC was wiped to defaults once (a custom-firmware flash during crash debugging), and the
recovery was only painless because a saved baseline existed — it now lives in Pi-Code
under `params/fc_baseline_463_20260821.parm`. The compare view is also the fastest way
to answer "what is different on this board from the baseline?"

!!! warning "Parameter files are version-specific"
    A `.param` file saved from one ArduPilot version loads incompletely on another —
    unknown names are skipped **silently**
    ([Flight Controller Firmware](flight-controller.md)). Keep the firmware version in
    the file name, as our baseline does, and never load SITL parameter dumps onto the
    real FC.

## Where to go next

- [Initial Setup](../hardware/drone/InitialSetup.md) — the Mission Planner setup
  sessions for this aircraft
- [Flight Controller Firmware](flight-controller.md) — version pinning and why it
  matters for parameter files
- [Setup Simulation](SetupSimulation.md) — connecting a GCS to SITL
