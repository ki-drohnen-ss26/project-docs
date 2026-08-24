# Build Guide

This is the **rebuild path**: the ordered checklist that takes you from a box of parts
to an autonomous indoor delivery drone, linking every section of this documentation at
the moment you need it. Each step states its **goal**, the **page(s)** that explain it,
and a **"done when"** criterion so you know when to move on.

!!! info "How far our own project got"
    Steps 1–5, 7 and 8 are **completed and verified** by our team (the full mission
    runs end-to-end in SITL; FC, sensor and companion link are bench-proven). Three
    steps are honestly marked **open**: the on-sensor `.rpk` model export (step 6, a
    teammate is on it),
    the 3D-printed frame mounts (step 9), and the real flight tests (step 10) —
    the aircraft is currently not flightworthy after the
    [2026-08-21 incident](../problems/incident-analysis-2026-08-21.md). Everything below is
    written so *you* can complete all ten.

!!! tip "The one rule that carries the whole guide"
    **SITL first.** Every parameter change and every line of companion code is
    validated against the ArduCopter 4.6.3 simulator before it touches the real
    flight controller. Set the simulator up early (step 7 tells you when) and never
    skip the rehearsal.

## Step 1 — Know the hardware

**Goal:** identify every component, its role, and how the pieces connect.

Read the [Hardware Overview](../hardware/index.md) and the
[Drone (Frame & FC)](../hardware/drone.md) page — including the architecture diagram
and the tools list (Smoke Stopper, CP2102 adapter, charger).

**Done when:** you can point at every part in the kit and name what it talks to
(which port, which protocol).

## Step 2 — Flash ArduPilot 4.6.3

**Goal:** the Flywoo GOKU GN745 runs ArduCopter — **pinned to 4.6.3**, not "latest".

Follow the firmware section of [Initial Setup](../hardware/drone/InitialSetup.md):
download the FlywooF745 build (`*_bl.hex`, or a [custom.ardupilot.org](https://custom.ardupilot.org/)
build on the **4.6.3 tag**), flash with STM32 Cube Programmer.

**Done when:** Mission Planner connects over USB and the banner reads
**ArduCopter V4.6.3**. Parameter names differ between releases and unknown names are
*silently ignored* — the wrong version fails quietly, so check the banner.

## Step 3 — Mandatory setup and parameters

**Goal:** a drone that arms, is calibrated, and flies safely in **Stabilize**.

Work through the rest of [Initial Setup](../hardware/drone/InitialSetup.md): frame
type, voltage/PID initial values, accel/compass/radio calibration, motor order and
ESC setup, serial ports, flight modes, failsafes, logging, and the indoor-flying
parameter block. The [Autopilot section](../autopilot/index.md) explains *why* these
choices ([ArduPilot Setup](../autopilot/ardupilot-setup.md) collects the parameter
work). Our recovered known-good parameter set lives in the Pi-Code repository
(`params/fc_baseline_463_20260821.parm` plus `params/fc_safe_overrides.parm` — fence
off, the mandated `EK3_SRC1_POSZ=2` with `RNGFND1_GNDCLEAR=2`, `ARMING_CHECK=786390`,
`BATT_LOW_VOLT=12.8`).

**Done when:** all calibrations pass, no `PreArm` errors, and the
[Quick Start](quickstart.md) hover test in Stabilize is calm and controllable.

## Step 4 — Configure the MTF-01P (optical flow + LiDAR)

**Goal:** the EKF gets horizontal velocity (flow) and height above ground (LiDAR)
— the indoor replacement for GPS.

The module **ships in MSP mode** and must be switched to **MAVLink @ 115200** once,
via the CP2102 adapter and the MicroAir assistant — see the
[MTF-01P hardware page](../hardware/mtf-01p.md) and
[MTF-01P Configuration](../sensors/mtf-01p-configuration.md). It connects to FC
**SERIAL5** (`RNGFND1_TYPE=10`, `FLOW_TYPE=5`); the EKF source setup is explained in
the [Sensors section](../sensors/index.md), with deep dives on
[Optical Flow](../sensors/optical-flow.md) and [LiDAR](../sensors/lidar.md).

**Done when:** Mission Planner shows a plausible rangefinder distance that tracks
when you lift the drone by hand, and optical-flow data arrives with usable quality
over textured, lit ground.

!!! danger "The rangefinder is the mandated EKF height source — fly it under the protocol"
    The assignment requires `EK3_SRC1_POSZ = 2` (rangefinder, not barometer). This is
    the configuration that crashed us on 2026-08-21 when flown without mitigations, so it
    is flown only under the safety protocol (ground-drift preflight, rangefinder-gated
    takeover, in-flight EKF-vs-rangefinder cross-check, `RNGFND1_GNDCLEAR = 2`), and why
    on-ground fusion never engaged is still under investigation — see the
    [crash analysis](../problems/incident-analysis-2026-08-21.md).

## Step 5 — Raspberry Pi OS and MAVLink routing

**Goal:** the Pi Zero 2 WH talks MAVLink2 to the FC and forwards it to local software.

Set up the OS ([Raspberry Pi OS](../software/raspberry-pi-os.md)), then follow the
[companion setup](../hardware/raspberry-pi.md): free the hardware UART via
`raspi-config`, wire the Pi to FC **SERIAL4** (`SERIAL4_PROTOCOL=2`,
`SERIAL4_BAUD=921` → 921600), install **mavlink-router** forwarding to
`udp 127.0.0.1:14550`.

**Done when:** a MAVLink heartbeat from the FC is visible on `127.0.0.1:14550` on
the Pi (e.g. via pymavlink), and optionally a GCS on your laptop connects through
the Pi's forwarded endpoint.

## Step 6 — AI camera and the on-sensor detector

**Goal:** the IMX500 AI camera detects the landing pad **on the sensor itself** —
the Pi Zero 2 W cannot run YOLO on its CPU next to the MAVLink stack.

Connect and set up the camera ([AI Camera Module](../hardware/ai-camera.md)), then
the model pipeline ([AI Software](../software/ai-software.md)): the IMX500 loads
**only Sony `.rpk` packages**, not `.tflite`; the export chain is
`yolo export format=imx` followed by `imx500-package` on the Pi.

**Done when:** `rpicam-hello --list-cameras` lists the IMX500 and your pad-detector
`.rpk` produces detections in the live stream.

!!! note "Status in our project: open"
    Our trained pad detector currently exists only as `pad_320_int8.tflite`; the
    `.rpk` re-export is pending (a teammate is on it). Until it lands, the mission
    code runs against the simulated detector.

## Step 7 — Companion code: SITL first, then milestones

**Goal:** the Pi-Code state machine (`IDLE → TAKEOFF → SEARCH → APPROACH → DROP →
RECOVER`, GUIDED via pymavlink) flies the complete mission — in the simulator.

Build the **ArduCopter 4.6.3 SITL** environment
([Setup Simulation](../software/SetupSimulation.md) — check out the `Copter-4.6.3`
tag, not master) and run the companion against it (`python main.py --sim`). The
mission logic and the staged **milestones 1–5** bring-up plan (each real flight adds
exactly one unknown, selected with `--milestone N`; `--takeover` covers pilot
handover) are described in [Mission Planning](../autopilot/mission-planning.md) and
demonstrated in the [Live Demo plan](../results/demo.md).

**Done when:** the full GPS-denied delivery mission completes end-to-end in SITL —
verified EKF origin, guided takeoff, search pattern, visual centring, drop, recover.

## Step 8 — Delivery mechanism

**Goal:** a payload release the companion can trigger.

The chosen design — a 9 g servo pin release on Pi **GPIO18** (50 Hz PWM, 1100 µs
closed / 1900 µs open, `gpiozero` + `lgpio`; **servo power from a separate 5 V BEC,
never the Pi's 5 V pin**) — is documented in the
[Delivery System section](../delivery-system/index.md), with implementation details
in [Servo Mechanism](../delivery-system/servo-mechanism.md) and the design rationale
in [Research & Concepts](../delivery-system/research.md).

**Done when:** the servo opens and closes reliably from the companion code on the
bench (props off!), releasing a test payload every time.

## Step 9 — Frame mounts

**Goal:** MTF-01P (nadir, clear optical path), AI camera (nadir), servo/payload bay
and Pi case mounted rigidly on the CineWhoop, within its tight mass budget.

Requirements and constraints: [Frame Extension](../frame/index.md); per-mount design
requirements: [CAD Models](../frame/cad-models.md); manufacturing workflow
(Tinkercad → Cura → printer): [Print Guide](../frame/print-guide.md) and
[3D Printing](../delivery-system/3d-printing.md). M3 standoffs/screws are provided
for a stacked platform.

**Done when:** all four components are mounted, the sensors' view is unobstructed,
and the drone still hovers with margin in Stabilize.

!!! note "Status in our project: open"
    The requirements are documented; the CAD design and printing have not been done
    yet. This is the main remaining hardware work besides the crash repair.

## Step 10 — Flight tests: milestones 1–5

**Goal:** transfer the SITL-proven mission to the real aircraft, one unknown at a
time.

Fly the staged milestones from [Mission Planning](../autopilot/mission-planning.md)
(hover → detector logging → search pattern → search + centre → full delivery),
each selected via `--milestone N`, always with a pilot ready on `--takeover`.
Before the first attempt, read [Limitations](../results/limitations.md) and the
[incident report](../problems/incident-analysis-2026-08-21.md) — and re-check `FENCE_*` and
`ARMING_CHECK` on the actual FC.

**Done when:** milestone 5 — the complete autonomous delivery — has been flown and
the logs confirm it.

!!! note "Status in our project: open"
    No milestone has been flown yet. The aircraft is awaiting the baro/I2C repair
    after the [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md); the SITL
    pipeline and companion code for all five milestones are ready.
