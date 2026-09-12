import threading
import numpy as np
import sounddevice as sd


class AudioEngine:
    NOTE_FREQUENCIES = {
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
        "B": 493.88,
    }

    def __init__(self, sample_rate=44100, block_size=512):
        self.sample_rate = sample_rate
        self.block_size = block_size

        self.active_notes = {}
        self.lock = threading.Lock()

        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )

        self.stream.start()

    def _note_frequency(self, note, octave):
        base_frequency = self.NOTE_FREQUENCIES[note]

        # C4 = base frequency
        return base_frequency * (2 ** (octave - 4))

    def note_on(self, note, octave=4):
        """
        Play a note.

        Example:
            note_on("C", 4)
            note_on("E", 4)
            note_on("G", 5)
        """

        frequency = self._note_frequency(note, octave)

        note_id = f"{note}{octave}"

        with self.lock:
            self.active_notes[note_id] = {
                "frequency": frequency,
                "age": 0,
            }

    def note_off(self, note, octave=4):
        note_id = f"{note}{octave}"

        with self.lock:
            self.active_notes.pop(note_id, None)

    def play_chord(self, frequencies):
        """
        Play multiple frequencies simultaneously.
        """

        with self.lock:
            self.active_notes.clear()

            for i, frequency in enumerate(frequencies):
                self.active_notes[f"chord_{i}"] = {
                    "frequency": float(frequency),
                    "age": 0,
                }

    def stop_all(self):
        with self.lock:
            self.active_notes.clear()

    def _callback(self, outdata, frames, time, status):
        audio = np.zeros(frames, dtype=np.float32)

        with self.lock:
            notes = list(self.active_notes.items())

        for note_id, data in notes:

            frequency = data["frequency"]
            age = data["age"]

            t = (
                np.arange(frames) + age
            ) / self.sample_rate

            # ---------------------------------
            # PIANO HARMONICS
            # ---------------------------------

            fundamental = np.sin(
                2 * np.pi * frequency * t
            )

            harmonic_2 = np.sin(
                2 * np.pi * frequency * 2 * t
            )

            harmonic_3 = np.sin(
                2 * np.pi * frequency * 3 * t
            )

            harmonic_4 = np.sin(
                2 * np.pi * frequency * 4 * t
            )

            harmonic_5 = np.sin(
                2 * np.pi * frequency * 5 * t
            )

            harmonic_6 = np.sin(
                2 * np.pi * frequency * 6 * t
            )

            signal = (
                1.00 * fundamental
                + 0.45 * harmonic_2
                + 0.22 * harmonic_3
                + 0.12 * harmonic_4
                + 0.07 * harmonic_5
                + 0.04 * harmonic_6
            )

            # ---------------------------------
            # PIANO ATTACK
            # ---------------------------------

            attack = 1.0 - np.exp(-t * 180)

            # ---------------------------------
            # NATURAL DECAY
            # ---------------------------------

            decay = (
                0.75 * np.exp(-t * 1.4)
                + 0.25 * np.exp(-t * 5.0)
            )

            envelope = attack * decay

            # ---------------------------------
            # HAMMER TRANSIENT
            # ---------------------------------

            hammer = (
                np.sin(2 * np.pi * frequency * 7 * t)
                * np.exp(-t * 35)
                * 0.15
            )

            signal = (
                signal * envelope
                + hammer
            )

            # ---------------------------------
            # NOTE VOLUME
            # ---------------------------------

            signal *= 0.13

            audio += signal.astype(np.float32)

            with self.lock:
                if note_id in self.active_notes:
                    self.active_notes[note_id]["age"] += frames

        # ---------------------------------
        # SOFT LIMITER
        # ---------------------------------

        audio = np.tanh(audio * 1.5)

        outdata[:, 0] = audio

    def close(self):
        self.stop_all()

        self.stream.stop()
        self.stream.close()