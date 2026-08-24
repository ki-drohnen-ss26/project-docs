---
tags:
  - ai
  - landing-pad
---

# Glossary

Every technical word used in this section, in one sentence. Nothing here is specific to
our project unless it says so.

## The model

**Object detector**
: A program that looks at a picture and draws a rectangle around each thing it
recognises. Ours recognises exactly one kind of thing: a landing pad.

**Model**
: The trained program itself — a file full of numbers that the computer uses to make
its decision. "Training a model" means adjusting those numbers until the answers get
good.

**YOLO / YOLO11n**
: A well-known family of object detectors. The `n` stands for *nano*, the smallest and
fastest version. We use the smallest one because it has to run on a tiny computer.

**Class**
: A category the model can recognise. Ours has one class, called `landingPad`. A model
with two classes could recognise pads *and* people.

**Bounding box**
: The rectangle the model draws around what it found — four numbers: left, top, right,
bottom.

**Inference**
: Running the finished model on a new picture to get an answer. Training is the slow
part done once; inference is the fast part done thousands of times.

**Input size**
: The picture size the model expects, ours 320 × 320 pixels. Camera pictures are shrunk
to this before the model sees them. Feeding a different size makes the model worse, even
though it still "works".

## The data

**Dataset**
: The collection of pictures used to teach the model, each one with the correct answer
marked by hand.

**Label / annotation**
: The hand-drawn marking that says "the pad is *here* in this picture". Ours are
polygons (outlines), not just rectangles.

**Train / validation / test split**
: The dataset is cut into three parts. The model *learns* from the training part,
is *checked during learning* on the validation part, and is *finally graded* on the
test part — which it must never have seen. Otherwise the grade is meaningless.

**Leakage**
: When pictures from the test part are also, effectively, in the training part — for
example two near-identical photos taken a second apart. The model then scores well by
remembering, not by understanding. This happened to us; see [Dataset](dataset.md).

**Augmentation**
: Making extra training pictures by altering the ones you have — flipping, rotating,
blurring, darkening. It teaches the model that a pad is still a pad when it looks
slightly different.

**Hard negative**
: A training picture that contains **no** pad at all. Without these, the model never
learns that "there is nothing here" is a valid answer. Adding them was the single most
useful thing we did.

**Roboflow**
: A website for storing, labelling and exporting datasets. Ours lives there.

## Measuring it

**Confidence**
: How sure the model is about one detection, from 0 to 1. `0.78` means fairly sure.

**Threshold**
: The confidence below which we throw a detection away. Set it too low and you get
nonsense; too high and you miss real pads.

**True positive / false positive**
: A *true positive* is a real pad the model found. A *false positive* is the model
claiming a pad where there is none — it once reported a rucksack as a landing pad.

**Recall**
: Of all the pads that were really there, what fraction did the model find? `1.00`
means it found every one.

**Precision**
: Of everything the model *claimed* was a pad, what fraction really was one?

**IoU (Intersection over Union)**
: How well the model's rectangle overlaps the correct one, from 0 (no overlap) to 1
(perfect). Usually a detection counts as correct at IoU ≥ 0.5.

**mAP**
: The standard **school grade for an object detector**: one number between 0 and 1,
where 1 is perfect. It rolls two things into one — did the model find the objects that
were there, and did it avoid inventing ones that were not. When someone says "the model
scores 0.99", they mean mAP.
:
    It comes in two strengths:
:
    - **mAP50** — *did you find it?* A detection counts as correct if the rectangle
      roughly overlaps the real pad (at least half).
    - **mAP50-95** — *did you find it AND draw a tight rectangle?* Much stricter, so
      this number is always lower. Our model scores 0.995 on the first and 0.81 on the
      second: it always finds the pad, but the rectangle is sometimes loose.
:
    In our project this grade turned out to be **useless for choosing between models**,
    because all six attempts scored almost exactly the same. See
    [Evaluation](evaluation.md).

**FP32 / INT8**
: How precisely the model's numbers are stored. **FP32** is full precision — the
original model as trained on a laptop. **INT8** stores the same numbers much more
coarsely, which makes the model roughly four times smaller and much faster, at a small
cost in accuracy. The drone needs INT8; the laptop does not.

**Epoch**
: One complete pass through all the training pictures. "80 epochs" means the model
looked at every picture 80 times.

**Checkpoint / weights**
: The saved file produced by training — the model itself. Ultralytics calls the best one
`best.pt`, which is why a folder can end up with several different files all called
"best".

**Saturated metric**
: A score that has stopped telling you anything because everything scores near the
maximum. Ours saturated at 0.995.

**Probe / stress test**
: Our own replacement for the saturated score: deliberately spoil the test pictures
the way flying spoils them — rotate them, shrink them, blur them — and see which model
survives.

**Nadir**
: Looking straight down. The drone's camera points nadir; all our training photos were
taken at an angle, by hand.

## Getting it onto the drone

**Raspberry Pi Zero 2 W**
: The small computer on the drone. It talks to the flight controller and runs the
mission logic. It is too slow to also run an AI model.

**IMX500 / Raspberry Pi AI Camera**
: A camera with a small AI processor built into the sensor itself. The model runs
*inside the camera*, and the Pi only receives the finished answer. This is the whole
reason we can do AI on this drone at all.

**NPU**
: Neural Processing Unit — the AI processor inside the camera sensor.

**Quantisation / INT8**
: Shrinking the model by storing its numbers with less precision (whole numbers instead
of decimals). It makes the model much smaller and faster, at a small cost in accuracy.
Required for the camera chip.

**`.tflite`**
: TensorFlow Lite — the model format for running on a normal processor, such as the
Pi's own CPU. Our fallback, not our main route.

**`.rpk`**
: Sony's package format. The **only** format the IMX500 camera chip can load. A
`.tflite` file cannot be used here.

**`packerOut.zip`**
: The half-finished result on the way from a trained model to an `.rpk`.

**ONNX**
: A general model-exchange format. We use it to *simulate* the quantised model on a
laptop, which is how most of the "quantised" numbers in [Evaluation](evaluation.md)
were measured — a good stand-in, but not the real sensor.

**NMS (Non-Maximum Suppression)**
: Cleaning up the model's raw output, which usually contains several overlapping
rectangles around the same object, down to one. On the IMX500 this already happens
inside the camera.

**Letterboxing**
: Shrinking a picture to the model's input size by adding grey bars instead of
squashing it, so nothing gets distorted. Getting this wrong silently ruins the results.

**`imx500-package`**
: The tool that builds the final `.rpk`. It only runs on ARM Linux — a Raspberry Pi or
an ARM build server, never a Mac or a normal PC.

## Flight side

**Companion computer**
: The Raspberry Pi, as opposed to the flight controller. It makes decisions; the flight
controller flies.

**Flight controller**
: The board that actually controls the motors and keeps the drone stable.

**MAVLink**
: The language the Pi and the flight controller speak to each other.

**EKF**
: The flight controller's internal estimate of where the drone is and how high. It
combines several sensors. Our detector depends on its height estimate to convert
"pad is 30 % to the right" into "pad is 1.2 m to the right".

**GUIDED mode**
: The flight mode in which the Pi, not the pilot, tells the drone where to go.

**Milestone 2**
: Our staged bring-up step in which the drone hovers and only *logs* what the camera
sees, without acting on it. The safe place to check that the detector's numbers are
right.
