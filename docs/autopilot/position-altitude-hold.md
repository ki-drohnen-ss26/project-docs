# Position & Altitude Hold

Indoors there is no GPS, so "position hold" is not a feature you switch on — it is the
product of an **EKF3 state estimate** built from the sensors we chose. This page
explains how the assisted flight modes depend on that estimate, how the EKF's sources
are configured for our indoor aircraft, and how to verify the estimate *before* it
flies — because when the estimate is wrong, the controllers chase it with full
authority. Ours did.

## How the flight modes use the EKF

ArduPilot's modes form a ladder: each rung hands one more control loop to the
autopilot, and each loop needs one more piece of the EKF estimate to be valid.

| Mode | Autopilot controls | Needs from the EKF |
|---|---|---|
| **Stabilize** | attitude only — throttle is the pilot's | attitude (gyro/accel), always available |
| **AltHold** | attitude + **altitude** | a valid **height** estimate |
| **Loiter / PosHold** | attitude + altitude + **horizontal position** | height **and** a horizontal position/velocity estimate |
| **Guided** | everything — flies position/velocity targets from the companion computer | full position estimate; indoors that means the flow/rangefinder chain below |

The ladder is also the risk model: a broken height estimate is harmless in Stabilize
and catastrophic in any altitude-controlled mode. Our crash happened the moment a
fence breach forced the vehicle *out of* Stabilize *into* LAND — the first
altitude-controlled mode of the flight.

## EKF sources for indoor flight

EKF3 lets each axis of the estimate take its measurement from a different sensor
(`EK3_SRC1_*`). The GPS defaults vs. our indoor configuration:

| Parameter | Default (GPS) | **Indoor (ours)** | Meaning |
|---|---|---|---|
| `EK3_SRC1_POSXY` | 3 (GPS) | **0 (None)** | no absolute horizontal position exists indoors |
| `EK3_SRC1_VELXY` | 3 (GPS) | **5 (Optical Flow)** | MTF-01P flow supplies horizontal velocity |
| `EK3_SRC1_POSZ` | 1 (Baro) | **2 (Range Finder)** — mandated | height comes from the LiDAR rangefinder, flown only under the safety protocol |
| `EK3_SRC1_VELZ` | 3 (GPS) | **0 (None)** | no sensor for vertical velocity |
| `EK3_SRC1_YAW` | 1 (Compass) | **1 (Compass)** | heading reference |
| `EK3_SRC_OPTIONS` | 0 | **0** | do not fuse all velocity sources at once |

Two subtleties in that table carry the whole story:

**Optical flow is a velocity, not a position — and it needs height.** Flow measures an
*angular* rate; converting it into metres per second requires the height above ground,
which comes from the MTF-01P's rangefinder. With flow as the only horizontal source the
EKF provides a **relative** position estimate (`EKF_POS_HORIZ_REL`), good enough for
local-NED navigation but anchored to nothing absolute.

**`EK3_SRC1_POSZ` is 2 (Range Finder), as the assignment mandates.** The barometer is
not permitted as the EKF height source; the rangefinder is the height source and the
barometer stays only as an independent witness in the logs. This is the configuration
that crashed us when flown without mitigations, so it is flown only under the safety
protocol below.

## Why `EK3_SRC1_POSZ = 2` crashed the aircraft — and how we fly it now

Our aircraft flew with the rangefinder as the **only** EKF height source. On the ground
the rangefinder reads a constant ~0.02 m — a constant carries no usable height
information, so EKF3 never fused a single height measurement. The vertical estimate
became pure inertial integration of accelerometer bias and diverged **quadratically
while the aircraft stood on the floor**: −268 m after 90 s, −1070 m after three
minutes. When a fence breach forced LAND, the altitude controller tried to arrest a
1000 m descent that only existed in the filter and went to 100 % throttle — into the
hall ceiling. The full chain (fence sized inside the baro's downwash noise band,
`ARMING_CHECK = 0` letting it arm at all) is analysed in the
**[incident report](../problems/incident-analysis-2026-08-21.md)**. The rangefinder hardware was
*not* at fault — it tracked the fatal climb sample by sample; the configuration made
its healthy readings meaningless.

One related lesson for anyone reproducing this: the barometer spikes **4–6.7 m** on
every takeoff from propeller downwash. Baro height is trustworthy in flight, but never
place a fence or a decision threshold inside that near-ground noise band.

The assignment mandates the rangefinder as the EKF height source, so "switch back to the
barometer" is not an available fix — the crash above is the documented failure mode of
exactly the configuration we are required to fly. We therefore fly `EK3_SRC1_POSZ = 2`
deliberately, under a safety protocol implemented in the Pi-Code companion:

- a ground-drift GO/NO-GO in `preflight.py` before every arming, plus a bench hand-lift
  test proving the EKF altitude follows a real lift;
- `ARMING_CHECK = 786390` and the geofence off (no baro-referenced threshold near the
  ground);
- a rangefinder-gated pilot takeover that refuses when the EKF altitude and the raw
  rangefinder disagree;
- a continuous in-flight EKF-vs-rangefinder cross-check (`EKF_ALT_DIVERGED` → LAND);
- `RNGFND1_GNDCLEAR = 2 cm` aligned with the true mounting height, so the reading the
  EKF expects when landed matches reality.

Why the on-ground fusion never engaged is **still under investigation**. A colleague
team flies the same sensor with `POSZ = 2` successfully, so the next step is a full
parameter diff against their aircraft — hot suspects are `RNGFND1_GNDCLEAR` (ours was
the 10 cm default while the sensor sits ~2 cm up), `RNGFND1_MIN_CM` and `EK3_ALT_M_NSE`;
the alternative explanation is that their EKF drifts on the ground too but is simply
never left standing for minutes. The barometer remains an independent witness in the
logs — never the EKF source.

## The on-ground deadlock, and the pilot takeover

A flow-only vehicle may not report `EKF_POS_HORIZ_REL` while it sits on the floor:
optical flow needs height above ground before the filter trusts it, and there is no
height without a takeoff. A companion that insists on a position estimate *before*
arming therefore deadlocks — no estimate without flying, no flying without the
estimate.

The designed escape is the companion's `--takeover` mode: the **pilot flies the first
metre by hand** (Stabilize/AltHold), and the companion requests GUIDED only once the
aircraft is above ~0.8 m *and* the EKF reports a usable position estimate. Since the
crash, that handover gate additionally checks the **rangefinder** height and refuses
when EKF and rangefinder disagree — the EKF altitude alone had read +1070 m *on the
floor* and would have handed over instantly.

## Verifying the estimate before flight

Two procedures, both from the Pi-Code companion repo, both possible with props off:

**1. `preflight.py` — the standing-still check.** Read-only FC inspection: parameters,
sensor health, EKF status flags, and an **EKF-altitude drift check** while the aircraft
is disarmed and motionless. The divergence that killed us is quadratic, so even its
first seconds are visible from the ground — twenty seconds of `preflight.py` would have
flagged it before any of the crash-day flights. It also mirrors live `STATUSTEXT`, so
"try to arm while it runs" shows the autopilot's own objection verbatim.

**2. Hand-lift test with `fclog.py` running.** `fclog.py` continuously records every
`STATUSTEXT`, mode change and EKF-flag transition. With it running (props **off**),
lift the aircraft by hand to about a metre and set it back down. The log must show the
rangefinder-derived height following the lift and the EKF position flags coming up —
on the ground a dead rangefinder and a healthy one both read ~0 m, so only a height
*change* proves the chain works. The mission code runs the same idea in the air:
`verify_rangefinder_tracks_altitude()` right after every takeoff.

!!! info "Status: real-flight validation still open"
    The source configuration and both verification procedures are validated **in SITL
    on ArduCopter 4.6.3** (the indoor mission flies green with flow + rangefinder, GPS
    off). The real aircraft has been grounded since the 2026-08-21 crash
    (barometer/I2C repair pending), so no real flight has yet flown the mandated
    `EK3_SRC1_POSZ = 2` under the full safety protocol — that validation, together with
    the pending parameter diff against the working team, is the first flight test once
    the aircraft is repaired.
