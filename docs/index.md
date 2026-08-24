# AI Drone – Automated Delivery

Welcome to the documentation of our project on **automated object delivery using an FPV drone with AI assistance**.

## About the project

In this project we develop, implement, and evaluate a practical drone-AI application. A flight-ready FPV drone is extended with the following capabilities:

- **Autopilot functionality** with ArduPilot
- **Position Hold** and **Altitude Hold** based on LiDAR and Optical Flow
- **Delivery mechanism** for the automated release of payloads
- **AI-assisted object detection** via the Raspberry Pi AI Camera Module

!!! info "Audience"
    This documentation is aimed at students, researchers, and lecturers who want to reproduce these AI drone scenarios or use them as a basis for their own modules and research projects.

!!! note "Project status (2026-08-24)"
    The full autonomous delivery pipeline runs **end-to-end in the ArduCopter 4.6.3
    simulator**; the MTF-01P sensor and the Raspberry Pi companion link are verified
    on the real aircraft. On 2026-08-21 a manual test flight ended in a crash whose
    cause is now **fully understood and fixed in software and parameters**. The flight
    controller hardware is **recovered**: the "destroyed" barometer was only unreachable
    behind a hung I2C bus — bent GPS-connector pins were straightened and, on
    2026-08-24, stock 4.6.3 detected the barometer again. Real-flight milestones are
    **unblocked**, pending a parameter reload after the firmware flash. The
    [crash & barometer recovery](problems/crash-2026-08-21.md) story and the
    [full incident analysis](problems/incident-analysis-2026-08-21.md) are required
    reading and among the most instructive artefacts of this project (see also all
    documented [Problems](problems/index.md)).

## Quick start

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Quick Start](tutorials/quickstart.md)**

    ---

    First steps with the drone — from unpacking to the first flight.

-   :material-cog: **[Hardware Overview](hardware/index.md)**

    ---

    All components of the drone and their characteristics.

-   :material-code-tags: **[Software Stack](software/index.md)**

    ---

    Firmware, operating system, and AI frameworks.

-   :material-airplane: **[Set up the autopilot](autopilot/ardupilot-setup.md)**

    ---

    Configure ArduPilot and enable Position / Altitude Hold.

</div>

## Project structure

The documentation follows the task structure defined in the project brief:

| Task | Topic | Documentation |
|------|-------|---------------|
| 1 | Get familiar with hardware and software | [Hardware](hardware/index.md), [Software](software/index.md) |
| 2 | Extension for automated delivery | Cross-cutting |
| 3 | Autopilot integration | [Autopilot](autopilot/index.md) |
| 4 | Position & Altitude Hold | [Sensors](sensors/index.md) |
| 5 | Delivery mechanism | [Delivery System](delivery-system/index.md) |
| 6 | Frame extension | [Frame Extension](frame/index.md) |
| 7 | Documentation & presentation | This site + poster + live demo |

## Team

This documentation is maintained by **Team Drone[X]**.

<!-- TODO: add team members -->
