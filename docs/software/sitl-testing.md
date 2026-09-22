---
tags:
  - SITL
  - Testing
  - Companion code
---

# Testing the Companion Code in SITL

Every mission is rehearsed in the simulator before it touches hardware. The companion
code that flies SITL is byte-for-byte the code that flies the drone (`python main.py
--sim` connects to the simulator on the same UDP endpoint the router provides on the Pi),
so the whole mission logic, the failsafes and the search patterns are validated on a
laptop before the aircraft is powered. This page is the step-by-step procedure: start the
simulator, load the flight-parameter mirror, then walk the test ladder from a preflight
check up to the full delivery mission and the failsafe drills.

## Prerequisites

- **A working SITL build**, checked out at the **same tag** the flight controller runs
  (`Copter-4.6.3`). If you have not built it yet, follow
  [SITL Simulation](SetupSimulation.md) first — that page covers the firmware version
  pin, the `setuptools<81` trap and the Gazebo option.
- **The [`Pi-Code`](https://github.com/ki-drohnen-ss26/Pi-Code) repository** checked out
  locally. All commands below are run from its root, and all parameter paths are relative
  to it.
- **Two conda environments**, kept separate:

    | Environment | Used for | Provides |
    |---|---|---|
    | `ardupilot` | building and running SITL | `sim_vehicle.py`, MAVProxy, the build toolchain |
    | `ki_drohnen_pi` | the companion code | `pymavlink`, `picamera2` stand-ins, the Pi-Code dependencies |

    Activate `ardupilot` in the terminal that runs the simulator, and `ki_drohnen_pi`
    in the terminal that runs `preflight.py` / `main.py`.

## 1. Start the simulator

In the `ardupilot` environment:

```
sim_vehicle.py -v ArduCopter --console -w \
    --custom-location=50.131196,8.692972,112,0
```

- `-w` wipes the simulated EEPROM so you start from firmware defaults — a clean slate for
  the parameter load in the next step.
- `--custom-location=50.131196,8.692972,112,0` starts the vehicle at the **real flight
  location** (the Frankfurt hall, 112 m). This matters because the companion sets the EKF
  origin there via `SET_GPS_GLOBAL_ORIGIN`, and **SITL models the earth's magnetic field
  at the position it was started at**. If the two do not match, pre-arm fails with
  `PreArm: Check mag field (z diff:976>200)` — 976 mGauss is the difference between the
  northern and southern hemisphere (the default SITL home is in Canberra). Starting at the
  same coordinates the companion uses as its origin keeps the simulated compass consistent
  with the origin the code sets.

## 2. Load the flight-parameter mirror

The mirror lives in the repo at **`params/sitl_flight_v2.parm`**. It is **generated from
the published flight set** (`params/flight_v2.param`, see
[Flight Parameters](../autopilot/parameters.md)) so the simulator tests the **same
behavioural parameters we actually fly** — the EKF sources, the failsafes, `ARMING_CHECK`,
the fence configuration and the navigation limits — while everything that is bound to the
physical aircraft is left at SITL-native values.

The published set **cannot be loaded into SITL wholesale**: its hardware-bound values
would break the simulator. For example `AHRS_ORIENTATION=13` describes how the real board
is mounted, but the SITL IMU is not rotated, so applying it turns the attitude estimate
into garbage; likewise the real `INS_*`/`COMPASS_*` calibration offsets mis-calibrate
SITL's already-ideal sensors, and the MTF-01P's MAVLink backends (`RNGFND1_TYPE=10`,
`FLOW_TYPE=5`) refer to hardware that does not exist in the sim. The mirror therefore
copies only the behavioural parameters, leaves board orientation, sensor calibrations,
port mapping and the frame-specific `ATC_*`/`MOT_*` tuning SITL-native, and appends the
simulator's own sensor backends (`RNGFND1_TYPE 100`, `FLOW_TYPE 10`, `SIM_FLOW_ENABLE 1`,
`SIM_TERRAIN 0`).

### Load it twice, with a reboot each time

In the MAVProxy console attached to SITL:

```
param load /Users/danieleamore/Studium/Drohnen-mit-KI/Pi-Code/params/sitl_flight_v2.parm
reboot
param load /Users/danieleamore/Studium/Drohnen-mit-KI/Pi-Code/params/sitl_flight_v2.parm
reboot
```

!!! warning "The double load is not optional"
    ArduPilot only creates the `RNGFND1_*` sub-parameters (`RNGFND1_MIN_CM`,
    `RNGFND1_MAX_CM`, `RNGFND1_GNDCLEAR`, `RNGFND1_ORIENT`) **after** `RNGFND1_TYPE` is set
    *and* the autopilot has rebooted. A file sorted alphabetically sends those
    sub-parameters *before* `RNGFND1_TYPE`, so on the **first** pass they are unknown and
    **silently discarded** — the rangefinder keeps the firmware defaults and reads 0.00 m
    on the ground. The second pass runs after the backend exists, so it fills them in. The
    procedure is always **load → reboot → load again → reboot**.

!!! note "Verified convenience alternative: load the mirror at startup"
    Loading the mirror as the simulator boots skips the double load entirely, because
    startup defaults are registered before the parameter tree is built — the `RNGFND1_*`
    sub-parameters pick their values up as soon as the backend exists. Verified in three
    SITL sessions on 2026-08-25 by starting the raw SITL binary with a comma-separated
    defaults chain (`arducopter -w --defaults .../copter.parm,.../sitl_flight_v2.parm`)
    and confirming the expected values by read-back. With `sim_vehicle.py` the equivalent
    is `--add-param-file=.../params/sitl_flight_v2.parm` together with `-w`. The explicit
    double load above remains the canonical procedure when the simulator is already
    running.

### Verify

```
param show RNGFND1_MIN_CM RNGFND1_MAX_CM RNGFND1_GNDCLEAR EK3_SRC1_POSZ FENCE_ENABLE WPNAV_SPEED ARMING_CHECK
```

Expected values:

| Parameter | Expected | Meaning |
|---|---|---|
| `RNGFND1_MIN_CM` | `0` | Minimum valid range — **`0` in SITL, `1` on the aircraft** (see the admonition below) |
| `RNGFND1_MAX_CM` | `800` | Maximum valid range (8 m) |
| `RNGFND1_GNDCLEAR` | `10` | Ground clearance — mirrored deliberately (the team kept it) |
| `EK3_SRC1_POSZ` | `2` | Height source is the rangefinder, not the barometer |
| `FENCE_ENABLE` | `0` | Fence off |
| `WPNAV_SPEED` | `100` | Horizontal cruise 1.0 m/s indoors |
| `ARMING_CHECK` | `41350` | The arming-check bitmask the team chose |

Any other value — most commonly `RNGFND1_MAX_CM`/`GNDCLEAR` reading their firmware defaults —
means the sub-parameters were dropped and the second load pass was skipped.

!!! abstract "Why the mirror deviates from the flight set in four places"
    The mirror copies the behavioural parameters 1:1, but a live SITL session (2026-08-25)
    pinned down four values it must **not** mirror — the generator forces each:

    - **Sensor backends.** `RNGFND1_TYPE 100`, `FLOW_TYPE 10`, `GPS1_TYPE 0` (+ appended
      `SIM_FLOW_ENABLE 1`, `SIM_TERRAIN 0`) replace the MTF-01P MAVLink backends, which do
      not exist in SITL.
    - **RC options.** `RC<n>_OPTION` is dropped: option-number validity is build-dependent —
      the real FC's `RC7_OPTION 182` boot-looped the default SITL build
      (*"Config Error: Failed to init: RC7_OPTION: 182"*).
    - **`RNGFND1_MIN_CM` validity floor → `0`.** SITL's landed rangefinder reads exactly
      `0.00 m`; the flight set's `1` (1 cm) floor flags it out-of-range-low and blocks **all**
      on-ground EKF fusion (verified by a 2×2 matrix: under `POSZ 2`, `MIN_CM 1` never fuses,
      `MIN_CM 0` fuses immediately). The real sensor reads `0.02 m`, a cm above its floor, so
      the aircraft keeps `1`.
    - **Battery voltages.** `BATT_ARM_VOLT 0`, `BATT_LOW_VOLT 10.5`, `BATT_CRT_VOLT 10` vs the
      real-pack `12.7 / 12.4 / 12`: the real thresholds refuse arming / would land constantly
      against SITL's ~12.6 V simulated pack. The failsafe **actions** stay mirrored.

## 3. The test ladder

Run each rung from the repo root in the `ki_drohnen_pi` environment. Do not skip up the
ladder — each rung establishes a precondition for the next.

### Preflight

```
python preflight.py --sim
```

**Pass criterion:** the EKF-altitude drift line stays **stable** while the disarmed
vehicle stands still (a drifting line means height is not being fused — go to
troubleshooting), and the **parameter-verification verdict** confirms the FC matches what
the mission expects.

### Telemetry only

```
python main.py --sim --tele
```

Prints live telemetry without flying — a quick confidence check that the companion is
connected to the simulator and reading sane state. **Pass:** attitude, altitude and mode
update and look reasonable.

### Milestones 1–6

Rehearse each staged bring-up milestone in the simulator with `--sim --milestone N`:

```
python main.py --sim --milestone 1   # ground arm test only (arm, hold armed, disarm)
python main.py --sim --milestone 2   # climb to 0.8 m, hold, land (position hold)
python main.py --sim --milestone 3   # + detector, logging only    (detector)
python main.py --sim --milestone 4   # fly the search pattern       (pattern)
python main.py --sim --milestone 5   # search + detect + centre     (approach)
python main.py --sim --milestone 6   # the full delivery            (release)
```

**Pass criteria:** milestones 2 through 6 each reach and hold their stage, then land
cleanly. Milestone 1 never leaves the ground: it arms, holds armed through the
diagnostics window, then disarms, and its pass condition is the log line
`[ARM_TEST] PASS: automatic arm and disarm both confirmed`.
**Milestone 4 correctly ends with `TARGET_NOT_FOUND`** — with no simulated pad in the
scene the search pattern runs to completion and reports that no target was found; that
abort reason *is* the pass condition for milestone 4, not a failure.

### Full mission

```
python main.py --sim
```

**Pass criterion:** the complete GPS-denied delivery mission
(`IDLE → TAKEOFF → SEARCH → APPROACH → DROP → RECOVER`) runs end-to-end in SITL and lands.

### Failsafe drills (in the MAVProxy console)

With a mission in the air, inject faults from the MAVProxy console and confirm the
companion reacts:

- **Low battery.** Mid-flight:

    ```
    param set SIM_BATT_VOLTAGE 10.5
    ```

    The companion detects `LOW_BATTERY` and **lands**.

- **Uncommanded mode change.** Mid-flight:

    ```
    mode LOITER
    ```

    The companion detects `MODE_CHANGED_LOITER`, treats the flight as taken over and
    **goes silent** (it stops commanding the vehicle — the human now has it).

- **Pilot-takeover rehearsal (optional).** Fly the vehicle up by hand, then hand it to the
  companion with `--takeover` (which does **not** arm or take off — it waits for the pilot
  to fly it up):

    ```
    mode alt_hold
    arm throttle
    rc 3 1650      # climb
    rc 3 1500      # hold
    ```

    then, in the companion terminal:

    ```
    python main.py --sim --milestone 2 --takeover
    ```

## 4. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| **No sensor data at all** (rangefinder/flow report nothing, height not fused) | The double load was skipped or only ran once. Load `sitl_flight_v2.parm` again and reboot — the `RNGFND1_*` sub-parameters only exist after the second pass. See [step 2](#load-it-twice-with-a-reboot-each-time). |
| **Abort `UNEXPECTED_FENCE_ENABLED`** | A fence is armed in the sim parameters. The companion refuses to fly rather than clear it. Disable it in MAVProxy and reboot: `param set FENCE_ENABLE 0`. |
| **`NO_POSITION_ESTIMATE` on the ground** (mission aborts before takeoff) | The known flow-only ground deadlock: with no GPS and no motion, optical flow gives the EKF nothing to lock a horizontal position onto while sitting still. Use `--takeover` and fly it up by hand so the EKF gets flow motion, then hand over. |

## When v3 parameters land

The mirror is generated from the published flight set, so it must be regenerated whenever
that set changes. When **`v3`** is published (it adds the `FLTMODE_CH` + `FLTMODE1`–`FLTMODE6`
switch mapping), regenerate the mirror from the new source and re-run the full ladder:

```
python params/generate_sitl_flight_params.py \
    --src params/flight_v3.param --out params/sitl_flight_v3.parm
```

The generator applies the split rule — behavioural parameters mirrored, hardware-bound
parameters left SITL-native, the simulator's sensor backends appended — so the regenerated
file continues to test the same behaviour we fly. After regenerating, repeat
[step 2](#2-load-the-flight-parameter-mirror) and the ladder against the new file.
