CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

MODEL_PATH="models/hand_landmarker.task"

SAMPLE_RATE=44100
AUDIO_BLOCK_SIZE=512

NOTES=[
  "C",
  "D",
  "E",
  "F",
  "G",
  "A",
  "B"
]

NOTE_FREQUENCIES={
    "C": 261.63,
    "D": 293.66,
    "E": 329.63,
    "F": 349.23,
    "G": 392.00,
    "A": 440.00,
    "B": 493.88
}

CHORD_INTERVALS = {
    "MAJOR": [0, 4, 7],
    "MINOR": [0, 3, 7],
    "7TH": [0, 4, 7, 10],
    "SUS4": [0, 5, 7]
}

NOTE_INDEX = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11
}

PIANO_TOP=500
PIANO_BOTTOM=700

MIN_DETECTION_CONFIDENCE=0.5
MIN_PRESENCE_CONFIDENCE=0.5
MIN_TRACKING_CONFIDENCE=0.5

POSITION_SMOOTHING=0.35