---
tags:
  - ai
  - landing-pad
---

# Getting it onto the drone

!!! abstract "In short"
    A trained model is a file on a laptop. To reach the drone it has to be repackaged
    into the format the camera chip understands.

    That takes three steps, and they cannot all run on the same machine: the last one
    only works on ARM hardware. We use GitHub's free ARM build server for it.

    The rest of this page is the traps, so nobody has to find them twice.

## Why the model runs inside the camera

The Raspberry Pi Zero 2 W has four small processor cores, and they are already fully
occupied talking to the flight controller, watching the failsafes and running the
mission. It cannot also run a detector at a useful rate.

The camera we were given solves that: the Raspberry Pi AI Camera has a small AI
processor built into the sensor itself. The model runs **inside the camera**, and the Pi
only receives the finished answer.

That leaves exactly one route to get the model onto the aircraft, and the rest of this
page is it.

| | |
|---|---|
| File format the camera needs | `.rpk` |
| Where the model runs | inside the camera, not on the Pi |
| Speed | up to 30 pictures per second |
| How many models at once | **one** |
| Confidence threshold | **0.5** ([why](evaluation.md#choosing-how-sure-the-model-has-to-be)) |

!!! note "A CPU version exists, and was never used"
    `export.py` can also produce a `.tflite` file that runs on the Pi's own processor.
    It was built and measured, but never put on the aircraft — the Pi is not fast enough
    for it. It is kept only as a reference point in [How we tested it](evaluation.md), and
    is not described further here.

## The three steps

They cannot all happen in one place:

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

### Why step 3 needs different hardware

The packaging tool is compiled for **ARM processors only**. It does not run on a Mac, an
ordinary PC or in Google Colab. That leaves two practical options:

- **the Raspberry Pi itself**, since the hardware is already there;
- **GitHub's free ARM build server**, which is what this project uses: upload
  `packerOut.zip`, and about two minutes later `network.rpk` is ready to download. The Pi
  does not even have to be switched on.

??? note "Steps 1 and 2 also run on macOS, despite the tool refusing"
    The training tool blocks the export on anything but Linux. That block is
    over-cautious rather than necessary — none of the software involved contains
    anything platform-specific, and `export_imx_local.py` lifts it and runs both steps on
    a Mac in about three and a half minutes.

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
    category, and how many detections are valid.

    The cleanup of overlapping boxes has already happened **inside the camera**, so the
    Pi only reads and converts. That is not a guess: the export tool bakes it in and says
    so — `IMX export requires nms=True, setting nms=True` — and the raw model produced
    2100 candidate boxes per picture before export, against the 300 slots the sensor
    returns.

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

The centre is where the pad sits in the picture — `0.5, 0.5` would be dead centre.

!!! note "Confidence comes back in steps"
    You will only ever see certain values — 0.32, 0.38, 0.44, 0.50, 0.56 and so on,
    about 0.06 apart. That is normal, and it is why the threshold is 0.5 rather than 0.3
    ([the reasoning](evaluation.md#what-the-real-camera-does-differently)).

## Two things that look broken and are not

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
| `export_imx_local.py`, `run_imx_local.sh` | steps 1–2, on a Mac |
| `export_imx.py` | the same steps on Linux |
| `make_imx_bundle.py`, `imx_colab.ipynb` | the same steps in the cloud instead |
| `.github/workflows/imx500-rpk.yml` | **step 3 on GitHub's free ARM server** |
| `detect_pad.py`, `pi_aicam.py` | run the model on the camera chip |
| `live.py` | try it on a webcam, a video or a single picture on a PC |
| `export.py`, `drone_pi.py` | the unused Raspberry Pi processor route |
