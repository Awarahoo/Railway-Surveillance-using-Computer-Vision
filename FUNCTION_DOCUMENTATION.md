# Function-by-Function Documentation

Complete explanation of every function in the Smart Railway Surveillance System.

---

## 1. UI.py (Entry Point)

### Main Execution Block
```python
if __name__ == "__main__":
```
- **Purpose**: Entry point of the application
- **What it does**: Creates Tkinter root window, initializes SecuritySystemApp, and starts the main event loop
- **Parameters**: None
- **Returns**: None

---

## 2. components/alert_window.py

### Class: AlertWindow

#### `__init__(self, parent, message)`
- **Purpose**: Constructor for alert popup window
- **What it does**: 
  - Creates a top-level window that appears above all others
  - Sets window size to 300x100 pixels
  - Configures black background with red text
  - Creates alert label with the message
  - Adds an "OK" button to close manually
  - Sets auto-close timer for 5 seconds
- **Parameters**:
  - `parent`: Parent Tkinter window
  - `message`: Alert message text to display
- **Returns**: None
- **Key Features**:
  - Always on top (`-topmost` attribute)
  - Word wrapping at 260 pixels
  - Auto-destroys after 5 seconds

---

## 3. components/ui_components.py

### Class: UIComponents

#### `__init__(self, root)`
- **Purpose**: Constructor for UI components manager
- **What it does**: Stores root window reference and calls setup_theme()
- **Parameters**: 
  - `root`: Main Tkinter window
- **Returns**: None

#### `setup_theme(self)`
- **Purpose**: Configure dark theme for entire application
- **What it does**:
  - Defines color palette (BG, CARD, FG, ACCENT colors)
  - Applies 'clam' ttk theme
  - Configures styles for:
    - Notebooks and tabs
    - Frames and label frames
    - Labels (normal and alert styles)
    - Buttons with hover effects
    - Sliders
- **Parameters**: None
- **Returns**: None
- **Color Scheme**:
  - Background: `#0f0f10` (near black)
  - Card: `#17171a` (dark gray)
  - Foreground: `#e4e4e7` (light gray)
  - Accent: `#3b82f6` (blue)
  - Accent Hover: `#2563eb` (darker blue)

#### `create_unified_dashboard(self, parent, callbacks)`
- **Purpose**: Create main dashboard with video feed and controls
- **What it does**:
  - Creates left panel with video display label
  - Creates right control panel (300px wide) with:
    - Model selection checkboxes (Trespassing, Fall, Crowd)
    - Video file selection button
    - Start/Stop detection buttons
    - People count display
  - Initializes confidence threshold variables
- **Parameters**:
  - `parent`: Parent frame to attach dashboard to
  - `callbacks`: Dictionary with functions:
    - `select_video`: Function to select video file
    - `start_detection`: Function to start detection (takes mode parameter)
    - `stop_detection`: Function to stop detection
- **Returns**: Dictionary containing:
  - `unified_video_label`: Label widget for video display
  - `model_vars`: Dictionary of BooleanVar for each model
  - `start_file_btn`: Start file detection button
  - `stop_btn`: Stop detection button
  - `confidence_var`: DoubleVar for trespassing confidence (default 0.5)
  - `fall_confidence_var`: DoubleVar for fall confidence (default 0.5)
  - `crowd_confidence_var`: DoubleVar for crowd confidence (default 0.4)
  - `crowd_count_var`: IntVar for crowd count
  - `crowd_count_label`: Label showing current count

#### `create_alert_system(self, parent)`
- **Purpose**: Create alert log and current alert display
- **What it does**:
  - Creates scrollable text widget (8 lines high, 150px frame)
  - Configures 'important' tag for red, bold text
  - Adds scrollbar
  - Creates current alert label below
  - Sets text widget to read-only (DISABLED state)
- **Parameters**:
  - `parent`: Parent frame to attach alert system to
- **Returns**: Tuple of:
  - `alert_text`: Text widget for alert log
  - `current_alert`: Label for current alert message

#### `select_video_file(self)`
- **Purpose**: Open file dialog to select video
- **What it does**: Shows file chooser dialog filtered for .mp4, .avi, .mov files
- **Parameters**: None
- **Returns**: Selected file path string, or None if cancelled

---

## 4. detection/base_detector.py

### Class: BaseDetector (Abstract Base Class)

#### `__init__(self, model, alert_cooldown=5)`
- **Purpose**: Constructor for base detector
- **What it does**: 
  - Stores YOLO model reference
  - Sets alert cooldown period (default 5 seconds)
  - Initializes last alert time to 0
  - Sets alert callback to None
- **Parameters**:
  - `model`: YOLO model object
  - `alert_cooldown`: Seconds between alerts (default 5)
- **Returns**: None

#### `set_alert_callback(self, callback)`
- **Purpose**: Register callback function for alerts
- **What it does**: Stores reference to function that will be called when alert is triggered
- **Parameters**:
  - `callback`: Function to call with (message, is_important) parameters
- **Returns**: None

#### `can_send_alert(self)`
- **Purpose**: Check if cooldown period has elapsed
- **What it does**: 
  - Gets current time
  - Compares with last alert time
  - Returns True if more than cooldown seconds have passed
- **Parameters**: None
- **Returns**: Boolean - True if alert can be sent, False otherwise

#### `send_alert(self, message, endpoint=None, is_important=True)`
- **Purpose**: Send alert with cooldown protection
- **What it does**:
  1. Checks if cooldown allows alert
  2. Calls alert callback if set
  3. If endpoint provided, sends HTTP GET request to backend
  4. Updates last alert time
  5. Handles request exceptions
- **Parameters**:
  - `message`: Alert message string
  - `endpoint`: Optional API endpoint (e.g., "track_alert")
  - `is_important`: Boolean flag for alert importance
- **Returns**: Boolean - True if alert sent successfully, False otherwise
- **Backend URL**: `http://127.0.0.1:8000/{endpoint}`

#### `process_frame(self, frame, confidence_threshold=0.5)` [Abstract]
- **Purpose**: Process frame and return display frame with visual overlays
- **What it does**: Must be implemented by subclasses
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Detection confidence threshold (0.0-1.0)
- **Returns**: Processed frame with visual overlays

#### `process_alerts_only(self, frame, confidence_threshold=0.5)` [Abstract]
- **Purpose**: Process frame for alerts without modifying visuals
- **What it does**: Must be implemented by subclasses
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Detection confidence threshold (0.0-1.0)
- **Returns**: None (only triggers alerts)

---

## 5. detection/trespassing_detector.py

### Class: TrespassingDetector (extends BaseDetector)

#### `__init__(self, track_model, person_model, alert_cooldown=5)`
- **Purpose**: Constructor for trespassing detector
- **What it does**:
  - Calls parent constructor with track_model
  - Stores person detection model
  - Initializes person count to 0
- **Parameters**:
  - `track_model`: YOLO model for track segmentation
  - `person_model`: YOLO model for person detection
  - `alert_cooldown`: Seconds between alerts (default 5)
- **Returns**: None

#### `process_frame(self, frame, confidence_threshold=0.5)`
- **Purpose**: Detect people on railway tracks with visual overlays
- **What it does**:
  1. Creates copy of frame for display
  2. Runs track segmentation model to get track mask
  3. If masks exist:
     - Combines all masks into single binary mask
     - Resizes to frame dimensions
     - Creates red colored overlay (BGR: 0,0,255)
     - Blends with frame at 50% opacity
  4. Runs person detection model
  5. For each detected person:
     - Draws green circle at center point
     - Adds "Person" label
     - Checks if center point is on track mask
     - Increments person count
  6. Updates shared person count
  7. If person on track detected, sends alert
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Detection confidence (not used, models use default)
- **Returns**: Display frame with track overlay and person markers
- **Alert**: "🚨 Person detected on railway track!" → endpoint: "track_alert"

#### `process_alerts_only(self, frame, confidence_threshold=0.5)`
- **Purpose**: Detect trespassing for alerts only (no visuals)
- **What it does**:
  - Same detection logic as process_frame()
  - Skips all visual overlay operations
  - Only sends alert if person detected on track
  - Updates person count for crowd detection
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Detection confidence
- **Returns**: None
- **Why it exists**: Prevents visual modifications from interfering with other detectors

#### `get_person_count(self)`
- **Purpose**: Get last detected person count
- **What it does**: Returns stored person count value
- **Parameters**: None
- **Returns**: Integer - number of people detected in last frame
- **Used by**: Crowd detector to avoid duplicate person detection

---

## 6. detection/fall_detector.py

### Class: FallDetector (extends BaseDetector)

#### `__init__(self, fall_model, alert_cooldown=5)`
- **Purpose**: Constructor for fall detector
- **What it does**: Calls parent constructor with fall detection model
- **Parameters**:
  - `fall_model`: YOLO model trained for fall detection
  - `alert_cooldown`: Seconds between alerts (default 5)
- **Returns**: None

#### `process_frame(self, frame, confidence_threshold=0.5)`
- **Purpose**: Detect falls with visual overlays
- **What it does**:
  1. Returns original frame if model is None
  2. Creates copy of frame for display
  3. Runs YOLO model with streaming mode
  4. For each detection:
     - Extracts bounding box coordinates
     - Gets confidence score and class label
     - If label is "fall-detected":
       - Draws red rectangle (BGR: 0,0,255) with 3px thickness
       - Adds "FALL {confidence}" text in red
       - Sends alert via send_alert()
     - If label is "nofall":
       - Draws green rectangle (BGR: 0,255,0) with 2px thickness
       - Adds "No Fall {confidence}" text in green
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Minimum confidence for detection (0.0-1.0)
- **Returns**: Display frame with fall detection overlays
- **Alert**: "🚨 Fall detected!" → endpoint: "fall_alert"

#### `process_alerts_only(self, frame, confidence_threshold=0.5)`
- **Purpose**: Detect falls for alerts only (no visuals)
- **What it does**:
  - Runs YOLO model on frame
  - Only checks for "fall-detected" label
  - Sends alert if fall detected
  - No visual modifications
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Minimum confidence for detection
- **Returns**: None

#### `process_visual_only(self, frame, confidence_threshold=0.5)`
- **Purpose**: Draw fall detection overlays without sending alerts
- **What it does**:
  - Same as process_frame() but without send_alert() call
  - Only draws visual overlays
  - Used in main loop to separate alert logic from visuals
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Minimum confidence for detection
- **Returns**: Display frame with fall detection overlays
- **Why it exists**: Allows alerts to be processed on clean frame while visuals are applied to display frame

---

## 7. detection/crowd_detector.py

### Class: CrowdDetector (extends BaseDetector)

#### `__init__(self, crowd_model, alert_cooldown=5)`
- **Purpose**: Constructor for crowd density detector
- **What it does**:
  - Calls parent constructor with crowd model
  - Initializes person count to 0
- **Parameters**:
  - `crowd_model`: YOLO model for person detection
  - `alert_cooldown`: Seconds between alerts (default 5)
- **Returns**: None

#### `process_frame(self, frame, confidence_threshold=0.4, shared_person_count=None)`
- **Purpose**: Count people and display crowd density
- **What it does**:
  1. Creates copy of frame for display
  2. If shared_person_count provided (trespassing detection active):
     - Uses that count instead of detecting again
     - Still draws bounding boxes for visualization
  3. Otherwise:
     - Runs YOLO model to detect people
     - Counts each person detection
     - Draws cyan bounding boxes (BGR: 0,255,255)
  4. Updates internal person count
  5. Draws "People: {count}" text in yellow at top-left
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Minimum confidence (default 0.4, lower than others)
  - `shared_person_count`: Optional count from trespassing detector
- **Returns**: Display frame with person count overlay
- **Why lower threshold**: Crowd detection prioritizes counting all people over precision

#### `process_alerts_only(self, frame, confidence_threshold=0.4)`
- **Purpose**: Placeholder for crowd-based alerts
- **What it does**: Currently does nothing (pass statement)
- **Parameters**:
  - `frame`: OpenCV frame (numpy array)
  - `confidence_threshold`: Minimum confidence
- **Returns**: None
- **Future use**: Could implement alerts for overcrowding thresholds

#### `get_person_count(self)`
- **Purpose**: Get current person count
- **What it does**: Returns stored person count value
- **Parameters**: None
- **Returns**: Integer - number of people in last processed frame
- **Used by**: Main app to update UI display

---

## 8. core/app_controller.py

### Class: SecuritySystemApp

#### `__init__(self, root)`
- **Purpose**: Main application constructor
- **What it does**:
  1. Stores root window reference
  2. Sets window title and size (1400x900)
  3. Initializes video path variables
  4. Initializes video capture objects (cap, video_capture)
  5. Sets running flag to True
  6. Creates modules dictionary with active states
  7. Calls initialize_models()
  8. Creates UIComponents instance
  9. Calls setup_ui()
  10. Starts update_video() loop
- **Parameters**:
  - `root`: Tkinter root window
- **Returns**: None
- **Modules**: trespassing_detection, fall_detection, crowd_detection

#### `initialize_models(self)`
- **Purpose**: Load YOLO models and create detector instances
- **What it does**:
  1. Loads YOLO models:
     - `train_segmented.pt` for track segmentation
     - `yolo11n.pt` for person detection (used twice)
     - `fall_model.pt` for fall detection
  2. Creates detector instances:
     - TrespassingDetector with track and person models
     - FallDetector with fall model
     - CrowdDetector with crowd model
  3. Sets alert callbacks to self.add_alert for all detectors
  4. Shows error dialog and exits if models fail to load
- **Parameters**: None
- **Returns**: None
- **Error Handling**: Catches exceptions, shows messagebox, destroys window

#### `setup_ui(self)`
- **Purpose**: Build user interface
- **What it does**:
  1. Creates main frame with dark background
  2. Defines callback dictionary for UI events
  3. Calls ui_components.create_unified_dashboard()
  4. Stores all returned UI component references
  5. Calls ui_components.create_alert_system()
  6. Stores alert text widget and current alert label
- **Parameters**: None
- **Returns**: None
- **Callbacks**:
  - `select_video`: self.select_unified_video
  - `start_detection`: self.start_unified_detection
  - `stop_detection`: self.stop_unified_detection

#### `select_unified_video(self)`
- **Purpose**: Handle video file selection
- **What it does**:
  1. Calls ui_components.select_video_file()
  2. If file selected:
     - Stores path in self.unified_video_path
     - Adds alert with filename
     - Enables start file button
- **Parameters**: None
- **Returns**: None

#### `start_unified_detection(self, mode)`
- **Purpose**: Start detection with selected models
- **What it does**:
  1. Gets list of selected models from checkboxes
  2. Validates at least one model selected
  3. If file mode, validates video file selected
  4. Opens video capture:
     - Realtime: Opens webcam (device 0) at 30 FPS
     - File: Opens video file
  5. Activates selected modules in self.modules dict
  6. Adds alert with started models and mode
  7. Updates button states (enable stop, disable start)
- **Parameters**:
  - `mode`: String - either 'file' or 'realtime'
- **Returns**: None
- **Validations**: Shows warning if no models selected or no file for file mode

#### `stop_unified_detection(self)`
- **Purpose**: Stop all active detection
- **What it does**:
  1. Sets all modules to inactive
  2. Releases video_capture if active
  3. Releases webcam capture if active
  4. Adds "Detection stopped" alert
  5. Updates button states (disable stop, enable start if file selected)
- **Parameters**: None
- **Returns**: None

#### `add_alert(self, message, is_important=False)`
- **Purpose**: Add message to alert log and display
- **What it does**:
  1. Enables alert text widget (normally read-only)
  2. If important:
     - Inserts timestamp with 'important' tag (red, bold)
     - Inserts message with 'important' tag
     - Calls show_alert_popup()
  3. If not important:
     - Inserts timestamp and message normally
  4. Scrolls to end of log
  5. Disables alert text widget
  6. Updates current alert label
  7. Sets label color/font based on importance
- **Parameters**:
  - `message`: Alert message string
  - `is_important`: Boolean - triggers popup if True
- **Returns**: None
- **Format**: `[HH:MM:SS] message`

#### `show_alert_popup(self, message)`
- **Purpose**: Display popup alert window
- **What it does**: Creates AlertWindow instance with message
- **Parameters**:
  - `message`: Alert message string
- **Returns**: None

#### `update_video(self)`
- **Purpose**: Main video processing loop (runs every 10ms)
- **What it does**:
  1. Checks if application is running
  2. Gets list of active models
  3. If models active:
     - Reads frame from webcam or video file
     - If video file ends, calls stop_unified_detection()
  4. If frame available:
     - Resizes to 640x480
     - Creates original_frame copy (for alerts)
     - Creates processed_frame copy (for visuals)
  5. For each active detection:
     - **Trespassing**: 
       - Processes alerts on original_frame copy
       - Applies visuals to processed_frame
     - **Fall**: 
       - Processes alerts on original_frame copy
       - Applies visuals to processed_frame (visual_only method)
     - **Crowd**: 
       - Processes alerts on original_frame copy
       - Applies visuals to processed_frame
       - Uses shared count from trespassing if active
       - Updates crowd count display
  6. Converts frame from BGR to RGB
  7. Converts to PIL Image
  8. Creates PhotoImage for Tkinter
  9. Updates video label
  10. Schedules next call after 10ms
- **Parameters**: None
- **Returns**: None
- **Critical Design**: Each detector processes original frame for alerts, preventing visual interference
- **Frame Rate**: ~100 FPS loop (10ms), actual FPS depends on processing time

#### `exit_app(self)`
- **Purpose**: Clean up and close application
- **What it does**:
  1. Sets running flag to False
  2. Releases webcam if active
  3. Releases video file if active
  4. Destroys root window
- **Parameters**: None
- **Returns**: None

---

## Key Design Patterns

### 1. **Frame Isolation Pattern**
- Alerts processed on `original_frame.copy()`
- Visuals applied to `processed_frame`
- Prevents visual modifications from affecting detection accuracy

### 2. **Shared State Pattern**
- Trespassing detector shares person count with crowd detector
- Avoids duplicate person detection when both active

### 3. **Callback Pattern**
- Detectors use callbacks to communicate with main app
- Decouples detection logic from UI logic

### 4. **Cooldown Pattern**
- All detectors enforce alert cooldowns
- Prevents alert spam

### 5. **Abstract Base Class Pattern**
- BaseDetector defines interface
- All detectors implement consistent methods
- Enables polymorphic processing in main loop

---

## Data Flow

1. **Video Frame** → Read from webcam/file
2. **Original Frame** → Copied for alert processing
3. **Processed Frame** → Copied for visual overlays
4. **Detection** → Each detector processes independently
5. **Alerts** → Sent to backend API and UI
6. **Visuals** → Combined sequentially on processed frame
7. **Display** → Converted to PhotoImage and shown in UI

---

## Performance Considerations

- **Frame Resizing**: All frames resized to 640x480 for consistency
- **Model Inference**: Each model runs once per frame
- **Shared Detection**: Crowd uses trespassing's person count when possible
- **Update Rate**: 10ms loop (~100 FPS theoretical, actual depends on processing)
- **Memory**: Frame copies created for isolation, garbage collected each loop
