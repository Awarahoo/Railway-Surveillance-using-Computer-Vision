## Directory Structure

```
Smart-Railway-Surveillance-System/
├── UI.py                           # Main entry point
├── components/                     # UI Components
│   ├── __init__.py
│   ├── alert_window.py            # Alert popup window
│   └── ui_components.py           # UI setup and styling
├── detection/                     # Detection modules
│   ├── __init__.py
│   ├── base_detector.py           # Base detector class
│   ├── trespassing_detector.py    # Trespassing detection logic
│   ├── fall_detector.py           # Fall detection logic
│   └── crowd_detector.py          # Crowd detection logic
├── core/                          # Core application logic
│   ├── __init__.py
│   └── app_controller.py          # Main application controller
└── api.py                         # FastAPI backend
```

## Module Descriptions

### 1. **UI.py** (Entry Point)
- Entry point that initializes the application
- Imports and starts the main application controller

### 2. **components/alert_window.py**
- Contains the `AlertWindow` class for popup alerts
- Handles alert display with auto-close functionality
- Separated from main UI logic for reusability

### 3. **components/ui_components.py**
- Contains the `UIComponents` class
- Handles all UI setup, theming, and component creation
- Methods for creating dashboard, alert system, and file dialogs
- Centralizes all UI styling and theme configuration

### 4. **detection/base_detector.py**
- Abstract base class `BaseDetector` for all detection modules
- Provides common functionality:
  - Alert cooldown management
  - HTTP alert sending
  - Abstract methods for frame processing
- Ensures consistent interface across all detectors

### 5. **detection/trespassing_detector.py**
- `TrespassingDetector` class extending `BaseDetector`
- Handles railway track segmentation and person detection
- Manages track mask overlay and person counting
- Sends alerts when people are detected on tracks

### 6. **detection/fall_detector.py**
- `FallDetector` class extending `BaseDetector`
- Processes fall detection using YOLO model
- Provides both visual-only and alert-only processing modes
- Handles fall/no-fall classification and visualization

### 7. **detection/crowd_detector.py**
- `CrowdDetector` class extending `BaseDetector`
- Counts people in frames for crowd density monitoring
- Can use shared person count from trespassing detection
- Provides live person count updates

### 8. **core/app_controller.py**
- Main `SecuritySystemApp` class
- Orchestrates all components and detectors
- Handles video processing loop with frame isolation
- Manages model initialization and UI coordination
- Implements the critical frame processing fix from memory


## Usage


```bash
# Start the backend
python api.py

# Start the UI (now modular)
python UI.py
```

## Benefits of Modularization

1. **Easier Testing**: Each module can be tested independently
2. **Better Debugging**: Issues can be isolated to specific modules
3. **Code Reuse**: Components can be reused across projects
4. **Team Development**: Multiple developers can work on different modules
5. **Maintenance**: Changes to one module don't affect others
6. **Documentation**: Each module has clear responsibilities
7. **Performance**: No performance impact, same functionality
