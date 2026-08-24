# Drone Tuning

!!! info "Status"
    The **initial** tuning (battery voltage range, `MOT_THST_EXPO`, PID starting
    values, filters, harmonic notch setup) is part of the setup guide — see
    [Initial Setup](InitialSetup.md#initial-tuning-parameters-and-linear-thrust).
    In-flight fine tuning (manual PID refinement or AutoTune) requires a flying
    aircraft and is **still open**: the drone is grounded since the
    [2026-08-21 incident](../../problems/incident-analysis-2026-08-21.md).

## Planned tuning path (once the aircraft flies again)

1. **Verify the basics** — vibration levels (`VIBE` in the dataflash log below 30 m/s²,
   no clipping), motor order/direction, `MOT_THST_HOVER` learned in a stable hover.
2. **Manual rate tuning** — if visible oscillations appear, halve
   `ATC_RAT_{RLL,PIT}_{P,I,D}` until they stop, then raise in 10 % steps
   (see the troubleshooting list in [Initial Setup](InitialSetup.md#hover-test)).
3. **Harmonic notch verification** — with bi-directional DShot RPM telemetry
   (`INS_HNTCH_MODE = 3`), check the pre-/post-filter batch-sampler FFT in the log.
4. **AutoTune** — only outdoors or in a large netted hall, one axis at a time
   (`AUTOTUNE_AXES`), with plenty of altitude — not an indoor exercise.

## Sources

- <https://ardupilot.org/copter/docs/tuning-process-instructions.html>
- <https://ardupilot.org/copter/docs/autotune.html>
