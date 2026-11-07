# Third-party notices and original-source attribution

## Original application source

Chethan Gesture Control is customized and maintained by **Chethan Kumar D**. It derives from an existing project supplied in a folder named `Control_pc_using_Hand-Gesture-main`.

The supplied source and documentation identified the original project as:

- **Hand Gesture Control System V1** (`README.md`), describing Version 2 functionality and ending with "Created for Portfolio Demonstration".
- **Project J.A.R.V.I.S (Gesture Interface V3)** (`README_V3.md` and `main_v3.py`), with the app name **J.A.R.V.I.S Gesture Interface** and the documentation closing text "Senior HCI Engineering Project".

The underlying tracking, gesture classification, cursor physics, application loop, and HUD implementation predate this rebrand. Chethan Kumar D is credited for customization and maintenance, not original authorship of all underlying code.

No original author identity, upstream repository URL, or standalone license file was present in the supplied project files when rebranded. These details have not been inferred. This notice does not establish a license or replace upstream terms. Preserve any original copyright and license notices supplied with the source.

## Dependencies and model

OpenCV (`opencv-python`), MediaPipe, NumPy, and PyAutoGUI remain subject to their respective copyright notices and license terms distributed with their packages. Those notices are unchanged.

The existing documentation referenced this MediaPipe Hand Landmarker model download:

https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

The `hand_landmarker.task` model is a third-party asset subject to its applicable terms.

The smoothing implementation retains its existing One Euro Filter source reference in `gesture_v3/perception/smoothing.py`:

http://cristal.univ-lille.fr/~casiez/1euro/
