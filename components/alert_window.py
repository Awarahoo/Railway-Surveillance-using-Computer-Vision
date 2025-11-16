import tkinter as tk


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
