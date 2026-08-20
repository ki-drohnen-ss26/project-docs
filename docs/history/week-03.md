---
title: Week 3
tags:
  - journal
---

# Week 3 — AI camera, IMX500 firmware, YOLO11n on the sensor

**Period:** _tbd_
**Focus areas:** Raspberry Pi networking, AI camera, IMX500 model deployment, YOLO11n export pipeline

## Summary

This week we brought the Raspberry Pi AI Camera fully online and ran our first
neural network on the IMX500 sensor — first the bundled MobileNet-SSD, then a
custom-exported **YOLO11n**. We also built a reproducible IMX export pipeline:
first via Google Colab, then locally in a Docker container on the MacBook,
which removes the dependency on cloud sessions. We finished the week with a
working headless Python script that streams YOLO detections to the terminal
and saves an annotated image — the foundation for any later drone-side AI
logic.

## What we did

### Networking — adding a phone hotspot to the Pi

`eduroam` blocks client-to-client traffic, so SSH to the Pi from the laptop is
not possible on campus. We added an iPhone hotspot as a second known network
in NetworkManager. The Pi now automatically associates with whichever known
network is in range (home Wi-Fi or hotspot).

```bash
# Force a fresh scan first (results from `nmcli device wifi list` can be cached)
sudo nmcli device wifi rescan
sleep 5
nmcli device wifi list

# Add the hotspot profile (autoconnect on, high priority)
sudo nmcli connection add \
  type wifi con-name "iphone-hotspot" ifname wlan0 \
  ssid "<EXACT_HOTSPOT_SSID>" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "<HOTSPOT_PASSWORD>" \
  connection.autoconnect yes \
  connection.autoconnect-priority 20
```

### AI camera — hardware, firmware, first picture

Connected the IMX500 to the Pi Zero 2 W via the Mini-CSI adapter cable.
Verified detection without taking a picture, then installed the IMX500
firmware bundle, then took a first JPEG.

```bash
# Verify the sensor is detected on the I2C bus
rpicam-hello --list-cameras
# Expected: "0 : imx500 [4056x3040 10-bit RGGB] ..."

# Install the IMX500 firmware, pre-built models and rpicam-apps post-processing stages
sudo apt install -y imx500-all
sudo reboot

# First sanity-check picture (no preview window because we run headless)
rpicam-jpeg --output ~/test.jpg --timeout 5000 \
  --width 2028 --height 1520 --nopreview
```

The pre-built models landed in `/usr/share/imx500-models/`. The bundle
deliberately does **not** contain YOLO — that has to be exported separately
(see below).

### First AI inference — MobileNet-SSD

Used the pre-built MobileNet-SSD model that ships with `imx500-all`, with the
matching post-processing JSON from `rpi-camera-assets`. This produced an
annotated still that correctly identified a person — first confirmation that
the whole pipeline (sensor → on-chip NN → metadata → drawn boxes → JPEG)
works end-to-end.

```bash
rpicam-still -t 60s \
  --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json \
  --output ~/detection.jpg --nopreview
```

### YOLO11n export pipeline — Colab as first iteration

The Ultralytics IMX exporter is **Linux-only**, so it cannot run on macOS at
all. We first used **Google Colab**, which is a Linux x86_64 environment with
GPU/CPU available for free, and exported a YOLO11n model with the (very
minimal) `coco8` calibration set.

```python
# In a Colab notebook
!pip install ultralytics --quiet
!yolo export model=yolo11n.pt format=imx
# After the run completes:
from google.colab import files
files.download('yolo11n_imx_model/packerOut.zip')
files.download('yolo11n_imx_model/labels.txt')
```

The export produces a `packerOut.zip` which still needs to be packaged into a
sensor-loadable `.rpk` file. On the Pi this is done by `imx500-package`
(part of `imx500-tools`, already pulled in as a dependency of `imx500-all`):

```bash
# On the Mac: copy files to the Pi
scp packerOut.zip labels.txt frouks@<PI-IP>:~/

# On the Pi: produce network.rpk
imx500-package -i ~/packerOut.zip -o ~/yolo11n_rpk
ls -lh ~/yolo11n_rpk/network.rpk
```

### YOLO11n export pipeline — local, reproducible, via Docker

To remove the dependency on Colab sessions (90-minute idle timeout, files
lost on browser close), we set up the same pipeline locally using
**OrbStack** as the Docker runtime on the MacBook. OrbStack is preferred
over Docker Desktop on Apple Silicon because it is faster and more
resource-efficient. The Ultralytics image is only published for `linux/amd64`,
so x86_64 emulation has to be forced — OrbStack handles this via Rosetta 2.

```bash
docker pull ultralytics/ultralytics:latest-cpu

docker run -it --rm --platform linux/amd64 \
  -v "$(pwd):/workspace" \
  -w /workspace \
  ultralytics/ultralytics:latest-cpu \
  bash

# Inside the container — calibrate with a larger dataset
yolo export model=yolo11n.pt format=imx data=coco128.yaml
```

The export ran for about 7 minutes inside the container. Output files
appeared directly in `~/drone-yolo/yolo11n_imx_model/` on the host, thanks to
the volume mount — no `docker cp` needed.

### Headless Python test script with annotated output

The Picamera2 `imx500_object_detection_demo.py` from the upstream repo
requires a display to render bounding boxes (DRM preview), which fails on
our headless Pi (`Failed to reserve DRM plane`). We wrote our own minimal
test script `~/yolo_test.py` that:

- Loads any `.rpk` model via `IMX500(args.model)`
- Runs the camera with `show_preview=False`
- Discards the first ~2 s of frames so AE/AWB can settle
  (otherwise an initial firmware upload eats the entire run time)
- Logs detections to the terminal per frame
- Saves the last frame with detections as a JPEG with OpenCV-drawn boxes

```bash
python3 ~/yolo_test.py \
  --model ~/yolo11n_v2_rpk/network.rpk \
  --labels ~/labels.txt \
  --threshold 0.3 \
  --duration 15 \
  --output ~/detection_v2.jpg
```

The script also worked when re-targeted at our v1 model
(`~/yolo11n_rpk/network.rpk`) without any code change — model path is just an
argument. This is the foundation we'll build the drone-side detection logic on.

## Decisions made

| Decision | Reasoning |
|----------|-----------|
| Use YOLO11n (not YOLOv8n) | YOLO11n is slightly more accurate at the same speed and parameter count, and is officially supported by the IMX export. Both would work; YOLO11n is strictly the better default. |
| Use Docker / OrbStack instead of a full VM for the IMX export | A container shares the kernel with the host (lightweight, near-native performance, seconds to start), a VM emulates a full machine (heavy, slow). On macOS there is an OrbStack-managed Linux mini-VM under the hood, but it is shared across all containers. For a wrap-up workload like `yolo export`, a container is the obvious fit. |
| Use OrbStack instead of Docker Desktop | OrbStack is faster on Apple Silicon, uses fewer resources, and integrates with Apple's Virtualization Framework. Free for personal/student use. |
| Use a dedicated Conda environment for Ultralytics on the Mac (before we moved to Docker) | Keeping the `base` conda environment clean. Mixing pip-installed and conda-installed packages in the same env had already caused trouble with `pip-autoremove` not being able to uninstall conda-managed packages. |
| Use Python 3.11 in the Conda env (not 3.13) | Several Ultralytics dependencies still trailed Python 3.13 support; 3.11 is the well-tested baseline. |
| Treat the IMX export as a two-stage pipeline (Mac/Cloud quantises → Pi packages) | The final `imx500-package` step is shipped as part of `imx500-tools` on the Raspberry Pi anyway. Splitting at the `packerOut.zip` boundary makes the workflow independent of which platform did the quantisation step. |
| Run the AI camera detection on the sensor itself (not on the Pi CPU) | The Pi Zero 2 W cannot run YOLO at usable frame rates on its CPU. The IMX500's on-chip NPU runs the same inference at ~30 FPS while leaving the Pi free for MAVLink, servo control, and other drone tasks. |

## Problems

### Resolved

- **Problem:** Pi could not find the iPhone hotspot in `nmcli device wifi list`.
  **Cause:** Two combined causes: (1) iPhones only broadcast the hotspot
  beacon actively while the *Personal Hotspot* settings screen is open, and
  (2) by default modern iPhones use 5 GHz, but the Pi Zero 2 W only has
  2.4 GHz Wi-Fi.
  **Fix:** Enable *Maximize Compatibility* on the iPhone (forces 2.4 GHz),
  keep the hotspot screen open during the scan, then run
  `sudo nmcli device wifi rescan; sleep 5; nmcli device wifi list`.

- **Problem:** `rpicam-jpeg` reported `failed to open file /home/pi/test.jpg`
  even though everything else worked.
  **Cause:** Modern Pi OS no longer creates a default `pi` user; our user is
  `frouks`, so `/home/pi/` does not exist.
  **Fix:** Use `~/test.jpg` or `$HOME/test.jpg` instead of hard-coding the
  path.

- **Problem:** `rpicam-hello -t 0s --post-process-file ... --nopreview`
  produced no terminal output, even though MobileNet-SSD was running.
  **Cause:** The `imx500_object_detection` post-processing stage emits its
  results as image overlay metadata, not as console logs. With `--nopreview`
  there is nowhere for the overlay to land, so the output is silent.
  **Fix:** Switched to `rpicam-still` to save an annotated frame to disk,
  which made the detections visible.

- **Problem:** YOLO export on macOS failed with
  `Export only supported on Linux.`
  **Cause:** Hard assertion in Ultralytics' `export_imx` (`assert LINUX, ...`).
  **Fix:** Moved the export to a Linux environment — first Google Colab,
  then a local Docker container (OrbStack) on the MacBook.

- **Problem:** Colab export crashed with
  `ImportError: cannot import name 'runtime_version' from 'google.protobuf'`.
  **Cause:** The Ultralytics auto-install downgraded `protobuf` for the
  `imx500-converter` dependency, breaking TensorFlow which had already been
  loaded against the newer `protobuf`.
  **Fix:** *Runtime → Restart session* in Colab so Python reloads with the
  reconciled package versions, then re-run the export. Worked on second
  attempt.

- **Problem:** OrbStack-Container was killed (`Killed`) during the IMX
  conversion, but the `packerOut.zip` was already on disk and the process
  appeared to hang for ~30 minutes afterwards.
  **Cause:** A subprocess was OOM-killed under memory pressure
  (or possibly forced to terminate by OrbStack due to unresponsiveness during
  the Rosetta-emulated quantisation peak). The parent process kept waiting
  for the zombie subprocess.
  **Fix:** Cancel the hung process — `packerOut.zip` was already generated.
  Increased OrbStack memory allocation to 12 GB for future runs. For very
  large runs (full COCO calibration) consider using `docker cp` instead of
  a bind mount to avoid the virtual filesystem overhead.

- **Problem:** Python demo `imx500_object_detection_demo.py` exited with
  `RuntimeError: Failed to reserve DRM plane`.
  **Cause:** The demo tries to start a DRM preview window, which requires a
  display. We run the Pi headless via SSH.
  **Fix:** Wrote our own minimal `yolo_test.py` that uses
  `Picamera2.start(config, show_preview=False)` and logs detections to the
  terminal directly.

- **Problem:** First run after switching to the v2 model only processed 1
  frame in 15 seconds.
  **Cause:** The first time a *new* model is selected, the IMX500 firmware
  upload of ~3 MB takes ~45 seconds. Our script's `--duration 15` timer was
  starting before the upload finished.
  **Fix:** Added a 2-second warm-up loop *after* the firmware-upload progress
  bar completes, before starting the duration timer.

- **Problem:** Subsequent run produced a flood of
  `V4L2 ... Failed to queue buffer` errors and the camera was unresponsive.
  **Cause:** The IMX500 / V4L2 pipeline ended up in a partially-configured
  state from the previous aborted run.
  **Fix:** `sudo reboot` on the Pi. After the reboot the sensor was usable
  again.

### Still open

- **Problem:** Saved detection JPEGs are pixelated.
  **Current hypothesis:** The script uses Picamera2's preview configuration
  (640×480) for the saved image, not the higher-resolution sensor output.
  **Next action:** Switch to `create_still_configuration` with e.g.
  2028×1520, increase the OpenCV text scale and rectangle line thickness.
  Watch RAM usage — the Pi Zero 2 W only has 512 MB.

- **Problem:** YOLO11n produces visibly more false positives (`toothbrush`,
  `surfboard`, `skateboard`) than expected at threshold 0.3.
  **Current hypothesis:** Quantisation calibration set is still too small
  (we ran with `coco128`, Sony recommends 300+). For the drone task itself
  this will become irrelevant once we train a custom model on our own
  target objects, but for a documented "off-the-shelf YOLO11n on IMX500"
  comparison we may want one full-COCO run.
  **Next action:** Optionally run a long `data=coco.yaml` export overnight
  in the Docker container (~3–6 h on the M4 Pro in Rosetta emulation) and
  compare detections side-by-side.

## Artefacts

- `yolo_test.py` — headless YOLO/MobileNet-SSD test script with annotated
  JPEG output (on the Pi at `~/yolo_test.py`)
- `yolo11n_rpk/network.rpk` — YOLO11n exported with `coco8` calibration
  (Colab, baseline)
- `yolo11n_v2_rpk/network.rpk` — YOLO11n exported with `coco128` calibration
  (Docker / OrbStack, improved)
- `labels.txt` — 80 COCO class names matching both `.rpk` files
- Annotated detection JPEGs `detection_v1.jpg`, `detection_v2.jpg`
- Initial side-by-side observations of v1 vs v2: v1 already detects
  `person` reliably (0.85–0.94) and finds the bottle intermittently
  (0.32–0.68), but produces several false-positive classes
  (`toothbrush`, `surfboard`)

## Next week

- [ ] Improve image quality of the test script (higher-resolution still
      configuration, larger text/line thickness, larger output JPEG).
- [ ] Stream the detection output as MJPEG over HTTP so the team can
      watch live during testing without copying files.
- [ ] Wire the script up to the servo so a detection of a specific class
      triggers the drop mechanism (first step towards Task 5).
- [ ] Begin researching the MTF-01P configuration over the CP2102 UART
      adapter (Task 4 — position / altitude hold).
- [ ] Decide which custom classes we want for the drone-specific YOLO model
      (landing markers, package, …) and start collecting training data.

---

*Related pages:* `../hardware/ai-camera.md`, `../hardware/raspberry-pi.md`,
`../software/ai-software.md`, `../software/raspberry-pi-os.md`