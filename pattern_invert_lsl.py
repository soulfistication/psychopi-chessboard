#!/usr/bin/env python3
"""
Pattern Invert for PsychoPy with LSL triggers.

Displays a flickering checkered board (EEG visual stimulus), sends a trigger
on each flip via Lab Streaming Layer for Brain Access / EEG equipment.

Usage:
  python pattern_invert_lsl.py [--grid 16] [--interval 1.0] [--flickers 180] [--fullscreen]

Requires: psychopy, pylsl
"""

import argparse
import sys

try:
    from psychopy import visual, core, event
    from psychopy.visual.elementarray import ElementArrayStim
except ImportError:
    sys.exit("PsychoPy is required: pip install psychopy")

try:
    import pylsl
except ImportError:
    sys.exit("pylsl is required for LSL triggers: pip install pylsl")

import numpy as np

# Defaults (match original app)
DEFAULT_GRID = 16
DEFAULT_INTERVAL = 0.5
DEFAULT_FLICKERS = 180
BOARD_SIZE_NORM = 0.85  # board as fraction of window height
CROSS_SQUARES = 1
CROSS_THICKNESS_NORM = 0.006
# PsychoPy rgb color space is -1 (black) to +1 (white)
WHITE = (1, 1, 1)
BLACK = (-1, -1, -1)
RED = (0.77, 0.24, 0.24)  # ~#c43c3c


def parse_args():
    p = argparse.ArgumentParser(description="Pattern Invert with LSL triggers")
    p.add_argument("--grid", type=int, default=DEFAULT_GRID, metavar="N",
                   help=f"Grid size (squares per row, default {DEFAULT_GRID})")
    p.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, metavar="SEC",
                   help=f"Seconds between flickers (default {DEFAULT_INTERVAL})")
    p.add_argument("--flickers", type=int, default=DEFAULT_FLICKERS, metavar="N",
                   help=f"Number of flickers (default {DEFAULT_FLICKERS})")
    p.add_argument("--fullscreen", action="store_true", help="Run fullscreen")
    return p.parse_args()


def build_checker_colors(size, invert=False):
    """Two color arrays: checker (i+j)%2 and its inverse."""
    n = size * size
    colors = np.zeros((n, 3))
    for i in range(size):
        for j in range(size):
            idx = i * size + j
            fill = ((i + j) % 2 == 0) ^ invert
            colors[idx] = WHITE if fill else BLACK
    return colors


def run():
    args = parse_args()
    grid = max(2, min(64, args.grid))
    interval = max(0.05, args.interval)
    n_flickers = max(1, args.flickers)

    # LSL marker stream for Brain Access / EEG
    stream_name = "PatternInvert"
    stream_type = "Markers"
    info = pylsl.StreamInfo(
        stream_name,
        stream_type,
        channel_count=1,
        nominal_srate=pylsl.IRREGULAR_RATE,
        channel_format=pylsl.cf_string,
        source_id="pattern_invert_psychopy",
    )
    outlet = pylsl.StreamOutlet(info)

    # Window
    win = visual.Window(
        size=(1200, 800),
        units="height",
        fullscr=args.fullscreen,
        color=(0.06, 0.06, 0.07),
        allowGUI=not args.fullscreen,
    )

    # Board: grid of squares in height units
    cell_size = (BOARD_SIZE_NORM / grid)
    half = (grid - 1) / 2.0
    xys = []
    for i in range(grid):
        for j in range(grid):
            x = (j - half) * cell_size
            y = (half - i) * cell_size
            xys.append([x, y])
    xys = np.array(xys, dtype=np.float32)
    n_elements = grid * grid
    sizes = np.tile([cell_size], (n_elements, 2))

    colors_a = build_checker_colors(grid, invert=False)
    colors_b = build_checker_colors(grid, invert=True)

    # Solid squares: default tex/mask are a sine grating + gaussian, which
    # look like gradients. None/None + no interpolation gives hard edges.
    checker = ElementArrayStim(
        win,
        nElements=n_elements,
        xys=xys,
        sizes=sizes,
        colors=colors_a,
        colorSpace="rgb",
        elementTex=None,
        elementMask=None,
        interpolate=False,
        sfs=0,
    )

    # Red cross in center (1 square each arm)
    cross_w = CROSS_SQUARES * cell_size
    cross_h = CROSS_THICKNESS_NORM
    cross_horiz = visual.Rect(
        win, width=cross_w, height=cross_h,
        fillColor=RED, lineColor=None, units="height"
    )
    cross_vert = visual.Rect(
        win, width=cross_h, height=cross_w,
        fillColor=RED, lineColor=None, units="height"
    )

    # Notify recorders that the block is starting
    outlet.push_sample(["start"], pylsl.local_clock())

    clock = core.Clock()
    next_flip = 0.0
    flicker_count = 0

    while flicker_count < n_flickers:
        t = clock.getTime()
        if t >= next_flip:
            # Invert
            checker.colors = colors_b if (flicker_count % 2 == 0) else colors_a
            # LSL trigger: push with current LSL time so recorders can sync
            ts = pylsl.local_clock()
            marker = f"flicker_{flicker_count}"
            outlet.push_sample([marker], ts)
            next_flip = t + interval
            flicker_count += 1

        checker.draw()
        cross_horiz.draw()
        cross_vert.draw()
        win.flip()

        if event.getKeys(keyList=["escape", "q"]):
            break

    # Black screen (like original turnOffDisplay)
    win.color = (0, 0, 0)
    win.flip()
    outlet.push_sample(["end"], pylsl.local_clock())
    core.wait(0.5)
    win.close()


if __name__ == "__main__":
    run()
