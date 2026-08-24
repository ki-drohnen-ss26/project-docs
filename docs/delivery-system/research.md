# Research & Concepts

Before building anything we compared the common ways drones release a payload.
The decision is dominated by our platform: a **3.5-inch CineWhoop**
(SpeedyBee BEE35 Pro) flying **indoors**. That means:

- **Tiny mass budget.** The frame already carries a GPS mast, the MTF-01P,
  a Raspberry Pi Zero 2, an AI camera and an FPV system on 2004-size motors.
  Every mechanism gram is a gram off the payload and off the hover margin.
- **Prop-guard clearance.** The ducts sit close to the body; anything that
  hangs low or swings sideways can touch a duct or shift the CG.
- **Indoors = no GPS.** Position holding comes from optical flow, which is
  good to roughly tens of centimetres, not the centimetre-level precision that
  a docking-style mechanism would need.
- **Simple electronics preferred.** The companion Pi has free GPIO pins and a
  5 V BEC is available; high-current switching hardware is extra weight and
  extra failure modes.

## Options compared

### 1. Servo trapdoor / pin release ← chosen

A micro servo either opens a small hatch under the payload bay or pulls a pin
that lets the payload slide off a hook. One moving part, one PWM signal.

| Pros | Cons |
|---|---|
| Lightest active option: a 9 g servo plus a printed bracket | One-shot per flight — reloading is done by hand on the ground |
| Trivial electronics: one signal wire to a GPIO, servo power from the existing 5 V BEC | Open-loop: no feedback that the payload actually left |
| Release point is fixed and repeatable — position accuracy is whatever the drone's hover accuracy is, no extra precision needed | Drop height = flight height; the payload falls freely, so it must tolerate the drop (soft payload or low release altitude) |
| Fails safe: an unpowered servo simply holds its last position, the payload stays attached | Mechanism must be designed so vibration cannot creep the pin open |

### 2. Servo claw / gripper

Two jaws (or a single lever) actively clamp the payload and open to release.

| Pros | Cons |
|---|---|
| Can grab irregular payloads; also allows *pickup*, not just release | Heavier: bigger servo (holding torque under load) plus jaw structure |
| Positive grip during aggressive maneuvers | Servo draws holding current the whole flight — heat and battery drain |
| | Jaws protrude below/beside the frame, exactly where duct clearance is tight |
| | Pickup would need centimetre-precision positioning we don't have indoors |

### 3. Winch lowering

The payload is lowered on a line by a motorized spool and released at the end,
so the drone can stay high.

| Pros | Cons |
|---|---|
| Gentle delivery — payload touches down at near-zero speed | By far the heaviest and most complex option (motor, spool, line guide, release at the hook) |
| Drone keeps distance from the ground — no downwash interaction at the target | A swinging tethered mass under a 400 g-class quad couples directly into the attitude controller — a real stability risk indoors |
| | Line can snag on the prop guards or on obstacles in the hall |
| | Overkill: our delivery height is 1–2 m indoors anyway |

### 4. Electromagnet

An electromagnet holds a ferromagnetic plate on the payload; cutting the
current releases it.

| Pros | Cons |
|---|---|
| No moving parts at all; release is instant | Continuous current draw for the whole flight just to *hold* — the worst possible trade on a small battery |
| Very simple release logic (one MOSFET) | Power loss (brownout, wiring fault) drops the payload immediately — fails *dangerous*, the opposite of the servo |
| | Payload must carry a steel plate (dead mass) |
| | Holding force vs. coil mass scales badly at this size; jerky flight can shear the payload off |

### 5. Passive hook

No actuator: the payload hangs on an open hook and is released by a flight
maneuver (touching down, dragging it off) or stays attached until a human
takes it.

| Pros | Cons |
|---|---|
| Zero mass beyond the hook, zero electronics, nothing to fail | No commanded release — the mission cannot decide *when* to drop, which defeats Task 5 |
| | Release-by-maneuver needs precise, aggressive flying near the floor — with optical-flow-only position hold that is exactly where the estimate is weakest |
| | Payload can detach unintentionally in any hard maneuver |

## Decision

The **servo pin release** wins on every criterion that matters for this
platform:

1. **Mass and clearance** — a 9 g servo and a printed bracket are the smallest
   footprint of any *active* option, and nothing protrudes into the duct zone.
2. **Fail-safe behaviour** — unpowered = closed. The electromagnet inverts
   this, the gripper needs constant current, the hook cannot be commanded.
3. **Electronics we already have** — one GPIO pin on the Pi and the existing
   5 V BEC. No new power stage, no extra battery load worth measuring.
4. **Precision match** — a fixed release point asks nothing more of the
   position estimate than hovering over the pad, which is exactly what the
   vision + optical-flow stack already does.

The mechanism is deliberately **one-shot and open-loop**: for a graded indoor
demo, one reliable drop per flight beats a reloadable mechanism that adds
mass and failure modes. The implementation is described in
[Servo Mechanism](servo-mechanism.md); the housing that turns the bare servo
into a payload bay is specified in [3D Printing](3d-printing.md).
