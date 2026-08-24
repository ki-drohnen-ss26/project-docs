# ArduPilot Setup

This page is the compact summary of how ArduPilot gets onto the aircraft and into a
flyable configuration. The **full step-by-step walkthrough** — every calibration screen,
every parameter, every troubleshooting case — lives in
**[Drone Initial Setup](../hardware/drone/InitialSetup.md)**; read that page when you
actually perform the setup. Here we cover the shape of the process and the one topic
that deserves its own section: **parameter hygiene**.

## Firmware: 4.6.3, custom-built

Everything is pinned to **ArduCopter 4.6.3** (stable). The stock
[`FlywooF745` build](https://firmware.ardupilot.org/Copter/stable-4.6.3/FlywooF745/)
is enough for manual flying, but our autonomy stack needs three features that are not
in the default build for this 1 MB-flash target. They are selected on
[custom.ardupilot.org](https://custom.ardupilot.org/) (choose **Copter → the 4.6.3
stable tag → FlywooF745**, never "latest"):

| Build option | Why we need it |
|---|---|
| MAVLink optical flow sensor | the MTF-01P delivers flow data as MAVLink messages on SERIAL5 |
| OpticalFlow fusion for EKF3 | the EKF must be able to *use* that flow as a velocity source indoors |
| Enable Mode Guided NoGPS | the companion computer commands the aircraft in GUIDED without a GPS fix |

Download the file ending in **`_bl.hex`** — it includes the bootloader, which matters
for the flashing method below.

## Flashing via DFU + STM32CubeProgrammer

1. Hold the FC's **boot button** while plugging in USB → the STM32F745 enters DFU mode.
2. Connect with [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html)
   (connection type USB).
3. **Full chip erase**, then program the downloaded `_bl.hex`.
4. Disconnect, power-cycle, connect with Mission Planner and **verify the version
   banner says 4.6.3** before touching anything else.

Screenshots of every step: [Initial Setup → Installation of Ardupilot](../hardware/drone/InitialSetup.md#installaltion-of-ardupilot).

## Mandatory-hardware checklist

After flashing, the aircraft is configured in Mission Planner. This is the order; each
item is a section of the [detailed guide](../hardware/drone/InitialSetup.md):

- [ ] **Frame type** — Quad X
- [ ] **Initial tuning parameters** — 3.5" props, 4S Li-Ion (4.1 V/cell full, 2.8 V/cell empty)
- [ ] **Board orientation** (`AHRS_ORIENTATION`) verified against the HUD, then **accel calibration**
- [ ] **Compass calibration**
- [ ] **Radio calibration** (stick centres at 1500, `RC1_TRIM`/`RC2_TRIM` if not)
- [ ] **Motor order and direction** via motor test — a wrong motor map crashes on the first takeoff
- [ ] **ESC / DShot600 setup** (`MOT_PWM_TYPE = 6`, bi-directional DShot for RPM telemetry)
- [ ] **Serial ports** per the wiring: Pi companion on SERIAL4 (MAVLink2, 921600), MTF-01P on SERIAL5 (MAVLink1, 115200), GPS on SERIAL6
- [ ] **Flight modes** on the transmitter switch
- [ ] **Failsafes** — indoors always *Land*, never RTL (RTL climbs first — into the ceiling)
- [ ] **Logging** to the 16 MB SPI flash (`LOG_BACKEND_TYPE = 4`; no SD slot on this FC)
- [ ] **Indoor EKF sources** — see [Position & Altitude Hold](position-altitude-hold.md)

## Parameter hygiene

Configuration *is* the aircraft: two identical airframes with different parameter sets
fly completely differently, and our crash chain was made of three parameter values.
Rules we now follow without exception:

1. **Save the full parameter list to a file before any change** (Mission Planner:
   Full Parameter List → *Save to file*). The *Compare Params* button then shows
   exactly what a later change touched.
2. **Parameter names are firmware-version-specific.** 4.7 renamed
   `RNGFND1_MIN_CM`/`RNGFND1_MAX_CM` (cm) to `RNGFND1_MIN`/`RNGFND1_MAX` (m) and
   `RTL_ALT` (cm) to `RTL_ALT_M` (m). A `.parm` file only makes sense together with the
   version it was captured from.
3. **Unknown names are silently ignored.** Loading a file with 4.7 names onto 4.6.3
   produces *no error* — the parameter simply keeps its old value. A setup can "load
   fine" and leave the rangefinder unusable. Always read values back after writing;
   the companion repo's `setparam.py` does exactly that (set + read-back verification).

### Our recovered baseline

The custom-firmware flash after the [2026-08-21 crash](../problems/incident-analysis-2026-08-21.md)
**wiped every parameter to firmware defaults**. The aircraft's configuration survived
only because ArduPilot writes all parameters into its own dataflash log at boot — the
baseline was reconstructed from the crash day's log. It lives in the Pi-Code repository
under `params/`:

| File | Content |
|---|---|
| `params/fc_baseline_463_20260821.parm` | Full real-FC baseline (1154 parameters, incl. accel calibration, ESC/servo setup, MTF-01P and Pi serial config). **Byte-faithful to the crash-day state — contains the crash configuration.** |
| `params/fc_safe_overrides.parm` | The corrections from the crash analysis: fence off, `EK3_SRC1_POSZ = 1` (baro, not rangefinder), `ARMING_CHECK = 786390`, `BATT_LOW_VOLT = 12.8`. |

!!! danger "Load order is mandatory"
    The baseline alone restores the configuration **that crashed the aircraft**.
    Restore always in this order:

    1. Load `fc_baseline_463_20260821.parm`
    2. Load `fc_safe_overrides.parm` on top
    3. Reboot the FC
    4. Run `python preflight.py` from Pi-Code (sensor health + EKF-drift verdict)

    The `sitl_*.parm` files in the same folder are **SITL artefacts** — they load
    cleanly onto the real FC (same firmware version!) and would silently replace its
    tuning, sensor backends and serial wiring. Never load them onto the aircraft.

!!! info "Status"
    Restoring the baseline onto the real FC is **blocked**: stock 4.6.3 currently halts
    at boot with a barometer initialisation error (suspected I2C-bus damage from the
    crash — see the [incident report](../problems/incident-analysis-2026-08-21.md)). The load
    order above has been rehearsed against SITL; the real restore happens once the
    baro/I2C repair is done.
