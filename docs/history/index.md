# Project Journal

This section documents our project progress on a weekly basis. Each entry captures what we worked on, what we learned, what went wrong, and what comes next.

!!! info "Why we keep a journal"
    A weekly log serves three purposes: it makes our progress traceable, it forces us to reflect on what we actually achieved, and it becomes the raw material for the final documentation, the poster, and the live demo.

## Weekly entries

| Week | Period | Focus | Status |
|------|--------|-------|--------|
| [Week 1](week-01.md) | _tbd_ | Kickoff, equipment handover, team formation | ✅ |
| [Week 2](week-02.md) | _tbd_ | Familiarisation, ArduPilot flash, repo setup | ✅ |
| [Week 3](week-03.md) | _tbd_ |  | X |
<!-- Add new rows as the project progresses -->

## How to write a weekly entry

Every week, one team member is responsible for writing the entry. We rotate the role to share the workload.

### Workflow

1. Copy `_template.md` to a new file `week-NN.md` (zero-padded, e.g. `week-03.md`).
2. Fill in the sections below — keep it factual, not narrative.
3. Add the new file to `mkdocs.yml` under the `Project Journal` section.
4. Add a row to the table above.
5. Open a pull request so the rest of the team can review before merging.

### What belongs in a weekly entry

- **Concrete actions** taken by the team (what was actually done, not what was planned)
- **Decisions** made and the reasoning behind them
- **Problems** encountered, separated into resolved and still open
- **Artefacts** produced (parameter files, CAD models, photos, log files)
- **Next steps** for the following week

### What does *not* belong here

- Detailed how-to instructions — those go into the topic pages (`hardware/`, `autopilot/`, etc.)
- Long technical analyses — link to the relevant topic page instead
- Personal opinions or off-topic discussion

### Style guide

- Write in **past tense** — the journal records what happened.
- Be **specific**: "set `MOT_PWM_TYPE = 6` (DShot600)" beats "configured the ESCs".
- **Link** to topic pages, parameter files, issues, or pull requests whenever possible.
- Keep it **short**: one screen of text per week is usually enough.
