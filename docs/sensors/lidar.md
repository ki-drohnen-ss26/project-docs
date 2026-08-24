# LiDAR

The second half of the [MTF-01P](mtf-01p-configuration.md) is a downward-facing
LiDAR rangefinder. It measures the distance to the floor directly below the
aircraft — the **height above ground**. That number has several jobs on our aircraft.
Most are uncontroversial; the contested one — being the EKF's *only* height source — is
simultaneously the job the assignment **mandates**, the job ArduPilot warns against in
general, and the job that crashed the drone on 2026-08-21 when we flew it without a
safety protocol. We now fly it deliberately: mandated, mitigated, and under
investigation.

!!! quote "ArduPilot's own guidance (EKF source selection)"
    *"Baro is the default and works well for most vehicles and situations. […]
    RangeFinder should almost never be used. This is only appropriate for indoor use
    where the floor is flat with no ground clutter (e.g. no chairs, boxes, etc)."*
    — [Copter docs: GPS / Non-GPS sources (EK3_SRC)](https://ardupilot.org/copter/docs/common-ekf-sources.html).
    We keep this quote because it names our situation exactly: a **flat indoor hall** is
    the one exception it allows. Our assignment *mandates* the rangefinder as the EKF
    height source (`EK3_SRC1_POSZ = 2`), so we operate in precisely that exception — and
    documenting that we deliberately work against the general recommendation, why it is
    permissible here, and with which mitigations, is part of the graded "limits of the
    systems" analysis. Our 2026-08-21 crash is the case study for why the mitigations are
    not optional.

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

## The mandated, contested job: the EKF's only height source

!!! danger "`EK3_SRC1_POSZ = 2` is mandated — and it is the configuration that crashed us"
    The assignment requires the rangefinder to be the EKF's **only** vertical position
    source (`EK3_SRC1_POSZ = 2`); the barometer as the EKF source is **not permitted**.
    This is exactly how our aircraft was configured on 2026-08-21, flown **without a
    safety protocol** — and EKF3 never fused a single height measurement. The vertical
    estimate diverged **quadratically while the aircraft stood on the floor** — −268 m
    after 90 seconds, **−1070 m** after three minutes, with an indicated "climb rate" of
    −12.6 m/s on a motionless vehicle. The first altitude-controlled mode (a fence-forced
    LAND) then chased that estimate to 100 % throttle and flew the aircraft into the hall
    ceiling. We may **not** fix this by moving the EKF back to the barometer — that is
    what the task forbids. We fly `POSZ = 2` under the safety protocol documented on
    [Position & Altitude Hold](../autopilot/position-altitude-hold.md), and we are still
    investigating why fusion never engaged: a colleague team flies the same sensor with
    `POSZ = 2` successfully, so the next step is a full parameter diff against their
    aircraft. Full chain of events:
    [incident analysis](../problems/incident-analysis-2026-08-21.md).

Why does this fail so badly? A rangefinder on a resting aircraft reports a
**constant** value (0.02 m, forever). A constant reading carries no absolute height
information: the filter cannot tell "vehicle height" and "terrain offset" apart, the
two become jointly unobservable and drift together, and the filter is left
integrating raw vertical accelerometer data with nothing ever correcting it. Hence
the quadratic divergence — the signature of pure double integration of a bias.

The barometer, by contrast, is an absolute pressure reference. It is noisy near the
ground (the downwash spike above) but it never *diverges*: in the same crash logs
`CTUN.BAlt` stayed within ±0.4 m the whole time the EKF estimate ran away by a
kilometre. That is exactly why we keep the barometer logging as an **independent
witness** against the EKF estimate, even though the assignment forbids it as the EKF
source.

## The division of labour

| Role | Sensor | Parameter |
|---|---|---|
| EKF height source (**mandated**) | **LiDAR rangefinder** | `EK3_SRC1_POSZ = 2`, flown only under the safety protocol |
| Optical-flow scaling & low-altitude terrain reference | **LiDAR rangefinder** | rangefinder configured as above |
| Independent height witness in the logs | **Barometer** | not an EKF source, a cross-check reference only |

This is how the EKF sources are documented on
[Position & Altitude Hold](../autopilot/position-altitude-hold.md); the safe-overrides
parameter file carries the mandated `EK3_SRC1_POSZ = 2` together with the protocol
parameters (fence off, `ARMING_CHECK = 786390`, `RNGFND1_GNDCLEAR = 2`).

!!! info "Status"
    The rangefinder itself is configured, verified on the real aircraft and healthy in
    every log. The mandated `EK3_SRC1_POSZ = 2` lives in the safe-overrides parameter
    file alongside the protocol parameters, and is applied when the FC is restored after
    the post-crash barometer/I2C repair. Why the on-ground fusion did not engage is still
    open — a parameter diff against a team flying the same sensor with `POSZ = 2` is the
    next step — so the aircraft has not yet flown the mandated, protocol-guarded
    configuration.
