# MTF-01P Configuration

This is the complete how-to for bringing the **MicroAir MTF-01P** (optical flow +
LiDAR rangefinder in one module) up on our flight controller. Follow the steps in
order — the sensor does not talk ArduPilot's language out of the box, and half of the
flight-controller parameters only exist after a reboot.

What the two measurements are *for* is covered on the
[optical flow](optical-flow.md) and [LiDAR](lidar.md) pages; how the EKF uses them is
in [Position & Altitude Hold](../autopilot/position-altitude-hold.md).

!!! warning "Everything below is for ArduCopter 4.6.3"
    Parameter names changed in 4.7 (`RNGFND1_MIN_CM`/`RNGFND1_MAX_CM` became
    `RNGFND1_MIN`/`RNGFND1_MAX`, now in metres), and ArduPilot **silently ignores
    parameter names it does not know**. On 4.6.3 the 4.7 names "set" without any
    error and change nothing — the rangefinder keeps its defaults and the failure
    only shows up in flight. Check the firmware banner in Mission Planner first,
    use the `_CM` names, and read every value back after writing it.

## Step 1 — Switch the sensor from MSP to MAVLink

The MTF-01P **ships in MSP mode** (the protocol Betaflight/INAV expect). ArduPilot
needs it in **MAVLink** mode, and the switch is done in the sensor itself, before it
ever meets the flight controller:

1. Connect the MTF-01P to a PC through a **CP2102 USB-UART adapter**
   (sensor TX → adapter RX, sensor RX → adapter TX, 5 V, GND).
2. Open the **MicoAssistant software**, connect to the sensor's COM port, and set the output protocol to **"mav-apm"** (the MAVLink/ArduPilot mode).
3. Set the output protocol to **MAVLink** and the baud rate to **115200**, save to
   the sensor.

This is persistent — it only has to be done once per sensor. If you skip it, the FC
side looks completely dead: no `OPTICAL_FLOW`, no `RANGEFINDER` messages, no error,
because the FC is listening for MAVLink and the sensor is speaking MSP.

## Step 2 — Wire it to the FC

The sensor lives on the flight controller's **SERIAL5** (UART 5 on the Flywoo GOKU
GN745 — see the wiring photo in the
[drone setup](../hardware/drone/InitialSetup.md)): sensor TX → FC RX5, sensor
RX → FC TX5, plus 5 V and GND. TX and RX crossed, as always.

## Step 3 — FC parameters (part 1), then reboot

In Mission Planner (CONFIG → Full Parameter List):

| Parameter | Value | Meaning |
|---|---|---|
| `SERIAL5_PROTOCOL` | `1` | MAVLink1 — what the MTF-01P speaks |
| `SERIAL5_BAUD` | `115` | 115200 baud, matching the sensor setting from step 1 |
| `SERIAL5_OPTIONS` | `1024` | do not forward MAVLink traffic on this port — the sensor is a private FC↔sensor link, not part of the telemetry network |
| `FLOW_TYPE` | `5` | Optical flow source: MAVLink |
| `RNGFND1_TYPE` | `10` | Rangefinder source: MAVLink |

Write the parameters and **reboot the flight controller**. This is not optional: the
`RNGFND1_*` sub-parameters in step 4 only come into existence once `RNGFND1_TYPE` is
set and the FC has booted with it.

## Step 4 — FC parameters (part 2), after the reboot

| Parameter | Value | Meaning |
|---|---|---|
| `RNGFND1_MIN_CM` | `1` | Minimum range in **centimetres** — see the warning below |
| `RNGFND1_MAX_CM` | `800` | Maximum range, 8 m |
| `RNGFND1_ORIENT` | `25` | Facing down |
| `RNGFND1_GNDCLEAR` | `2` | Ground clearance in **cm** = the sensor's real mounted height (~2 cm), not the 10 cm default: EKF3 treats it as the rangefinder reading to expect when landed, so it must match reality — a mitigation for the on-ground EKF divergence with `EK3_SRC1_POSZ = 2`. |

Reboot once more so the rangefinder backend re-reads its limits.

!!! danger "`RNGFND1_MIN_CM = 1`, not the 20 cm default"
    The MTF-01P sits only about **2 cm above the floor** on our frame. With the
    default minimum of 20 cm the driver reports "out of range low" the whole time
    the aircraft is on the ground: the EKF gets no terrain height, the optical flow
    cannot be scaled into a velocity, and arming fails with
    *"Need Position Estimate"*. This failure only shows up on the real floor — SITL's simulated rangefinder does not sit 2 cm above the ground.

## Step 5 — Verify

Connect Mission Planner and open **Ctrl-F → MAVLink Inspector**. Two messages must
be arriving:

| Message | What healthy looks like (our measured values) |
|---|---|
| `RANGEFINDER` / `DISTANCE_SENSOR` | **0.02 m with the aircraft on the floor** — this is *correct*, the sensor sits ~2 cm up. A constant 0.00 m or no message at all means something is wrong. |
| `OPTICAL_FLOW` | `quality` between **45 and 113** over a textured floor (the range we measured across all our flight logs). Quality 0 means no usable texture, no light, or no message. |

Then lift the aircraft by hand: the rangefinder distance must follow your hand. In a
dataflash log, `RFND.Dist` must track the true height — during our flights it
tracked a climb from 0.02 m to 4.94 m sample-for-sample, and the sensor was healthy
in **3441 of 3441** samples on the crash day (the crash was a configuration error,
not this sensor — see the [incident analysis](../problems/incident-analysis-2026-08-21.md)).

!!! note "The sensor being healthy is only half the job"
    These steps make the FC *receive* flow and range data. Making the EKF *use*
    them (`EK3_SRC1_VELXY = 5` and the assignment-mandated `EK3_SRC1_POSZ = 2` — the
    rangefinder as the EKF height source, **not** the barometer) is a separate step
    with its own failure modes: it is exactly this configuration that crashed us on
    2026-08-21, so it is flown only under the safety protocol covered in
    [Position & Altitude Hold](../autopilot/position-altitude-hold.md) and on the
    [LiDAR page](lidar.md).

## Troubleshooting

| Symptom | Cause |
|---|---|
| No `OPTICAL_FLOW` / `RANGEFINDER` messages at all | Sensor still in MSP mode (step 1), TX/RX not crossed, or wrong `SERIAL5_BAUD` |
| `RNGFND1_MIN_CM` etc. not in the parameter list | `RNGFND1_TYPE` written but FC not rebooted (step 3) |
| Rangefinder "out of range low" on the ground, "Need Position Estimate" on arming | `RNGFND1_MIN_CM` still at the 20 cm default (step 4) |
| Parameters "set fine" but nothing changes | You used the 4.7 names (`RNGFND1_MIN`/`RNGFND1_MAX`) on 4.6.3 — silently ignored |
| Flow quality stuck at 0 | Floor without texture, too dark, or lens covered — see [optical flow](optical-flow.md) |
