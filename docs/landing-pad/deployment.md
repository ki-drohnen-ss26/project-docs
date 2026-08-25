---
tags:
  - ai
  - landing-pad
---

# Getting it onto the drone

!!! abstract "In short"
    A trained model is a file on a laptop. To use it on the drone it has to be
    repackaged, and there are two possible destinations: the Raspberry Pi's own
    processor, or the small AI chip built into the camera.

    **The camera is the right one**, because the Pi is already busy flying the drone.

    Repackaging for the camera takes three steps, and they cannot all run on the same
    machine — the last one only works on ARM Linux, which means a Raspberry Pi or a free
    ARM build server on GitHub.

    The rest of this page is the traps, so nobody has to find them twice.

## The two destinations

| | The Pi's own processor | The camera chip |
|---|---|---|
| File format | `.tflite` | `.rpk` |
| Where the model runs | on the Raspberry Pi | **inside the camera** |
| Speed | can only manage about one picture in three | up to 30 pictures per second |
| How many models at once | two (pad *and* people) | **one** |
| Confidence threshold | 0.4 | **0.5** ([why](evaluation.md#choosing-how-sure-the-model-has-to-be)) |

!!! tip "Why the camera chip is the better choice"
    The Raspberry Pi Zero 2 W has four small processor cores, and they are already
    fully occupied talking to the flight controller, watching the failsafes and running
    the mission. Moving the model into the camera takes the whole job off the Pi.

    That was the reason for buying this camera in the first place.

## Route 1: the Pi's own processor

!!! note "Prepared, but never used on the aircraft"
    This route works and is kept as a fallback, but nothing from it has ever flown. The
    drone went straight to the camera chip. If you only care about what is on the
    aircraft, skip to [route 2](#route-2-the-camera-chip).

```bash
python3 export.py runs/F_neg_fpv_320/weights/best.pt
```

That produces `pad_320_int8.tflite`, 3 MB. Copy it, the people model and `drone_pi.py`
into the same folder on the Pi and run:

```bash
python3 drone_pi.py --stream     # live picture at http://<pi-ip>:8080
```

??? bug "Three faults we had to fix in the old inference script"
    All three produced wrong boxes silently, rather than an error message.

    **Squashed pictures.** The camera picture was squeezed into a square instead of
    being padded to shape. Training pads the picture, so the model was being shown a pad
    25 % narrower than anything it had learned from. Fixing it improved box accuracy.

    **The wrong input.** The people model was being fed the *pad* model's prepared data.
    That happens to work while both models expect the same shape, and breaks silently as
    soon as one of them is exported differently.

    **A hard-coded size.** The picture size was written into the script as 320 while
    being read from the model everywhere else, so any other export produced boxes in the
    wrong place.

    `test_pi_inference.py` checks the corrected version against the marked-up pictures.

## Route 2: the camera chip

Three steps, and they cannot all happen in one place:

| Step | Where it runs | What comes out |
|---|---|---|
| 1. Shrink the model | any Linux machine — and macOS works too | a shrunk model |
| 2. Convert it | same | `packerOut.zip` |
| 3. Package it | **only on ARM Linux** | `network.rpk` |

```bash
./run_imx_local.sh                                   # steps 1-2, about 3.5 minutes
imx500-package -i packerOut.zip -o ~/models/pad      # step 3, on the Pi
```

`~/models/pad` is where the flight code expects to find it.

### Why step 3 only runs on ARM

Sony's documentation says this step must run on a Raspberry Pi. That is checkable rather
than something to take on trust: the software package contains **no version for normal
PCs**, and the program inside it is compiled for ARM processors only. No ordinary
computer can run it — not a Mac, not a cloud machine, not Google Colab.

Any ARM Linux machine works, which leaves three options:

- **the Raspberry Pi itself** — simplest, the hardware is already there;
- **a free ARM build server on GitHub** — our setup does exactly this: you upload
  `packerOut.zip`, and two minutes later `network.rpk` is ready to download. No Pi
  needs to be switched on;
- **an ARM container on an Apple Silicon Mac.**

??? note "Steps 1 and 2 do run on macOS, despite the tool refusing"
    The training tool blocks the export on anything but Linux. That block turns out to
    be over-cautious rather than necessary — none of the software involved contains
    anything Linux-specific:

    | Component | What it actually is |
    |---|---|
    | `imx500-converter` | plain Python, only passes work along |
    | `sdspconv` | plain Java, no platform-specific parts |
    | `model-compression-toolkit` | plain Python |
    | `ortools` | ships a macOS version |

    `export_imx_local.py` lifts the block and runs steps 1 and 2 on a Mac in about
    three and a half minutes.

### Two traps in the shrinking step

!!! danger "TensorFlow must not be installed"
    Sony's converter needs an older version of a shared library than TensorFlow does.
    The shrinking tool loads TensorFlow simply *because it is installed*, and the export
    then dies with a confusing import error.

    Use a separate Python environment with no TensorFlow in it.

!!! danger "Do not include the empty pictures when shrinking"
    Shrinking works by comparing the original model's answers with the shrunk one's on a
    set of sample pictures. On a picture with no pad, both answers are near zero, the
    comparison divides by roughly zero, and the whole process aborts with an error that
    never mentions pictures at all.

    So the [76 empty pictures](dataset.md#the-pictures-with-nothing-in-them) are
    essential for *training* and harmful for *shrinking*. `export_imx_local.py` filters
    them out; 197 sample pictures remain.

## Running it on the Pi

Two scripts, because there are two ways into the camera.

=== "`detect_pad.py`"

    Loads `network.rpk` directly.

    ```bash
    python3 detect_pad.py                # threshold 0.5
    python3 detect_pad.py --conf 0.4
    python3 detect_pad.py --preview      # needs a monitor attached
    ```

    The camera hands back four blocks of data: the boxes, how confident it is, which
    category, and how many detections are valid. The overlapping-box cleanup has already
    happened inside the camera, so the Pi only has to read and convert.

    !!! warning "Two details that silently produce boxes in the wrong place"
        - **The numbers are pixels, not fractions.** The boxes come back measured in
          pixels of the 320-pixel window, not as values between 0 and 1. They have to be
          divided by the window size first.
        - **The order is different.** The model gives left-top-right-bottom; the helper
          that maps them onto the real picture expects top-left-bottom-right. They have
          to be swapped.

        Both are taken from the camera manufacturer's own example. Getting either wrong
        gives you plausible-looking boxes in entirely the wrong place — see
        [Integration](integration.md).

=== "`pi_aicam.py`"

    Uses Sony's own library instead.

    ```bash
    python3 pi_aicam.py
    python3 pi_aicam.py --conf 0.4 --no-display
    ```

    This one wants `packerOut.zip` rather than `network.rpk` — it does the packaging
    step internally.

    First-time setup on the Pi:

    ```bash
    sudo apt update && sudo apt full-upgrade
    sudo apt install imx500-all
    sudo reboot
    pip install git+https://github.com/SonySemiconductorSolutions/aitrios-rpi-application-module-library.git
    ```

!!! warning "The camera's built-in demo will not show our detections"
    The demo software that ships with the camera can only read the output formats Sony's
    own models use. Ours is laid out differently, so the demo appears to run and shows
    nothing useful. Use one of the two scripts above.

!!! note "Do not change the picture size"
    The model expects 320 pixels. Run it at a different size and false alarms rise
    sharply — measured at none per picture at 320, and more than one per picture at 416.

## What a working test looks like

Confirmed on the drone's own Pi. The model uploads into the camera in a few seconds and
reports its size:

```
model input size: (320, 320)
number of tensor outputs: 4
```

Then, with the pad in front of the camera:

```
landingPad  centre 0.637,0.131  size 0.189x0.175  conf 0.50
landingPad  centre 0.637,0.132  size 0.189x0.177  conf 0.50
landingPad  centre 0.638,0.133  size 0.189x0.175  conf 0.56
```

The centre is where the pad sits in the picture — `0.5, 0.5` would be dead centre. Watch
how little it moves between frames: that smoothness is what a working detector looks
like.

!!! note "Confidence comes back in steps"
    You will only ever see certain values — 0.32, 0.38, 0.44, 0.50, 0.56 and so on,
    about 0.06 apart. That is normal, and it is why the threshold is 0.5 rather than 0.3
    ([the reasoning](evaluation.md#what-the-real-camera-does-differently)).

## Three things that look broken and are not

!!! warning "The first run after changing models seems to do nothing"
    Loading a new model into the camera uploads about 3 MB and takes roughly **45
    seconds**. A test with a 15-second timer that starts before the upload finishes will
    process one picture and look broken. Start the timer after the upload finishes.

!!! warning "`Failed to reserve DRM plane`"
    The camera's example script wants to open a preview window, which needs a monitor.
    Over a remote connection there is none, so it aborts. Both scripts above run without
    a window and print to the terminal instead.

!!! warning "A flood of `Failed to queue buffer` messages"
    After an aborted run the camera can be left half-configured, and the next run fills
    the screen with errors. `sudo reboot` on the Pi clears it. Nothing needs
    reinstalling.

## The scripts

| File | What it does |
|---|---|
| `export.py` | makes the file for the Pi's processor, and measures what shrinking costs |
| `export_imx.py` | steps 1–2 for the camera chip, on Linux |
| `export_imx_local.py`, `run_imx_local.sh` | the same steps on a Mac |
| `make_imx_bundle.py`, `imx_colab.ipynb` | the same steps in the cloud instead |
| `.github/workflows/imx500-rpk.yml` | step 3 on GitHub's free ARM server |
| `drone_pi.py` | runs the model on the Pi's processor |
| `detect_pad.py`, `pi_aicam.py` | run the model on the camera chip |
| `live.py` | try it on a webcam, a video or a single picture on a PC |
