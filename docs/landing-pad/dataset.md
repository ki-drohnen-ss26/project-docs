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
| Pad-free images | **0 of 175** | "there is no pad here" was never a supported answer |
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

<figure markdown>
  ![Twelve of the 76 pad-free training images](../Images/LandingPad/negatives.jpg){ width="720" }
  <figcaption>Twelve of the 76 negatives — pieces of our own hall and office photos, cut from wherever the pad is not.</figcaption>
</figure>

These are not new photographs. They are **cut-outs of the pictures we already had**,
taken from the parts of the frame where there is no pad — floor, lines, shadows,
skirting boards. The model is shown them with an empty answer sheet: *this picture
contains nothing*.

76 negatives brings the training set to 251 images, of which 30 % contain no pad.

!!! bug "Three of the empty answer sheets are a labelling mistake"
    The finished set has **79** images with an empty answer sheet, not 76. The extra
    three are not pad-free — they are three copies of photo **1776**, which shows the
    pad filling most of the frame and was simply never marked up in Roboflow.

    <figure markdown>
      ![Photo 1776 with an empty label, next to its correctly labelled neighbour](../Images/LandingPad/mislabelled-1776.jpg){ width="640" }
    </figure>

    It is the only mistake of its kind in the export — 3 empty labels out of 295 images,
    all three of them copies of that one photo, and every neighbouring frame is labelled
    correctly. The Roboflow augmentation then multiplied one missed annotation into
    three training images.

    **And it spread.** `negatives.py` builds hard negatives by cutting random windows
    out of the photos, rejecting any window that overlaps a **labelled** pad. Photo 1776
    has no labelled pad, so nothing was rejected — and three windows were cut straight
    out of the pad and saved as *background*:

    <figure markdown>
      ![Three hard negatives that are actually close-ups of the pad](../Images/LandingPad/poisoned-negatives.jpg){ width="720" }
      <figcaption>neg_0003, neg_0004 and neg_0005 — traced back to the three copies of 1776 by template matching.</figcaption>
    </figure>

    These are worse than the original mistake. They are close-ups of exactly the feature
    the detector is supposed to key on — red tape on a dark mat — labelled "nothing
    here".

    **Effect:** 6 of 251 training images (2.4 %) tell the model that a clear pad is
    nothing: 3 whole images plus 3 crops. One missed annotation, amplified twice — first
    by the augmentation, then by the negative harvester. Whether it measurably hurt the
    deployed model is untested.

    **Fix:** annotate 1776 in Roboflow, re-export, and re-run `negatives.py` — the
    harvester will then avoid the pad by itself. Alternatively drop the three images and
    the three crops. Either takes minutes and is worth doing before the next training
    run.

    The held-out false-positive benchmark (`pad-negatives-bench`, 91 crops) is **not**
    affected: it is built from the validation and test splits, and 1776 is in training.
    The measured 0.02 false positives per image stands.

That single change turned out to be the most valuable one in the whole project — see
[Training](training.md#the-false-positive-lesson).

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

## A full audit of every image

Every image in the export and in the training set was checked mechanically — label
present and well-formed, class id, coordinates in range, box geometry, duplicate
detection, and a colour test comparing how much red tape falls inside the marked
region versus outside it. Everything the checks flagged was then looked at by eye.

| Check | Result |
|---|---|
| Missing, malformed or empty-by-mistake labels | **1 photo** — `1776`, above |
| Wrong class id, coordinates outside 0–1 | none |
| Identical images across splits (leakage) | none |
| More than one object marked | **1 photo** — `1761`, below |
| Extremely elongated boxes (up to 1:6.5) | 26 images, **all correct** — the pad seen almost edge-on really is that shape |
| Box containing almost no red | 1 image, **correct** — the pad is far away and only a few pixels across |
| Lots of red *outside* the marked pad | 65 images, **all correct** — the sports hall floor is painted with red lines |

The last row is worth noting on its own: in two thirds of the hall photographs, most of
the red in the picture is **not** the pad. That is the same fact that makes the red-X
verification filter useless, measured from a completely different direction — see
[Evaluation](evaluation.md#pattern-recognition).

**The double annotation (`1761`).** One image carries two overlapping outlines of the
same pad. Ground truth would then expect two detections where there is one, counting a
correct answer as a miss. It has no effect on anything here: the image is in the
original export's validation split and was dropped by our leak-free re-split, so no run
ever saw it and no measurement includes it.

## Files

| File | Purpose |
|---|---|
| `build_dataset.py` | leak-free re-split of the Roboflow export |
| `negatives.py` | harvest pad-free crops as hard negatives |
| `synth.py` | composite distant pads onto real floor (run E) |
| `build_2class.py` | merge pad + person data (runs G/H, see [Training](training.md#one-model-or-two)) |
