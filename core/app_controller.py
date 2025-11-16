import tkinter as tk
from tkinter import messagebox
import cv2
import time
import os
from PIL import Image, ImageTk
from ultralytics import YOLO

from components.alert_window import AlertWindow
from components.ui_components import UIComponents
from detection.trespassing_detector import TrespassingDetector
from detection.fall_detector import FallDetector
from detection.crowd_detector import CrowdDetector


class SecuritySystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Railway Surveillance System")
        self.root.geometry("1400x900")
        
        # Initialize all attributes
        self.video_file_path = None
        self.unified_video_path = None
        
        # Video capture objects
        self.cap = None
        self.video_capture = None
        self.current_frame = None
        
        # Variables
        self.running = True
        self.modules = {
            "trespassing_detection": {"active": False},
            "fall_detection": {"active": False},
            "crowd_detection": {"active": False}
        }
        
        # Initialize models and detectors
        self.initialize_models()
        
        # Initialize UI components
        self.ui_components = UIComponents(root)
        
        # Setup UI
        self.setup_ui()
        
        # Start the video update thread
        self.update_video()
    
    def initialize_models(self):
        """Initialize all the required models"""
        try:
            track_model = YOLO("train_segmented.pt")
            person_model = YOLO("yolo11n.pt")
            crowd_model = YOLO("yolo11n.pt")
            fall_model = YOLO("fall_model.pt")
            
            # Initialize detectors
            self.trespassing_detector = TrespassingDetector(track_model, person_model)
            self.fall_detector = FallDetector(fall_model)
            self.crowd_detector = CrowdDetector(crowd_model)
            
            # Set alert callbacks
            self.trespassing_detector.set_alert_callback(self.add_alert)
            self.fall_detector.set_alert_callback(self.add_alert)
            self.crowd_detector.set_alert_callback(self.add_alert)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize models: {str(e)}")
            self.root.destroy()
    
    def setup_ui(self):
        """Setup the main UI components"""
        main_frame = tk.Frame(self.root, bg=self.ui_components.BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create unified dashboard
        callbacks = {
            'select_video': self.select_unified_video,
            'start_detection': self.start_unified_detection,
            'stop_detection': self.stop_unified_detection
        }
        
        dashboard_components = self.ui_components.create_unified_dashboard(main_frame, callbacks)
        
        # Store UI components
        self.unified_video_label = dashboard_components['unified_video_label']
        self.model_vars = dashboard_components['model_vars']
        self.start_file_btn = dashboard_components['start_file_btn']
        self.stop_btn = dashboard_components['stop_btn']
        self.confidence_var = dashboard_components['confidence_var']
        self.fall_confidence_var = dashboard_components['fall_confidence_var']
        self.crowd_confidence_var = dashboard_components['crowd_confidence_var']
        self.crowd_count_var = dashboard_components['crowd_count_var']
        self.crowd_count_label = dashboard_components['crowd_count_label']
        
        # Create alert system
        self.alert_text, self.current_alert = self.ui_components.create_alert_system(main_frame)
    
    def select_unified_video(self):
        """Select video file for unified detection"""
        file_path = self.ui_components.select_video_file()
        if file_path:
            self.unified_video_path = file_path
            self.add_alert(f"Video selected: {os.path.basename(file_path)}")
            self.start_file_btn.config(state=tk.NORMAL)
    
    def start_unified_detection(self, mode):
        """Start unified detection with selected models"""
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
        """Stop unified detection"""
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
                    self.trespassing_detector.process_alerts_only(original_frame.copy(), self.confidence_var.get())
                    # Apply visual overlays to display frame
                    processed_frame = self.trespassing_detector.process_frame(processed_frame, self.confidence_var.get())
                    
                if "fall_detection" in active_models:
                    # Process for alerts on clean frame  
                    self.fall_detector.process_alerts_only(original_frame.copy(), self.fall_confidence_var.get())
                    # Apply visual overlays to display frame
                    processed_frame = self.fall_detector.process_visual_only(processed_frame, self.fall_confidence_var.get())
                    
                if "crowd_detection" in active_models:
                    # Process for alerts on clean frame
                    self.crowd_detector.process_alerts_only(original_frame.copy(), self.crowd_confidence_var.get())
                    # Apply visual overlays to display frame - use shared person count if trespassing is active
                    shared_count = self.trespassing_detector.get_person_count() if "trespassing_detection" in active_models else None
                    processed_frame = self.crowd_detector.process_frame(processed_frame, self.crowd_confidence_var.get(), shared_count)
                    
                    # Update crowd count display
                    count = self.crowd_detector.get_person_count()
                    self.crowd_count_var.set(count)
                    self.crowd_count_label.config(text=f"Current: {count}")
                
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
