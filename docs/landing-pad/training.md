---
tags:
  - ai
  - landing-pad
---

# Training

## Before the retraining: the weakest of three checkpoints was the deployed one

Three landing-pad checkpoints existed when this work started, and the inference
script on the Pi loaded the **oldest and worst** of them. Measured in FP32 on the
leak-free test split:

| Checkpoint | Trained | mAP50 | mAP50-95 |
|---|---|---|---|
| `best.pt` — **the one the Pi and the live demo loaded** | May, 50 ep @ 320 | 0.734 | 0.643 |
| `best-2.pt` | 27 May, 80 ep @ 416 | 0.799 | 0.647 |
| `pad_v2/weights/best.pt` | 24 Jun, 80 ep @ 416 | 0.995 | 0.971 |

After INT8 quantisation the deployed `best_int8.tflite` measured **mAP50 0.657**
(confirmed independently by `yolo val` on the `.tflite` itself). Simply pointing the
export at the June checkpoint was the single largest available improvement, and it
cost nothing.

That is also why the comparison below **retrains the old recipe from scratch** (run A)
instead of reusing any of these weights: all three were trained on the leaky split, so
none of them has uncontaminated data left to be measured on.

## The six runs

Six runs, all on the **same leak-free split**, so only the recipe differs.

| Run | Recipe | Outcome |
|---|---|---|
| A | the old recipe reproduced — 80 ep @ 416, `degrees=0`, `scale=0.5` | weak at altitude |
| B | drone recipe @ 320 — `degrees=180`, `flipud=0.5`, `scale=0.8`, `perspective`, cosine LR, 150 ep | large gain at altitude |
| C | drone recipe @ 416 | worse *and* 1.69× the compute |
| D | as B + FPV capture-path degradation (`fpv_aug.py`) | best under combined stress |
| E | as D + 124 composited distant pads (`synth.py`) | no improvement |
| **F** | **as D + 76 pad-free hard negatives** | **deployed** |

Every run reaches **mAP50 0.995** on validation. mAP does not separate them at
all — the stress probes in [Evaluation](evaluation.md) do.

## What each change was actually worth

- **Scale augmentation** (`scale=0.5 → 0.8`, run B) is the bulk of the gain.
  Worst-case altitude recall goes **0.25 → 0.56** purely from showing the
  network pads at more sizes.
- **FPV degradation** (run D) looks worthless on the capture-path probe alone,
  where every model scores 1.00 — a sharp photo downscaled to 320 px is easy no
  matter what. It only pays off *combined* with a small, rotated pad:
  **0.12 → 0.69** on the hardest case. Blur alone is easy; blur on a 35 px pad
  is not.
- **416 px** (run C) is not worth 1.69× the compute. It is *worse* than 320 at
  small sizes (0.00 vs 0.56 worst case), because the model is then run further
  from its training scale.
- **`degrees=180`** bought nothing measurable (rotation worst case 0.88 → 0.75,
  a two-image difference on 16). The pad is a square with a symmetric cross, so
  it is already 90°-symmetric and rotation invariance was largely free. Kept
  because it costs nothing, but it is not where the gain came from.
- **Synthetic distant pads** (run E) improved box precision (test mAP50-95 0.833
  vs D's 0.732) but lost on the hard combined cases.

!!! tip "Run each model at its training resolution"
    Every model degrades sharply off its native size. Run D produces **0.00**
    false positives per image at 320 px and **1.12** at 416 px — the same
    weights, a different input size.

## The false-positive lesson

Run D was the pick — and it was wrong.

Running D on a live webcam in an office produced landing pads on a **rucksack, a
wall poster and a chair back**. The tables above could not have caught this:
every one of the 16 test images *contains* a pad, so "false positives per image"
there only counts spurious *extra* boxes — never the failure that matters, a
detection in a scene with no pad in it at all.

`fp_bench.py` scores detections on **91 pad-free crops from the held-out
splits**, against recall on real pads:

| At conf 0.4 | False pos. / img | Recall | Recall at ×0.3 | Max conf. on an empty image |
|---|---|---|---|---|
| A (old recipe) | 0.02 | 1.00 | 0.81 | 0.54 |
| D | **0.33** | 1.00 | 0.94 | **0.87** |
| **F** = D + 76 negatives | **0.02** | 1.00 | **0.94** | 0.66 |

Run D fired on pad-free images with up to **0.87** confidence — higher than many
true detections, so **no threshold could have separated them**. Adding negatives
until the training set is 30 % background gives the old recipe's false-positive
rate together with the new recipe's range, and improves everything else too:

| | Rotation, worst | Altitude, worst | Test mAP50-95 |
|---|---|---|---|
| D | 0.75 | 0.62 | 0.732 |
| **F** | **0.94** | **0.69** | **0.810** |

!!! success "The general lesson"
    A detector trained almost entirely on images that contain the target learns
    that **the target is always present**. Measure on images that contain
    nothing.

**Run F is the deployed model, at conf 0.4** (0.3 on the quantised `.rpk` — see
[Deployment](deployment.md)).

## The cost: box precision

Heavy augmentation trades localisation accuracy for detection range. Mean IoU on
close-up pads — the last metre before touchdown:

| Run | Cut-out scene | Hall | Office |
|---|---|---|---|
| A (old) | 0.97 | 0.93 | 0.96 |
| D | 0.76 | 0.91 | 0.85 |

It comes from `scale=0.8` rarely showing the network a pad that fills the frame.
If the landing controller needs a precise pad centre in the last metre, this
regression is worth measuring in flight.

## One model or two?

The Pi CPU path runs **two** detectors per frame: run F for the pad, stock
YOLO11n for people (a person on the pad means the landing zone is blocked). The
AI Camera cannot do that — the IMX500 holds **one** network on the sensor, and
swapping costs a camera restart. So a single two-class detector was built.

`build_2class.py` merges the pad labels (class 0) with **2784 person instances**
recovered from a truncated `People-Detection-8` export (class 1), plus persons
pseudo-labelled by YOLO11n on our own photos. Without the recovered set the
person class was untrainable — 66 instances, and **zero in the test split**, so
it could not even have been measured.

| Run | Rotation aug | Pad mAP50 | Person mAP50 |
|---|---|---|---|
| G | `degrees=180`, `flipud=0.5` | 0.993 | 0.511 |
| **H** | `degrees=30`, `flipud=0` | **0.995** | **0.644** |

Run G's aggressive rotation halved person detection, which was predictable:
`degrees=180` had already been measured to buy the pad *nothing*, while people
in ordinary photos are upright.

H is still a trade, and standard mAP hides it entirely — H scores 0.995 on pads,
the same as F:

| | Pad, yaw 135° ×0.2 all | Pad, yaw 90° ×0.12 all | Person recall @ 0.4 |
|---|---|---|---|
| F + stock YOLO11n (two nets) | **0.75** | **0.62** | **0.59** |
| H (one net) | 0.38 | 0.12 | 0.51 |

!!! note "The recommendation depends on the target"
    - **Pi Zero CPU: keep the two networks.** Both jobs are done better.
    - **AI Camera: H is the only option** if the person class is needed at all.
      The per-frame loss may not be the whole story — the IMX500 runs on-sensor
      at up to 30 fps while the CPU path needs `SKIP_FRAMES = 2` to keep up, and
      more frames at lower per-frame recall can beat fewer frames at higher
      recall over a trajectory. That is a hypothesis worth testing in flight, not
      a proven claim.
    - **What is deployed today is the single-class pad model** (`labels.txt`
      contains exactly `landingPad`), because the pad is what the mission needs.

If H has to improve, two levers in order: re-download the person dataset (the
zip was truncated — `train/labels` and `valid/` never arrived), and oversample
the pad images, which are 172 of 2601 instances.

## Reproducing

```bash
python3 build_dataset.py                     # leak-free split
python3 negatives.py                         # hard negatives
python3 train_neg.py                         # run F  (the deployed model)
python3 compare.py    runs/*/weights/best.pt
python3 robustness.py runs/*/weights/best.pt
python3 fp_bench.py   runs/*/weights/best.pt
```

Training used Ultralytics 8.4.50 on Apple MPS: about **4 s/epoch** at 320 px on
175 images, ~13 minutes for the full run. Set `device="cpu"` if MPS is
unavailable.

!!! bug "Run G/H needs a newer Ultralytics"
    On Ultralytics 8.4.50 with torch 2.11, training the two-class set dies in the
    task-aligned assigner:

    ```
    RuntimeError: shape mismatch: value tensor of shape [31926]
    cannot be broadcast to indexing result of shape [39347]   (utils/tal.py)
    ```

    It is an MPS bug in boolean-mask assignment that only fires once images carry
    many objects — runs A–F had about one pad per image, the person images have
    up to 48. Ultralytics 8.4.90 with torch 2.12.1 runs it fine.
