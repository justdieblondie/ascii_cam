# MIT License
#
# Copyright (c) 2025
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import shutil

import cv2
import numpy as np
from PIL import Image

if os.name == "nt":
    import ctypes
    import msvcrt
else:
    import select
    import termios
    import tty

ASCII_CHARS = np.asarray(list(" .,:;irsXA253hMHGS#9B&@"))
CHAR_ASPECT = 0.55
FONT_SCALE = 1.0

GREEN = "\033[32m"
RESET = "\033[0m"
CURSOR_HOME = "\033[H"
CLEAR_TO_END = "\033[J"


def enable_vt_mode() -> None:
    """Enable ANSI escape sequences on Windows consoles."""
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


class KeyboardListener:
    """Platform independent, non-blocking keyboard reader."""

    def __enter__(self):
        if os.name != "nt":
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if os.name != "nt":
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def poll(self):
        if os.name == "nt":
            if msvcrt.kbhit():
                key = msvcrt.getwch()
                if key in ("\x00", "\xe0") and msvcrt.kbhit():
                    msvcrt.getwch()
                    return None
                return key
            return None
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if not ready:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            # Swallow the rest of an escape sequence for special keys.
            while select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)
            return "\x1b"
        return ch


def compute_ascii_shape(frame_shape, term_size):
    height, width = frame_shape[:2]
    columns = max(1, term_size.columns)
    rows = max(1, term_size.lines)
    scale_width = columns / (FONT_SCALE * width)
    scale_height = rows / (height * CHAR_ASPECT)
    scale = min(scale_width, scale_height)
    if scale <= 0:
        return 0, 0
    ascii_width = max(1, int(width * scale))
    ascii_height = max(1, int(height * scale * CHAR_ASPECT))
    ascii_width = min(ascii_width, columns)
    ascii_height = min(ascii_height, rows)
    return ascii_width, ascii_height


def frame_to_ascii(frame, term_size):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ascii_width, ascii_height = compute_ascii_shape(gray.shape, term_size)
    if ascii_width < 1 or ascii_height < 1:
        return ""
    image = Image.fromarray(gray)
    resized = image.resize((ascii_width, ascii_height))
    pixels = np.asarray(resized)
    indices = (pixels / 255 * (ASCII_CHARS.size - 1)).astype(np.int32)
    lines = ["".join(row) for row in ASCII_CHARS[indices]]
    return "\n".join(lines)


def render_frame(ascii_art):
    sys.stdout.write(CURSOR_HOME + CLEAR_TO_END)
    if ascii_art:
        sys.stdout.write(GREEN)
        sys.stdout.write(ascii_art)
        sys.stdout.write(RESET)
    sys.stdout.flush()


def main():
    enable_vt_mode()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to open camera.", file=sys.stderr)
        return 1
    try:
        sys.stdout.write("\033[2J")
        sys.stdout.flush()
        with KeyboardListener() as keyboard:
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue
                key = keyboard.poll()
                if key:
                    if key.lower() == "q" or key == "\x1b":
                        break
                term_size = shutil.get_terminal_size(fallback=(80, 24))
                ascii_art = frame_to_ascii(frame, term_size)
                render_frame(ascii_art)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        sys.stdout.write(RESET + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
