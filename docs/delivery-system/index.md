# Delivery System

Task 5 of the project: the drone must **carry a small payload to the detected
landing pad and release it there**. This section documents how the release
mechanism was chosen, how it is built and driven, and how the mechanical parts
around it get manufactured.

## The chosen design in one paragraph

The payload is held by a **9 g micro servo acting as a pin release**: a servo
arm blocks the payload (or a small trapdoor) in the closed position and swings
clear to let it fall. The servo's signal wire is driven **directly from the
Raspberry Pi companion computer** (GPIO18, 50 Hz PWM, 1100 µs closed /
1900 µs open) using `gpiozero` with the `lgpio` backend, while its power comes
from a **separate 5 V BEC** — never from the Pi's 5 V rail. The companion
software (`release.py` in the Pi-Code repo) hides the servo behind a small
`ReleaseMechanism` interface, so the same mission code that drops via an FC
output in simulation drops via the Pi GPIO on the real aircraft. This won over
grippers, winches and electromagnets because on a 3.5-inch indoor CineWhoop
every gram and every millimetre of prop-guard clearance counts — see
[Research & Concepts](research.md) for the full comparison.

## Pages in this section

| Page | What it covers |
|---|---|
| [Research & Concepts](research.md) | The release options we compared (trapdoor/pin, gripper, winch, electromagnet, passive hook) and why the servo pin release won |
| [Servo Mechanism](servo-mechanism.md) | The implemented mechanism: wiring, PWM values, software stack on the Pi, the FC-output alternative used in SITL, and how the mission triggers the drop |
| [3D Printing](3d-printing.md) | The Tinkercad → Cura → university-printer workflow and the design requirements for the servo/payload housing |

Related pages elsewhere in the docs:

- [Frame Extension](../frame/index.md) — the mounting platform the housing will attach to
- [Raspberry Pi](../hardware/raspberry-pi.md) — the companion computer that generates the servo PWM
- [Incident 2026-08-21](../problems/incident-analysis-2026-08-21.md) — why the aircraft is currently grounded

## Status

!!! info "Status (2026-08-22)"
    - **Concept and electronics: decided and implemented.** The servo drive
      pattern (gpiozero/`lgpio` on GPIO18, separate BEC) is verified on the
      bench, and the software path is fully validated in SITL via the FC-servo
      variant.
    - **Open:** a real **drop during flight** has not happened yet — the drone
      is not flightworthy after the [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md).
      The 3D-printed servo/payload **housing is still to be designed**
      ([requirements here](3d-printing.md)), as is its mounting on the
      [frame platform](../frame/index.md).
