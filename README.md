# Pattern Invert (PsychoPy + LSL)

PsychoPy version of the pattern-invert flickering checkerboard for EEG. Sends **trigger events via Lab Streaming Layer (LSL)** so Brain Access and other EEG equipment can record stimulus timing.

## Setup

```bash
cd psychopy_pattern_invert
pip install -r requirements.txt
```

## Run

```bash
python pattern_invert_lsl.py
```

Optional arguments:

| Argument       | Default | Description                    |
|----------------|---------|--------------------------------|
| `--grid N`     | 16      | Squares per row (checkerboard) |
| `--interval SEC`| 1.0     | Seconds between flickers       |
| `--flickers N`  | 180     | Number of flickers             |
| `--fullscreen`  | off     | Run in fullscreen              |

Examples:

```bash
python pattern_invert_lsl.py --fullscreen
python pattern_invert_lsl.py --grid 8 --interval 0.5 --flickers 120
```

## LSL stream

- **Stream name:** `PatternInvert`
- **Stream type:** `Markers`
- **Channel format:** string
- **Markers:**
  - `start` – block start (once)
  - `flicker_0`, `flicker_1`, … – one per flip
  - `end` – block end (once)

Use the same machine (or synchronized clock) for your LSL recorder (e.g. Brain Access, Lab Recorder) so it can subscribe to this stream and align markers with the EEG.

## Controls

- **Escape** or **Q** – quit early (still sends `end` before closing).
