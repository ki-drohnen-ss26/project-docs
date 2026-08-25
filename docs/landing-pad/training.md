---
tags:
  - ai
  - landing-pad
---

# Teaching the model

!!! abstract "In short"
    We trained the model six times with different settings, to find out which settings
    actually help.

    **What helped most:** showing it the pad at many different sizes. Without that it
    only recognised pads that were large in the picture — useless for a drone looking
    down from a height.

    **The mistake worth remembering:** our best-scoring model reported landing pads on
    a rucksack, a poster and a chair. It had almost never seen a photo *without* a pad,
    so "there is nothing here" was an answer it had never learned.

    **What we use:** the sixth attempt, which we call run F.

## First: three old models, and the scripts pointed at the worst one

When this work started, three trained models from earlier attempts were lying around,
all with names like *"best"*. The test scripts loaded the **oldest and weakest** of the
three.

Here they are, graded on the same photos. The grade is a single number between 0 and 1;
higher is better, 1.0 would be perfect. (It is called *mAP* — [what it measures](glossary.md#measuring-it).)

| Model file | Trained | Grade |
|---|---|---|
| `best.pt` — **the one the scripts loaded** | May | 0.73 |
| `best-2.pt` | end of May | 0.80 |
| `pad_v2` | June | **0.99** |

A much better model already existed. Nobody had switched over to it.

!!! note "None of these ever ran on the drone"
    They only ever ran on laptops — in test scripts and in a webcam demo. The first
    model to actually reach the aircraft is the one described in
    [Getting it onto the drone](deployment.md), and it went straight onto the camera
    chip. There was never an older model on the drone to replace.

!!! warning "None of these three grades can be trusted"
    All three were trained on the badly sorted pictures described in
    [Dataset](dataset.md#the-sorting-problem). They had already seen the photos they
    were being graded on, so the grades measure memory, not ability.

    That is why the comparison below **starts the old settings again from scratch**
    (we call it run A). Only then are the numbers comparable.

??? note "The exact figures, for the record"
    Measured at full precision on a laptop, on the re-sorted grading pile:

    | Checkpoint | Trained | mAP50 | mAP50-95 |
    |---|---|---|---|
    | `best.pt` (the one the scripts loaded) | May, 50 epochs @ 320 px | 0.734 | 0.643 |
    | `best-2.pt` | 27 May, 80 epochs @ 416 px | 0.799 | 0.647 |
    | `pad_v2/weights/best.pt` | 24 Jun, 80 epochs @ 416 px | 0.995 | 0.971 |

    A shrunk copy of that same checkpoint had also been prepared for the Raspberry Pi's
    processor, and measured **mAP50 0.657** in that form. It was never put on the
    aircraft.

## The six attempts

Same pictures every time, so only the settings differ.

| Run | What changed | Result |
|---|---|---|
| A | the old settings, repeated | bad at spotting distant pads |
| B | show the pad at many more sizes, and rotated | big improvement at distance |
| C | feed the model larger pictures (416 instead of 320 px) | worse, and 1.7× slower |
| D | as B, plus fake motion blur, noise and compression | best under combined stress |
| E | as D, plus fake distant pads pasted onto floors | no improvement |
| **F** | **as D, plus the 76 pictures with no pad** | **this is the one we use** |

**Every single one scored about 0.995.** The standard grade could not tell them apart
at all — which is what the [Evaluation](evaluation.md) page is about.

## What actually helped, and what did not

**Showing the pad at many sizes: this was the whole gain.** In the first attempt the
model lost half its detections once the pad got small in the picture. Simply varying the
size during training more than doubled how well it coped. Nothing else came close.

**Fake motion blur: useless on its own, valuable in combination.** Tested by itself, it
made no measurable difference — every model handled a blurry photo fine. But on a pad
that was *both* small *and* rotated *and* blurred — which is what an approaching drone
actually sees — it lifted the hit rate from 0.12 to 0.69.

**Bigger pictures: not worth it.** 416 pixels instead of 320 costs 1.7× the computing
time and made the model *worse* at small pads, because it was then being used further
from the size it was trained at.

**Turning the pad through a full circle during training: bought nothing.** That was
expected in hindsight — the pad is a square with a symmetrical cross, so it already
looks the same every quarter turn. We kept it because it costs nothing.

**Pasted-on fake distant pads: no.** They made the box slightly tighter but performed
worse on exactly the hard cases they were meant to fix. See
[Dataset](dataset.md#what-did-not-work-fake-pictures).

!!! tip "Use the model at the size it was trained at"
    The same model produces **no** false alarms at 320 pixels and **more than one per
    picture** at 416. Nothing about the model changed — only the size of the picture fed
    into it.

## The false-alarm lesson

Attempt D was the winner, and it was the wrong choice.

Run on a live webcam in an office, it reported landing pads on a **rucksack, a wall
poster and a chair back** — with confidence up to 0.87, higher than many of its correct
detections. No threshold could have separated them.

**Why our tests missed this.** Every one of the 16 grading photos *contains* a pad. So
"false alarms per picture" only ever counted extra boxes drawn *next to* a real pad. The
failure that matters — claiming a pad in a room where there is none — could not show up,
because there was no such picture to show it in.

**Why the model did it.** Not one of the 175 training pictures was empty. "There is
nothing here" was an answer it had literally never seen, so it always pointed at
whatever looked most pad-like.

**The fix:** the 76 empty pictures from [Dataset](dataset.md#the-pictures-with-nothing-in-them).
Measured on 91 pad-free pictures the model had never seen:

| | False alarms per picture | Still finds real pads | Still finds *distant* pads |
|---|---|---|---|
| A (old settings) | 0.02 | yes, all | 0.81 |
| D | **0.33** | yes, all | 0.94 |
| **F** = D + 76 empty pictures | **0.02** | yes, all | **0.94** |

Run F has the old settings' false-alarm rate *and* the new settings' range. It also got
better at rotated and distant pads at the same time.

!!! success "The lesson in one sentence"
    A model trained only on pictures that contain the thing learns that the thing is
    always there. Test it on pictures containing nothing.

## What it cost: box accuracy

Training on heavily varied pictures buys detection range and costs precision in where
exactly the box sits. On close-up pads — the last metre before touchdown:

| Run | Black background | **Hall** | Office |
|---|---|---|---|
| A (old) | 0.97 | **0.93** | 0.96 |
| D | 0.76 | **0.91** | 0.85 |

Read the **Hall** column first — it is the only one showing the place the drone actually
works. It is also the one that barely moves: 0.93 → 0.91, against 0.97 → 0.76 on the
black-background pictures.

If the landing needs a very precise centre in the final metre, this is worth measuring
in flight.

## A short detour: spotting people too

It would be useful to know whether somebody is standing on the pad. On a normal computer
that is easy — run a second, off-the-shelf model alongside ours.

**The camera chip cannot do that.** It holds exactly one model at a time, and swapping
means restarting the camera. So detecting people as well would mean training *one*
model that recognises both, from scratch, including gathering and marking up pictures of
people.

We tried it to see what it would cost. **The pad half kept working** — the combined
model finds pads just as well as ours does. The people half worked less well, and the
combined model got noticeably worse at the difficult pad cases.

We did not pursue it further. **The model on the drone is the pad-only one**, because
the pad is what the mission needs, and that decision is easy to revisit later.

??? note "The numbers, if you want them"
    Two attempts at the combined model:

    | Run | What changed | Finds pads | Finds people |
    |---|---|---|---|
    | G | pad rotated through a full circle during training | 0.993 | 0.511 |
    | **H** | only slight rotation | **0.995** | **0.644** |

    Heavy rotation halved the ability to spot people — predictable, since people in
    photos are upright and the pad gains nothing from rotation.

    Even the better attempt is a trade, and the standard grade hides it completely (0.995
    on pads either way). Only the stress tests show it:

    | | Pad: rotated and distant | Pad: worst case | People |
    |---|---|---|---|
    | Two separate models | **0.75** | **0.62** | **0.59** |
    | One combined model (H) | 0.38 | 0.12 | 0.51 |

    That comparison is not quite fair to the combined model: the camera chip runs at up
    to 30 pictures per second while a Raspberry Pi processor manages roughly one in
    three, and more attempts at lower accuracy can beat fewer at higher accuracy. That
    is a reasonable guess, not something we measured.

    If it ever needs improving: re-download the person pictures (the archive we used was
    truncated), and show the pad pictures more often during training — they are only 172
    of 2601 marked objects.

## Doing it again yourself

```bash
python3 build_dataset.py     # re-sort the piles
python3 negatives.py         # cut out the empty pictures
python3 train_neg.py         # run F, the model we use
python3 compare.py    runs/*/weights/best.pt
python3 robustness.py runs/*/weights/best.pt
python3 fp_bench.py   runs/*/weights/best.pt
```

Run F takes about **20 minutes** on an Apple laptop with a graphics chip — 149 passes
over the pictures at roughly 8 seconds each. The shorter runs take 8 to 18 minutes; the
combined pad-and-people model takes about 36. Set `device="cpu"` if there is no graphics
chip available; it just takes longer.

??? bug "The combined model needs a newer version of the training tool"
    On Ultralytics 8.4.50 with torch 2.11, training the two-class set crashes:

    ```
    RuntimeError: shape mismatch: value tensor of shape [31926]
    cannot be broadcast to indexing result of shape [39347]   (utils/tal.py)
    ```

    It is a bug in Apple's graphics support that only appears once pictures contain many
    objects — our pad pictures have about one each, the person pictures up to 48.
    Ultralytics 8.4.90 with torch 2.12.1 runs it fine.
