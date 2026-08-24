# Drone (Frame & Flight Controller)

This page covers the airframe and the flight controller — the platform everything
else (sensors, companion computer, drop mechanism) is built on. The step-by-step
firmware installation and parameter setup lives in
[Initial Setup](./drone/InitialSetup.md); tuning is covered in
[Tuning](./drone/Tuning.md).

## Components

| Component | Part |
|---|---|
| Frame | SpeedyBee BEE35 Pro 3.5" CineWhoop frame kit (ducted, with propeller guards) |
| Flight controller | Flywoo GOKU GN745 45A AIO 2-6S (STM32F745 @ 216 MHz, 1 MB flash), AM32 ESCs |
| Firmware | ArduCopter **4.6.3** (FlywooF745 target) — version is pinned, see [Initial Setup](./drone/InitialSetup.md) |
| Motors | Emax Eco II 2004 3000KV (3-6S) |
| Propellers | Gemfan D90-5 90 mm 3.5" ducted 5-blade |
| Receiver | Radiomaster XR4 Gemini dual-band ELRS (see [RC & FPV](./rc-fpv.md)) |
| GPS / compass | HGLRC M100 with integrated compass |
| FPV camera / VTX | RunCam Phoenix 2 / SpeedyBee TX800 (see [RC & FPV](./rc-fpv.md)) |
| Battery | 4S Li-Ion pack (16.4 V full, 11.2 V empty) |
| Additional | MicroAir MTF-01P ([sensor page](./mtf-01p.md)), Raspberry Pi Zero 2 WH ([companion page](./raspberry-pi.md)) |

The GN745 is an *all-in-one* board: flight controller and 45 A 4-in-1 ESC on a
single PCB. That keeps the CineWhoop build compact, but it also means one board
failure can take out both flight control and motor drive.

## Component details

### SpeedyBee BEE35 Pro frame

The [SpeedyBee BEE35 Pro 3.5" CineWhoop frame kit](https://www.speedybee.com/speedybee-bee35-3-5-inch-frame/#Parameters)
is designed for the DJI O3 Air Unit, with dedicated heat-dissipation hardware and
support for other compatible 20×20 video transmitters as well as external action
cameras. For this project its ducts/propeller guards are what matter: they make
indoor flight near people and walls survivable.

### Flywoo GOKU GN745 45A AIO

The [Flywoo GOKU GN745 45A AIO 2-6S AM32](https://flywoo.net/products/goku-gn745-45a-aio-bl_32-mpu6000-v3)
combines the flight controller and a 4-in-1 ESC on a single 33.5 × 33.5 mm board,
reducing wiring, weight and required frame space. At its core sits an STM32F745
32-bit processor at 216 MHz, paired with an onboard gyro, barometer, 16 MB
blackbox storage and seven hardware UARTs. The integrated ESC supports 2S-6S
packs, delivers 45 A continuous and runs AM32 firmware with protocols up to
DShot1200 (we use DShot600).

## FC quirks every rebuilder must know

These are properties of the FlywooF745 hardware definition that are easy to miss
in the datasheet and that directly affected this project.

### One I2C bus — baro and compass share it

!!! danger "The single I2C bus is a single point of failure"
    The FlywooF745 target exposes **exactly one I2C bus**. The onboard barometer
    (BMP280/SPL06/DPS310 at address 0x76) and the external compass inside the GPS
    module both hang off it. A fault anywhere on that bus — a shorted wire, a
    damaged connector, a dying peripheral — can hang the whole bus and take **all**
    I2C devices down at once.

    This is exactly what happened after our
    [crash on 2026-08-21](../problems/incident-analysis-2026-08-21.md): the GPS connector
    was torn off, and afterwards the FC no longer *detected* the barometer at all
    (plus "Bad Compass Health" errors). The hypothesis was confirmed on
    2026-08-24: **bent pins in the GPS connector** had hung the shared bus. After
    straightening them, compass *and* barometer worked again — no chip had died.
    The full story: [crash & barometer recovery](../problems/crash-2026-08-21.md).

    Practical consequence for rebuilders: treat the GPS/compass cable as
    flight-critical wiring even indoors where GPS itself is useless, and after
    *any* hard landing check that the baro is still detected before the next arm.

### 16 MB SPI flash logging — no SD card slot

The board has **no SD card slot**. Dataflash logs go to a 16 MB SPI flash chip
(`LOG_BACKEND_TYPE = 4`), and 16 MB fills up fast:

- Keep `LOG_DISARMED = 0`. Logging while disarmed silently eats the flash while
  the drone sits on the bench, and old logs get overwritten — after our crash the
  crash-day logs were retained (with `LOG_DISARMED = 0`, the default, the flash budget goes to actual flights).
- Full batch-sampler IMU logging (needed for notch-filter tuning) is a lot of
  data; enable it only for tuning flights, not permanently.
- With the companion computer installed, logs can additionally be streamed over
  MAVLink to the Pi (`LOG_BACKEND_TYPE = 2` or `6`), whose SD card is effectively
  unlimited compared to 16 MB. See the logging section of
  [Initial Setup](./drone/InitialSetup.md).

### UART map

Seven UARTs, all in use. This is the wiring as configured on our aircraft
(SERIALn parameter numbering; details in [Initial Setup](./drone/InitialSetup.md)):

| Port | Connected to | Protocol | Baud |
|---|---|---|---|
| SERIAL1 | Telemetry (DJI VTX pad) | MAVLink | 57600 |
| SERIAL2 | Radiomaster XR4 receiver | RCIN (CRSF) | auto |
| SERIAL3 | SpeedyBee TX800 VTX control | IRC Tramp | auto |
| SERIAL4 | Raspberry Pi Zero 2 WH | MAVLink2 | 921600 |
| SERIAL5 | MicroAir MTF-01P | MAVLink1 | 115200 |
| SERIAL6 | HGLRC M100 GPS (UART part) | GPS | 115200 |
| SERIAL7 | ESC telemetry (RX only) | ESC Telemetry | 115200 |

Note the split on the GPS module: the GPS receiver itself talks over UART
(SERIAL6), while its integrated compass is on the shared I2C bus described above.

### ESCs: AM32, DShot600, bi-directional

The integrated 4-in-1 ESC runs **AM32** firmware and is driven with
**DShot600** (`MOT_PWM_TYPE = 6`) — digital, so no ESC PWM calibration is
needed. The documented target setup uses bi-directional DShot (`SERVO_BLH_BDMASK = 15`,
`SERVO_DSHOT_ESC = 1` for AM32, `SERVO_BLH_POLES = 12` for the Eco II 2004's
12 magnets) so the ESCs report per-motor RPM back to the FC; that RPM feed
drives the harmonic notch filters (`INS_HNTCH_MODE = 3`). Full walk-through in
[Initial Setup](./drone/InitialSetup.md).

## Related pages

- [Initial Setup](./drone/InitialSetup.md) — firmware flash, mandatory hardware
  setup, serial ports, EKF sources, indoor failsafes
- [Tuning](./drone/Tuning.md) — PID and filter tuning
- [Incident 2026-08-21](../problems/incident-analysis-2026-08-21.md) — the crash analysis
  referenced throughout this page
