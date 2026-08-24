# Quick Start

Your first session with the delivered kit: from charging the batteries to a first
**manual** flight. Follow the steps in order — the sequence is deliberate, and every
safety rule in here was paid for in burned components or a crash somewhere.

!!! danger "Do not repeat our mistakes"
    If you fly an aircraft that **someone else configured** (a previous team, a
    teammate, your past self after a firmware reflash), check the parameters *before*
    the first arm: look at every `FENCE_*` parameter and at `ARMING_CHECK` in Mission
    Planner. A leftover geofence with `FENCE_ACTION = Land`, combined with disabled
    arming checks and a misconfigured EKF height source, destroyed our drone on
    takeoff — the full chain is analysed in the
    [incident report of 2026-08-21](../problems/incident-analysis-2026-08-21.md). Five minutes
    in the parameter list would have prevented it.

## 1. Charge the flight batteries (Li-Ion, not LiPo!)

The kit contains three **4S Li-Ion** packs and a **SkyRC B6neo+** charger.

- On the charger, select the **Li-Ion** program, **4S**. Li-Ion cells are full at
  ~4.1 V per cell — the pack reads **16.4 V full**. Do **not** use the LiPo program
  (4.2 V/cell): it overcharges Li-Ion cells.
- Treat **11.2 V** (~2.8 V/cell) as empty. Land well before that; our flight
  controller is configured to warn at 12.8 V (`BATT_LOW_VOLT`).
- Charge on a non-flammable surface and stay nearby. Store packs partially charged
  if you will not fly for a while.

## 2. Power the transmitter and goggles (18650 cells)

Both the **Radiomaster GX12** transmitter and the **Skyzone Cobra X** goggles are
powered by **18650 Li-Ion cells**. Insert them with correct polarity (the springs
mark the negative end) and charge them fully before the first session — a
transmitter that browns out mid-flight is an uncommanded aircraft.

## 3. Check the ExpressLRS bind

Transmitter and receiver bind via a shared **binding phrase**, not a button dance:

- Transmitter: Radiomaster GX12, **EdgeTX 2.11.5**, internal ELRS module.
- Receiver on the drone: Radiomaster XR4, **ExpressLRS 4.0.0**.
- Binding phrase: `drone1ffm` / `drone2ffm` / `drone3ffm` — **matching your drone's
  number**. Both sides flashed with the same phrase bind automatically on power-up.

Power the transmitter **first**, then the drone (via the Smoke Stopper, see step 4,
and with **props removed**). The ELRS status on the transmitter should show a link
with telemetry (link quality/RSSI). If it does not, verify both sides carry the same
binding phrase before touching anything else — details in
[RC & FPV](../hardware/rc-fpv.md).

## 4. Smoke Stopper before the first battery plug — every "first" plug

!!! warning "Non-negotiable"
    The **first time** a battery is connected to the drone — and again after *any*
    soldering, rewiring, or crash — connect it **through the Smoke Stopper**. It is
    a current-limited adapter: a short circuit lights its bulb instead of vaporising
    a trace on the AIO board. The flight controller and 45 A ESC live on **one**
    board; one short can total both.

If the Smoke Stopper stays dark and the FC boots normally, you may connect the
battery directly from then on (until the next hardware change).

## 5. Prop guards on, props off for bench work

- The BEE35 Pro is a ducted CineWhoop: fly it **only with the propeller guards
  (ducts) installed**, always, and especially indoors.
- **Remove the propellers for every bench test** — receiver checks, parameter
  changes, motor tests, servo tests, companion-computer experiments. Motors that
  spin up unexpectedly on a desk are the most common way people get cut. Put the
  props back on only when you are about to fly.

## 6. Connect Mission Planner and read the Messages tab

Connect the flight controller to your PC via **USB** and open **Mission Planner**
(see [Ground Control Station](../software/gcs.md)):

1. Select the COM port, connect, and confirm the firmware banner reads
   **ArduCopter V4.6.3**. If it shows another version, stop and read the
   [Initial Setup](../hardware/drone/InitialSetup.md) page — parameter names differ
   between releases and unknown names are *silently ignored*.
2. Open **Messages** (Data screen) and actually read it. This tab is where ArduPilot
   tells you what is wrong: `PreArm:` lines name every failed check, sensor init
   errors appear here, and after a fence-triggered landing you will find
   `Arm: LAND mode not armable` here — which means the vehicle is still in LAND
   mode, not that the battery is dead.

## 7. Preflight checks

Before every flight, in this order:

- [ ] Battery charged (16.4 V full) and **strapped tight** — a shifting pack shifts
      the centre of gravity.
- [ ] Prop guards mounted, propellers tight, correct rotation direction.
- [ ] Nothing loose near the props (cables, camera ribbon, antenna).
- [ ] Transmitter on **first**, model selected, ELRS link up.
- [ ] **Kill switch assigned and tested** (see step 8) — you must know which switch
      it is without looking.
- [ ] Battery connected; wait for the FC to boot and the EKF/gyros to settle.
- [ ] No `PreArm` errors in the Messages tab / on the GCS HUD.
- [ ] Flight area clear of people; bystanders behind you.

The parameter-side preflight (arming checks, failsafes, fence) is part of the
[Initial Setup](../hardware/drone/InitialSetup.md) and the danger box at the top of
this page.

## 8. First manual flight — the rules

The first flights are **manual, line-of-sight**, without any companion-computer or
autonomy involvement:

- **Mode: Stabilize.** It needs no position estimate and no GPS — the pilot controls
  attitude and throttle directly. Do not attempt Loiter/Guided indoors before the
  optical-flow setup ([Sensors](../sensors/index.md)) is configured *and* verified.
- **Location: open space or a netted hall.** No people in the flight volume. Indoors
  means no GPS and no RTL — if anything goes wrong, *you* are the failsafe.
- **Kill switch:** an arm/disarm (motor kill) switch must be assigned on the GX12
  before the first takeoff. If the drone does anything unexpected close to the
  ground or a person: kill it. A dropped drone with prop guards is cheaper than any
  alternative.
- Keep the first hops low (below head height) and short. Get a feel for hover
  throttle, then practise gentle position corrections. Budget real practice time —
  later autonomous tests rely on a pilot who can take over instantly
  (`--takeover` in the companion code).
- Watch the battery: land at the latest at the 12.8 V warning.

## Where to go next

Once you can hover and land calmly in Stabilize, continue with the
[Build Guide](build-guide.md) — it chains every subsystem page of this documentation
into the full rebuild path towards autonomous delivery.
