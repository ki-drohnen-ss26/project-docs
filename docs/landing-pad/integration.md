---
tags:
  - ai
  - landing-pad
---

# Integration with the flight code

The detector does not fly the aircraft. It hands the mission state machine one
answer per frame, and the mission's `SEARCH` and `APPROACH` stages act on it.
This page is the **contract** between the two, and the list of things to verify
before the detector is trusted in flight.

## The contract

The flight code (`Pi-Code/camera.py`) expects each frame to produce:

```python
{"detected": bool, "dx": float, "dy": float, "distance": float}
```

| Field | Meaning | Unit |
|---|---|---|
| `detected` | was a pad found above the confidence threshold | — |
| `dx` | ground offset, positive = pad is to the drone's **right** | **metres** |
| `dy` | ground offset, positive = pad is **ahead** of the drone | **metres** |
| `distance` | height above ground used for the conversion | metres |

!!! info "Why metres and not image fractions"
    A camera natively reports *"the pad is 30 % of the frame to the right"*. The
    mission's tuning (`centre_tolerance`, `approach_gain`, `max_nudge_m`) is
    calibrated in **ground metres**, and the whole state machine was validated
    against SITL with a simulated camera that reports metres. Returning image
    fractions instead would silently change the meaning of every one of those
    numbers.

The conversion is the pinhole relation:

```
ground_offset = tan(image_fraction × half_FOV) × height_above_ground
```

with the height taken from the rangefinder / relative altitude, and the lens
values from the config (`cam_hfov_deg = 66.0`, `cam_vfov_deg = 52.3` for the
stock AI Camera lens over the full sensor area).

!!! warning "The FOV values assume a nadir mount and the full sensor area"
    Every correction scales with them. If the camera is tilted, cropped, or
    switched to a different sensor mode, these values are wrong and the whole
    approach loop is mis-scaled. A tilted camera additionally needs the tilt
    angle folded into the conversion, which is not currently modelled.

## Calibrating the mounting

The image→body axis mapping depends on how the camera is physically rotated in
its mount, so it **must be verified on the real airframe**. It is configuration,
not code, so calibration is a parameter change between test flights rather than
a source edit:

| Setting | Meaning |
|---|---|
| `cam_swap_axes` | camera rotated 90° in its mount |
| `cam_invert_x` | positive `dx` must mean "pad is to the right" |
| `cam_invert_y` | positive `dy` must mean "pad is ahead" |

**Procedure:** hover, place the pad clearly to the drone's **right**, and check
that the logged `dx` is **positive**. Repeat with the pad **ahead** for `dy`.
This is bring-up milestone 2 (`python main.py --milestone 2`), which runs the
detector in logging-only mode with no drop.

!!! danger "A wrong sign is worse than no detection"
    With the sign inverted the aircraft corrects *away* from the pad, smoothly
    and confidently, and nothing in the log looks wrong.

## Settings that have to change before the detector flies

The flight code ships with defaults chosen for *safety in the absence of a
detector*, not for this model. Five values have to be set:

| Setting | Default in `Pi-Code/config.py` | Set to | Why |
|---|---|---|---|
| `camera_source` | `"timed"` | `"real"` | `"timed"` is the honest camera-less mode — it declares "found" after a fixed delay and detects nothing |
| `cam_box_order` | `"yxyx"` | **`"xyxy"`** | `"yxyx"` is the picamera2 sample convention. Ultralytics `format=imx` — which produced our `.rpk` — emits `(x0, y0, x1, y1)`. The order cannot be inferred from the numbers |
| `camera_confidence` | `0.5` | **keep `0.5`** | confirmed correct on the sensor. Everything implausible in the live bench run sat at 0.32, the lowest quantisation step; the real pad tracked at 0.50–0.78. 0.5 costs one distant-pad image in sixteen ([Evaluation](evaluation.md#choosing-the-threshold)) |
| `camera_model_path` | `/home/drone/models/pad/network.rpk` | keep — and copy the `.rpk` there | the team convention from [AI Software](../software/ai-software.md) is `imx500-package -o ~/models/pad`; the on-Pi reader scripts still point one directory higher, so make them agree |
| `camera_target_class` | `None` (accept any class) | keep `None` | correct for the deployed **single-class** model. If the two-class model H is ever loaded this **must** be set to the pad's class id — chasing a person instead of the pad is worse than not detecting at all |

## Open items to verify on the bench

`RealCamera` logs the first raw box next to its decoded form, exactly so these can
be checked before flying:

```
[CAM] First raw box [...] (cam_box_order=xyxy) -> normalised (x0=…, y0=…, x1=…, y1=…)
```

!!! success "Closed: pixel-valued boxes"
    The decoder once assumed boxes normalised to 0…1, while the sensor returns
    **pixels in the model's input window**. `_decode_box()` now detects this
    (`max(box) > 1.5`) and normalises by the model's input size.

!!! success "Closed: the input-size fallback"
    `_input_size()` falls back to 640 × 640 if `IMX500.get_input_size()` raises, which
    would have halved every correction for our 320 px model. On the aircraft's own
    hardware the call **works and returns `(320, 320)`**, so the fallback never fires.
    Pinning it to 320 anyway costs nothing and removes the trap.

!!! warning "1. `cam_box_order` must be flipped to `xyxy`"
    **Confirmed on the sensor.** The raw tensor is `(x0, y0, x1, y1)` in 320 px units;
    the working on-Pi decoder divides by the input height and then reorders to
    `(y0, x0, y1, x1)` for `convert_inference_coords()`.

    Pi-Code's default is `"yxyx"`, which reads that raw tensor transposed. A wrong
    order shows up as **swapped `dx`/`dy`** — easy to "fix" with `cam_swap_axes` in a
    way that hides the real cause. This is the one setting that is still wrong.

!!! warning "2. The height that scales every offset is barometric near the ground"
    `_height_above_ground()` takes the EKF vertical estimate
    (`get_local_position()["down"]`). After the [2026-08-21
    incident](../problems/incident-analysis-2026-08-21.md) the EKF height source is
    `EK3_SRC1_POSZ = 1`, i.e. **baro primary** — and the team's own logs show
    barometric altitude spiking to
    [4.05–6.73 m in propeller downwash](../results/limitations.md#sensors) while the
    aircraft is centimetres off the floor.

    `ground_offset` scales **linearly** with that height. A height that reads 4 m
    while the drone is at 1 m makes every commanded nudge roughly four times too
    large, precisely during the final approach. Worth checking whether the
    rangefinder should feed this conversion directly instead of the EKF estimate.

!!! note "3. Tensor count"
    Confirmed on hardware: the sensor returns **four** tensors — boxes `(300, 4)`,
    scores `(300,)`, classes `(300,)` and the number of valid detections `(1,)`.
    Pi-Code's guard accepts *at least three* and ignores the fourth, scanning all 300
    rows and filtering by score. Workable; using the count tensor is cheaper.

!!! warning "4. Nothing rejects a single-frame outlier"
    Not a Pi-Code defect — a missing layer. `RealCamera` returns the
    highest-confidence detection **per frame**, and `APPROACH` acts on it. The bench
    run produced occasional impossible boxes (frame edge, 1:2.5 aspect) that a
    single-frame consumer cannot tell from a real pad.

    Before the detector drives the aircraft, the mission side needs either a
    persistence requirement (pad present in 3 of 4 consecutive frames at roughly the
    same place) or a plausibility filter (reject aspect ratios beyond ~1:3 and boxes
    touching the frame edge). See
    [Evaluation](evaluation.md#what-the-sensor-does-that-the-simulation-does-not).

!!! tip "How to check items 1 and 2 in one hover"
    Milestone 2 (`python main.py --milestone 2`) runs the detector in logging-only
    mode with no drop. Put the pad at a **measured** offset — say 1.0 m to the
    drone's right, 0 m ahead, at a known height — and compare the logged metres
    against the tape measure.

    - `dx` and `dy` swapped → item 1, `cam_box_order`
    - factor ≈ 4 too large near the floor → item 2, the barometric height

## Related pages

- [Deployment](deployment.md) — how the `.rpk` is built and which script loads it
- [Evaluation](evaluation.md) — where the confidence-threshold recommendation comes from
- [AI Camera Module](../hardware/ai-camera.md) — connecting the camera and installing the IMX500 firmware
- [AI Software](../software/ai-software.md) — why the network runs on the sensor at all
- [Limitations](../results/limitations.md) — the sensor and firmware limits this page depends on
