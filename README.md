## Smart Railway Surveillance System

An AI-powered, desktop-based surveillance suite for railway safety: track trespassing detection, fall detection, and crowd density monitoring. The app provides a dark-only Tkinter UI and a lightweight FastAPI backend for event alerts.

## Features

- **Track Trespassing (segmentation + person detection)**: Segments tracks and flags people on the rail area.
- **Fall Detection (YOLO classifier/detector)**: Detects falls; alert with cooldown.
- **Crowd Density (YOLOv11n)**: Counts people per frame; overlays live count.
- **Alerts (FastAPI)**: Event-triggered GET requests from UI to backend; cooldown to avoid spam.

## Architecture

- UI/inference: `UI.py` (Tkinter, OpenCV, Ultralytics YOLO)
- Backend alerts: `api.py` (FastAPI endpoints)

### Models used (expected files)
- Track segmentation: `train_segmented.pt`
- Person detection: `yolo11n.pt`
- Fall detection: `fall_model.pt`
- Crowd counting: `yolo11n.pt`

### Demo Video Link 
- https://drive.google.com/drive/folders/1OFBQWhs9xsoZTGFOhjN9iP4FzsGngUt-?usp=drive_link

## Setup

1. Clone
```bash
git clone https://github.com/Awarahoo/Railway-Surveillance-using-Computer-Vision
cd Railway-Surveillance-using-Computer-Vision
```

2. Install dependencies (CPU default)
```bash
pip install -r requirements.txt
```
If you have CUDA, install matching Torch/Torchvision from PyTorch first, then install the rest.

3. Place model files
- `train_segmented.pt`
- `yolo11n.pt`
- `fall_model.pt`

## Run

1. Start backend (alerts)
```bash
python api.py
```

2. Start UI
```bash
python UI.py
```

## Using the App

- Select detection models: Trespassing Detection, Fall Detection, Crowd Density.
- Choose source: Select Video File or Start Realtime Detection.
- Adjust confidence sliders per module as needed.
- Watch overlays, counts, and the alert log. Popups appear on important events.

### Crowd Density
- Counts `person` detections each frame; shows overlay and a live number.


## Backend API (FastAPI)

- `GET /track_alert`
- `GET /fall_alert`

Endpoints print to the backend console and return a JSON confirmation. The UI triggers these only on events and respects cooldowns.

## Notes

- Cooldown is enforced in UI (default 5s unless changed in code).
- Video frames are resized to 640x480 for performance consistency.
- If a model file is missing, that module will show a friendly error and remain disabled until provided.

## Repo hygiene

- Requirements include Ultralytics, Torch, OpenCV, FastAPI, Uvicorn, Pillow, NumPy, etc.

## Troubleshooting

- If ttk style errors occur, ensure Tcl/Tk is available (Python’s standard install ships with it).
- For GPU acceleration, install the correct CUDA-enabled Torch build before `pip install -r requirements.txt`.
