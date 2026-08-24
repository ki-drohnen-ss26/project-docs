---
tags:
  - ai
  - landing-pad
---

# Dataset

## What we photographed

The pad was labelled in [Roboflow](https://roboflow.com) and exported in YOLO
format with polygon annotations. The export contains **295 images** — but those
come from only **123 source photos**, taken as three near-continuous bursts:

| Burst | Photos | Content |
|---|---|---|
| `1739 … 1778` | 38 | pad alone on a dark background (cut-out) |
| `IMG_1659 … IMG_1705` | 46 | sports hall floor, pad small and oblique |
| `IMG_1739 … IMG_1778` | 39 | office, close-ups |

Within a burst, consecutive frames are near-identical: the camera moved a few
centimetres between shots.

## Why we rebuilt the train/test split

!!! warning "The original 0.94 mAP was never a generalisation score"
    Roboflow splits images **at random**. Because consecutive frames of a burst
    are almost the same picture, frame *N* landed in training and frame *N+1* in
    validation. The validation score was measuring **memorisation**, not
    learning.

`build_dataset.py` re-splits by **contiguous blocks** instead: whole stretches
of each burst go to validation or test, and the frames immediately adjacent to
every held-out block are dropped, so no training frame is a near-duplicate of a
test frame.

```bash
python3 build_dataset.py      # 175 train / 25 val / 16 test, leak-free
```

!!! note "Why we retrained the old recipe instead of reusing the old weights"
    The previous model also scores 0.995 on the new split — but only because it
    was trained on those exact images. There is no uncontaminated data left to
    test it on. So the comparison in [Training](training.md) retrains the old
    recipe **from scratch** on the leak-free split, and only then are the
    numbers comparable.

## The bias we could measure in the data

| Property | Value | Consequence |
|---|---|---|
| Median pad size | **47 % of the image side** | the model had essentially never seen a distant pad |
| Camera height | handheld, standing height | no nadir view |
| Pad-free images | **3 of 175** | "there is no pad here" was never a supported answer |
| Cut-out burst | 31 % of source photos | a view the drone will never have |

The first row explains the altitude weakness in [Evaluation](evaluation.md), and
the third explains the false positives in [Training](training.md#the-false-positive-lesson).

## Hard negatives

`negatives.py` harvests **pad-free crops from our own photos** — any region
overlapping a labelled pad is excluded, so a "negative" cannot accidentally
contain the target:

```bash
python3 negatives.py          # 76 negatives -> 30 % background images
```

76 negatives brings the training set to 251 images, of which 30 % contain no
pad. That single change turned out to be the most valuable one in the whole
project — see [Training](training.md#the-false-positive-lesson).

!!! tip "Negatives help training and hurt calibration"
    The same negatives must be **excluded** from the calibration set used for
    IMX500 quantisation, where an image with no detection makes the solver
    divide by ~0. See [Deployment](deployment.md#pitfalls-we-hit).

## Synthetic images — tried, did not pay off

`synth.py` composites small pads onto real floor images to fake distant views.
It produced 124 extra images and *improved box precision*, but lost on exactly
the hard cases it was meant to fix (run E in [Training](training.md)). The
composites look plausible and are evidently not a substitute for real distant
photographs.

## Files

| File | Purpose |
|---|---|
| `build_dataset.py` | leak-free re-split of the Roboflow export |
| `negatives.py` | harvest pad-free crops as hard negatives |
| `synth.py` | composite distant pads onto real floor (run E) |
| `build_2class.py` | merge pad + person data (runs G/H, see [Training](training.md#one-model-or-two)) |
