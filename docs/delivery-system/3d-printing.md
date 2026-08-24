# 3D Printing

The drop mechanism needs one custom mechanical part: a **housing** that turns
the bare 9 g servo into a payload bay — holding the servo, guiding the payload
and bolting onto the frame platform. This page documents the printing workflow
available to the team and the design requirements for that part.

!!! info "Status: housing not yet designed"
    The workflow below is in place and the requirements are fixed, but the
    **actual housing model does not exist yet** — no CAD file, no test print.
    What follows is the requirements list a design must meet, not a report on
    a finished part. General frame printing (platform, mounts) is covered in
    [Frame Extension](../frame/index.md).

## The workflow

| Step | Tool | Notes |
|---|---|---|
| CAD | **Tinkercad** | browser-based, no install, good enough for boxy brackets; export as STL |
| Slicing | **UltiMaker Cura** | free; profile for the university's printers |
| Printing | university 3D printers | FDM; plan for queue time — iterate in CAD before printing, not by reprinting |

The loop is deliberately simple: model in Tinkercad, export STL, slice in
Cura, print, test-fit, adjust. For a part this small a print is fast — the
bottleneck is printer access, so measure twice (calipers on the real servo
and payload) and print once.

## Material and print settings

- **PLA is fine.** The drone flies indoors; there is no UV or heat exposure,
  and PLA prints dimensionally accurately — which matters more for a
  press-fit servo pocket than impact resistance does. PETG is an option if a
  part ever turns out too brittle, at the cost of stringier prints.
- **Walls over infill.** For a small bracket, strength comes from perimeters:
  3 wall lines (≈1.2 mm with a 0.4 mm nozzle) and modest infill (20–40 %)
  beat thick infill with thin walls.
- **Orient for the load.** FDM parts are weakest between layers — orient the
  print so the payload's weight and the servo's torque load the part along
  the layers, not across them. Avoid supports inside the servo pocket; a
  support-scarred pocket will not fit.
- **Mass matters.** Every gram of housing is a gram off the payload budget of
  a 3.5-inch CineWhoop. Aim for the lightest part that survives handling —
  cut away material that carries no load.

## Designing around the 9 g servo

The standard 9 g micro servo has a **23 × 12.5 mm body** with two mounting
tabs on the long axis. Practical dimensions for the pocket:

- Cut the pocket **23 × 12.5 mm plus ~0.2–0.4 mm clearance** per side and
  test-fit — FDM holes and pockets come out slightly undersized, and exact
  shrinkage depends on the printer, so calibrate on a small test piece first.
- Support the servo by its **mounting tabs** (screwed or zip-tied), not by
  friction on the body alone; servo torque will work a friction fit loose.
- Leave room above the body for the **cable exit** and for the arm's full
  swing between the 1100 µs and 1900 µs positions
  (see [Servo Mechanism](servo-mechanism.md)).

## M3 mounting

The frame platform provides **M3 standoffs and screws**, so the housing
mounts with M3 hardware:

- **Screw bosses**: ≥ 3 mm of plastic wall around each hole; don't put a hole
  at the edge of a thin wall.
- Hole diameters: **3.2–3.4 mm** for a clearance hole (screw into a standoff
  or nut), **~2.8 mm** for M3 self-tapping directly into PLA. Self-tapping
  into PLA survives only a few insertion cycles — for a part that gets
  removed often, use clearance holes and the standoffs' threads.
- Match the hole pattern to the platform described in
  [Frame Extension](../frame/index.md) — design the two parts against the
  same drawing, not from memory.

## Requirements for the housing (design checklist)

- [ ] Holds the payload captive with the servo at **1100 µs** (closed) and
      releases it cleanly at **1900 µs** (open) — gravity drop, no pushing.
- [ ] Servo pocket per the dimensions above; servo fixed by its tabs.
- [ ] Pin/arm path designed so **vibration cannot creep the release open**
      (over-centre geometry or a positive stop, not friction).
- [ ] Mounts to the platform's **M3 standoffs**; payload hangs below the
      centre of gravity, clear of the prop ducts.
- [ ] Payload can be **reloaded on the ground in seconds**, by hand, without
      tools.
- [ ] Cable routing to the Pi (signal) and the BEC (power) without pinching.
- [ ] As light as possible — target the housing plus servo well under the
      mass of the payload it carries.

Once a model exists, its STL and print settings belong in
[Frame Extension → CAD models](../frame/cad-models.md) alongside the other
printed parts.
