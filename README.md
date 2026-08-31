# ST7796 INVON bug — evidence (Waveshare ESP32-S3-Touch-LCD-3.5, 2026-08-30)

Root cause of the "camera preview looks like an x-ray" report: the vendored
st7796 init never sent INVON (0x21), so the IPS panel displayed EVERYTHING in
negative from first boot. The inverted UI passed for a dark theme; camera
photos exposed it. Fix: PR MicroPythonOS/MicroPythonOS#280 (commit 555c3f6f),
upstream MicroPythonOS/lvgl_micropython#11.

- `shot_1to1.png` — on-device LVGL snapshot (lv.snapshot readback of the live
  launcher + RGB565 color-bar test image) taken WHILE the physical panel
  showed the same scene inverted. Bars and launcher are color-correct here,
  proving the render pipeline was fine and the corruption was panel-side.
  (A photo of the physical panel at the same moment showed cyan/magenta/
  yellow/black bars = exact bitwise inversion, and the launcher in negative.)
- `appframe_le.png` — a live camera preview frame (240x240 RGB565, OV5640)
  tapped out of the running Camera app and decoded little-endian: natural
  colors, proving the sensor data and capture path were clean all along.

Copies also pushed to the bitcoin3us/MicroPythonOS fork branch
`media/st7796-invon-evidence` and embedded in the PR discussions.
