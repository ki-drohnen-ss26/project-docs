---
tags:
  - ai
  - landing-pad
---

# Evaluation

## Why mAP was the wrong target

After the [leak-free re-split](dataset.md#why-we-rebuilt-the-traintest-split) we
retrained the **old** recipe as a baseline. It scored:

```
run                imgsz | val mAP50  val 50-95 | test mAP50  test 50-95 | FP/img
A_baseline           320 |     0.995      0.925 |      0.995      0.937 |   0.00
A_baseline           416 |     0.995      0.982 |      0.995      0.957 |   0.00
```

100 % recall in every size bucket and every scene, zero false positives. The new
recipe scored 0.995 as well.

The metric had **saturated**: 16 test photos of one high-contrast pad on a clean
floor is simply too easy, and no recipe change can show up in it. So
`robustness.py` measures the axes the drone actually moves in instead, using the
**polygon** labels so ground truth stays exact under rotation.

=== "Yaw"

    A multirotor holds no particular heading, so the pad arrives at the camera
    rotated. Images are rotated about their centre, and the polygon labels are
    rotated with them.

=== "Altitude"

    Higher means fewer pixels on the pad. The frame is scaled down onto a
    floor-coloured canvas, shrinking the pad exactly as climbing would.

=== "Capture path"

    Motion blur from the props, sensor noise and JPEG compression — applied at
    the resolution the network actually sees.

## Altitude — where the baseline broke

Recall on the 16 test images at 320 px, frame zoomed out, pad shrinking:

| | ×1.0 | ×0.5 | ×0.3 | ×0.2 | ×0.12 | ×0.08 |
|---|---|---|---|---|---|---|
| Median pad size (px) | 296 | 148 | 89 | 59 | 35 | 24 |
| A (old recipe) | 1.00 | 1.00 | 0.81 | 0.69 | **0.50** | **0.25** |
| B | 1.00 | 1.00 | **1.00** | **0.94** | 0.69 | 0.56 |
| C @416 | 1.00 | 1.00 | 0.94 | 0.81 | 0.38 | 0.00 |
| **D** | 1.00 | 1.00 | 0.94 | 0.81 | **0.75** | **0.62** |
| E | 1.00 | 1.00 | 0.88 | 0.62 | 0.69 | 0.62 |

The baseline's recall **halves** by the time the pad is 35 px across — which is
exactly the approach phase, when the detector is needed most. The cause is in the
data: the median training pad covers
[47 % of the image side](dataset.md#the-bias-we-could-measure-in-the-data).

## Combined — an actual approach

Yaw, altitude and capture degradation together:

| | yaw45 ×0.3 | yaw45 ×0.3 blur | yaw135 ×0.2 all | yaw90 ×0.12 all |
|---|---|---|---|---|
| A (old) | 0.44 | 0.44 | 0.06 | 0.00 |
| B | 0.94 | 0.81 | 0.00 | 0.12 |
| C @416 | 0.94 | 0.88 | 0.12 | 0.00 |
| **D** | **0.94** | **0.94** | **0.50** | **0.69** |
| E | 0.94 | 0.94 | 0.38 | 0.31 |

The old recipe reaches **0.00** on the hardest case. This is the table that
picked the recipe; mAP could not have.

## False positives on empty scenes

The probe that changed the deployed model. Detections on 91 **pad-free** crops
from the held-out splits, against recall on real pads — full discussion in
[Training](training.md#the-false-positive-lesson):

| At conf 0.4 | False pos. / img | Recall | Recall at ×0.3 | Max conf. on empty image |
|---|---|---|---|---|
| A (old recipe) | 0.02 | 1.00 | 0.81 | 0.54 |
| D | 0.33 | 1.00 | 0.94 | 0.87 |
| **F** (deployed) | **0.02** | 1.00 | **0.94** | 0.66 |

## What quantisation costs

Measured rather than assumed, on the same held-out test set:

| | mAP50 | mAP50-95 | Recall |
|---|---|---|---|
| PyTorch FP32 | 0.9950 | 0.8098 | 1.000 |
| TFLite INT8 | 0.9950 | 0.6764 | 1.000 |
| IMX500 quantised | 0.9950 | 0.6737 | 1.000 |

Detection is unaffected; only box tightness drops. Under the stress probes, the
quantised `.rpk` matches the float model to within one or two images out of
sixteen:

| Probe | PyTorch | Quantised (`.rpk`) |
|---|---|---|
| Yaw, worst case | 0.94 | 0.94 |
| Altitude, worst case (24 px pad) | 0.69 | 0.69 |
| Blur / noise / JPEG | 1.00 | 1.00 |
| Combined: yaw 90°, ×0.12, all degradations | 0.62 | 0.69 |
| mAP50 | 0.995 | 0.995 |

!!! warning "But the threshold has to move"
    Quantisation shifts the whole confidence distribution **down**. The `.tflite`
    model works at conf **0.4**; the `.rpk` should run at conf **0.3**. At 0.5 it
    starts missing distant pads — recall at ×0.3 zoom falls from **0.94 to 0.75**.

## Pattern recognition

Two ideas were tried, with opposite results.

=== "Verifying the red X — does not work here"

    The idea: reject a detection unless the box contains a red cross.
    `pattern_check.py` measures it — at a threshold that keeps 88 % of real pads,
    **21 of 41 false detections survive**.

    The reason is the environment: the sports hall floor is painted with red
    lines that cross each other, so "red cross" is not a rare feature in the one
    place where the filter would need to work.

=== "Measuring the pad once found — works"

    Inside a *confirmed* box the red mask is clean. `pad_pose.py` fits a rotated
    rectangle to it and returns contour, centre and yaw.

    The pad is square with a symmetric X, so **yaw is only determined modulo
    90°**. An asymmetric marking would resolve it.

!!! tip "The cheapest real upgrade needs no new annotation"
    The Roboflow labels are already **polygons**, so `yolo11n-seg` can be trained
    on exactly this data and return the pad outline instead of a box. Contour →
    4 corners → homography → true distance and attitude, which is what an
    autonomous approach actually wants.

## Files

| File | Purpose |
|---|---|
| `compare.py` | mAP and recall broken down by pad size and by scene |
| `robustness.py` | yaw / altitude / capture-path stress probes |
| `fp_bench.py` | false positives on pad-free images vs recall |
| `person_bench.py` | two-class person recall vs stock YOLO11n |
| `pattern_check.py` | red-X verification (measured: does not work here) |
| `pad_pose.py` | contour, centre and yaw from a confirmed detection |
