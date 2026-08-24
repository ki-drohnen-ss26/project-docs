# LiDAR

The second half of the [MTF-01P](mtf-01p-configuration.md) is a downward-facing
LiDAR rangefinder. It measures the distance to the floor directly below the
aircraft — the **height above ground**. That number has two jobs on our aircraft,
and one job it must **never** be given. Getting that distinction wrong is what
crashed the drone on 2026-08-21.

!!! quote "ArduPilot's own guidance (EKF source selection)"
    *"Baro is the default and works well for most vehicles and situations. […]
    RangeFinder should almost never be used. This is only appropriate for indoor use
    where the floor is flat with no ground clutter (e.g. no chairs, boxes, etc)."*
    — [Copter docs: GPS / Non-GPS sources (EK3_SRC)](https://ardupilot.org/copter/docs/common-ekf-sources.html).
    The [optical-flow setup guide](https://ardupilot.org/copter/docs/common-optical-flow-sensor-setup.html)
    likewise lists **`EK3_SRC1_POSZ = 1` (barometer)** in its recommended non-GPS
    parameter set. Our crash is the case study for why.

## The sensor as configured on our aircraft

| Property | Value | Note |
|---|---|---|
| Orientation | down (`RNGFND1_ORIENT = 25`) | |
| Minimum range | `RNGFND1_MIN_CM = 1` | **not** the 20 cm default — the sensor sits only ~2 cm above the floor |
| Maximum range | `RNGFND1_MAX_CM = 800` | 8 m, plenty for an indoor hall |
| Reading on the floor | **0.02 m** | correct, not an error: that is the mounting height |
| Interface | MAVLink1 on FC SERIAL5 | see the [configuration page](mtf-01p-configuration.md) |

In our flight logs the rangefinder was flawless: **3441 of 3441 samples healthy**
on the crash day, tracking the fatal climb sample-for-sample from 0.02 m up to
4.94 m. Whatever went wrong that day, it was not this sensor.

## What the rangefinder is for

1. **Scaling optical flow.** Flow measures an angular rate; multiplying it by the
   rangefinder height turns it into a horizontal velocity. Without this height the
   whole indoor navigation chain is dead — see [Optical flow](optical-flow.md).
2. **Height-above-ground / terrain reference at low altitude.** The EKF and the
   landing logic use the rangefinder as a *terrain* source near the ground
   (ArduPilot's `EK3_RNG_USE_HGT` mechanism), where it is far more precise than the
   barometer — which, as our logs show, spikes by **4–6.7 m** from propeller
   downwash at the moment of takeoff.
3. **A trustworthy independent height check.** The companion's `--takeover` pilot
   handover and its post-climb sanity check
   (*does the rangefinder actually follow the altitude?*) gate on the rangefinder,
   precisely because it is a direct measurement rather than an estimate.

## What it must NOT be: the EKF's only height source

!!! danger "`EK3_SRC1_POSZ = 2` caused our crash — use `1` (Baro)"
    Our aircraft flew with the rangefinder configured as the EKF's **only**
    vertical position source. The result: EKF3 never fused a single height
    measurement, and the vertical estimate diverged **quadratically while the
    aircraft stood on the floor** — −268 m after 90 seconds, **−1070 m** after
    three minutes, with an indicated "climb rate" of −12.6 m/s on a motionless
    vehicle. The first altitude-controlled mode (a fence-forced LAND) then chased
    that estimate to 100 % throttle and flew the aircraft into the hall ceiling.
    Full chain of events: [incident analysis](../problems/incident-analysis-2026-08-21.md).

Why does this fail so badly? A rangefinder on a resting aircraft reports a
**constant** value (0.02 m, forever). A constant reading carries no absolute height
information: the filter cannot tell "vehicle height" and "terrain offset" apart, the
two become jointly unobservable and drift together, and the filter is left
integrating raw vertical accelerometer data with nothing ever correcting it. Hence
the quadratic divergence — the signature of pure double integration of a bias.

The barometer, by contrast, is an absolute pressure reference. It is noisy near the
ground (the downwash spike above) but it never *diverges*: in the same crash logs
`CTUN.BAlt` stayed within ±0.4 m the whole time the EKF estimate ran away by a
kilometre.

## The correct division of labour

| Role | Sensor | Parameter |
|---|---|---|
| Primary EKF height source | **Barometer** | `EK3_SRC1_POSZ = 1` |
| Terrain / height-above-ground at low altitude | **LiDAR rangefinder** | rangefinder configured as above; used via terrain following, never as the sole reference |

This is exactly what our recovered parameter baseline plus safe-overrides file
enforces, and how the EKF sources are documented in
[Position & Altitude Hold](../autopilot/position-altitude-hold.md).

!!! info "Status"
    The rangefinder itself is configured, verified on the real aircraft and healthy
    in every log. The corrected `EK3_SRC1_POSZ = 1` lives in the safe-overrides
    parameter file and is applied when the FC is restored after the post-crash
    barometer/I2C repair — the aircraft has not yet flown with the corrected
    configuration.
