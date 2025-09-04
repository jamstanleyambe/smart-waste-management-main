#!/usr/bin/env python3
"""
📸 Camera Utilities Module
Smart Waste Management System - test-v3-cam branch
"""

import cv2
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraManager:
    """Manages camera operations and image capture"""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.camera = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Connect to camera device"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera at index {self.camera_index}")
                return False
            self.is_connected = True
            logger.info(f"Successfully connected to camera {self.camera_index}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to camera: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from camera"""
        if self.camera:
            self.camera.release()
            self.is_connected = False
    
    def capture_image(self, save_path: str = None) -> np.ndarray:
        """Capture a single image from camera"""
        if not self.is_connected:
            logger.error("Camera not connected")
            return None
            
        ret, frame = self.camera.read()
        if ret and save_path:
            cv2.imwrite(save_path, frame)
            logger.info(f"Image saved to {save_path}")
        return frame if ret else None

def test_camera():
    """Test camera functionality"""
    print("🔍 Testing camera...")
    camera = CameraManager()
    
    if camera.connect():
        print("✅ Camera connected")
        image = camera.capture_image("test_capture.jpg")
        if image is not None:
            print(f"📸 Image captured (shape: {image.shape})")
        camera.disconnect()
    else:
        print("❌ Camera connection failed")

if __name__ == "__main__":
    test_camera()
