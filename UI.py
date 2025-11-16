import tkinter as tk
from core.app_controller import SecuritySystemApp


if __name__ == "__main__":
    root = tk.Tk()
    app = SecuritySystemApp(root)
    root.mainloop()
