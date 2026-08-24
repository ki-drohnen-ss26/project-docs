# Print Guide

!!! info "Status: generic guidance — concrete profiles pending"
    No mount has been printed yet ([CAD models](cad-models.md) are still open). This
    page collects the Cura settings and fastening techniques we will start from; the
    **actual profiles, materials and per-part settings will be filled in once the
    first parts are printed and fit-checked**.

All parts are functional brackets, not display pieces: they hold sensors level, take
screw loads, and sit in prop downwash on a vibrating airframe. The settings below
optimise for strength-per-gram, because on a 3.5" CineWhoop
[every gram costs hover margin](index.md#hard-constraints-from-the-platform).

## Material

**PLA** is the working choice: stiff, dimensionally accurate, easy to print, and
fine for an indoor aircraft. Its main weakness — softening in heat — matters near
ESCs and motors; keep printed parts off hot components or revisit the material if a
part sits against one.

## Cura settings for functional parts

Starting points for strong, light PLA brackets (tune per part, then record the final
profile here):

| Setting | Starting point | Why |
|---|---|---|
| Wall line count | 3–4 | Walls carry the load; strength comes from perimeters, not infill |
| Top/bottom layers | 4–5 | Closes the shell so screw areas do not crush |
| Infill | 25–40 %, gyroid or grid | Enough to support walls and screw areas; more is mostly wasted mass |
| Layer height | 0.2 mm | Good strength/time balance for structural parts |
| Infill/wall overlap | keep default or slightly higher | Bonds the shell to the core |
| Supports | avoid by design | Support scars land on mating faces; reorient or split the part instead |
| Build plate adhesion | brim for small/tall parts | These parts are small; a brim prevents mid-print detachment |

**Around screw holes and bosses**, rely on walls, not infill: extra perimeters (or a
locally solid region via a support blocker/modifier mesh set to 100 % infill) around
every hole. A screw pulled into sparse infill strips out.

## Orientation: layers decide the strength

FDM parts are weakest **between** layers — they delaminate along layer lines long
before the plastic itself fails. Orient every part so:

- The main bending/tension load runs **in the layer plane**, not across it. A bracket
  that hangs a sensor should be printed lying flat, not standing up.
- **Screw bosses print vertically** (hole axis = Z) where possible: holes come out
  round, and screw torque loads the layer plane instead of prying layers apart.
- Faces that must be flat and level (the MTF-01P mounting face, the camera seat) go
  **on the build plate** — the first layer is the flattest surface a print has.

If a part cannot satisfy both load direction and flat-face requirements at once,
split it into two printed parts screwed together rather than accepting a weak
orientation.

## M3 fastening options

Three ways to put an M3 thread into a printed part, in order of preference for parts
that will be opened repeatedly:

1. **Heat-set brass inserts** — melted in with a soldering iron. Strongest and
   reusable; needs the insert's specified hole diameter modelled into the part.
   Best for the Pi case and anything serviced often.
2. **Self-tapping directly into plastic** — model the hole ~2.5 mm and let the M3
   screw cut its own thread. Zero extra hardware, but survives only a few
   assembly cycles; fine for parts that are set once.
3. **Through-hole + nut** — model the hole ~3.2 mm, use a nut (ideally a nyloc, or a
   modelled hex pocket) on the far side. Strongest clamp, needs access to both sides;
   the natural choice where parts bolt to the provided **M3 standoffs (M3x9/M3x12)**,
   which bring their own female threads.

On a vibrating airframe, plain screws in plastic loosen: prefer nylocs or a drop of
low-strength threadlocker on metal-to-metal joints (threadlocker chemically attacks
some plastics — keep it off the printed part itself).

## Post-print fit check

Before a part goes anywhere near the drone:

- [ ] Deburr and remove the brim/elephant's foot so mating faces sit flat.
- [ ] Test-fit every screw, insert and the actual component **on the bench** —
      adjust hole clearances in CAD and reprint rather than forcing.
- [ ] Check the critical face with a straightedge: the sensor/camera seat must be
      flat and, once mounted, level.
- [ ] Weigh the part and record the mass (it feeds the CG check in the
      [validation checklist](cad-models.md#validation-checklist-before-flight)).
- [ ] Give it the crash test handshake: flex it hard by hand — if layers crack now,
      they would have cracked on the first hard landing.

!!! note "To be added after the first print batch"
    Final Cura profile per part, chosen fastening per mount, measured masses, and
    photos of the printed parts.
