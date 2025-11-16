import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os


class UIComponents:
    def __init__(self, root):
        self.root = root
        self.setup_theme()
    
    def setup_theme(self):
        """Setup dark theme configuration"""
        self.BG = '#0f0f10'
        self.CARD = '#17171a'
        self.FG = '#e4e4e7'
        self.ACCENT = '#3b82f6'
        self.ACCENT_HOVER = '#2563eb'

        self.root.configure(bg=self.BG)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Notebook and tabs
        style.configure('TNotebook', background=self.BG, borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=(16, 8),
                        background=self.CARD, foreground=self.FG)
        style.map('TNotebook.Tab', background=[('selected', self.ACCENT)], foreground=[('selected', 'white')])

        # Containers and labels
        style.configure('TFrame', background=self.BG)
        style.configure('TLabelframe', background=self.BG, foreground=self.FG, font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background=self.BG, foreground=self.FG)
        style.configure('TLabel', background=self.BG, foreground=self.FG, font=('Segoe UI', 10))
        style.configure('Alert.TLabel', background=self.CARD, foreground='#ff4545', font=('Segoe UI', 13, 'bold'))

        # Buttons and sliders
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=(12, 8))
        style.map('TButton', foreground=[('!disabled', 'white')], background=[('!disabled', self.ACCENT), ('active', self.ACCENT_HOVER)])
        style.configure('Horizontal.TScale', background=self.BG)

    def create_unified_dashboard(self, parent, callbacks):
        """Create unified dashboard with multi-model selection"""
        dashboard = ttk.Frame(parent)
        dashboard.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        
        # Video display
        video_frame = ttk.LabelFrame(dashboard, text="Detection Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        unified_video_label = ttk.Label(video_frame)
        unified_video_label.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.Frame(dashboard, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Model selection
        model_frame = ttk.LabelFrame(control_frame, text="Select Models")
        model_frame.pack(fill=tk.X, pady=5)
        
        model_vars = {
            'trespassing_detection': tk.BooleanVar(value=False),
            'fall_detection': tk.BooleanVar(value=False),
            'crowd_detection': tk.BooleanVar(value=False),
        }
        
        ttk.Checkbutton(model_frame, text="Trespassing Detection", 
                       variable=model_vars['trespassing_detection']).pack(anchor='w', padx=8, pady=2)
        ttk.Checkbutton(model_frame, text="Fall Detection", 
                       variable=model_vars['fall_detection']).pack(anchor='w', padx=8, pady=2)
        ttk.Checkbutton(model_frame, text="Crowd Density", 
                       variable=model_vars['crowd_detection']).pack(anchor='w', padx=8, pady=2)
        
        # Controls
        ctrl_frame = ttk.LabelFrame(control_frame, text="Controls")
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(ctrl_frame, text="Select Video File", 
                  command=callbacks['select_video']).pack(fill=tk.X, pady=5)
        
        start_file_btn = ttk.Button(ctrl_frame, text="Start File Detection", 
                                   command=lambda: callbacks['start_detection']('file'),
                                   state=tk.DISABLED)
        start_file_btn.pack(fill=tk.X, pady=5)
        
        ttk.Button(ctrl_frame, text="Start Realtime Detection", 
                  command=lambda: callbacks['start_detection']('realtime')).pack(fill=tk.X, pady=5)
        
        stop_btn = ttk.Button(ctrl_frame, text="Stop Detection", 
                             command=callbacks['stop_detection'],
                             state=tk.DISABLED)
        stop_btn.pack(fill=tk.X, pady=5)
        
        # Confidence sliders and counters
        confidence_var = tk.DoubleVar(value=0.5)
        fall_confidence_var = tk.DoubleVar(value=0.5)
        crowd_confidence_var = tk.DoubleVar(value=0.4)
        crowd_count_var = tk.IntVar(value=0)
        
        # Add crowd counter display
        count_frame = ttk.LabelFrame(control_frame, text="People Count")
        count_frame.pack(fill=tk.X, pady=5)
        crowd_count_label = ttk.Label(count_frame, text="Current: 0")
        crowd_count_label.pack(fill=tk.X, padx=5, pady=5)
        
        return {
            'unified_video_label': unified_video_label,
            'model_vars': model_vars,
            'start_file_btn': start_file_btn,
            'stop_btn': stop_btn,
            'confidence_var': confidence_var,
            'fall_confidence_var': fall_confidence_var,
            'crowd_confidence_var': crowd_confidence_var,
            'crowd_count_var': crowd_count_var,
            'crowd_count_label': crowd_count_label
        }

    def create_alert_system(self, parent):
        """Create alert system UI"""
        alert_frame = ttk.LabelFrame(parent, text="System Alerts", height=150, style='TLabelframe')
        alert_frame.pack(fill=tk.X, pady=(5,0))
        alert_frame.pack_propagate(False)
        
        alert_text = tk.Text(
            alert_frame, 
            height=8, 
            state=tk.DISABLED,
            font=('Consolas', 10),
            bg=self.CARD,
            fg=self.FG,
            insertbackground=self.FG,
            selectbackground=self.ACCENT,
            relief=tk.FLAT
        )
        alert_text.tag_config('important', foreground='#ff4545', font=('Consolas', 10, 'bold'))
        
        scrollbar = ttk.Scrollbar(alert_frame, command=alert_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        alert_text.config(yscrollcommand=scrollbar.set)
        alert_text.pack(fill=tk.BOTH, expand=True)
        
        current_alert = ttk.Label(parent, text="", style='Alert.TLabel', wraplength=1200)
        current_alert.pack(fill=tk.X, pady=(5,0))
        
        return alert_text, current_alert

    def select_video_file(self):
        """Select video file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        return file_path
