import cv2
import numpy as np
from .base_detector import BaseDetector


class TrespassingDetector(BaseDetector):
    def __init__(self, track_model, person_model, alert_cooldown=5):
        super().__init__(track_model, alert_cooldown)
        self.person_model = person_model
        self.last_person_count = 0
    
    def process_frame(self, frame, confidence_threshold=0.5):
        """Process frame for trespassing detection with visual overlays"""
        display_frame = frame.copy()
        height, width = frame.shape[:2]
        person_detected_on_track = False
        person_count = 0
        
        track_results = self.model(frame, verbose=False)[0]
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
        
        if person_detected_on_track:
            alert_message = "🚨 Person detected on railway track!"
            self.send_alert(alert_message, "track_alert")
        
        return display_frame
    
    def process_alerts_only(self, frame, confidence_threshold=0.5):
        """Process trespassing detection for alerts only (no visual modifications)"""
        height, width = frame.shape[:2]
        person_detected_on_track = False
        person_count = 0
        
        track_results = self.model(frame, verbose=False)[0]
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
        if person_detected_on_track:
            alert_message = "🚨 Person detected on railway track!"
            self.send_alert(alert_message, "track_alert")
    
    def get_person_count(self):
        """Get the last detected person count"""
        return self.last_person_count
