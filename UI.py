import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import time
import os
import numpy as np
import requests
from ultralytics import YOLO

class AlertWindow(tk.Toplevel):
    def __init__(self, parent, message):
        super().__init__(parent)
        self.title("ALERT!")
        self.geometry("300x100")
        self.attributes('-topmost', True)
        self.configure(bg='black')
        
        alert_label = tk.Label(
            self, 
            text=message, 
            font=('Helvetica', 16, 'bold'), 
            fg='red', 
            bg='black',
            wraplength=260
        )
        alert_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        close_btn = tk.Button(
            self, 
            text="OK", 
            command=self.destroy,
            font=('Helvetica', 8),
            bg='red',
            fg='white'
        )
        close_btn.pack(pady=10)
        self.after(5000, self.destroy)

class SecuritySystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Railway Surveillance System")
        self.root.geometry("1400x900")
        
        # Initialize all attributes
        self.video_file_path = None
        self.weapon_alert_sent = False
        self.trespassing_alert_sent = False
        self.weapon_alert_time = 0
        self.trespassing_alert_time = 0
        self.fall_alert_time = 0
        
        # Individual cooldown periods for each alert type (in seconds)
        self.weapon_alert_cooldown = 5
        self.trespassing_alert_cooldown = 5
        self.fall_alert_cooldown = 5
        self.fire_alert_cooldown = 5
        
        # Shared person count between trespassing and crowd detection
        self.last_person_count = 0
        
        self.cap = None
        self.video_capture = None
        self.current_frame = None
        self.weapon_detection_mode = None
        self.trespassing_detection_mode = None
        self.fall_detection_mode = None
        self.crowd_detection_mode = None
        self.fire_detection_mode = None
        self.dustbin_detection_mode = None
        self.fire_alert_time = 0
        
        # Variables
        self.running = True
        self.active_module = None
        self.modules = {
            "weapon_detection": {"active": False, "tab": None},
            "trespassing_detection": {"active": False, "tab": None},
            "fall_detection": {"active": False, "tab": None},
            "crowd_detection": {"active": False, "tab": None},
            "fire_detection": {"active": False, "tab": None},
            "dustbin_detection": {"active": False, "tab": None}
        }
        
        # Initialize models
        self.initialize_models()
        
        # Setup UI
        self.setup_ui()
        
        # Start the video update thread
        self.update_video()
    
    def initialize_models(self):
        """Initialize all the required models"""
        try:
            self.weapon_model = None  # Weapon detection disabled
            self.track_model = YOLO("train_segmented.pt")
            self.person_model = YOLO("yolo11n.pt")
            self.crowd_model = YOLO("yolo11n.pt")
            # Initialize fall detection model
            try:
                fall_model_path = "fall_model.pt"
                if os.path.exists(fall_model_path):
                    self.fall_model = YOLO(fall_model_path)
                else:
                    print(f"Warning: Fall detection model not found at {fall_model_path}. Fall detection will be disabled.")
                    self.fall_model = None
            except Exception as e:
                print(f"Warning: Failed to initialize fall detection model: {str(e)}. Fall detection will be disabled.")
                self.fall_model = None
            # Fire and dustbin detection disabled
            self.fire_model = None
            self.dustbin_model = None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize models: {str(e)}")
            self.root.destroy()
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Dark-only theme configuration
        BG = '#0f0f10'
        CARD = '#17171a'
        FG = '#e4e4e7'
        ACCENT = '#3b82f6'
        ACCENT_HOVER = '#2563eb'

        self.root.configure(bg=BG)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Notebook and tabs
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=(16, 8),
                        background=CARD, foreground=FG)
        style.map('TNotebook.Tab', background=[('selected', ACCENT)], foreground=[('selected', 'white')])

        # Containers and labels
        style.configure('TFrame', background=BG)
        style.configure('TLabelframe', background=BG, foreground=FG, font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background=BG, foreground=FG)
        style.configure('TLabel', background=BG, foreground=FG, font=('Segoe UI', 10))
        style.configure('Alert.TLabel', background=CARD, foreground='#ff4545', font=('Segoe UI', 13, 'bold'))

        # Buttons and sliders
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=(12, 8))
        style.map('TButton', foreground=[('!disabled', 'white')], background=[('!disabled', ACCENT), ('active', ACCENT_HOVER)])
        style.configure('Horizontal.TScale', background=BG)

        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Unified Dashboard (no tabs)
        self.setup_unified_dashboard(main_frame)
        
        alert_frame = ttk.LabelFrame(main_frame, text="System Alerts", height=150, style='TLabelframe')
        alert_frame.pack(fill=tk.X, pady=(5,0))
        alert_frame.pack_propagate(False)
        
        self.alert_text = tk.Text(
            alert_frame, 
            height=8, 
            state=tk.DISABLED,
            font=('Consolas', 10),
            bg=CARD,
            fg=FG,
            insertbackground=FG,
            selectbackground=ACCENT,
            relief=tk.FLAT
        )
        self.alert_text.tag_config('important', foreground='#ff4545', font=('Consolas', 10, 'bold'))
        
        scrollbar = ttk.Scrollbar(alert_frame, command=self.alert_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_text.config(yscrollcommand=scrollbar.set)
        self.alert_text.pack(fill=tk.BOTH, expand=True)
        
        self.current_alert = ttk.Label(main_frame, text="", style='Alert.TLabel', wraplength=1200)
        self.current_alert.pack(fill=tk.X, pady=(5,0))
    
    def setup_unified_dashboard(self, parent):
        """Setup unified dashboard with multi-model selection"""
        dashboard = ttk.Frame(parent)
        dashboard.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        
        # Video display
        video_frame = ttk.LabelFrame(dashboard, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.unified_video_label = ttk.Label(video_frame)
        self.unified_video_label.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.Frame(dashboard, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Model selection
        model_frame = ttk.LabelFrame(control_frame, text="Select Models")
        model_frame.pack(fill=tk.X, pady=5)
        
        self.model_vars = {
            'trespassing_detection': tk.BooleanVar(value=False),
            'fall_detection': tk.BooleanVar(value=False),
            'crowd_detection': tk.BooleanVar(value=False),
        }
        
        ttk.Checkbutton(model_frame, text="Trespassing Detection", 
                       variable=self.model_vars['trespassing_detection']).pack(anchor='w', padx=8, pady=2)
        ttk.Checkbutton(model_frame, text="Fall Detection", 
                       variable=self.model_vars['fall_detection']).pack(anchor='w', padx=8, pady=2)
        ttk.Checkbutton(model_frame, text="Crowd Density", 
                       variable=self.model_vars['crowd_detection']).pack(anchor='w', padx=8, pady=2)
        
        # Controls
        ctrl_frame = ttk.LabelFrame(control_frame, text="Controls")
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(ctrl_frame, text="Select Video File", 
                  command=self.select_unified_video).pack(fill=tk.X, pady=5)
        
        self.start_file_btn = ttk.Button(ctrl_frame, text="Start File Detection", 
                                         command=lambda: self.start_unified_detection('file'),
                                         state=tk.DISABLED)
        self.start_file_btn.pack(fill=tk.X, pady=5)
        
        ttk.Button(ctrl_frame, text="Start Realtime Detection", 
                  command=lambda: self.start_unified_detection('realtime')).pack(fill=tk.X, pady=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop Detection", 
                                   command=self.stop_unified_detection,
                                   state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        # Confidence sliders and counters
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.fall_confidence_var = tk.DoubleVar(value=0.5)
        self.crowd_confidence_var = tk.DoubleVar(value=0.4)
        self.crowd_count_var = tk.IntVar(value=0)
        
        # Add crowd counter display
        count_frame = ttk.LabelFrame(control_frame, text="People Count")
        count_frame.pack(fill=tk.X, pady=5)
        self.crowd_count_label = ttk.Label(count_frame, text="Current: 0")
        self.crowd_count_label.pack(fill=tk.X, padx=5, pady=5)
    
    def select_unified_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.unified_video_path = file_path
            self.add_alert(f"Video selected: {os.path.basename(file_path)}")
            self.start_file_btn.config(state=tk.NORMAL)
    
    def start_unified_detection(self, mode):
        selected = [k for k, v in self.model_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one model!")
            return
        
        if mode == 'file' and not hasattr(self, 'unified_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
        
        # Open capture
        if mode == 'realtime':
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        else:
            self.video_capture = cv2.VideoCapture(self.unified_video_path)
        
        # Activate selected models
        for k in self.modules.keys():
            self.modules[k]["active"] = (k in selected)
        
        self.add_alert(f"Started: {', '.join([s.replace('_', ' ').title() for s in selected])} ({mode})")
        self.stop_btn.config(state=tk.NORMAL)
        self.start_file_btn.config(state=tk.DISABLED)
    
    def stop_unified_detection(self):
        for k in self.modules.keys():
            self.modules[k]["active"] = False
        
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.add_alert("Detection stopped")
        self.stop_btn.config(state=tk.DISABLED)
        self.start_file_btn.config(state=tk.NORMAL if hasattr(self, 'unified_video_path') else tk.DISABLED)
    
    def setup_weapon_detection_tab(self):
        """Setup the weapon detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Weapon Detection")
        self.modules["weapon_detection"]["tab"] = tab
        
        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.weapon_video_label = ttk.Label(video_frame)
        self.weapon_video_label.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        weapon_ctrl_frame = ttk.LabelFrame(control_frame, text="Weapon Detection")
        weapon_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.select_weapon_file_btn = ttk.Button(weapon_ctrl_frame, text="Select Video File", 
                                              command=self.select_weapon_video_file)
        self.select_weapon_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_weapon_file_btn = ttk.Button(weapon_ctrl_frame, text="Start File Detection", 
                                             command=lambda: self.start_weapon_detection('file'),
                                             state=tk.DISABLED)
        self.start_weapon_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_weapon_realtime_btn = ttk.Button(weapon_ctrl_frame, text="Start Realtime Detection", 
                                                 command=lambda: self.start_weapon_detection('realtime'))
        self.start_weapon_realtime_btn.pack(fill=tk.X, pady=5)
        
        self.stop_weapon_btn = ttk.Button(weapon_ctrl_frame, text="Stop Detection", 
                                        command=self.stop_weapon_detection,
                                        state=tk.DISABLED)
        self.stop_weapon_btn.pack(fill=tk.X, pady=5)
        
        self.confidence_var = tk.DoubleVar(value=0.5)
        confidence_frame = ttk.LabelFrame(control_frame, text="Confidence Threshold")
        confidence_frame.pack(fill=tk.X, pady=5)
        
        self.confidence_slider = ttk.Scale(confidence_frame, from_=0.1, to=0.9, 
                                         variable=self.confidence_var,
                                         command=lambda v: self.confidence_var.set(round(float(v), 1)))
        self.confidence_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.confidence_label = ttk.Label(confidence_frame, text=f"Current: {self.confidence_var.get():.1f}")
        self.confidence_label.pack()
        
        self.confidence_var.trace_add("write", lambda *_: self.confidence_label.config(
            text=f"Current: {self.confidence_var.get():.1f}"))
    
    def setup_trespassing_detection_tab(self):
        """Setup the trespassing detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Trespassing Detection")
        self.modules["trespassing_detection"]["tab"] = tab
        
        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.trespassing_video_label = ttk.Label(video_frame)
        self.trespassing_video_label.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        trespass_ctrl_frame = ttk.LabelFrame(control_frame, text="Trespassing Detection")
        trespass_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.select_trespassing_file_btn = ttk.Button(trespass_ctrl_frame, text="Select Video File", 
                                                    command=self.select_trespassing_video_file)
        self.select_trespassing_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_trespassing_file_btn = ttk.Button(trespass_ctrl_frame, text="Start File Detection", 
                                                  command=lambda: self.start_trespassing_detection('file'),
                                                  state=tk.DISABLED)
        self.start_trespassing_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_trespassing_realtime_btn = ttk.Button(trespass_ctrl_frame, text="Start Realtime Detection", 
                                                      command=lambda: self.start_trespassing_detection('realtime'))
        self.start_trespassing_realtime_btn.pack(fill=tk.X, pady=5)
        
        self.stop_trespassing_btn = ttk.Button(trespass_ctrl_frame, text="Stop Detection", 
                                             command=self.stop_trespassing_detection,
                                             state=tk.DISABLED)
        self.stop_trespassing_btn.pack(fill=tk.X, pady=5)
    
    def setup_fall_detection_tab(self):
        """Setup the fall detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Fall Detection")
        self.modules["fall_detection"]["tab"] = tab
        
        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fall_video_label = ttk.Label(video_frame)
        self.fall_video_label.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        fall_ctrl_frame = ttk.LabelFrame(control_frame, text="Fall Detection")
        fall_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.select_fall_file_btn = ttk.Button(fall_ctrl_frame, text="Select Video File", 
                                                    command=self.select_fall_video_file)
        self.select_fall_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_fall_file_btn = ttk.Button(fall_ctrl_frame, text="Start File Detection", 
                                                  command=lambda: self.start_fall_detection('file'),
                                                  state=tk.DISABLED)
        self.start_fall_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_fall_realtime_btn = ttk.Button(fall_ctrl_frame, text="Start Realtime Detection", 
                                                      command=lambda: self.start_fall_detection('realtime'))
        self.start_fall_realtime_btn.pack(fill=tk.X, pady=5)
        
        self.stop_fall_btn = ttk.Button(fall_ctrl_frame, text="Stop Detection", 
                                             command=self.stop_fall_detection,
                                             state=tk.DISABLED)
        self.stop_fall_btn.pack(fill=tk.X, pady=5)
        
        # Confidence threshold for fall detection
        self.fall_confidence_var = tk.DoubleVar(value=0.5)
        fall_confidence_frame = ttk.LabelFrame(control_frame, text="Confidence Threshold")
        fall_confidence_frame.pack(fill=tk.X, pady=5)
        
        self.fall_confidence_slider = ttk.Scale(fall_confidence_frame, from_=0.1, to=0.9, 
                                         variable=self.fall_confidence_var,
                                         command=lambda v: self.fall_confidence_var.set(round(float(v), 1)))
        self.fall_confidence_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.fall_confidence_label = ttk.Label(fall_confidence_frame, text=f"Current: {self.fall_confidence_var.get():.1f}")
        self.fall_confidence_label.pack()
        
        self.fall_confidence_var.trace_add("write", lambda *_: self.fall_confidence_label.config(
            text=f"Current: {self.fall_confidence_var.get():.1f}"))
    
    def on_tab_changed(self, event):
        """Handle tab changes"""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        
        self.stop_all_detections()
        
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        
        if selected_tab == "Weapon Detection":
            self.modules["weapon_detection"]["active"] = True
        elif selected_tab == "Trespassing Detection":
            self.modules["trespassing_detection"]["active"] = True
        elif selected_tab == "Fall Detection":
            self.modules["fall_detection"]["active"] = True
        elif selected_tab == "Crowd Density":
            self.modules["crowd_detection"]["active"] = True
        elif selected_tab == "Fire Detection":
            self.modules["fire_detection"]["active"] = True
        elif selected_tab == "Dustbin Health":
            self.modules["dustbin_detection"]["active"] = True
    
    def stop_all_detections(self):
        """Stop all active detections"""
        if self.modules["weapon_detection"]["active"]:
            self.stop_weapon_detection()
        if self.modules["trespassing_detection"]["active"]:
            self.stop_trespassing_detection()
        if self.modules["fall_detection"]["active"]:
            self.stop_fall_detection()
        if self.modules["crowd_detection"]["active"]:
            self.stop_crowd_detection()
        if self.modules["fire_detection"]["active"]:
            self.stop_fire_detection()
        if self.modules["dustbin_detection"]["active"]:
            self.stop_dustbin_detection()

    def setup_crowd_detection_tab(self):
        """Setup the crowd density detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Crowd Density")
        self.modules["crowd_detection"]["tab"] = tab

        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.crowd_video_label = ttk.Label(video_frame)
        self.crowd_video_label.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)

        crowd_ctrl_frame = ttk.LabelFrame(control_frame, text="Crowd Density Detection")
        crowd_ctrl_frame.pack(fill=tk.X, pady=5)

        self.select_crowd_file_btn = ttk.Button(crowd_ctrl_frame, text="Select Video File", 
                                                command=self.select_crowd_video_file)
        self.select_crowd_file_btn.pack(fill=tk.X, pady=5)

        self.start_crowd_file_btn = ttk.Button(crowd_ctrl_frame, text="Start File Detection", 
                                               command=lambda: self.start_crowd_detection('file'),
                                               state=tk.DISABLED)
        self.start_crowd_file_btn.pack(fill=tk.X, pady=5)

        self.start_crowd_realtime_btn = ttk.Button(crowd_ctrl_frame, text="Start Realtime Detection", 
                                                   command=lambda: self.start_crowd_detection('realtime'))
        self.start_crowd_realtime_btn.pack(fill=tk.X, pady=5)

        self.stop_crowd_btn = ttk.Button(crowd_ctrl_frame, text="Stop Detection", 
                                          command=self.stop_crowd_detection,
                                          state=tk.DISABLED)
        self.stop_crowd_btn.pack(fill=tk.X, pady=5)

        self.crowd_count_var = tk.IntVar(value=0)
        count_frame = ttk.LabelFrame(control_frame, text="People Count")
        count_frame.pack(fill=tk.X, pady=5)
        self.crowd_count_label = ttk.Label(count_frame, text="Current: 0")
        self.crowd_count_label.pack(fill=tk.X, padx=5, pady=5)

        self.crowd_confidence_var = tk.DoubleVar(value=0.4)
        conf_frame = ttk.LabelFrame(control_frame, text="Confidence Threshold")
        conf_frame.pack(fill=tk.X, pady=5)
        self.crowd_conf_slider = ttk.Scale(conf_frame, from_=0.1, to=0.9, 
                                           variable=self.crowd_confidence_var,
                                           command=lambda v: self.crowd_confidence_var.set(round(float(v), 1)))
        self.crowd_conf_slider.pack(fill=tk.X, padx=5, pady=5)
        self.crowd_conf_label = ttk.Label(conf_frame, text=f"Current: {self.crowd_confidence_var.get():.1f}")
        self.crowd_conf_label.pack()
        self.crowd_confidence_var.trace_add("write", lambda *_: self.crowd_conf_label.config(
            text=f"Current: {self.crowd_confidence_var.get():.1f}"))

    def select_crowd_video_file(self):
        """Select video file for crowd density detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.crowd_video_path = file_path
            self.add_alert(f"Crowd detection video set: {os.path.basename(file_path)}")
            self.start_crowd_file_btn.config(state=tk.NORMAL)

    def start_crowd_detection(self, mode):
        """Start crowd density detection in specified mode"""
        self.crowd_detection_mode = mode

        if mode == 'file' and not hasattr(self, 'crowd_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return

        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.crowd_video_path)

        self.modules["crowd_detection"]["active"] = True
        self.add_alert(f"Crowd density detection started ({mode} mode)")

        self.select_crowd_file_btn.config(state=tk.DISABLED)
        self.start_crowd_file_btn.config(state=tk.DISABLED)
        self.start_crowd_realtime_btn.config(state=tk.DISABLED)
        self.stop_crowd_btn.config(state=tk.NORMAL)

    def stop_crowd_detection(self):
        """Stop crowd density detection"""
        self.modules["crowd_detection"]["active"] = False
        self.crowd_detection_mode = None

        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None

        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None

        self.add_alert("Crowd density detection stopped")

        self.select_crowd_file_btn.config(state=tk.NORMAL)
        self.start_crowd_file_btn.config(state=tk.NORMAL if hasattr(self, 'crowd_video_path') else tk.DISABLED)
        self.start_crowd_realtime_btn.config(state=tk.NORMAL)
        self.stop_crowd_btn.config(state=tk.DISABLED)

    def process_crowd_detection(self, frame):
        """Process frame for crowd density detection and counting"""
        display_frame = frame.copy()
        
        # If trespassing detection is also active, use its person count
        if self.modules["trespassing_detection"]["active"] and hasattr(self, 'last_person_count'):
            count_person = self.last_person_count
            # Draw bounding boxes for visualization
            results = self.crowd_model(frame, conf=self.crowd_confidence_var.get(), verbose=False)
            res0 = results[0]
            for box in res0.boxes:
                cls = int(box.cls[0])
                if self.crowd_model.names[cls] == 'person':
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        else:
            # Run independent crowd detection
            count_person = 0
            results = self.crowd_model(frame, conf=self.crowd_confidence_var.get(), verbose=False)
            res0 = results[0]
            for box in res0.boxes:
                cls = int(box.cls[0])
                if self.crowd_model.names[cls] == 'person':
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    count_person += 1

        self.crowd_count_var.set(count_person)
        self.crowd_count_label.config(text=f"Current: {count_person}")
        cv2.putText(display_frame, f"People: {count_person}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

        return display_frame
    
    def setup_fire_detection_tab(self):
        """Setup the fire detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Fire Detection")
        self.modules["fire_detection"]["tab"] = tab
        
        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fire_video_label = ttk.Label(video_frame)
        self.fire_video_label.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        fire_ctrl_frame = ttk.LabelFrame(control_frame, text="Fire Detection")
        fire_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.select_fire_file_btn = ttk.Button(fire_ctrl_frame, text="Select Video File", 
                                                    command=self.select_fire_video_file)
        self.select_fire_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_fire_file_btn = ttk.Button(fire_ctrl_frame, text="Start File Detection", 
                                                  command=lambda: self.start_fire_detection('file'),
                                                  state=tk.DISABLED)
        self.start_fire_file_btn.pack(fill=tk.X, pady=5)
        
        self.start_fire_realtime_btn = ttk.Button(fire_ctrl_frame, text="Start Realtime Detection", 
                                                      command=lambda: self.start_fire_detection('realtime'))
        self.start_fire_realtime_btn.pack(fill=tk.X, pady=5)
        
        self.stop_fire_btn = ttk.Button(fire_ctrl_frame, text="Stop Detection", 
                                             command=self.stop_fire_detection,
                                             state=tk.DISABLED)
        self.stop_fire_btn.pack(fill=tk.X, pady=5)
        
        # Confidence threshold for fire detection
        self.fire_confidence_var = tk.DoubleVar(value=0.5)
        fire_confidence_frame = ttk.LabelFrame(control_frame, text="Confidence Threshold")
        fire_confidence_frame.pack(fill=tk.X, pady=5)
        
        self.fire_confidence_slider = ttk.Scale(fire_confidence_frame, from_=0.1, to=0.9, 
                                         variable=self.fire_confidence_var,
                                         command=lambda v: self.fire_confidence_var.set(round(float(v), 1)))
        self.fire_confidence_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.fire_confidence_label = ttk.Label(fire_confidence_frame, text=f"Current: {self.fire_confidence_var.get():.1f}")
        self.fire_confidence_label.pack()
        
        self.fire_confidence_var.trace_add("write", lambda *_: self.fire_confidence_label.config(
            text=f"Current: {self.fire_confidence_var.get():.1f}"))
    
    def select_fire_video_file(self):
        """Select video file for fire detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.fire_video_path = file_path
            self.add_alert(f"Fire detection video set: {os.path.basename(file_path)}")
            self.start_fire_file_btn.config(state=tk.NORMAL)
    
    def start_fire_detection(self, mode):
        """Start fire detection in specified mode"""
        if self.fire_model is None:
            messagebox.showerror("Error", "Fire detection model not available. Please ensure the model file exists.")
            return
            
        self.fire_detection_mode = mode
        
        if mode == 'file' and not hasattr(self, 'fire_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
            
        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.fire_video_path)
        
        self.modules["fire_detection"]["active"] = True
        self.add_alert(f"Fire detection started ({mode} mode)")
        
        self.select_fire_file_btn.config(state=tk.DISABLED)
        self.start_fire_file_btn.config(state=tk.DISABLED)
        self.start_fire_realtime_btn.config(state=tk.DISABLED)
        self.stop_fire_btn.config(state=tk.NORMAL)
    
    def stop_fire_detection(self):
        """Stop fire detection"""
        self.modules["fire_detection"]["active"] = False
        self.fire_detection_mode = None
        
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            
        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None
        
        self.add_alert("Fire detection stopped")
        
        self.select_fire_file_btn.config(state=tk.NORMAL)
        self.start_fire_file_btn.config(state=tk.NORMAL if hasattr(self, 'fire_video_path') else tk.DISABLED)
        self.start_fire_realtime_btn.config(state=tk.NORMAL)
        self.stop_fire_btn.config(state=tk.DISABLED)
    
    def process_fire_detection(self, frame):
        """Process frame for fire and smoke detection with 5-second alert delay"""
        if self.fire_model is None:
            return frame
            
        display_frame = frame.copy()
        fire_detected = False
        smoke_detected = False
        
        results = self.fire_model(frame, stream=True, conf=self.fire_confidence_var.get(), verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.fire_model.names[cls]
                
                if label == "Fire":
                    fire_detected = True
                    
                    # Draw bounding box in orange/red for fire detection
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 69, 255), 3)
                    cv2.putText(display_frame, f'FIRE {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 69, 255), 2)
                    
                elif label == "smoke":
                    smoke_detected = True
                    
                    # Draw bounding box in gray/white for smoke detection
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (192, 192, 192), 3)
                    cv2.putText(display_frame, f'SMOKE {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (192, 192, 192), 2)
        
        # Send alert if fire or smoke detected (after processing all boxes)
        current_time = time.time()
        if (fire_detected or smoke_detected) and current_time - self.fire_alert_time > self.fire_alert_cooldown:
            if fire_detected and smoke_detected:
                alert_message = "🚨 Fire and Smoke detected!"
            elif fire_detected:
                alert_message = "🚨 Fire detected!"
            else:
                alert_message = "🚨 Smoke detected!"
            
            self.add_alert(alert_message, is_important=True)
            try:
                response = requests.get("http://127.0.0.1:8000/fire_alert")
                self.fire_alert_time = current_time
            except requests.exceptions.RequestException as e:
                self.add_alert(f"Error sending alert: {e}")
        
        return display_frame

    def setup_dustbin_detection_tab(self):
        """Setup the dustbin health detection module tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dustbin Health")
        self.modules["dustbin_detection"]["tab"] = tab

        video_frame = ttk.LabelFrame(tab, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.dustbin_video_label = ttk.Label(video_frame)
        self.dustbin_video_label.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(tab, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)

        dustbin_ctrl_frame = ttk.LabelFrame(control_frame, text="Dustbin Health Detection")
        dustbin_ctrl_frame.pack(fill=tk.X, pady=5)

        self.select_dustbin_file_btn = ttk.Button(dustbin_ctrl_frame, text="Select Video File", 
                                                  command=self.select_dustbin_video_file)
        self.select_dustbin_file_btn.pack(fill=tk.X, pady=5)

        self.start_dustbin_file_btn = ttk.Button(dustbin_ctrl_frame, text="Start File Detection", 
                                                 command=lambda: self.start_dustbin_detection('file'),
                                                 state=tk.DISABLED)
        self.start_dustbin_file_btn.pack(fill=tk.X, pady=5)

        self.start_dustbin_realtime_btn = ttk.Button(dustbin_ctrl_frame, text="Start Realtime Detection", 
                                                      command=lambda: self.start_dustbin_detection('realtime'))
        self.start_dustbin_realtime_btn.pack(fill=tk.X, pady=5)

        self.stop_dustbin_btn = ttk.Button(dustbin_ctrl_frame, text="Stop Detection", 
                                            command=self.stop_dustbin_detection,
                                            state=tk.DISABLED)
        self.stop_dustbin_btn.pack(fill=tk.X, pady=5)

        # Confidence threshold for dustbin detection
        self.dustbin_confidence_var = tk.DoubleVar(value=0.5)
        dustbin_confidence_frame = ttk.LabelFrame(control_frame, text="Confidence Threshold")
        dustbin_confidence_frame.pack(fill=tk.X, pady=5)

        self.dustbin_confidence_slider = ttk.Scale(dustbin_confidence_frame, from_=0.1, to=0.9, 
                                                   variable=self.dustbin_confidence_var,
                                                   command=lambda v: self.dustbin_confidence_var.set(round(float(v), 1)))
        self.dustbin_confidence_slider.pack(fill=tk.X, padx=5, pady=5)

        self.dustbin_confidence_label = ttk.Label(dustbin_confidence_frame, text=f"Current: {self.dustbin_confidence_var.get():.1f}")
        self.dustbin_confidence_label.pack()

        self.dustbin_confidence_var.trace_add("write", lambda *_: self.dustbin_confidence_label.config(
            text=f"Current: {self.dustbin_confidence_var.get():.1f}"))

        # Live counts per label
        self.dustbin_counts_text = tk.Text(control_frame, height=10, state=tk.DISABLED)
        self.dustbin_counts_text.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

    def select_dustbin_video_file(self):
        """Select video file for dustbin health detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.dustbin_video_path = file_path
            self.add_alert(f"Dustbin detection video set: {os.path.basename(file_path)}")
            self.start_dustbin_file_btn.config(state=tk.NORMAL)

    def start_dustbin_detection(self, mode):
        """Start dustbin detection in specified mode"""
        if getattr(self, 'dustbin_model', None) is None:
            messagebox.showerror("Error", "Dustbin model not available. Ensure dustbin.pt exists.")
            return

        self.dustbin_detection_mode = mode

        if mode == 'file' and not hasattr(self, 'dustbin_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return

        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.dustbin_video_path)

        self.modules["dustbin_detection"]["active"] = True
        self.add_alert(f"Dustbin detection started ({mode} mode)")

        self.select_dustbin_file_btn.config(state=tk.DISABLED)
        self.start_dustbin_file_btn.config(state=tk.DISABLED)
        self.start_dustbin_realtime_btn.config(state=tk.DISABLED)
        self.stop_dustbin_btn.config(state=tk.NORMAL)

    def stop_dustbin_detection(self):
        """Stop dustbin detection"""
        self.modules["dustbin_detection"]["active"] = False
        self.dustbin_detection_mode = None

        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None

        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None

        self.add_alert("Dustbin detection stopped")

        self.select_dustbin_file_btn.config(state=tk.NORMAL)
        self.start_dustbin_file_btn.config(state=tk.NORMAL if hasattr(self, 'dustbin_video_path') else tk.DISABLED)
        self.start_dustbin_realtime_btn.config(state=tk.NORMAL)
        self.stop_dustbin_btn.config(state=tk.DISABLED)

    def process_dustbin_detection(self, frame):
        """Process frame for dustbin health detection and counts"""
        if getattr(self, 'dustbin_model', None) is None:
            return frame

        display_frame = frame.copy()
        results = self.dustbin_model(frame, conf=self.dustbin_confidence_var.get(), verbose=False)
        res0 = results[0]

        # Count per label
        counts = {}
        for box in res0.boxes:
            cls = int(box.cls[0])
            label = self.dustbin_model.names[cls]
            counts[label] = counts.get(label, 0) + 1

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display_frame, f"{label}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Update counts panel
        self.dustbin_counts_text.config(state=tk.NORMAL)
        self.dustbin_counts_text.delete('1.0', tk.END)
        for name in ['Broken trash can', 'Close_empty', 'Close_full', 'Healthy trash can', 'Open_empty', 'Open_full', 'Trash flow', 'closed', 'empty', 'full']:
            self.dustbin_counts_text.insert(tk.END, f"{name}: {counts.get(name, 0)}\n")
        self.dustbin_counts_text.config(state=tk.DISABLED)

        return display_frame
    
    def select_weapon_video_file(self):
        """Select video file for weapon detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.weapon_video_path = file_path
            self.add_alert(f"Weapon detection video set: {os.path.basename(file_path)}")
            self.start_weapon_file_btn.config(state=tk.NORMAL)
    
    def start_weapon_detection(self, mode):
        """Start weapon detection in specified mode"""
        self.weapon_detection_mode = mode
        
        if mode == 'file' and not hasattr(self, 'weapon_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
            
        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.weapon_video_path)
        
        self.modules["weapon_detection"]["active"] = True
        self.add_alert(f"Weapon detection started ({mode} mode)")
        
        self.select_weapon_file_btn.config(state=tk.DISABLED)
        self.start_weapon_file_btn.config(state=tk.DISABLED)
        self.start_weapon_realtime_btn.config(state=tk.DISABLED)
        self.stop_weapon_btn.config(state=tk.NORMAL)
    
    def stop_weapon_detection(self):
        """Stop weapon detection"""
        self.modules["weapon_detection"]["active"] = False
        self.weapon_detection_mode = None
        
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            
        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None
        
        self.add_alert("Weapon detection stopped")
        
        self.select_weapon_file_btn.config(state=tk.NORMAL)
        self.start_weapon_file_btn.config(state=tk.NORMAL if hasattr(self, 'weapon_video_path') else tk.DISABLED)
        self.start_weapon_realtime_btn.config(state=tk.NORMAL)
        self.stop_weapon_btn.config(state=tk.DISABLED)
    
    def select_trespassing_video_file(self):
        """Select video file for trespassing detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.trespassing_video_path = file_path
            self.add_alert(f"Trespassing detection video set: {os.path.basename(file_path)}")
            self.start_trespassing_file_btn.config(state=tk.NORMAL)
    
    def start_trespassing_detection(self, mode):
        """Start trespassing detection in specified mode"""
        self.trespassing_detection_mode = mode
        
        if mode == 'file' and not hasattr(self, 'trespassing_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
            
        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.trespassing_video_path)
        
        self.modules["trespassing_detection"]["active"] = True
        self.add_alert(f"Trespassing detection started ({mode} mode)")
        
        self.select_trespassing_file_btn.config(state=tk.DISABLED)
        self.start_trespassing_file_btn.config(state=tk.DISABLED)
        self.start_trespassing_realtime_btn.config(state=tk.DISABLED)
        self.stop_trespassing_btn.config(state=tk.NORMAL)
    
    def stop_trespassing_detection(self):
        """Stop trespassing detection"""
        self.modules["trespassing_detection"]["active"] = False
        self.trespassing_detection_mode = None
        
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            
        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None
        
        self.add_alert("Trespassing detection stopped")
        
        self.select_trespassing_file_btn.config(state=tk.NORMAL)
        self.start_trespassing_file_btn.config(state=tk.NORMAL if hasattr(self, 'trespassing_video_path') else tk.DISABLED)
        self.start_trespassing_realtime_btn.config(state=tk.NORMAL)
        self.stop_trespassing_btn.config(state=tk.DISABLED)
    
    def select_fall_video_file(self):
        """Select video file for fall detection"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.fall_video_path = file_path
            self.add_alert(f"Fall detection video set: {os.path.basename(file_path)}")
            self.start_fall_file_btn.config(state=tk.NORMAL)
    
    def start_fall_detection(self, mode):
        """Start fall detection in specified mode"""
        if self.fall_model is None:
            messagebox.showerror("Error", "Fall detection model not available. Please ensure the model file exists.")
            return
            
        self.fall_detection_mode = mode
        
        if mode == 'file' and not hasattr(self, 'fall_video_path'):
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
            
        if mode == 'realtime':
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.video_capture = cv2.VideoCapture(self.fall_video_path)
        
        self.modules["fall_detection"]["active"] = True
        self.add_alert(f"Fall detection started ({mode} mode)")
        
        self.select_fall_file_btn.config(state=tk.DISABLED)
        self.start_fall_file_btn.config(state=tk.DISABLED)
        self.start_fall_realtime_btn.config(state=tk.DISABLED)
        self.stop_fall_btn.config(state=tk.NORMAL)
    
    def stop_fall_detection(self):
        """Stop fall detection"""
        self.modules["fall_detection"]["active"] = False
        self.fall_detection_mode = None
        
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            
        if self.cap is not None and not any(module["active"] for module in self.modules.values()):
            self.cap.release()
            self.cap = None
        
        self.add_alert("Fall detection stopped")
        
        self.select_fall_file_btn.config(state=tk.NORMAL)
        self.start_fall_file_btn.config(state=tk.NORMAL if hasattr(self, 'fall_video_path') else tk.DISABLED)
        self.start_fall_realtime_btn.config(state=tk.NORMAL)
        self.stop_fall_btn.config(state=tk.DISABLED)
    
    def add_alert(self, message, is_important=False):
        """Add message to alert log"""
        self.alert_text.config(state=tk.NORMAL)
        if is_important:
            self.alert_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ", 'important')
            self.alert_text.insert(tk.END, f"{message}\n", 'important')
            self.show_alert_popup(message)
        else:
            self.alert_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        
        self.alert_text.see(tk.END)
        self.alert_text.config(state=tk.DISABLED)
        
        self.current_alert.config(text=message)
        if is_important:
            self.current_alert.config(foreground='red', font=('Helvetica', 16, 'bold'))
        else:
            self.current_alert.config(foreground='black', font=('Helvetica', 12))
    
    def show_alert_popup(self, message):
        """Show popup alert window"""
        AlertWindow(self.root, message)
    
    def process_weapon_detection(self, frame):
        """Process frame for weapon detection with 5-second alert delay"""
        display_frame = frame.copy()
        weapon_detected = False
        
        results = self.weapon_model(frame, stream=True, conf=self.confidence_var.get(), verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.weapon_model.names[cls]
                
                if label.lower() == "weapon":
                    weapon_detected = True
                    
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    cv2.putText(display_frame, f'{label} {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    
                    current_time = time.time()
                    if current_time - self.weapon_alert_time > self.weapon_alert_cooldown:
                        alert_message = "🚨 Weapon detected!"
                        self.add_alert(alert_message, is_important=True)
                        try:
                            response = requests.get("http://127.0.0.1:8000/weapon_alert")
                            self.weapon_alert_time = current_time
                        except requests.exceptions.RequestException as e:
                            self.add_alert(f"Error sending alert: {e}")
        
        if not weapon_detected:
            self.weapon_alert_sent = False
        
        return display_frame
    
    def process_trespassing_detection(self, frame):
        """Process frame for trespassing detection with 5-second alert delay"""
        display_frame = frame.copy()
        height, width = frame.shape[:2]
        person_detected_on_track = False
        person_count = 0
        
        track_results = self.track_model(frame, verbose=False)[0]
        track_mask = None

        if track_results.masks:
            masks = track_results.masks.data.cpu().numpy()
            combined_mask = np.any(masks > 0.5, axis=0).astype(np.uint8)
            mask_resized = cv2.resize(combined_mask, (width, height))
            track_mask = mask_resized

            colored_mask = np.zeros_like(frame)
            colored_mask[track_mask == 1] = (0, 0, 255)
            display_frame = cv2.addWeighted(display_frame, 1.0, colored_mask, 0.5, 0)

        person_results = self.person_model(frame, verbose=False)[0]

        for box in person_results.boxes:
            cls = int(box.cls[0])
            if self.person_model.names[cls] == 'person':
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                person_count += 1

                cv2.circle(display_frame, (cx, cy), 5, (0, 255, 0), -1)
                cv2.putText(display_frame, "Person", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if track_mask is not None and track_mask[cy, cx] == 1:
                    person_detected_on_track = True

        # Update shared person count for crowd detection
        self.last_person_count = person_count
        
        current_time = time.time()
        if person_detected_on_track and current_time - self.trespassing_alert_time > self.trespassing_alert_cooldown:
            alert_message = "🚨 Person detected on railway track!"
            self.add_alert(alert_message, is_important=True)
            try:
                res = requests.get("http://127.0.0.1:8000/track_alert")
                self.trespassing_alert_time = current_time
            except Exception as e:
                self.add_alert(f"Failed to send alert: {e}")
        elif not person_detected_on_track:
            self.trespassing_alert_sent = False
        
        return display_frame
    
    def process_fall_detection(self, frame):
        """Process frame for fall detection with 5-second alert delay"""
        if self.fall_model is None:
            return frame
            
        display_frame = frame.copy()
        fall_detected = False
        
        results = self.fall_model(frame, stream=True, conf=self.fall_confidence_var.get(), verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.fall_model.names[cls]
                
                if label.lower() == "fall-detected":
                    fall_detected = True
                    
                    # Draw bounding box in red for fall detection
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(display_frame, f'FALL {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    current_time = time.time()
                    if current_time - self.fall_alert_time > self.fall_alert_cooldown:
                        alert_message = "🚨 Fall detected!"
                        self.add_alert(alert_message, is_important=True)
                        try:
                            response = requests.get("http://127.0.0.1:8000/fall_alert")
                            self.fall_alert_time = current_time
                        except requests.exceptions.RequestException as e:
                            self.add_alert(f"Error sending alert: {e}")
                elif label.lower() == "nofall":
                    # Draw bounding box in green for no-fall
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f'No Fall {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return display_frame
    
    def process_trespassing_detection_alerts_only(self, frame):
        """Process trespassing detection for alerts only (no visual modifications)"""
        height, width = frame.shape[:2]
        person_detected_on_track = False
        person_count = 0
        
        track_results = self.track_model(frame, verbose=False)[0]
        track_mask = None

        if track_results.masks:
            masks = track_results.masks.data.cpu().numpy()
            combined_mask = np.any(masks > 0.5, axis=0).astype(np.uint8)
            mask_resized = cv2.resize(combined_mask, (width, height))
            track_mask = mask_resized

        person_results = self.person_model(frame, verbose=False)[0]

        for box in person_results.boxes:
            cls = int(box.cls[0])
            if self.person_model.names[cls] == 'person':
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                person_count += 1

                if track_mask is not None and track_mask[cy, cx] == 1:
                    person_detected_on_track = True

        # Update shared person count for crowd detection
        self.last_person_count = person_count
        
        # Send alert if needed
        current_time = time.time()
        if person_detected_on_track and current_time - self.trespassing_alert_time > self.trespassing_alert_cooldown:
            alert_message = "🚨 Person detected on railway track!"
            self.add_alert(alert_message, is_important=True)
            try:
                res = requests.get("http://127.0.0.1:8000/track_alert")
                self.trespassing_alert_time = current_time
            except Exception as e:
                self.add_alert(f"Failed to send alert: {e}")
        elif not person_detected_on_track:
            self.trespassing_alert_sent = False
    
    def process_fall_detection_alerts_only(self, frame):
        """Process fall detection for alerts only (no visual modifications)"""
        if self.fall_model is None:
            return
            
        results = self.fall_model(frame, stream=True, conf=self.fall_confidence_var.get(), verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                label = self.fall_model.names[cls]
                
                if label.lower() == "fall-detected":
                    current_time = time.time()
                    if current_time - self.fall_alert_time > self.fall_alert_cooldown:
                        alert_message = "🚨 Fall detected!"
                        self.add_alert(alert_message, is_important=True)
                        try:
                            response = requests.get("http://127.0.0.1:8000/fall_alert")
                            self.fall_alert_time = current_time
                        except requests.exceptions.RequestException as e:
                            self.add_alert(f"Error sending alert: {e}")
    
    def process_fall_detection_visual_only(self, frame):
        """Process fall detection for visual display only (no alerts)"""
        if self.fall_model is None:
            return frame
            
        display_frame = frame.copy()
        
        results = self.fall_model(frame, stream=True, conf=self.fall_confidence_var.get(), verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.fall_model.names[cls]
                
                if label.lower() == "fall-detected":
                    # Draw bounding box in red for fall detection
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(display_frame, f'FALL {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                elif label.lower() == "nofall":
                    # Draw bounding box in green for no-fall
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f'No Fall {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return display_frame
    
    def process_crowd_detection_alerts_only(self, frame):
        """Process crowd detection for alerts only (no visual modifications)"""
        # Crowd detection doesn't typically send alerts, just counts
        # But we can add logic here if needed for crowd-based alerts
        pass
    
    
    def update_video(self):
        """Main video update loop - supports multiple models simultaneously"""
        if self.running:
            frame = None
            active_models = [k for k in ("trespassing_detection", "fall_detection", "crowd_detection") 
                           if self.modules[k]["active"]]
            
            if active_models:
                # Read frame from active source
                if self.cap is not None:
                    ret, frame = self.cap.read()
                    if not ret:
                        frame = None
                elif self.video_capture is not None:
                    ret, frame = self.video_capture.read()
                    if not ret:
                        self.stop_unified_detection()
                        frame = None
            
            if frame is not None:
                frame = cv2.resize(frame, (640, 480))
                original_frame = frame.copy()
                processed_frame = frame.copy()
                
                # Process each detection on original frame for alerts, but apply visuals sequentially for crisp display
                # This ensures alerts work independently while maintaining clear visual overlays
                
                if "trespassing_detection" in active_models:
                    # Process for alerts on clean frame
                    self.process_trespassing_detection_alerts_only(original_frame.copy())
                    # Apply visual overlays to display frame
                    processed_frame = self.process_trespassing_detection(processed_frame)
                    
                if "fall_detection" in active_models:
                    # Process for alerts on clean frame  
                    self.process_fall_detection_alerts_only(original_frame.copy())
                    # Apply visual overlays to display frame
                    processed_frame = self.process_fall_detection_visual_only(processed_frame)
                    
                if "crowd_detection" in active_models:
                    # Process for alerts on clean frame
                    self.process_crowd_detection_alerts_only(original_frame.copy())
                    # Apply visual overlays to display frame
                    processed_frame = self.process_crowd_detection(processed_frame)
                
                # Display on unified label
                img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                if hasattr(self, 'unified_video_label'):
                    self.unified_video_label.imgtk = imgtk
                    self.unified_video_label.configure(image=imgtk)
        
        self.root.after(10, self.update_video)
    
    def exit_app(self):
        """Cleanup and exit application"""
        self.running = False
        
        if self.cap is not None:
            self.cap.release()
        if self.video_capture is not None:
            self.video_capture.release()
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SecuritySystemApp(root)
    root.mainloop()
