# Servo Mechanism

The implemented release: a **9 g micro servo** whose arm holds the payload
closed and swings clear on command. On the real aircraft the servo is wired to
the **Raspberry Pi**, not to the flight controller — the Pi generates the PWM
itself, and the FC is not involved in the drop at all.

## Wiring (real aircraft)

| Servo wire | Goes to | Notes |
|---|---|---|
| Signal (orange/white) | **Pi GPIO18** (BCM numbering = **physical pin 12**) | hardware-PWM capable pin; configurable via `drop_gpio_pin` in `config.py` |
| Power (red) | **separate 5 V BEC** | **never the Pi's 5 V pin** — see warning below |
| Ground (brown/black) | BEC ground **and** Pi ground | common ground is mandatory, or the PWM signal has no reference |

!!! danger "Power the servo from its own BEC"
    A micro servo's stall/inrush current can **brown out a Pi Zero 2 W and
    reboot it mid-flight** — which kills the companion process while the
    aircraft is armed. Only the signal wire touches the Pi; the servo's 5 V
    comes from a separate BEC, with a common ground between BEC and Pi.

## PWM signal

Standard hobby-servo PWM at **50 Hz** (20 ms frame):

| State | Pulse width | Config value |
|---|---|---|
| Hatch **closed** (neutral, set at startup) | **1100 µs** | `neutral_pwm` |
| Hatch **open** (release) | **1900 µs** | `drop_pwm` |

`PiServo` maps these microsecond values onto gpiozero's `[-1, 1]` range over
the standard 1000–2000 µs band. Both values are plain config entries — adjust
them to whatever the actual servo + linkage needs, don't force the mechanism
to fit the numbers.

## Software stack on the Pi: gpiozero + lgpio — **not pigpio**

```bash
sudo apt install python3-gpiozero python3-lgpio
```

!!! warning "Do not follow older guides that install pigpio"
    The pigpio daemon was **removed from Debian 13 (trixie)**, which our
    Raspberry Pi OS is based on: `apt install pigpio` fails with *"has no
    installation candidate"*, and forcing `GPIOZERO_PIN_FACTORY=pigpio` makes
    `Servo()` raise `BadPinFactory` — inside the mechanism's `setup()`, so the
    mission would die on the ground before ever arming. Verified on our real
    Pi: gpiozero selects **`LGPIOFactory`** by default, which drives the pin
    through the kernel's GPIO character device — no daemon, no configuration.
    Check with:

    ```bash
    python3 -c "from gpiozero import Device; Device.ensure_pin_factory(); print(type(Device.pin_factory).__name__)"
    # -> LGPIOFactory
    ```

## Open-loop — bench-test before every flight

A GPIO output has no read-back, so the release is **open-loop**: `confirm()`
trusts the commanded pulse. That makes the bench test the only verification
there is:

- [ ] `neutral_pwm` (1100 µs) holds the mechanism firmly closed — no creep,
      no buzzing against an end stop.
- [ ] `drop_pwm` (1900 µs) opens it cleanly and the payload actually falls.
- [ ] Repeat with the payload loaded — a servo that moves freely empty can
      stall under load.

## Alternative wiring: servo on an FC output (used in SITL)

The same mission code can drive a servo on a flight-controller AUX output
instead. Pi-Code sends MAVLink `DO_SET_SERVO`, and the FC generates the PWM:

| `release_mechanism` | Class | Servo wired to | Signal path |
|---|---|---|---|
| `"pi"` — our indoor build | `PiServo` | Pi GPIO18 | Pi generates PWM directly |
| `"fc"` — SITL / tests | `FcServo` | FC AUX output (`SERVO9`) | Pi → `DO_SET_SERVO` → FC → servo |

For the FC path, `SERVOx_FUNCTION = 0` (Disabled) must be set so the FC lets
`DO_SET_SERVO` control the output — `FcServo.setup()` writes that
automatically. This is the path SITL uses (there is no GPIO on a Mac), and it
has one advantage the Pi path lacks: SITL echoes the servo value back, so the
drop is actually *verified* in simulation, not just commanded.

## How Pi-Code triggers the drop

Both variants sit behind one small interface in `release.py`
(`ReleaseMechanism`: `setup()` / `reset()` / `drop()` / `confirm()`), selected
by `config.release_mechanism`. The state machine programs against the
interface only, so the mission logic is **identical** in SITL and on the real
aircraft:

```mermaid
stateDiagram-v2
    direction LR
    SEARCH --> APPROACH : pad detected
    APPROACH --> DROP : centred over pad
    DROP --> RECOVER : drop() + confirm()
```

- At startup (IDLE) the mechanism's `setup()` runs and `reset()` drives the
  servo to the closed position — a reboot can never leave the hatch open.
- In the **DROP** state the mission calls `drop()`, then `confirm()`; on the
  Pi path `confirm()` always returns `True` (open-loop), on the FC path it
  compares the FC's servo read-back against `drop_pwm`.
- The staged bring-up decouples flying from dropping: **milestone 4** sets
  `skip_drop = True` — the drone searches, detects and centres over the pad
  but releases nothing, so after a clean milestone-4 flight only the release
  itself is untested. **Milestone 5** is the full delivery.

## Status

!!! info "Status (2026-08-22)"
    - **Software stack verified on the real Pi:** gpiozero selects the
      `lgpio` backend as documented, and the full mission-to-drop chain is
      validated in SITL
      via the `FcServo` path (with read-back confirmation).
    - **Open:** a real **drop in flight** has not happened yet (aircraft
      grounded after the [2026-08-21 incident](../problems/incident-analysis-2026-08-21.md)),
      and the **3D-printed servo/payload housing is still pending** — see
      [3D Printing](3d-printing.md) for its requirements and
      [Frame Extension](../frame/index.md) for the platform it mounts to.
