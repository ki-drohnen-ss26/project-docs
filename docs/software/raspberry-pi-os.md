# Raspberry Pi OS

The companion computer is a **Raspberry Pi Zero 2 WH** running **Raspberry Pi OS**
(based on **Debian 13 *trixie***). This page is the overview of what has to be true on
the OS side for the companion stack to work; the full step-by-step walkthrough with
screenshots — wiring, `raspi-config`, building mavlink-router, first pymavlink tests —
lives in [Setup Board Computer](../hardware/raspberry-pi.md).

## What the OS has to provide

| Piece | Purpose |
|---|---|
| Hardware UART (`/dev/serial0`) | The MAVLink2 link to the flight controller (FC SERIAL4, 921600 baud) |
| **mavlink-router** (systemd service) | Owns the UART and fans the FC stream out to local UDP consumers |
| Python + **pymavlink** | Runs the Pi-Code mission state machine against `udp 127.0.0.1:14550` |
| **gpiozero + lgpio** | Drives the drop-servo PWM on GPIO 18 (BCM) |
| **picamera2 / IMX500 firmware** | The AI camera stack — see [AI Software](ai-software.md) |

## 1. Free the serial port

Raspberry Pi OS attaches a **login console** to the hardware serial pins (GPIO 14/15)
by default, which blocks any other process from using them. In `sudo raspi-config` →
*Interface Options* → *Serial Port*: answer **No** to the login shell over serial and
**Yes** to enabling the serial port hardware, then reboot. After that, `/dev/serial0`
is free for MAVLink. (Details and screenshots:
[Setup Board Computer](../hardware/raspberry-pi.md).)

## 2. mavlink-router as a systemd service

Only one process can own a UART, but several need the FC stream — the mission script,
the flight recorder, optionally a ground station over Wi-Fi. **mavlink-router** solves
this: it reads `/dev/serial0` and forwards the stream to any number of UDP endpoints.
It was chosen over heavier options (MAVProxy, DroneKit, full companion OS images like
BlueOS/Rpanion) because the Pi Zero 2 W has little CPU to spare and the router does
exactly one job.

Our `/etc/mavlink-router/main.conf` defines:

```ini
[UartEndpoint flightcontroller]
Device = /dev/serial0
Baud = 921600

[UdpEndpoint local_script]
# the mission (main.py) binds here
Mode = normal
Address = 127.0.0.1
Port = 14550

[UdpEndpoint logger]
# second endpoint for the continuous FC recorder (fclog.py) —
# two processes cannot bind the same UDP port
Mode = Normal
Address = 127.0.0.1
Port = 14551
```

A systemd unit starts the router at boot (`systemctl enable mavlink-router`), so the
FC link is up before anyone logs in. Build and service-file instructions:
[Setup Board Computer](../hardware/raspberry-pi.md).

!!! note "The companion talks UDP, not serial"
    Because the router owns `/dev/serial0`, the mission script connects to
    `udp 127.0.0.1:14550` — the **same endpoint string it uses against SITL** on a
    development machine. That is what makes the SITL-first workflow work without code
    changes.

## 3. Python environment

Pi-Code keeps its dependencies minimal and pinned in `requirements.txt` (pymavlink,
pytest). On the Pi, plain `pip` installs them:

```bash
cd Pi-Code
pip install -r requirements.txt
```

The same file drives the development environment on a laptop, so the Pi runs exactly
the library versions the mission was tested with.

## 4. GPIO: gpiozero + lgpio — not pigpio

The drop servo hangs off Pi **GPIO 18** and is pulsed directly by the companion
(1100 µs closed / 1900 µs open, open-loop).

!!! warning "pigpio is gone in Debian 13 (trixie)"
    Most older Raspberry Pi servo guides say "install the pigpio daemon". On trixie,
    `apt install pigpio` fails with *"has no installation candidate"* — the package was
    removed. Do not fight it: install
    ```bash
    sudo apt install python3-gpiozero python3-lgpio
    ```
    gpiozero then selects the **`LGPIOFactory`** backend by default, which drives the
    pin through the kernel's GPIO character device — no daemon, no configuration.
    Verified on our Pi:
    ```bash
    python3 -c "from gpiozero import Device; Device.ensure_pin_factory(); print(type(Device.pin_factory).__name__)"
    # -> LGPIOFactory
    ```

The servo itself is powered from a **separate 5 V BEC**, never from the Pi's 5 V pin —
only the signal wire and a common ground meet the Pi.

## Where to go next

- [Setup Board Computer](../hardware/raspberry-pi.md) — the full walkthrough: wiring
  the UART to the FC, building mavlink-router, the systemd unit, first pymavlink
  scripts
- [AI Software](ai-software.md) — the IMX500 camera stack on top of this OS
- [Software Overview](index.md) — how the Pi fits into the whole stack
