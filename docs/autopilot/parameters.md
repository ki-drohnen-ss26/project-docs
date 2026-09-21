# Flight Parameters

The configuration *is* the aircraft: this page is the single written reference for the
parameter set that defines how our drone flies, and for the rule that governs **who is
allowed to change it**.

## Ownership: one source of truth (2026-08-24)

Every flight-controller parameter is set in **exactly one place — Mission Planner —
against the published, versioned flight parameter set**. The companion computer
**never writes a parameter**. Before every mission it reads a curated subset of the
flight parameters back and **verifies** them read-only against the published set, and it
refuses to fly when a flight-critical value differs (abort reason
`FC_PARAMS_MISMATCH`); it does not "fix" anything on the FC. Until that check moved into
the mission start-up, only the manual `preflight.py` tool compared the two.

Two reasons drove this decision:

- **Single source of truth.** A parameter has one owner and one authoritative file.
  There is no second actor quietly changing values, so "what is on the aircraft" is
  answerable by looking at one place instead of reconstructing the union of Mission
  Planner and whatever the companion happened to write on its last run.
- **No surprise overwrites.** A companion that writes parameters leaves them behind.
  The [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md) chain included
  exactly this failure mode: a companion-written geofence outlived the run that created
  it and ambushed a later, purely manual flight. Parameters persist across power cycles
  and outlive the process that wrote them — so no process except the human-driven GCS
  session writes them.

!!! note "The enforcement code was removed entirely (2026-08-25)"
    The companion's old parameter-writing machinery (the "safety envelope") — once kept
    behind an `enforce_safety_envelope` opt-in in `config.py` — was **deleted on
    2026-08-25**. The doctrine above had already reduced it to dead code, so the flag,
    `setup_safety_envelope()`, `restore_params()`, `recover_stale_params()` and the
    `logs/fc_params_backup.json` mirror are all gone. The companion is now **structurally
    read-only** towards FC parameters: there is no code path that writes one (the sole
    exception is the SITL drop-servo `SERVO9_FUNCTION=0` setup, which never runs on the
    real aircraft). The SITL indoor limits live in the flight set's SITL mirror
    (`params/sitl_flight_v2.parm`); the FC is configured in Mission Planner, full stop.

### The stale-fence check: refuse, don't rewrite

The companion still *detects* a geofence that was left enabled by an earlier run or
suggested by Mission Planner. What changed is the response: it no longer writes
`FENCE_ENABLE=0` to clear it. It **refuses to fly** (abort reason
`UNEXPECTED_FENCE_ENABLED`) and tells you to disable the fence in Mission Planner before
flying. Detection stayed; writing went.

## The published set

<div class="result" markdown>

:material-download: **[Download `2026_08_24_v2_params.param`](../assets/2026_08_24_v2_params.param)**
— the full 1159-parameter flight set, copied from the aircraft on 2026-08-24
(`params/flight_v2.param` in the Pi-Code repository).

</div>

The SITL parameter mirror (`params/sitl_flight_v2.parm`) is **generated from this set** so
the simulator tests the same behavioural parameters we fly — see
[Testing the Companion Code in SITL](../software/sitl-testing.md).

Publishing a new version is two commands in the Pi-Code repository: `python dumpparams.py`
captures the aircraft into `params/flight_v<next>.param`, then
`python params/generate_sitl_flight_params.py` regenerates the SITL mirror from it. The
mission parameter check and `preflight.py` both resolve the highest published version
automatically, so they follow the new file without an edit.

!!! info "A v3 will supersede this file"
    `v2` does not yet contain the flight-mode switch mapping (`FLTMODE1`–`FLTMODE6` are
    all `0` in this file — the mapping is done on the transmitter for now). **`v3` adds
    that mapping** and becomes the authoritative set once published. Always fly the
    highest published version.

## The parameters that define this aircraft

The full set is 1159 parameters; the ~35 below are the ones that make *this* airframe
what it is. All values are taken verbatim from the published `v2` file — verify against
it, do not memorise.

### Frame

| Parameter | Value | Why |
|---|---|---|
| `FRAME_CLASS` | `1` | Quadcopter |
| `FRAME_TYPE` | `1` | X configuration |

### EKF sources — indoor, GPS-denied

Full rationale on the [Position & Altitude Hold](position-altitude-hold.md) page.

| Parameter | Value | Why |
|---|---|---|
| `AHRS_EKF_TYPE` | `3` | EKF3 is the active estimator |
| `EK3_ENABLE` | `1` | EKF3 enabled |
| `EK3_SRC1_POSXY` | `0` | No absolute horizontal position exists indoors (None) |
| `EK3_SRC1_VELXY` | `5` | Horizontal velocity from optical flow (MTF-01P) |
| `EK3_SRC1_POSZ` | `2` | **Height from the rangefinder** |
| `EK3_SRC1_VELZ` | `0` | No vertical-velocity sensor (None) |
| `EK3_SRC1_YAW` | `1` | Heading from the compass |

### Rangefinder & optical flow (MTF-01P on SERIAL5)

| Parameter | Value | Why |
|---|---|---|
| `RNGFND1_TYPE` | `10` | MAVLink rangefinder (the MTF-01P streams `DISTANCE_SENSOR`) |
| `RNGFND1_ORIENT` | `25` | Facing straight down |
| `RNGFND1_MIN_CM` | `1` | Minimum valid range (4.6.3 `_CM` name) |
| `RNGFND1_MAX_CM` | `800` | Maximum valid range, 8 m (4.6.3 `_CM` name) |
| `RNGFND1_GNDCLEAR` | `10` | Ground clearance when landed — **kept at 10, an open item** (see below) |
| `FLOW_TYPE` | `5` | MAVLink optical flow |
| `SERIAL5_PROTOCOL` | `1` | MAVLink1 on the MTF-01P port |
| `SERIAL5_BAUD` | `115` | 115200 baud for the MTF-01P |

### Failsafes & battery

Indoors every failsafe action is **Land**, never RTL (RTL climbs first — into the
ceiling).

| Parameter | Value | Why |
|---|---|---|
| `FS_THR_ENABLE` | `3` | Radio failsafe active (Land) |
| `FS_THR_VALUE` | `975` | PWM below which the radio link counts as lost |
| `FS_GCS_ENABLE` | `0` | No GCS failsafe — the companion, not a GCS, is the control link |
| `FS_EKF_ACTION` | `1` | EKF failsafe → Land |
| `FS_EKF_THRESH` | `0.8` | EKF variance threshold that triggers the failsafe |
| `FS_OPTIONS` | `16` | Continue the mission-relevant behaviour per ArduPilot option bits |
| `BATT_LOW_VOLT` | `12.4` | Low-battery threshold — **kept at 12.4** (see below) |
| `BATT_CRT_VOLT` | `12` | Critical-battery threshold |
| `BATT_FS_LOW_ACT` | `1` | Low battery → Land |
| `BATT_FS_CRT_ACT` | `1` | Critical battery → Land |
| `BATT_LOW_TIMER` | `10` | Seconds below threshold before the failsafe fires |
| `BATT_CAPACITY` | `3300` | Pack capacity (mAh) for the fuel gauge |

### Arming checks

| Parameter | Value | Why |
|---|---|---|
| `ARMING_CHECK` | `41350` | Bitmask — **kept at 41350** (decoded below) |

### Navigation limits

Walked back from ArduPilot's open-sky defaults to hall-safe values.

| Parameter | Value | Why |
|---|---|---|
| `WPNAV_SPEED` | `100` | Horizontal cruise 1.0 m/s indoors |
| `WPNAV_SPEED_UP` | `50` | Climb 0.5 m/s |
| `WPNAV_SPEED_DN` | `150` | Descent 1.5 m/s |
| `WPNAV_ACCEL` | `250` | Gentle horizontal acceleration (cm/s²) |
| `WPNAV_RADIUS` | `200` | Waypoint-reached radius (cm) |
| `PILOT_SPEED_UP` | `250` | Max pilot-commanded climb rate (cm/s) |
| `RTL_ALT` | `200` | Low RTL altitude (cm) — RTL is not used indoors, but kept sane |

### Geofence — disabled on this set

| Parameter | Value | Why |
|---|---|---|
| `FENCE_ENABLE` | `0` | **Off.** No baro-referenced threshold near the ground; the companion refuses to fly if it finds this enabled |
| `FENCE_TYPE` | `7` | (Configured shape, inert while disabled) |
| `FENCE_ALT_MAX` | `120` | (Inert while disabled) |
| `FENCE_RADIUS` | `150` | (Inert while disabled) |

### Key tuning

| Parameter | Value | Why |
|---|---|---|
| `ATC_RAT_PIT_P` | `0.0675` | Pitch rate P — **halved** from v1 (`0.135`), the oscillation fix |
| `ATC_RAT_PIT_I` | `0.0675` | Pitch rate I — halved from v1 (`0.135`) |
| `ATC_RAT_PIT_D` | `0.0018` | Pitch rate D — halved from v1 (`0.0036`) |
| `ATC_RAT_RLL_P` | `0.0675` | Roll rate P — halved from v1 (`0.135`) |
| `ATC_RAT_RLL_I` | `0.0675` | Roll rate I — halved from v1 (`0.135`) |
| `ATC_RAT_RLL_D` | `0.0018` | Roll rate D — halved from v1 (`0.0036`) |
| `MOT_THST_HOVER` | `0.1953294` | **Learned** hover throttle (~19.5 %) |
| `MOT_THST_EXPO` | `0.43` | Thrust-curve linearisation for these motors/props |
| `MOT_PWM_TYPE` | `6` | **DShot600** ESC protocol (bi-directional for RPM telemetry) |
| `MOT_SPIN_ARM` | `0.06` | Motor output when armed and idle |
| `MOT_SPIN_MIN` | `0.1` | Minimum in-flight motor output |

### Flight modes (switch mapping) — lands in v3

| Parameter | Value | Why |
|---|---|---|
| `FLTMODE_CH` | `5` | Mode switch is on RC channel 5 |
| `FLTMODE1`–`FLTMODE6` | `0` | Not mapped here yet — the mapping is on the transmitter, and **arrives in `v3`** |

## Team decisions vs. recommendations

Several values are **deliberate team choices** that differ from a recommendation. They
are decisions, not oversights — recorded here so nobody "corrects" them by accident.

!!! warning "Where we knowingly differ from a recommendation"
    - **`BATT_LOW_VOLT` kept at `12.4`** — the recommendation was `12.8`. Kept lower for
      now to preserve usable flight time; revisit if low-battery Lands trigger too late.
    - **`ARMING_CHECK` kept at `41350`** — the recommendation `786390` (which additionally
      includes the INS and RC checks) was **declined for now**. `41350` decodes to
      **Baro (2) + Compass (4) + Board voltage (128) + Battery (256) + System (8192) +
      RangeFinder (32768)** = 41350. The declined `786390` adds INS and RC groups on top.
    - **`RNGFND1_GNDCLEAR` still `10`** — `2` was recommended (the sensor sits ~2 cm above
      the ground). Left at `10` for now; this is an **open** item, and a candidate suspect
      in the on-ground EKF-height investigation on the
      [Position & Altitude Hold](position-altitude-hold.md) page.
    - **`RNGFND1_MIN_CM = 1` now under review** — a SITL 2×2 matrix (2026-08-25) showed the
      on-ground EKF-fusion blocker is this **validity floor**, not the height source: SITL's
      landed rangefinder reads `0.00 m`, so `MIN_CM 1` marks it out-of-range-low and no
      fusion starts, while `MIN_CM 0` fuses immediately. The SITL mirror already forces
      `MIN_CM 0`; the real aircraft sits only **1 cm above** the floor (reads `0.02 m`),
      making `RNGFND1_MIN_CM = 0` a concrete, evidence-backed option for the team — the
      change would go through Mission Planner. See the
      [Position & Altitude Hold](position-altitude-hold.md) investigation.
    - **Flight-mode mapping lives on the transmitter** meanwhile (so `FLTMODE1`–`6` are
      `0` in `v2`); it moves into the parameter set in **`v3`**.

## Changelog: v1 → v2

| Change | v1 → v2 | Why |
|---|---|---|
| Rate-loop PID **halved** | `ATC_RAT_{PIT,RLL}_{P,I}` `0.135` → `0.0675`, `_D` `0.0036` → `0.0018` | Removed the attitude oscillation seen on v1 |
| Geofence **off** | `FENCE_ENABLE` `1` → `0` | No baro-referenced fence in the near-ground noise band (the crash trigger) |
| Low-battery action → **Land** | `BATT_FS_LOW_ACT` `2` → `1` | Land indoors, never RTL |
| Hover throttle **learned** | `MOT_THST_HOVER` learned to `0.1953294` | Correct feed-forward for altitude control |

With `EK3_SRC1_POSZ = 2` and this tuning, **AltHold and Loiter both work on the real
aircraft** (verified 2026-08-24).
