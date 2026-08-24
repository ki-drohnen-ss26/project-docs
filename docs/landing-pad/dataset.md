---
tags:
  - ai
  - landing-pad
---

# Dataset

!!! abstract "In short"
    We trained on **123 photos**. Only 46 are ours (taken in the sports hall) — the
    other 77 come from a free dataset on the internet, and that is why our pad is built
    the way it is.

    The photos arrived badly organised: near-identical copies were spread across both
    the "learn from these" and the "test on these" piles, so the model could score well
    by simply remembering. We reorganised them so that cannot happen.

    We also added 76 photos with **no pad in them**. That sounds pointless and turned
    out to be the most valuable thing on this page.

## Where the data comes from

The dataset has **two sources**, and knowing which is which explains most of the
model's behaviour further down.

| Source | Photos | Content | Origin |
|---|---|---|---|
| `1739 … 1778` | 38 | the pad alone on a black background, freed from any scene | **public dataset** |
| `IMG_1739 … IMG_1778` | 39 | office carpet, close-ups | **public dataset** |
| `IMG_1659 … IMG_1705` | 46 | **sports hall floor**, pad small and oblique | **ours** |

**77 of 123 source photos — 63 % — are third-party**, from
[`cgomolak/landing-pad-zvclx`](https://universe.roboflow.com/cgomolak/landing-pad-zvclx)
on Roboflow Universe. The pad in them is a dark foam mat with a red tape border and
red tape diagonals, shot on a black background and on an office carpet.

The 46 hall photos are ours, and they exist for one reason: **the public data contains
no image of the place the drone actually flies.** A sports hall floor is grey, glossy,
painted with coloured lines and lit from above — nothing like an office carpet. So we
built a matching pad, put it on the hall floor and photographed it, to give the model
at least one scene it would really encounter.

The merged set was re-labelled with **polygon** annotations in a
[Roboflow](https://roboflow.com) fork of the public project and exported in YOLO
format.

!!! warning "The only operational scene is the smallest part of the dataset"
    The hall is the environment the drone flies in, and it is **37 %** of the source
    material. The other 63 % is a room we have never flown in and a background that
    does not exist. Every "it generalises" claim below rests on that split.

!!! info "Attribution"
    The `1739 … 1778` images originate from **[`cgomolak/landing-pad-zvclx`](https://universe.roboflow.com/cgomolak/landing-pad-zvclx)**,
    licensed **CC BY 4.0**. Our merged fork is
    [`amir-ebrahimi/landing-pad-zvclx-gs3dc`](https://universe.roboflow.com/amir-ebrahimi/landing-pad-zvclx-gs3dc).

### Why our pad is built the way it is

This is the reason the [physical pad](index.md#the-pad) looks like it does — a dark
mat with a red border and a red cross. **We built it to match the pad in the public
dataset**, so that its 77 already-labelled images could be reused instead of
photographing and annotating everything from scratch.

That was the right call for a semester project: it turned 46 photographs of our own
into a 123-photo dataset and cut the annotation work by roughly two thirds. It also
has two consequences that are worth stating rather than discovering later:

- **31 % of the source material is a view the drone will never have.** A pad freed
  from its background on black is not a floor.
- **"Does it generalise to a different pad?" is untested by construction.** The pad was
  chosen to match the data, so the data cannot answer the question.

### 123 photos became 295 images

The export contains **295 images** from only **123 source photos**. Roboflow generated
**three augmented versions of each source image** — 50 % horizontal flip, brightness
±20 %, Gaussian blur 0–2.5 px, box rotation ±15° — on top of the fact that our own
photos were already shot as near-continuous bursts, a few centimetres apart.

So the same underlying photograph appears in the export several times over, twice for
different reasons. That matters immediately below.

## Why we rebuilt the train/test split

!!! warning "The original 0.94 mAP was never a generalisation score"
    Roboflow splits images **at random**, and two things made that fatal here:

    1. **Augmented copies.** Three versions of the same photograph exist. A random
       split puts version 1 in training and version 2 in validation — the *same
       picture*, flipped and slightly blurred.
    2. **Burst frames.** Our own photos were taken a few centimetres apart, so frame
       *N* landed in training and frame *N+1* in validation.

    Either alone would inflate the score. Together, the validation set was measuring
    **memorisation**, not learning.

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
| Camera height (hall photos) | handheld, standing height | no nadir view |
| Pad-free images | **3 of 175** | "there is no pad here" was never a supported answer |
| Cut-out images (public set) | 31 % of source photos | a view the drone will never have |

The first row explains the altitude weakness in [Evaluation](evaluation.md), and
the third explains the false positives in [Training](training.md#the-false-positive-lesson).

## Hard negatives

`negatives.py` harvests **pad-free crops from the hall and office photographs** — the
black-background images have no floor to crop — and excludes any region overlapping a
labelled pad, so a "negative" cannot accidentally contain the target:

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
