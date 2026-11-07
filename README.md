# Chethan Gesture Control

A Python desktop application that uses webcam hand tracking to control the mouse, with a live gesture status and FPS overlay.

**Customizer and maintainer: Chethan Kumar D**

This is a customized and rebranded version of an existing hand gesture control project. Chethan Kumar D maintains this version; the underlying application was adapted from existing source code. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for original-source attribution.

## Requirements

- Windows, a webcam, and a desktop session.
- The existing project-local `.venv`, with dependencies from `requirements.txt` installed.
- `hand_landmarker.task` beside `main_v3.py`.

Dependencies include OpenCV, MediaPipe, NumPy, and PyAutoGUI. Keep `.venv` in the project directory.

## Launch

Double-click **Start_Gesture_Control.cmd**. It uses `.venv\Scripts\python.exe` and sets the working directory to its own folder, regardless of where it is started. Missing launch files and application errors remain visible in the console.

Alternatively, from PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe .\main_v3.py
```

Starting the application opens the webcam. Focus the camera window and press **Q** to quit.

## Existing controls

| Gesture | Action |
| --- | --- |
| Open palm, all fingers extended | Drop an active drag; otherwise move the cursor |
| Thumb and index pinch | Left click |
| Thumb and middle pinch | Right click |
| Index and middle raised, ring and pinky lowered | Scroll by moving the hand vertically |
| Closed fist | Grab once and keep dragging while held |
| Q key in the camera window | Quit |

While drag is active, eligible hand movement moves the held cursor. Losing hand tracking releases active dragging. The existing low-FPS safety pause remains in place. A held fist never repeatedly toggles. Pinches confirm once and require separation before another click; cursor movement freezes during confirmation.

## Configuration and structure

Edit `gesture_v3/config.py` for application settings, sensitivity, gesture thresholds, cooldowns, and UI colors. Root-level `config.py` belongs to the legacy implementation.

- `main_v3.py`: application entry point.
- `gesture_v3/core/`: application loop and action handling.
- `gesture_v3/perception/`: tracking and smoothing.
- `gesture_v3/intent/`: gesture classification.
- `gesture_v3/control/`: cursor physics.
- `gesture_v3/ui/`: visual overlay.

## Desktop shortcut

1. Right-click `Start_Gesture_Control.cmd` and choose **Show more options > Send to > Desktop (create shortcut)**, or **Send to > Desktop (create shortcut)** where available.
2. Rename the shortcut **Chethan Gesture Control**.
3. In Properties, confirm that **Target** contains the full, quoted path to the launcher. **Start in** is optional because the launcher sets its own working directory.

Keep the project and `.venv` together. If the project moves, update the shortcut target; virtual environments may need recreation after relocation.

## Attribution and licensing

This rebrand does not claim original authorship of all underlying code or grant new rights to upstream code, dependencies, or model assets. Preserve original copyright and license notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Control regression checks

Run without opening the webcam or controlling the real mouse:

```powershell
.\.venv\Scripts\python.exe tests/test_controls.py
```

The checks inject a fake mouse module and forbid camera creation. They cover pinch confirmation and release, grab/drop, movement transitions, stationary tremor, hand loss, capture failure, low-FPS suspension, and exception cleanup.

For a user-started camera session, the console prints mean capture-read and inference times on exit, with call counts. Mocked timing is not a camera performance measurement. Capture settings, inference model, and the low-FPS threshold remain unchanged; no performance improvement is claimed.

Manual verification: check slow/fast pointing and stopping, hold each pinch (one click), separate and repeat, hold a fist while dragging, open your palm to drop once, try pinching/scrolling during a drag, and remove/reintroduce your hand. Confirm no pointer jumps, unexpected actions, or stuck drag. Verify perceived responsiveness and timing with the actual webcam.
