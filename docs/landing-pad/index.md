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
  <figcaption>The pad in the sports hall — the environment most of the dataset was shot in.</figcaption>
</figure>

A dark square mat with a red border and a red cross from corner to corner.
Two properties of that design matter for everything below:

- **It is 90°-symmetric.** Rotating it by a quarter turn produces the same
  image. That is convenient for detection — the model needs no rotation
  invariance beyond 90° — but it means the pad's **yaw can only ever be
  recovered modulo 90°**. An asymmetric marking (one corner in a different
  colour) would resolve it.
- **Red crossing lines are not rare.** A sports hall floor is painted with red,
  green, blue and black lines that cross each other. Verifying "is there a red
  X inside this box?" therefore does **not** filter false positives here — we
  measured it, see [Evaluation](evaluation.md#pattern-recognition).

## The model at a glance

| | |
|---|---|
| Architecture | YOLO11n (nano — the smallest variant, chosen for the Pi Zero 2 W) |
| Classes | 1 — `landingPad` |
| Input size | 320 × 320 px |
| Training images | 251 (175 pad + 76 pad-free negatives) |
| Framework | Ultralytics 8.4 |
| Deployed artefacts | `pad_320_int8.tflite` (Pi CPU) · `network.rpk` (AI Camera) |
| Confidence threshold | **0.4** on TFLite · **0.3** on the `.rpk` |

## Results

Held-out test set, 16 images from stretches of the dataset the model never saw:

| | mAP50 | mAP50-95 | Recall | False positives / image |
|---|---|---|---|---|
| PyTorch (FP32) | 0.9950 | 0.8098 | 1.000 | 0.02 |
| TFLite INT8 | 0.9950 | 0.6764 | 1.000 | 0.00 |
| IMX500 quantised (`.rpk`) | 0.9950 | 0.6737 | 1.000 | — |

Quantisation costs essentially nothing in *detection*. It only loosens the
boxes, which is what the mAP50-95 column shows.

Against the model that was on the Pi before this work, run end-to-end through
the inference script:

| Model | Recall | Mean IoU | False positives / image |
|---|---|---|---|
| **`pad_320_int8.tflite`** (run F) | **1.000** | 0.851 | **0.00** |
| `best_int8.tflite` (previously deployed) | 0.625 | 0.919 | 0.31 |

!!! info "Status (2026-08-24)"
    The model is trained, exported and measured; the `.rpk` builds and its
    quantisation loss is known. **It has not run on the sensor in flight yet.** The
    remaining work is deployment and a bench check of the decoded offsets —
    see [Flight-Code Integration](integration.md#settings-that-have-to-change-before-the-detector-flies).

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

    123 photos, three bursts, and why the original 0.94 mAP was not a
    generalisation score.

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
    Every training photo was taken **by hand, from standing height**, of **one
    physical pad**, in **three indoor rooms**. 31 % of the source photos show
    the pad floating on a black background — a view the drone will never have.

- **No aerial images.** The model has never seen a true nadir view from several
  metres up, which is what the camera sees for most of the approach.
- **Indoor only.** Grass, asphalt, gravel, wet ground and low sun are untested.
- **One pad.** Generalisation to a differently built pad is unknown.
- **Negatives from the same three rooms.** False positives outdoors are
  untested.
- **The `.rpk` has not flown yet.** It builds, it loads onto the sensor, and the
  quantised model measures as well as the float one — but it has not run on the
  sensor in flight.

The most valuable next step is not another training run. It is **a few hundred
frames pulled from an actual flight recording**.
