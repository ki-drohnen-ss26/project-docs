# Live Demo

This page is the plan for demonstrating the system live. It is structured around
what the current hardware state allows: a **simulator demo** that shows the complete
autonomous mission logic today, **bench demos** of the real subsystems, and a
**flight demo** that is contingent on the hardware repair.

!!! info "Status (2026-08-24)"
    The flight-controller hardware is **recovered**: the barometer that seemed
    destroyed after the [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md)
    was only unreachable behind a hung I2C bus — the bent GPS-connector pins were
    straightened and stock 4.6.3 detects it again (the full story:
    [crash & barometer recovery](../problems/crash-2026-08-21.md)). Demos (a) and (b)
    below can be shown today (b3 once the `.rpk` model export lands); demo (c) is
    unblocked and follows the parameter reload, compass recalibration and
    milestones 1–5.

## (a) SITL demo — the full autonomous delivery, on a laptop

The strongest demonstration available today, and it shows the *entire* mission
logic, not a subset. The ArduCopter **4.6.3** SITL simulator (same firmware version
as the real FC) runs on a laptop; the companion code connects to it exactly as it
would to the real aircraft:

```bash
python main.py --sim
```

What the audience sees, end to end:

1. Preflight checks, EKF origin set **and verified** by the companion (GPS-denied
   configuration — GPS is genuinely off in the simulator).
2. Guided takeoff, with the altitude *held*, not just crossed.
3. **SEARCH** — the expanding-square pattern flies local-NED waypoints looking for
   a pad whose position is not known in advance.
4. **APPROACH** — once the (simulated) camera detects the pad, visual servoing on
   `dx/dy` centres the aircraft over it; sustained target loss falls back to SEARCH.
5. **DROP** and **RECOVER** (landing) — mission complete, fully logged with the
   autopilot's own status messages.

Variations that can be shown live by changing only the configuration: lawnmower
instead of expanding-square search, continuous instead of stop-and-look detection,
and a low-battery abort. This is the same code path the real aircraft will run —
the simulation differs in exactly three named configuration values.

## (b) Bench demos — real hardware, no propellers

Three self-contained demonstrations of the physical subsystems:

**b1 — MTF-01P live data.** The optical-flow + LiDAR sensor streams over MAVLink;
moving a hand or the airframe shows the rangefinder distance and flow quality
changing live. This sensor is already flight-proven: in all five logs from the
test days its status was *good* in 3441/3441 samples. *(Available today.)*

**b2 — Drop mechanism.** The servo release (Pi GPIO18, 1100 µs closed / 1900 µs
open, powered from a separate 5 V BEC) triggered from the companion — the same
call the DROP state uses in flight. *(Available today.)*

**b3 — AI-camera pad detection.** The Raspberry Pi AI Camera (IMX500) running the
pad detector *on the sensor* and printing detection offsets (`dx/dy`) live.
*(Pending: the detector exists as `pad_320_int8.tflite`; the IMX500 requires a
Sony `.rpk` package, and that re-export is in progress with a teammate.)*

## (c) Flight demo — contingent on the hardware repair

A real indoor flight demo follows the staged milestone plan — each stage adds
exactly one unknown, selected with `--milestone N`:

| Milestone | Demonstrates | Pass condition |
|---|---|---|
| 1 | Companion-controlled hover at 1 m | Logged drift within bounds — not merely "it hovered" |
| 2 | Same hover, detector running (logging only) | `dx`/`dy` signs verified |
| 3 | Search pattern, no detector | Ends in `TARGET_NOT_FOUND` — that *is* the pass |
| 4 | Search + detect + centre | Centres over the pad, nothing droppable on board |
| 5 | **Full indoor delivery** | The complete mission of demo (a), for real |

Which milestone can be shown at demo time depends on how far the flight-test
campaign has progressed by then; a realistic minimal flight demo is milestone 1 or
3, with milestone 5 as the goal.

Prerequisites, in order:

1. **Baro/I2C repair** — first the zero-cost test (unplug the GPS module's I2C
   wires, boot stock 4.6.3), then either connector repair or replacement hardware
   (see the [incident page](../problems/incident-analysis-2026-08-21.md#collateral-damage-and-the-current-hardware-state)).
2. **Parameter restore** — load `fc_baseline_463_20260821.parm`, then
   `fc_safe_overrides.parm` (fence off, the mandated `EK3_SRC1_POSZ=2` with
   `RNGFND1_GNDCLEAR=2`, arming checks on).
3. **Mounts** — 3D-printed mounts for MTF-01P, camera and servo (to be designed).
4. **Manual shakedown** — AltHold and PosHold by a pilot before any milestone.

A safety pilot with an independent kill switch on the transmitter is present for
every flight; the `--takeover` handover covers the takeoff phase, where optical
flow cannot yet provide a position estimate.

## Fallback plan

If the aircraft is not repaired in time, the demo is (a) + (b): the complete
autonomous delivery in the simulator, plus every real subsystem shown individually
on the bench — which together cover the full pipeline except the airframe itself.
