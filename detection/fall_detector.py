import cv2
from .base_detector import BaseDetector


class FallDetector(BaseDetector):
    def __init__(self, fall_model, alert_cooldown=5):
        super().__init__(fall_model, alert_cooldown)
    
    def process_frame(self, frame, confidence_threshold=0.5):
        """Process frame for fall detection with visual overlays"""
        if self.model is None:
            return frame
            
        display_frame = frame.copy()
        fall_detected = False
        
        results = self.model(frame, stream=True, conf=confidence_threshold, verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.model.names[cls]
                
                if label.lower() == "fall-detected":
                    fall_detected = True
                    
                    # Draw bounding box in red for fall detection
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(display_frame, f'FALL {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    alert_message = "🚨 Fall detected!"
                    self.send_alert(alert_message, "fall_alert")
                    
                elif label.lower() == "nofall":
                    # Draw bounding box in green for no-fall
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f'No Fall {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return display_frame
    
    def process_alerts_only(self, frame, confidence_threshold=0.5):
        """Process fall detection for alerts only (no visual modifications)"""
        if self.model is None:
            return
            
        results = self.model(frame, stream=True, conf=confidence_threshold, verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                label = self.model.names[cls]
                
                if label.lower() == "fall-detected":
                    alert_message = "🚨 Fall detected!"
                    self.send_alert(alert_message, "fall_alert")
    
    def process_visual_only(self, frame, confidence_threshold=0.5):
        """Process fall detection for visual display only (no alerts)"""
        if self.model is None:
            return frame
            
        display_frame = frame.copy()
        
        results = self.model(frame, stream=True, conf=confidence_threshold, verbose=False)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()
                cls = int(box.cls[0])
                label = self.model.names[cls]
                
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
