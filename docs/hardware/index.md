# Hardware Overview

This page gives an overview of all hardware components used in the project.

## Equipment per team

Each team receives the following main components:

- :material-quadcopter: **3.5" FPV drone** with CineWhoop frame (flight-ready)
- :material-glasses: **Skyzone Cobra X** FPV goggles
- :material-battery: **Li-Ion batteries** (3 pieces)
- :material-remote: **Radiomaster GX12 ELRS** radio controller
- :material-raspberry-pi: **Raspberry Pi Zero 2 WH**
- :material-camera: **Raspberry Pi AI Camera Module**
- :material-radar: **MicroAir MTF-01P** (LiDAR + Optical Flow)

!!! warning "Safety note"
    Always use a **Smoke Stopper** before powering up the drone, to prevent damage from short circuits. Never fly indoors without the propeller guard.

## Component overview

=== "Flight components"

    Components required directly for flight:

    - Frame with propeller guard (CineWhoop)
    - Flight controller with motor control
    - 4× motors
    - 4× propellers (Gemfan D90-5 / HQProp DT90MMX5)
    - ELRS receiver
    - GPS receiver with compass

=== "FPV / Video"

    !!! info "Removed from the current build"
        The **FPV camera (RunCam Phoenix 2)** and the **video transmitter (SpeedyBee
        TX800 VTX)** with its antenna have been removed from the current build.

    - FPV camera (RunCam Phoenix 2) — *removed from the current build*
    - Video transmitter (SpeedyBee TX800 VTX) — *removed from the current build*
    - Skyzone Cobra X FPV goggles
    - A/V video grabber (MacroSilicon MS210x)

=== "AI / Companion"

    - Raspberry Pi Zero 2 WH
    - Raspberry Pi AI Camera Module
    - 32 GB MicroSD card

=== "Sensing & Delivery"

    - **MicroAir MTF-01P**: optical flow + LiDAR rangefinder, on FC **SERIAL5**
    - **9 g drop servo**: payload release driven from the Pi on **GPIO18** (PWM); see
      [Servo mechanism](../delivery-system/servo-mechanism.md)

## Architecture

```mermaid
graph TD
    A[Radio controller<br/>Radiomaster GX12] -->|ELRS 2.4 GHz| B[ELRS receiver]
    B --> C[Flight controller]
    C --> D[Motors]
    C --> E[GPS + compass]
    F[MTF-01P] -->|UART| C
    G[Raspberry Pi Zero 2] -->|MAVLink/UART| C
    H[AI camera] -->|CSI| G
    G -->|GPIO18 PWM| K[Drop servo]
    C --> I["VTX (removed)"]
    I -.->|5.8 GHz| J["FPV goggles (removed)"]
```

## Tools & accessories

- Hex and Allen keys (1.5 / 2.0 / 4.0 / 5.5 / 8.0 mm)
- 48-piece precision bit set
- SkyRC B6neo+ charger
- Speedybee Adapter V3
- CP2102 USB-UART adapter
- Power bank 20000 mAh PD 20 W

## Further reading

- [Drone (Frame & Flight Controller)](drone.md)
- [Raspberry Pi Zero 2](raspberry-pi.md)
- [AI Camera Module](ai-camera.md)
- [MTF-01P Sensor](mtf-01p.md)
- [RC & FPV System](rc-fpv.md)
