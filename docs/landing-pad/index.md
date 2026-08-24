---
tags:
  - ai
  - landing-pad
---

# Landing Pad Detection

The drone has to deliver a payload to a place that is **not known in advance**.
Indoors there is no GPS to fly to, so the target has to be *seen*. This section
documents the detector that does the seeing: a YOLO11n object detector for one
class, `landingPad`, trained on our own photographs and deployed onto the
Raspberry Pi AI Camera.

!!! info "What this model answers"
    *"Where is the landing pad in this frame?"* — as a bounding box. The mission
    code turns that box into a ground offset in metres and nudges the aircraft
    towards it ([Integration](integration.md)).

## The pad

<figure markdown>
  ![The landing pad on the sports hall floor](../Images/LandingPad/landing-pad-hall.jpg){ width="480" }
  <figcaption>Our pad in the sports hall — rebuilt to match the public dataset's pad, and photographed in the one place the drone actually flies.</figcaption>
</figure>

A dark square mat with a red border and a red cross from corner to corner.

**We did not invent that design — we copied it.** A public Roboflow dataset,
[`cgomolak/landing-pad-zvclx`](https://universe.roboflow.com/cgomolak/landing-pad-zvclx),
already contained **77 labelled images** of a pad with exactly this marking. Building
our physical pad to match meant all of them could be merged straight into our training
set instead of being photographed and annotated from scratch — see
[Dataset](dataset.md#where-the-data-comes-from).

We then photographed our pad **in the sports hall**, because the public images show a
black background and an office carpet, and neither is the floor the drone flies over.
Those 46 hall photos are the only part of the dataset that shows the operational
environment.

Three properties of the design matter for everything below:

- **It is 90°-symmetric.** Rotating it by a quarter turn produces the same
  image. That is convenient for detection — the model needs no rotation
  invariance beyond 90° — but it means the pad's **yaw can only ever be
  recovered modulo 90°**. An asymmetric marking (one corner in a different
  colour) would resolve it.
- **Red crossing lines are not rare.** A sports hall floor is painted with red,
  green, blue and black lines that cross each other. Verifying "is there a red
  X inside this box?" therefore does **not** filter false positives here — we
  measured it, see [Evaluation](evaluation.md#pattern-recognition).
- **It was chosen for data availability, not for detectability.** Both points above
  are inherited, not designed. Fixing either — an asymmetric corner to resolve yaw, a
  marking that is not red to survive a hall floor — means the 38 public images no
  longer match our pad and the dataset shrinks by a third. That trade is worth
  re-opening if the pad is ever rebuilt.

## The model at a glance

| | |
|---|---|
| Architecture | YOLO11n (nano — the smallest variant, chosen for the Pi Zero 2 W) |
| Classes | 1 — `landingPad` |
| Input size | 320 × 320 px |
| Training images | 251 (175 pad + 76 pad-free negatives) |
| Framework | Ultralytics 8.4 |
| Deployed artefacts | `pad_320_int8.tflite` (Pi CPU) · `network.rpk` (AI Camera) |
| Confidence threshold | **0.4** on TFLite · **0.5** on the `.rpk` ([why](evaluation.md#choosing-the-threshold)) |

## Results

Held-out test set, 16 images from stretches of the dataset the model never saw:

| | mAP50 | mAP50-95 | Recall | False positives / image |
|---|---|---|---|---|
| PyTorch (FP32) | 0.9950 | 0.8098 | 1.000 | 0.02 |
| TFLite INT8 | 0.9950 | 0.6764 | 1.000 | 0.00 |
| IMX-quantised, ONNX simulation | 0.9950 | 0.6737 | 1.000 | 0.02 |

Quantisation costs essentially nothing in *detection*. It only loosens the
boxes, which is what the mAP50-95 column shows.

Against the model that was on the Pi before this work, run end-to-end through
the inference script:

| Model | Recall | Mean IoU | False positives / image |
|---|---|---|---|
| **`pad_320_int8.tflite`** (run F) | **1.000** | 0.851 | **0.00** |
| `best_int8.tflite` (previously deployed) | 0.625 | 0.919 | 0.31 |

!!! success "Status (2026-08-24): it runs on the sensor"
    `network.rpk` is on the Pi and **detecting in real time on the IMX500's own NPU**.
    A bench run tracked the pad across dozens of consecutive frames and reported "no
    pad" continuously once it left the field of view. The chain from training on a
    laptop to inference on the camera chip is closed.

    **It has not flown.** No detection has been produced in the air, and none of the
    numbers on these pages comes from a flight.

    Remaining before the detector may steer the aircraft: one wrong configuration
    value, a single-frame outlier filter, and the milestone-2 tape-measure check —
    [Flight-Code Integration](integration.md#open-items-to-verify-on-the-bench).

!!! note "Where the pipeline lives"
    The scripts referenced throughout this section (`build_dataset.py`,
    `negatives.py`, `train_neg.py`, `robustness.py`, `fp_bench.py`, `export_imx_local.py`, …)
    are the `drone-ai` training pipeline. It is **not yet published in this
    organisation** — until it is, the commands below are reproducible only on the
    machine that holds it.

## How to read this section

<div class="grid cards" markdown>

-   :material-database: **[Dataset](dataset.md)**

    ---

    Where the images come from, why our pad copies a public one, and why the
    original 0.94 mAP was not a generalisation score.

-   :material-school: **[Training](training.md)**

    ---

    Six recipes on one leak-free split. What helped, what bought nothing, and
    why negatives mattered most.

-   :material-chart-line: **[Evaluation](evaluation.md)**

    ---

    Why mAP saturated at 16 test images, and the yaw / altitude / capture-path
    probes we replaced it with.

-   :material-rocket-launch: **[Deployment](deployment.md)**

    ---

    TFLite for the Pi CPU, `.rpk` for the AI Camera, and why one build step only
    runs on ARM.

-   :material-connection: **[Integration](integration.md)**

    ---

    The contract with the flight code: metres, axis calibration, confidence
    threshold.

</div>

## Limitations

!!! danger "The ceiling is the data, not the training recipe"
    The training set is 123 source photographs of **one pad design**, and **63 % of
    them are third-party** — a black background (31 %) and an office carpet (32 %),
    neither of which the drone will ever fly over. Our own contribution is 46 handheld
    photographs from **standing height** in the sports hall. No image in the set is a
    nadir view from flight altitude.

- **No aerial images.** The model has never seen a true nadir view from several
  metres up, which is what the camera sees for most of the approach.
- **Indoor only.** Grass, asphalt, gravel, wet ground and low sun are untested.
- **One pad design, and it was chosen to fit the data.** The physical pad was built
  to match the public dataset's pad, so the dataset cannot answer whether the model
  generalises to a differently built pad. If the pad is ever redesigned, this has to
  be re-measured from scratch.
- **Negatives from two rooms, only one of them ours.** They are crops of the hall and
  of the public set's office, so corridor and outdoor clutter is untested.
- **Nothing has been measured in the air.** The detector runs on the sensor and
  tracks the pad on the bench, but every *number* on these pages comes from
  photographs. Detection range, frame rate under vibration and the behaviour of the
  approach loop are all still unknown.
- **The robustness figures for the quantised model are a simulation.** They were
  measured on `model_imx.onnx`, not on the sensor — and the sensor has already been
  shown to differ in one respect the simulation could not predict, its
  [discrete confidence output](evaluation.md#what-the-sensor-does-that-the-simulation-does-not).

## What would move the needle next

Recipe tuning is close to exhausted on 123 photographs of one pad design, of which
only 46 come from the hall the drone flies in. In rough order of expected return:

1. **Photograph the pad from the air, in the hall.** Every training image is handheld
   from standing height; none is a nadir view from the height the drone actually
   searches at. A few hundred frames pulled from an actual FPV recording would be
   worth more than any further augmentation — and it would also fix the deeper
   problem, that the operational scene is the *smallest* part of the dataset. The
   aircraft already records.
2. **More than one pad, and outdoors.** Grass, asphalt, gravel, wet ground, low sun.
   The model currently knows one pad design on two indoor floors — and since the pad
   was built to match the dataset, a second pad is the only way to find out whether it
   learned "landing pad" or "this exact strip of red tape".
3. **More negatives, from other places.** Run F's negatives are crops of the same three
   rooms, so corridor and outdoor clutter is untested. This was the highest-value
   change made so far, and it is not exhausted.
4. **Drop or re-shoot the cut-out burst.** 31 % of the source photos are the pad
   floating on black, which is not a view the drone will ever have.
5. **Train `yolo11n-seg` on the existing polygons.** No new annotation needed — the
   Roboflow labels are already polygons. Contour → 4 corners → homography gives true
   distance and attitude instead of a box.

The first item is the one that matters. **The most valuable next step is not another
training run — it is a few hundred frames pulled from an actual flight recording.**
