import cv2
from .base_detector import BaseDetector


class CrowdDetector(BaseDetector):
    def __init__(self, crowd_model, alert_cooldown=5):
        super().__init__(crowd_model, alert_cooldown)
        self.person_count = 0
    
    def process_frame(self, frame, confidence_threshold=0.4, shared_person_count=None):
        """Process frame for crowd density detection and counting"""
        display_frame = frame.copy()
        
        # If trespassing detection is also active, use its person count
        if shared_person_count is not None:
            count_person = shared_person_count
            # Draw bounding boxes for visualization
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            res0 = results[0]
            for box in res0.boxes:
                cls = int(box.cls[0])
                if self.model.names[cls] == 'person':
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        else:
            # Run independent crowd detection
            count_person = 0
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            res0 = results[0]
            for box in res0.boxes:
                cls = int(box.cls[0])
                if self.model.names[cls] == 'person':
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    count_person += 1

        self.person_count = count_person
        cv2.putText(display_frame, f"People: {count_person}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

        return display_frame
    
    def process_alerts_only(self, frame, confidence_threshold=0.4):
        """Process crowd detection for alerts only (no visual modifications)"""
        # Crowd detection doesn't typically send alerts, just counts
        # But we can add logic here if needed for crowd-based alerts
        pass
    
    def get_person_count(self):
        """Get the current person count"""
        return self.person_count
