import time
import requests
from abc import ABC, abstractmethod


class BaseDetector(ABC):
    def __init__(self, model, alert_cooldown=5):
        self.model = model
        self.alert_cooldown = alert_cooldown
        self.last_alert_time = 0
        self.alert_callback = None
    
    def set_alert_callback(self, callback):
        """Set callback function for alerts"""
        self.alert_callback = callback
    
    def can_send_alert(self):
        """Check if enough time has passed since last alert"""
        current_time = time.time()
        return current_time - self.last_alert_time > self.alert_cooldown
    
    def send_alert(self, message, endpoint=None, is_important=True):
        """Send alert with cooldown protection"""
        if not self.can_send_alert():
            return False
            
        if self.alert_callback:
            self.alert_callback(message, is_important)
        
        if endpoint:
            try:
                response = requests.get(f"http://127.0.0.1:8000/{endpoint}")
                self.last_alert_time = time.time()
                return True
            except requests.exceptions.RequestException as e:
                if self.alert_callback:
                    self.alert_callback(f"Error sending alert: {e}")
                return False
        
        self.last_alert_time = time.time()
        return True
    
    @abstractmethod
    def process_frame(self, frame, confidence_threshold=0.5):
        """Process frame and return display frame with overlays"""
        pass
    
    @abstractmethod
    def process_alerts_only(self, frame, confidence_threshold=0.5):
        """Process frame for alerts only (no visual modifications)"""
        pass
