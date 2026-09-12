import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTracker:
  def __init__(
      self,
      model_path,
      max_hands=2
  ):
    
    base_options=python.BaseOptions(
      model_asset_path=model_path
    )

    options=vision.HandLandmarkerOptions(
      base_options=base_options,
      running_mode=vision.RunningMode.VIDEO,
      num_hands=max_hands,
      min_hand_detection_confidence=0.5
      min_hand_presence_confidence=0.5,
      min_tracking_confidence=0.5
    )

    self.detector=(
      vision.HandLandmarker.create_from_options(options)
    )
    self.timestamp=0

    def process(self,frame):
      rgb=cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
      )
      image=mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
      )

      self.timestamp += 33
      result=self.detector.detect_for_video(
        image,
        self.timestamp
      )

      return result
    def close(self):
      self.detector.close()
