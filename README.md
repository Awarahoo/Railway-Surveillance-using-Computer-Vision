## Smart Railway Surveillance System

An AI-powered, desktop-based surveillance suite for railway safety: weapon detection, track trespassing, fall detection, crowd density, fire/smoke detection, and dustbin health monitoring. The app provides a dark-only Tkinter UI and a lightweight FastAPI backend for event alerts.

## Features

- **Weapon Detection (custom YOLO)**: Detects weapons and sends alerts.
- **Track Trespassing (segmentation + person detection)**: Segments tracks and flags people on the rail area.
- **Fall Detection (YOLO classifier/detector)**: Detects falls; alert with cooldown.
- **Crowd Density (YOLOv11n)**: Counts people per frame; overlays live count.
- **Fire & Smoke Detection (fire.pt)**: Detects labels "Fire" and "Smoke" with distinct overlays and alerts.
- **Dustbin Health (dustbin.pt)**: Classifies trash can state with labels: `['Broken trash can','Close_empty','Close_full','Healthy trash can','Open_empty','Open_full','Trash flow','closed','empty','full']` and shows live per-label counts.
- **Alerts (FastAPI)**: Event-triggered GET requests from UI to backend; cooldown to avoid spam.

## Architecture

- UI/inference: `UI.py` (Tkinter, OpenCV, Ultralytics YOLO)
- Backend alerts: `api.py` (FastAPI endpoints)

### Models used (expected files)
- Weapons: `runs/detect/train/weights/best.pt`
- Track segmentation: `runs/segment/track_segmentation_1/weights/best.pt`
- Person detection: `yolo11n.pt` (also used earlier as `yolov8n.pt`)
- Fall detection (optional): `fall_model.pt`
- Crowd counting: `yolo11n.pt`
- Fire/Smoke: `fire.pt` (labels: "Fire", "Smoke")
- Dustbin health: `dustbin.pt`

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
- `runs/detect/train/weights/best.pt`
- `runs/segment/track_segmentation_1/weights/best.pt`
- `yolo11n.pt`
- `fall_model.pt`
- `fire.pt`
- `dustbin.pt`

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

- Pick a tab: Weapon, Trespassing, Fall, Crowd Density, Fire Detection, Dustbin Health.
- Choose source: Select Video File or Start Realtime Detection.
- Adjust confidence sliders per module as needed.
- Watch overlays, counts, and the alert log. Popups appear on important events.

### Crowd Density
- Counts `person` detections each frame; shows overlay and a live number.

### Fire & Smoke
- Detects labels "Fire" (orange/red box) and "Smoke" (gray box).
- Sends `GET /fire_alert` with cooldown.

### Dustbin Health
- Shows class overlay on each bin and updates a side panel with per-label counts for:
  `Broken trash can, Close_empty, Close_full, Healthy trash can, Open_empty, Open_full, Trash flow, closed, empty, full`.

## Backend API (FastAPI)

- `GET /weapon_alert`
- `GET /track_alert`
- `GET /fall_alert`
- `GET /fire_alert`

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
