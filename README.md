# 🎹 Gesture Piano

A real-time computer-vision piano controlled entirely through **hand gestures**.

Gesture Piano uses a webcam to track both hands with **MediaPipe**, interprets finger gestures as musical input, and plays **real recorded Steinway piano samples** in real time.

No physical keyboard required.

---

## ✨ Features

- 🎥 Real-time webcam hand tracking
- ✋ Two-hand gesture control
- 🎹 Real acoustic piano samples
- 🎼 Right hand controls melody
- 🎵 Left hand controls chords
- 🎚️ Fixed middle octave for a simple playing experience
- 🔊 Polyphonic audio playback
- 🎙️ Melody and chord recording
- ▶️ Recorded performance playback
- 🖥️ OpenCV-based piano interface
- ⚡ Low-latency gesture recognition
- 🛑 Anti-retriggering system prevents notes from being repeatedly triggered
- 🎧 Smooth note release to reduce clicks and pops
- 🍎 Optimized for Apple Silicon macOS

---

## 🧠 How It Works

The system consists of four main stages:

```text
             Webcam
                │
                ▼
       ┌─────────────────┐
       │  MediaPipe Hand │
       │    Landmarker   │
       └────────┬────────┘
                │
                ▼
       Hand Landmark Data
                │
                ▼
       ┌─────────────────┐
       │ Gesture Detector│
       └────────┬────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   Right Hand       Left Hand
     Melody           Chords
        │                │
        └───────┬────────┘
                ▼
       ┌─────────────────┐
       │   Audio Engine  │
       │ Real Piano WAVs │
       └────────┬────────┘
                │
                ▼
             Speakers
```

---

## 🎹 Gesture Controls

### Right Hand — Melody

The right hand controls individual piano notes.

| Gesture | Action |
|---|---|
| ☝️ Index finger | Play selected piano note |
| ✌️ Two fingers | Play selected piano note |
| 🤟 Three fingers | Play selected piano note |
| ✋ Open hand | Play selected piano note |
| ✊ Fist | Release current note |

The horizontal position of the fingertip determines which piano key is selected.

The melody is locked to the **normal middle octave (C4–B4)**.

There is no octave switching.

---

### Left Hand — Chords

The left hand controls chord accompaniment.

| Gesture | Chord |
|---|---|
| ☝️ Index | Major |
| ✌️ Two fingers | Minor |
| 🤟 Three fingers | Dominant 7th |
| ✋ Open hand | Suspended 4th |
| ✊ Fist | Release chord |

The horizontal position of the left hand determines the chord root.

For example:

```text
Index + C → C Major
Two fingers + A → A Minor
Three fingers + G → G7
Open hand + F → F Sus4
```

---

## 🔊 Real Piano Audio

The project uses **real recorded Steinway & Sons Model B Concert Grand Piano samples** from the:

**Versilian Community Sample Library (VCSL)**

The samples are recorded acoustic piano strikes rather than synthesized sine waves.

### Sample characteristics

- Steinway & Sons Model B Concert Grand
- Concert grand piano
- Close-mic recording
- 24-bit PCM WAV
- Stereo
- 44.1 kHz
- Multiple recorded notes
- CC0 1.0 licensed sample source

The samples are stored locally in:

```text
piano_samples/
```

See:

```text
piano_samples/LICENSE.txt
piano_samples/SOURCE_INFO.txt
```

for licensing and source information.

---

## 🛡️ Anti-Retriggering

Hand tracking produces many frames per second. Without protection, holding a finger over one key could cause the same sample to be triggered repeatedly.

Gesture Piano prevents this using:

- Active-note tracking
- Note-change detection
- Temporal debounce
- Smooth note transitions
- Controlled voice release

Instead of:

```text
C C C C C C C C C C ...
```

while holding one key, the system behaves like:

```text
C ───────────────────────
```

until the finger moves to another key.

The same principle is applied to chords so that a held chord isn't restarted every frame.

---

## 🖥️ Interface

The application displays a virtual piano using OpenCV.

The interface provides visual feedback for:

- Detected hands
- Finger landmarks
- Selected piano key
- Active melody note
- Active chord
- Gesture state
- Recording/playback state

The visual piano remains a simple **7-key C–B layout** while the audio engine handles the corresponding sampled piano playback.

---

## 🎙️ Recording

The built-in recorder can capture:

- Melody notes
- Chords
- Timing information

Recorded performances can then be played back through the same audio engine.

### Keyboard controls

| Key | Action |
|---|---|
| `R` | Start recording |
| `S` | Stop recording |
| `Q` | Quit |

---

## 📁 Project Structure

```text
gesture-piano/
│
├── main.py
├── config.py
├── hand_tracker.py
├── gesture_detector.py
├── piano.py
├── audio_engine.py
├── recorder.py
├── requirements.txt
├── README.md
│
├── models/
│   └── hand_landmarker.task
│
└── piano_samples/
    ├── *.wav
    ├── LICENSE.txt
    └── SOURCE_INFO.txt
```

### File descriptions

#### `main.py`

Main application loop.

Handles:

- Webcam capture
- Hand tracking
- Gesture processing
- Melody control
- Chord control
- Recording
- OpenCV UI

#### `hand_tracker.py`

Handles MediaPipe Hand Landmarker initialization and hand landmark detection.

#### `gesture_detector.py`

Converts hand landmark positions into gestures such as:

```text
INDEX
TWO
THREE
OPEN
THUMB
FIST
UNKNOWN
```

#### `piano.py`

Handles the visual piano keyboard and maps hand positions to piano keys.

#### `audio_engine.py`

Handles real-time piano sample playback.

Responsibilities include:

- WAV loading
- Sample caching
- Sample selection
- Pitch shifting
- Polyphonic playback
- Note release
- Audio streaming
- Master volume
- Anti-click processing

#### `recorder.py`

Records and plays back musical events.

#### `config.py`

Contains project configuration such as:

- Camera resolution
- Audio sample rate
- Piano configuration
- Note frequencies
- Chord intervals
- Confidence thresholds
- Piano UI dimensions

---

## ⚙️ Requirements

- Python 3.11
- macOS
- Apple Silicon recommended
- Webcam
- Speakers or headphones

Python packages:

```text
mediapipe
opencv-python
numpy
sounddevice
```

---

## 🚀 Installation

### 1. Clone or download the project

```bash
git clone <repository-url>
cd gesture-piano
```

### 2. Create a virtual environment

Python 3.11 is recommended for compatibility with the MediaPipe native stack.

```bash
python3.11 -m venv .venv
```

### 3. Activate the environment

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify the hand model

Make sure the following file exists:

```text
models/hand_landmarker.task
```

### 6. Make sure piano samples are present

The following directory should exist:

```text
piano_samples/
```

with the provided WAV samples and license information.

---

## ▶️ Running the Application

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then:

```bash
python3 main.py
```

A webcam window should open.

Position your hands in front of the camera and use the gestures to play.

---

## 🎮 Recommended Playing Setup

For the best experience:

1. Place the webcam directly in front of you.
2. Keep both hands visible.
3. Use good lighting.
4. Keep the background reasonably uncluttered.
5. Position the right hand above the virtual piano.
6. Use the left hand for chord accompaniment.
7. Use headphones or speakers with low latency.

---

## 🔧 Troubleshooting

### Camera does not open

Make sure Terminal/your Python environment has permission to access the camera.

On macOS:

```text
System Settings
→ Privacy & Security
→ Camera
```

Enable camera access for the application being used to run Python.

---

### No audio

Check that macOS has an available output device and verify that SoundDevice can access it.

You can inspect available audio devices with:

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

---

### Piano sounds like repeated hammering

This can happen when the same gesture triggers the same note repeatedly across consecutive camera frames.

The project contains anti-retriggering logic that prevents:

```text
note_on()
note_on()
note_on()
note_on()
```

for the same held key.

If the issue returns, check the active-note state and audio voice management in:

```text
main.py
audio_engine.py
```

---

### MediaPipe warnings appear

Messages such as:

```text
Feedback manager requires a model with a single signature inference.
```

or:

```text
Using NORM_RECT without IMAGE_DIMENSIONS...
```

are MediaPipe warnings and do not necessarily indicate an application failure.

---

## 🎼 Current Musical Range

The melody system intentionally uses a fixed octave:

```text
C4  D4  E4  F4  G4  A4  B4
```

Octave switching is intentionally disabled to keep the instrument simple and natural to play.

The chord system can use the required notes around the normal playing range.

---

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| OpenCV | Webcam + UI |
| MediaPipe Tasks | Hand tracking |
| NumPy | Audio/sample processing |
| SoundDevice | Real-time audio output |
| WAV/PCM | Piano samples |
| VCSL | Steinway piano recordings |

---

## 🔐 Privacy

Gesture Piano processes webcam frames locally.

The application does not require uploading camera footage to a remote server for hand tracking.

---

## 📜 Sample License

The piano samples are sourced from the **Versilian Community Sample Library (VCSL)**.

Refer to:

```text
piano_samples/LICENSE.txt
piano_samples/SOURCE_INFO.txt
```

for the exact license and attribution information included with the project.

---

## 🚧 Future Improvements

Potential future enhancements include:

- More accurate finger-to-key mapping
- Velocity-sensitive playing
- Hand-distance based dynamics
- Sustain pedal gesture
- More piano octaves
- Additional instruments
- Better chord voicings
- MIDI output
- Performance visualization
- Improved recording timeline
- Saved performance files
- Metronome
- Tempo control
- More advanced gesture recognition

---

## 👨‍💻 Project

**Gesture Piano**

A computer-vision powered virtual piano that turns natural hand gestures into real-time acoustic piano performance.

**Computer Vision × Gesture Recognition × Digital Audio × Music**