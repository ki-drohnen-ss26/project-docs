---
tags:
  - ai
  - landing-pad
---

# Deployment

The trained model is a PyTorch checkpoint. It has to be converted for the
aircraft, and there are **two targets** with different trade-offs.

| | Raspberry Pi CPU | Raspberry Pi AI Camera (IMX500) |
|---|---|---|
| Format | `.tflite` (INT8) | `.rpk` (Sony package) |
| Where inference runs | Pi Zero 2 W CPU | **on the sensor's NPU** |
| Frame rate | needs `SKIP_FRAMES = 2` to keep up | up to 30 fps, CPU free |
| Models per frame | two (pad + person) | **one** — the sensor holds one network |
| Confidence threshold | 0.4 | **0.3** |

!!! tip "Why the AI Camera is the better target"
    The Pi Zero 2 W has four cores that are already busy with MAVLink and the
    mission state machine. Moving inference onto the sensor removes the detector
    from the flight-critical CPU budget entirely — which was the original reason
    for choosing this camera.

## Raspberry Pi CPU (TFLite)

```bash
python3 export.py runs/F_neg_fpv_320/weights/best.pt
```

Produces `pad_320_int8.tflite` (3.0 MB). Copy it, `yolo11n_int8.tflite` and
`drone_pi.py` into the same directory on the Pi and run:

```bash
python3 drone_pi.py --stream      # MJPEG on http://<pi-ip>:8080
```

!!! bug "Three defects that were fixed in the inference path"
    These silently produced wrong boxes rather than errors, so they are worth
    naming:

    - **Aspect ratio.** `cv2.resize(frame, (S, S))` squashed 640×480 into a
      square. Training and validation *letterbox*, so the network was shown a pad
      25 % narrower than anything it had been trained on. Letterboxing raised
      mean IoU from 0.834 to 0.851.
    - **Shared input tensor.** The person model was fed the *pad* model's tensor.
      It works only while both exports happen to share a shape and dtype, and
      misfeeds silently as soon as one is re-exported.
    - **Hard-coded `IMG_SIZE`.** 320 was hard-coded while the input size was read
      from the model, so box coordinates were wrong for any other export size.

    `test_pi_inference.py` checks the corrected path against the dataset labels.

## AI Camera (IMX500, `.rpk`)

Three steps, and they **cannot all happen in one place**:

| Step | Where | Tool | Output |
|---|---|---|---|
| 1. Quantise (MCT) | any x86 Linux — Colab works; macOS also works | `model-compression-toolkit` | quantised model |
| 2. Convert | same | `imx500-converter[pt]` | `packerOut.zip` |
| 3. Package | **aarch64 Linux only** | `imx500-tools` | `network.rpk` |

```bash
./run_imx_local.sh                                   # steps 1-2, ~3.5 min on an M-series Mac
imx500-package -i packerOut.zip -o ~/models/pad      # step 3, on the Pi
```

`~/models/pad` is the path the flight code expects (`config.camera_model_path`) and
the one used in [AI Software](../software/ai-software.md).

### Why step 3 is ARM-only

The Raspberry Pi documentation states that this step must run on a Raspberry Pi.
That is verifiable rather than a matter of trust: `imx500-tools` ships **no
`amd64` and no `all` package**, and its `rpk_packager` and `fpk2rpk` are
aarch64 ELF binaries. No x86 machine runs them — not Colab, not a cloud VM.

Any *aarch64* Linux does, which gives three options:

- the **Raspberry Pi** itself — simplest, the hardware is already there;
- a **GitHub Actions `ubuntu-24.04-arm` runner** — free, and the package's
  dependencies (`libarchive13`, `bc`, `default-jre-headless`, `jq`, `zip`) are
  all stock Ubuntu, so the Raspberry Pi `.deb` installs there unchanged. The
  workflow takes `packerOut.zip` and uploads `network.rpk` as an artifact, so no
  Pi has to be powered on;
- an **arm64 container on an Apple Silicon Mac**, which runs them without
  emulation.

### Steps 1–2 run on macOS after all

Ultralytics guards the IMX export with `assert LINUX`, but that assertion is
conservative rather than necessary — the toolchain carries no Linux-specific
code:

| Package | What it actually is |
|---|---|
| `imx500-converter` | pure Python, only dispatches |
| `sdspconv` | pure Java — Scala/Kotlin JARs, no `.so` / `.dylib` / `.dll` |
| `model-compression-toolkit`, `edge-mdt-*` | pure Python |
| `ortools` | ships `macosx_11_0_arm64` wheels |

`imxconv-pt --version` runs on macOS, so `export_imx_local.py` lifts the guard
(`exporter.LINUX = True`) and does steps 1–2 locally.

### Pitfalls we hit

!!! danger "No TensorFlow in the export environment"
    Sony's converter pins `protobuf==4.25.5`; TensorFlow needs 5.x.
    `model_compression_toolkit` imports TF merely *because it is installed*, and
    the export then dies with `cannot import name 'runtime_version'`. Use a
    separate virtualenv with no TensorFlow in it.

!!! danger "No pad-free images in the calibration set"
    MCT's mixed-precision search compares float and quantised outputs and
    normalises by their norm. On an image with no pad the confidence output is
    ~0, the normalisation divides by ~0, and the solver aborts with
    `PulpError: Cannot multiply variables with NaN/inf values`.

    The 76 hard negatives are **essential for training and harmful for
    calibration**, so `export_imx_local.py` filters them out — 197 calibration
    images remain.

!!! note "Quantisation here is not the same as INT8 conversion"
    The IMX path uses gradient-based post-training quantisation over a
    representative dataset, which is why it takes a `data` argument and several
    minutes, unlike the plain INT8 TFLite conversion.

## Running it on the Pi

Two scripts, because there are two ways into the sensor:

=== "`detect_pad.py` — picamera2 + `IMX500`"

    Loads `network.rpk` directly through the `picamera2` device API.

    ```bash
    python3 detect_pad.py                # conf 0.3
    python3 detect_pad.py --conf 0.4
    python3 detect_pad.py --preview      # needs a monitor
    ```

    The sensor returns **four** tensors — boxes `(300,4)`, confidences `(300,)`,
    classes `(300,)` and the number of valid detections `(1,)`. NMS has already
    run on the sensor.

    !!! warning "Two details that silently produce wrong boxes"
        - **Normalisation.** The boxes arrive as **pixels in the 320 px input
          window, not as 0…1**. They must be divided by the input height before
          use.
        - **Coordinate order.** YOLO emits `(x0, y0, x1, y1)`, but
          `convert_inference_coords()` expects `(y0, x0, y1, x1)`. The values
          have to be reordered.

        Both are taken from `picamera2`'s own example. Getting either wrong
        produces plausible-looking boxes in the wrong place. The flight code now
        normalises the pixel case automatically and selects the order via
        `cam_box_order` — which still has to be set to `xyxy` for this export, see
        [Integration](integration.md#open-items-to-verify-on-the-bench).

=== "`pi_aicam.py` — Sony `modlib`"

    ```bash
    python3 pi_aicam.py
    python3 pi_aicam.py --conf 0.4 --no-display
    ```

    `modlib` takes **`packerOut.zip`, not `network.rpk`** — it packages
    internally. The `.rpk` is only needed for the `picamera2`/`rpicam-apps`
    route.

    Prerequisites on the Pi:

    ```bash
    sudo apt update && sudo apt full-upgrade
    sudo apt install imx500-all
    sudo reboot
    pip install git+https://github.com/SonySemiconductorSolutions/aitrios-rpi-application-module-library.git
    ```

!!! warning "`rpicam-apps` post-processing does not fit this model"
    The bundled `imx500_object_detection` stage parses the output formats Sony
    ships models in. It does **not** match Ultralytics' YOLO output layout, so
    the built-in demo will not display our detections correctly. Use one of the
    two scripts above.

### Three things that look like failures and are not

!!! warning "The first run after switching models processes almost no frames"
    Selecting a *new* model uploads ~3 MB of firmware to the sensor, which takes about
    **45 seconds**. A run with a 15-second duration timer that starts before the upload
    finishes will process a single frame and look broken. Start the timer *after* the
    upload progress bar completes, and add a short warm-up so auto-exposure settles —
    the first frames after start are dark or washed out and produce spurious
    (non-)detections.

!!! warning "`Failed to reserve DRM plane` — the demo wants a display"
    `picamera2`'s bundled `imx500_object_detection_demo.py` starts a DRM preview
    window, which needs a screen. Over SSH on a headless Pi it aborts with
    `RuntimeError: Failed to reserve DRM plane`. Both scripts above use
    `show_preview=False` and log to the terminal instead.

    The same applies to `rpicam-hello --nopreview`: the post-processing stage emits its
    results as *image overlay* metadata, so with no preview there is nowhere for them
    to land and the output is silently empty. Use `rpicam-still` to save an annotated
    frame if you want to see them.

!!! warning "A flood of `V4L2 ... Failed to queue buffer` needs a reboot"
    After an aborted run the IMX500 / V4L2 pipeline can be left partially configured;
    the next run then floods the terminal with queue-buffer errors and the camera stays
    unresponsive. `sudo reboot` on the Pi clears it — no reinstall required.

!!! note "Do not change the input size"
    The model expects a **320 px** input. Run outside its training resolution and
    false positives rise sharply — measured at 0.00 → 1.12 per image going from
    320 to 416.

## Files

| File | Purpose |
|---|---|
| `export.py` | TFLite INT8 export, with quantisation loss measured |
| `export_imx.py` | IMX500 export, steps 1–2 (Linux) |
| `export_imx_local.py` / `run_imx_local.sh` | the same steps on macOS |
| `make_imx_bundle.py` / `imx_colab.ipynb` | bundle + ready-to-run Colab cell |
| `.github/workflows/imx500-rpk.yml` | arm64 CI job: `packerOut.zip` → `network.rpk` |
| `drone_pi.py` | on-drone inference, Pi CPU path |
| `detect_pad.py` / `pi_aicam.py` | on-drone inference, AI Camera path |
| `live.py` | webcam / video / image demo on a PC |
