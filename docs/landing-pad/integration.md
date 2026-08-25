---
tags:
  - ai
  - landing-pad
---

# Talking to the flight software

!!! abstract "In short"
    Two separate programs on the Pi read the same camera, and they do **not** produce
    the same thing.

    What runs today prints **positions in the picture** — *"the pad's centre is at 0.63,
    0.13"* — to the terminal, and sends them nowhere.

    What the flight software needs is **distances on the ground** — *"the pad is 1.2 m
    to your right"*. The code to convert one into the other exists, and has never been
    run.

    This page is the agreement between the two halves, and the list of what is still
    missing between them.

## What actually runs today

`detect_pad.py` on the Pi. It loads the model into the camera, reads a detection per
picture and prints it:

```
landingPad  Mitte 0.628,0.135  Groesse 0.178x0.175  conf 0.32  px=(345, 23, 114, 84)
```

| What it prints | What it means |
|---|---|
| `Mitte 0.628,0.135` | where the pad's centre sits **in the picture**. `0.5, 0.5` would be dead centre |
| `Groesse 0.178x0.175` | how much of the picture the pad fills. Bigger means closer to it |
| `conf 0.32` | how sure the model is |
| `px=(...)` | the same box in pixels |

Three things to notice, because they are the whole point of this page:

- **These are fractions of the picture, not metres.** There is no distance anywhere in
  that line.
- **The drone's height is not involved.** The program never asks how high the aircraft
  is, because it does not need to in order to print a fraction.
- **It sends nothing anywhere.** It prints to a terminal. The flight software is not
  listening, and is not even running at the same time.

That is a complete, working detector. It is not yet connected to anything.

!!! warning "Status: the detector and the flight software have never met"
    They work, separately.

    `detect_pad.py` tracks the pad in real time on the drone's own Pi. The flight
    software has flown, but only ever with the pretend camera — a mode that simply
    claims to have found the pad after a fixed delay, so a flight can be tested without
    a detector.

    Nobody has yet started the flight software with the real camera switched on. Three
    things stand in the way, all listed below: one wrong setting, one missing safeguard,
    and one number that needs checking.

## Where this fits in the flight

The camera points **straight down**. The drone climbs to about 2 m and flies a search
pattern across the hall, and this page describes what happens on every single picture
while it does so:

| The drone is | The detector says | The flight software does |
|---|---|---|
| searching | "no pad" | keep flying the pattern |
| searching | "pad, 1.2 m right, 0.4 m ahead" | stop searching, start closing in |
| closing in | "pad, 0.3 m right, 0.1 m ahead" | nudge sideways, at most 30 cm at a time |
| closing in | "pad, 0.05 m right, 0.02 m ahead" | that counts as centred — release, then land |

"Centred" means within **15 cm**. Everything below exists so that those metre figures
mean what both halves think they mean.

## What the flight software expects instead

The flight software does not want fractions. It has its own camera module
(`RealCamera` in the Pi-Code repository) which reads the same camera and produces this:

| Value | Meaning |
|---|---|
| found | was a pad seen at all |
| **left / right** | how far the pad is to the drone's right, **in metres** |
| **forward / back** | how far the pad is ahead of the drone, **in metres** |
| height | the height used to work those out |

**That module has never run.** It is the missing link: same camera, same model, but it
converts the fractions into ground distances before handing them over.

!!! info "Why metres, and not "30 % of the picture""
    A camera naturally reports *"the pad is 30 % of the frame to the right"*. But the
    mission logic is written in metres — how close counts as centred, how big a
    correction to make — and all of it was tested in the simulator against a camera that
    reported metres.

    If the real camera reported percentages instead, every one of those settings would
    quietly mean something different, and none of the simulator testing would carry over.

### How a fraction becomes a distance

This is the step `detect_pad.py` does not do and `RealCamera` does. It needs the drone's
height, because the further up the aircraft is, the more ground each percent of the
picture covers:

```
distance on the ground = tan( fraction of the picture × half the camera's angle ) × height
```

The camera's viewing angle is 66° across and 52.3° top to bottom.

!!! warning "That assumes the camera points straight down and uses the full sensor"
    Every correction is scaled by these numbers. If the camera is tilted, or cropped, or
    switched to a different mode, they are wrong and every correction is wrong with them.
    A tilted camera would need its tilt taken into account, which nothing currently does.

## Checking which way round it is

Which way the camera is mounted decides whether "right in the picture" means right for
the drone. That cannot be guessed — it has to be checked on the real aircraft. It is a
setting rather than code, so checking it does not mean editing anything mid-test:

| Setting | Meaning |
|---|---|
| `cam_swap_axes` | camera mounted rotated a quarter turn |
| `cam_invert_x` | "positive" must mean the pad is to the **right** |
| `cam_invert_y` | "positive" must mean the pad is **ahead** |

**How to check.** Hover. Put the pad clearly to the drone's **right** and confirm the
logged sideways number is **positive**. Then put it **ahead** and check the other one.

That is bring-up step 2 (`python main.py --milestone 2`), which flies the detector in
watch-only mode — it logs what it sees and drops nothing.

!!! danger "A wrong sign is worse than no detection at all"
    With the sign inverted, the drone corrects *away* from the pad — smoothly,
    confidently, and with nothing in the log looking wrong.

## The settings that still have to change

The flight software ships with values chosen to be safe when there is no detector at
all. Three need changing before the detector may fly:

| Setting | Currently | Change to | Why |
|---|---|---|---|
| `camera_source` | `"timed"` | `"real"` | `"timed"` is the honest no-camera mode: it just claims to have found the pad after a fixed delay |
| `cam_box_order` | `"yxyx"` | **`"xyxy"`** | our camera reports the box the other way round, so the default reads it sideways |
| `camera_model_path` | `/home/drone/models/pad/network.rpk` | leave, and put the file there | the on-Pi scripts currently point one folder higher — make them agree |

`camera_confidence` is already correct at `0.5`
([why](evaluation.md#what-the-real-camera-does-differently)).

## What is still open

Two things were checked against the real camera and turned out fine. Two are not fine
yet.

!!! success "Fixed: the box numbers are read correctly"
    The camera reports its boxes in pixels rather than fractions, which used to be
    misread. The flight software now detects that and converts automatically.

    It falls back to assuming a 640-pixel model if it cannot ask the camera — which
    would halve every correction, since ours is 320. On the drone's own hardware the
    question is answered correctly, so the fallback never happens. Setting it to 320
    anyway costs nothing and removes the trap.

!!! warning "1. `cam_box_order` is on the wrong setting"
    **Confirmed on the camera.** It reports the box as left-top-right-bottom; the flight
    software's default expects top-left-bottom-right, so it reads the two axes swapped.

    The symptom is that left/right and forward/back come out **exchanged** — which is
    easy to "fix" by flipping `cam_swap_axes`, hiding the real cause. Set
    `cam_box_order` to `"xyxy"`.

!!! warning "2. Nothing rejects a single bad frame"
    The detector returns its best guess for **every** picture, and the approach logic
    acts on it. In the bench test, occasional impossible boxes appeared — stuck to the
    edge of the frame, far too long and thin — each lasting one frame, while the real
    pad held steady for dozens.

    Something has to sit between the two. Either require the pad in **3 of 4
    consecutive pictures** in roughly the same place, or throw away impossible shapes,
    or both. A landing controller should never react to a single picture anyway.

!!! warning "3. The height used for the conversion is unreliable near the floor"
    Every distance is scaled by the drone's height, and that height comes from the
    flight controller's own estimate — which since the
    [August crash](../problems/incident-analysis-2026-08-21.md) is based mainly on the
    **air-pressure sensor**.

    The team's own logs show that sensor reading **4 to 6.7 metres** while the drone is
    centimetres off the floor, because the propellers push air down onto it.

    Distance scales directly with height, so a height that reads 4 m when the drone is
    at 1 m makes every correction about four times too big.

    **When this bites.** During the search at 2 m the estimate should be reasonable — the
    downwash effect is worst close to the ground. The dangerous moment is the **final
    descent**, which is exactly when the corrections need to be smallest and most
    accurate.

    Nobody has measured how bad it actually is. Worth comparing the reported height
    against the downward-facing distance sensor during a hover, and considering feeding
    that sensor into this calculation directly.

!!! note "For the record: four blocks of data, not three"
    The camera returns boxes, confidences, categories **and** a count of valid
    detections. The flight software checks for at least three and ignores the fourth,
    scanning all 300 slots and filtering by confidence instead. That works; using the
    count would be cheaper.

!!! tip "One hover checks all of it"
    Bring-up step 2 flies the detector in watch-only mode. Put the pad at a **measured**
    distance — say exactly 1 metre to the drone's right, level with it, at a known
    height — and compare the logged metres against a tape measure.

    - left/right and forward/back swapped → problem 1, the box order
    - occasional wild readings between good ones → problem 2, no single-frame filter
    - roughly four times too large close to the floor → problem 3, the height

## Related pages

- [Deployment](deployment.md) — how the model gets onto the camera, and which script reads it
- [Evaluation](evaluation.md) — where the confidence threshold comes from
- [AI Camera Module](../hardware/ai-camera.md) — connecting the camera and installing its firmware
- [AI Software](../software/ai-software.md) — why the model runs inside the camera at all
- [Limitations](../results/limitations.md) — the sensor and firmware limits this page depends on
