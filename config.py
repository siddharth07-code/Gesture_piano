CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

MODEL_PATH="models/hand_landmarker.task"

SAMPLE_RATE=44100
AUDIO_BLOCK_SIZE=512

AUDIO_CHANNELS=2
PIANO_SAMPLES_DIR="piano_samples"

NOTES=[
  "C",
  "D",
  "E",
  "F",
  "G",
  "A",
  "B"
]

CHROMATIC_NOTES=[
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

NOTE_FREQUENCIES={
    "C": 261.63,
    "C#": 277.18,
    "D": 293.66,
    "D#": 311.13,
    "E": 329.63,
    "F": 349.23,
    "F#": 369.99,
    "G": 392.00,
    "G#": 415.30,
    "A": 440.00,
    "A#": 466.16,
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
    "C#": 1,
    "D": 2,
    "D#": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "G#": 8,
    "A": 9,
    "A#": 10,
    "B": 11
}

PIANO_TOP=500
PIANO_BOTTOM=700

MIN_DETECTION_CONFIDENCE=0.5
MIN_PRESENCE_CONFIDENCE=0.5
MIN_TRACKING_CONFIDENCE=0.5

POSITION_SMOOTHING=0.35