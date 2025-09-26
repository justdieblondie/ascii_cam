# ASCII Cam

ASCII Cam streams webcam footage as ASCII characters directly in your terminal. The script samples frames from your default camera, converts them to grayscale, maps each pixel to a character based on brightness, and continuously redraws the terminal with the resulting text image.

## Requirements

- Python 3.9 or newer
- OpenCV (`opencv-python` package)
- NumPy
- Pillow

Install the dependencies with:

```bash
pip install opencv-python numpy pillow
```

## Usage

```bash
python ascii_cam.py
```

- Press `q` or `Esc` to exit the program.
- Resize the terminal to change how much of the ASCII image is visible; the renderer adjusts to the current window size while preserving aspect ratio.

## How It Works

1. The program opens the default webcam using OpenCV.
2. Each frame is converted to grayscale and resized to match the terminal dimensions.
3. Pixel intensities are mapped to a predefined gradient of ASCII characters.
4. The console is cleared and redrawn with the new ASCII frame on every iteration.
5. Keyboard input is polled without blocking so you can quit instantly with `q` or `Esc`.

## License

This project is released under the MIT License. See the header in `ascii_cam.py` for details.
