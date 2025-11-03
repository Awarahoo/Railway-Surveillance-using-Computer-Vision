# Railway Surveillance System

An AI-powered surveillance system for enhancing safety and security at railway stations.
This project integrates weapon detection, trespassing detection, fall/slip detection, crowd detection and a unified system with a Tkinter UI and Flask API alerts.

# 🔍 Features

### 🔫 Weapon Detection (YOLOv8)

- #### Detects weapons like knives and guns in live video.

- #### Triggers alerts via Flask API.

### 🚷 Trespassing Detection (YOLOv8 Segmentation)

- #### Detects unauthorized entry into railway tracks.

- #### Sends alerts in real-time.

###  Crowd Detection (YOLOv11)

- #### Detects number of people in the frame

- #### Alert when number of people exceeds some limit

### Fall/Slip Detection (YOLOv11 classification)

- ### Alert when someone falls down


### 📢 Alert System

- #### Flask API provides real-time alerting.


### 🖥️ User Interface (Tkinter)

- #### Displays real-time camera feed.

- #### Shows bounding boxes, detected labels, and alerts.

- #### Allows runtime upload of a target person’s image.

# ⚙️ Installation

### 1️⃣ Clone the repo:
```bash
git clone https://github.com/Awarahoo/Railway-Surveillance-using-Computer-Vision
cd Smart-Railway-Surveillance-System
```
### 2️⃣ Install dependencies:
```bash
pip install -r requirements.txt
```
### 3️⃣ Run the Flask API:
```bash
python api.py
```
### 4️⃣ Run the Tkinter UI:
```bash
python UI.py
```
