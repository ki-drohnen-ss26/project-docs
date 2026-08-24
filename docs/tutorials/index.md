# Tutorials

This section is the guided entry point into the project. While the topic sections
(Hardware, Software, Autopilot, Sensors, Delivery System, Frame Extension) document each
subsystem in depth, the tutorials tell you **in which order** to work through them and
what a first hands-on session with the kit looks like.

## What the tutorials cover

| Tutorial | For whom | What you get |
|----------|----------|--------------|
| [Quick Start](quickstart.md) | A new team on day one with the delivered kit | Charging, binding, first power-up with a Smoke Stopper, first manual flight — safely |
| [Build Guide](build-guide.md) | Anyone rebuilding the full autonomous-delivery setup | An ordered checklist that chains every page of this documentation into one rebuild path, with a "done when" criterion per step |

## Recommended reading order for a new team

1. **[Quick Start](quickstart.md)** — get the delivered drone flying *manually* first.
   You will need confident manual flying (and the pilot-takeover safety net it enables)
   throughout the whole project, and the quick start front-loads the safety habits
   (Smoke Stopper, prop guards, props-off bench rule, kill switch) that everything else
   assumes.
2. **[Build Guide](build-guide.md)** — then follow the rebuild path step by step. It
   links into the topic sections at the right moments, so you read each deep-dive page
   exactly when you need it.
3. **Topic sections as reference** — once you know the order, use
   [Hardware](../hardware/index.md), [Software](../software/index.md),
   [Autopilot](../autopilot/index.md), [Sensors](../sensors/index.md),
   [Delivery System](../delivery-system/index.md) and
   [Frame Extension](../frame/index.md) as lookup material while you work.
4. **[Results](../results/index.md)** — read the
   [Limitations](../results/limitations.md) page and the
   [incident report of 2026-08-21](../problems/incident-analysis-2026-08-21.md) *before* your
   first autonomous flight attempt. They exist so you do not have to repeat our
   most expensive lessons.

!!! tip "Simulation before hardware"
    The single most valuable workflow decision we made was **SITL first**: every piece
    of companion code and every parameter change is validated against an
    ArduCopter 4.6.3 software-in-the-loop simulation before it touches the real flight
    controller. The [simulation setup page](../software/SetupSimulation.md) explains how
    to build it; the [Build Guide](build-guide.md) tells you when to use it.

## Prerequisites

- Basic Linux command-line skills (the Raspberry Pi companion runs Debian).
- Python fundamentals (the companion code uses `pymavlink`).
- No prior FPV or ArduPilot experience is required — that is what these pages are for —
  but budget real practice time for manual flying before any autonomous test.
