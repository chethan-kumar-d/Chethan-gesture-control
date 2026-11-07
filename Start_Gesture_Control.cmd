@echo off
setlocal
title Chethan Gesture Control
pushd "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not open the Chethan Gesture Control project folder.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Missing .venv\Scripts\python.exe in the project folder.
    goto :launch_error
)
if not exist "main_v3.py" (
    echo ERROR: Missing main_v3.py in the project folder.
    goto :launch_error
)
if not exist "hand_landmarker.task" (
    echo ERROR: Missing hand_landmarker.task in the project folder.
    goto :launch_error
)
"%~dp0.venv\Scripts\python.exe" "%~dp0main_v3.py"
set "launch_exit=%errorlevel%"
if not "%launch_exit%"=="0" (
    echo Chethan Gesture Control exited with error code %launch_exit%.
    pause
)
popd
exit /b %launch_exit%

:launch_error
pause
popd
exit /b 1
