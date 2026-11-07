# Chethan Gesture Control

**Developer: Chethan Kumar D**

## Overview

Chethan Gesture Control is a Windows desktop application that turns hand gestures into mouse actions through a webcam. It supports cursor movement, left and right clicks, dragging, and vertical scrolling, with a live camera view and on-screen gesture status.

Built with Python, OpenCV, MediaPipe, NumPy, and PyAutoGUI, the application combines real-time hand tracking with gesture recognition for hands-free desktop interaction. It includes adaptive cursor smoothing, confirmed pinch clicks, drag-and-drop control, and a Windows launcher for convenient startup.

## Features

- Relative cursor movement from the index-finger base, with adaptive smoothing, limited acceleration, and a dead zone for small movements.
- Confirmed left and right pinches, with one click per pinch, separation required before another click, and a click cooldown.
- Cursor movement suspended during pinch confirmation and while a pinch is held.
- Fist-to-grab and open-palm-to-drop dragging, without repeated toggling while held.
- Vertical hand-motion scrolling, blocked during dragging along with click actions.
- Movement references reset when switching modes or losing tracking, to avoid carrying stale movement into a new action.
- Drag release on hand loss, capture failure, low-FPS suspension, and normal loop cleanup.
- A live camera view with gesture visuals and FPS; console capture/inference timing summaries on exit.

Recognition and perceived responsiveness depend on lighting, camera placement, hand pose, and hardware. Timing summaries are measurements from the current session, not a claim of improved performance.

## Requirements

- Windows with an interactive desktop session and a working webcam. The application selects camera index `0`.
- Python with compatible releases of the packages in [requirements.txt](requirements.txt).
- A project-local virtual environment named `.venv`.
- The supplied `hand_landmarker.task` model beside `main_v3.py`.

The virtual environment is excluded from Git. A fresh download or clone needs its own local environment. Keep the required model in the project folder.

## Installation

1. Clone or download the project and open PowerShell in its root folder.
2. If a working `.venv` already exists, keep it. Otherwise create one:

   ```powershell
   py -m venv .venv
   ```

3. Install the project requirements with that environment's interpreter:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. Confirm that `.venv\Scripts\python.exe`, `main_v3.py`, and `hand_landmarker.task` are present. Allow desktop applications to access the webcam in Windows camera privacy settings.

Use a Python version supported by all required packages. If installation reports that no compatible distribution exists, use a compatible Python installation to create the environment rather than renaming or copying an environment from another computer.

## Launch and desktop shortcut

Double-click **Start_Gesture_Control.cmd**. The launcher runs the existing `.venv\Scripts\python.exe` and sets its working directory to the project folder, so it can be started from any directory. It checks for the interpreter, entry point, and model, and keeps launch errors visible in the console.

To create a desktop shortcut:

1. Right-click `Start_Gesture_Control.cmd` and choose **Show more options > Send to > Desktop (create shortcut)**, or **Send to > Desktop (create shortcut)** where available.
2. Rename the shortcut **Chethan Gesture Control**.
3. In shortcut Properties, confirm that **Target** is the full, quoted path to `Start_Gesture_Control.cmd`. **Start in** is optional because the launcher sets its own working directory.

Keep the project files together. After moving the project, update the shortcut target; a virtual environment may need recreation after relocation.

For a manual launch, run this from the project root:

```powershell
.\.venv\Scripts\python.exe .\main_v3.py
```

Launching starts webcam tracking and real mouse control. Keep one hand clearly visible; the current loop uses the first detected hand.

## Gesture guide

| Gesture | Behavior |
| --- | --- |
| Open palm with all fingers extended and thumb out | Move the cursor; if dragging, release once before resuming movement |
| Thumb and index finger pinched, with a stable hand | Confirm one left click; separate the thumb from both index and middle fingers before another click |
| Thumb and middle finger pinched, with a stable hand | Confirm one right click; separate the thumb from both index and middle fingers before another click |
| Index and middle fingers raised, ring and pinky lowered | Scroll up or down by moving the hand vertically |
| Closed fist, with all four fingers curled | Press and hold the left mouse button once; move the fist to drag |
| Open palm during dragging | Release the left mouse button once |
| Hand leaves the camera view | Release an active drag and reset tracking/movement references |

While dragging, pinch and scroll actions are suppressed. Drag movement is allowed for fist and idle classifications; an open palm drops the item. Holding a fist never repeatedly toggles the button. Movement is rebased on mode changes, so the first frame in a new movement mode establishes a reference.

After tracking loss or a safety suspension, visibly separate the thumb from both pinch fingers before attempting another click. Pinch confirmation accumulates over frames, so its duration depends on frame rate. Keep fingers distinct from a closed fist when clicking: fist recognition takes priority.

## Quit

Focus the camera window and press the **Q** key (lowercase `q`). Normal loop cleanup releases an active drag, closes the camera and application windows, and prints mean capture-read and inference times when samples are available. The launcher console closes on success and pauses on an application error.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Launcher reports a missing interpreter | Create `.venv` in the project root and install requirements using its interpreter. Activating another environment does not change the launcher's interpreter. |
| `ModuleNotFoundError` | Run the installation command above with `.venv\Scripts\python.exe`. |
| Missing model error | Restore `hand_landmarker.task` beside `main_v3.py`. Launch through the provided script or run manually from the project root. |
| Camera view is unavailable or frozen | Check the webcam connection, Windows desktop-app camera permissions, and whether another application is using the camera. The current application uses camera index `0`. |
| Click does not register | Keep the hand stable through confirmation, visibly separate both pinch pairs before retrying, allow the existing cooldown, and ensure dragging is not active. |
| Drag does not release | Show a fully open palm or remove the hand from view. Focus the camera window and press Q to exit normally. |
| Cursor is stationary or shows a safety pause | Use the open-palm pose outside dragging, improve lighting, and check the FPS display. The existing low-FPS safeguard suspends actions below its configured threshold after startup. |
| Pointer trembles or feels slow | Use steady lighting and a clear, consistent hand distance. Small movements are intentionally suppressed. Verify actual camera behavior before adjusting settings. |
| `FailSafeException` | PyAutoGUI's corner failsafe remains enabled. Move the pointer away from the corner and restart; do not disable the safeguard. |

## Configuration and verification

Current application settings are in `gesture_v3/config.py`. Root-level `config.py` belongs to the legacy implementation. The entry point is `main_v3.py`; tracking, gesture classification, cursor movement, and HUD code are under `gesture_v3/`.

Run focused mocked checks without opening the webcam or controlling the real mouse:

```powershell
.\.venv\Scripts\python.exe tests/test_controls.py
```

The checks cover confirmation, pinch release and cooldown, grab/drop, movement transitions, tremor suppression, hand loss, capture failure, low-FPS suspension, and exception cleanup. They do not establish real-camera recognition accuracy or performance.

For manual verification, check pointing and stopping, one click per held pinch, separation and repeat, sustained fist dragging, open-palm release, suppressed click/scroll while dragging, and hand-loss recovery. Review the console timing summaries after a user-started session to measure capture and inference on your hardware.
