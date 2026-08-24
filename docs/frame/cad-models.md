# CAD Models

!!! info "Status: requirements fixed, no finished models yet"
    There are **no completed CAD models** at this point. This page pins down the
    design requirements each mount has to satisfy, the planned Tinkercad workflow,
    and the checklist a mount must pass before it flies. It will grow STL downloads
    and photos as the parts get modelled and printed.

## Design ground rules (all parts)

These follow directly from the [frame constraints](index.md#hard-constraints-from-the-platform):

- **Mass is the budget.** On a 3.5" CineWhoop every gram costs hover margin — prefer
  thin ribs and cut-outs over solid slabs, and weigh every printed part.
- **Keep mass central.** Place parts so they balance around the frame centre; the
  payload bay sits directly under the CG.
- **Use the provided M3 hardware.** M3 standoffs plus M3x9 and M3x12 screws are
  available for a stacked platform on the frame's existing M3 pattern — design bolt
  patterns around M3, not glue.
- **Fail without collateral damage.** The crash tore off the GPS module and its
  wiring likely took the FC's single I2C bus down with it
  ([incident report](../problems/incident-analysis-2026-08-21.md)). Mounts must stay inside the
  frame's protective outline or break away without ripping wires out of the FC.
- **Strain relief everywhere.** Downwash from the ducted props will flutter any loose
  cable; every wire gets a tie-down point on its mount.

## Per-mount design requirements

### MTF-01P mount (underside)

The optical flow + LiDAR unit is the only indoor position source — its mount has the
strictest requirements:

- **Level and pointing straight down.** A tilted sensor scales flow and range wrong;
  the mounting face must be parallel to the FC plane (the aircraft's level reference).
- **Free optical path** for both the flow camera and the LiDAR aperture — no frame
  edge, cable or payload anywhere in view.
- **~2 cm ground clearance, kept permanently clear.** Nothing may ever slide under
  the sensor, on the ground or in flight; the rangefinder is configured to read down
  to centimetres (`RNGFND1_MIN_CM = 1`), so an intruding object produces a
  confidently wrong height.
- **Wiring** runs to FC `SERIAL5`; route it upward away from the lens with strain
  relief at the mount.
- Exact sensor footprint and hole positions will be taken with calipers from the
  physical unit before modelling — no dimensions are guessed here.

### AI camera mount (nadir view)

- **Straight-down view.** The pad detector runs on the IMX500 sensor itself; the
  approach logic assumes a nadir image.
- **The full field of view (66° × 52.3°) must be clear** — no propellers, ducts or
  frame parts may enter the image at any point, or the detector sees them instead of
  the pad. Verify with a live preview, not by eye.
- **Rigid mounting.** A vibrating camera blurs exactly the low-light indoor frames
  the detector needs.
- **Ribbon cable care.** The CSI cable to the Pi Zero is fragile: keep the run short,
  avoid sharp bends, and clamp it at both ends.

### Drop mechanism and payload bay

- **Pocket for a standard 9 g micro servo**, held rigidly enough that the release
  torque cannot flex the mount (positions: 1100 µs closed, 1900 µs open — see the
  [servo mechanism](../delivery-system/servo-mechanism.md)).
- **Payload centred under the CG** so the drone trims the same loaded and empty, and
  so the release does not shift the balance mid-flight.
- **Release path clear of the sensors:** the falling payload must not pass under the
  MTF-01P or through the camera's field of view.
- **Wiring:** signal from Pi GPIO18; servo power comes from its **separate 5 V BEC**,
  never the Pi's 5 V pin — the bay needs routing space for both leads.

### Pi Zero 2 case (top platform)

- Sits on the M3 standoff platform (M3x9 / M3x12 screws).
- **Accessible without disassembly:** the USB gadget port (the Pi is administered
  over USB), the microSD slot, the CSI connector and the GPIO header pin for the
  servo signal must all stay reachable.
- **Ventilation openings** — the Pi runs the state machine and mavlink-router
  continuously.
- Short cable runs to FC `SERIAL4` and to the camera.

## Planned Tinkercad workflow

1. **Measure** the real part with calipers (footprint, hole spacing, connector
   positions). Never model from datasheet drawings alone.
2. **Model in Tinkercad** in millimetres; give holes ~0.1–0.2 mm extra clearance for
   printing tolerance (to be calibrated with a test print).
3. **Export STL** and slice in Cura with the settings in the
   [Print Guide](print-guide.md).
4. **Test print and fit-check** against the real hardware before mounting anything
   on the drone; iterate on clearances.
5. **Weigh** the final part and log the mass.

## Validation checklist before flight

Every mount must pass this on the assembled aircraft before the first armed test:

- [ ] **Sensor level:** with the drone on a flat surface, the MTF-01P face is
      parallel to the ground and the FC reports level attitude.
- [ ] **Unobstructed rangefinder:** Mission Planner shows a plausible rangefinder
      distance on the bench and while lifting the drone by hand.
- [ ] **Unobstructed flow:** optical flow quality is nonzero over a textured floor.
- [ ] **Clear camera view:** a live camera preview shows no propeller, duct or frame
      part anywhere in the image.
- [ ] **Nothing under the MTF-01P:** with payload loaded and servo cycled, nothing
      can reach the ~2 cm zone under the sensor.
- [ ] **Servo travel:** full 1100–1900 µs sweep without fouling the frame or wiring.
- [ ] **Strain relief:** every cable is clamped; tugging any wire does not move a
      connector.
- [ ] **Screws torqued** and standoffs tight; nothing rattles when shaken.
- [ ] **Mass and CG:** total takeoff weight recorded; the drone balances at the
      frame centre with the payload installed.
