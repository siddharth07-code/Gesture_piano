import os
import glob
import re
import wave
import threading
import numpy as np
import sounddevice as sd


class AudioEngine:
    """
    High-performance sampled acoustic piano audio engine.
    Uses real recorded piano samples from the Creative Commons 0 (CC0)
    Versilian Community Sample Library (VCSL) Steinway Model B concert grand.
    
    Features:
    - Real acoustic piano attack, hammer transient, and natural decay.
    - Automatic sample discovery mapping filenames to normalized (note, octave).
    - Intelligent whole-tone pitch-shifting & resampling for missing chromatic notes.
    - Low-latency memory caching (samples loaded into memory once; zero disk I/O during playback).
    - Polyphonic multi-note playback with independent voice tracking.
    - Smooth anti-click damper release envelope on note_off and stop_all.
    - Soft-knee limiter (tanh) with calibrated headroom to prevent clipping on chords.
    - Non-blocking audio output stream via SoundDevice callback.
    """

    CHROMATIC_NOTES = [
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
    ]

    ENHARMONIC_MAP = {
        "DB": "C#",
        "EB": "D#",
        "GB": "F#",
        "AB": "G#",
        "BB": "A#",
        "B#": "C",
        "E#": "F",
        "CB": "B",
        "FB": "E"
    }

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

    def __init__(
        self,
        sample_rate=44100,
        block_size=512,
        channels=2,
        samples_dir=None,
        master_volume=0.85
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.master_volume = master_volume

        # Locate piano_samples directory
        if samples_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.samples_dir = os.path.join(base_dir, "piano_samples")
        else:
            self.samples_dir = samples_dir

        self.native_samples = {}    # (note, octave) -> file path
        self.sample_cache = {}      # (note, octave) -> np.ndarray float32 (N, channels)
        self.active_voices = []     # List of active voice dicts
        self.lock = threading.Lock()

        # Step 1: Discover all sample files in the library
        self._discover_sample_files()

        # Step 2: Pre-cache standard playing octaves for zero-latency note triggering
        self._precache_octaves([3, 4, 5, 6])

        # Step 3: Initialize and start non-blocking SoundDevice output stream
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self.stream.start()

    # -------------------------------------------------------------------------
    # Sample Discovery Layer
    # -------------------------------------------------------------------------

    def _discover_sample_files(self):
        """
        Scan piano_samples/ directory and map arbitrary filenames to normalized
        (note, octave) identifiers.
        
        Handles filenames like:
          - JHPiano_Sus_Close_C4_vl3_rr1.wav
          - JHPiano_Sus_Close_F#3_vl3_rr1.wav
          - C4.wav, Db4.wav, F#5.wav
          - Upright1_Sus_G4_vl2_rr1.wav
        """
        if not os.path.isdir(self.samples_dir):
            print(f"[AudioEngine] Warning: Sample directory '{self.samples_dir}' not found.")
            return

        pattern = re.compile(r"(?:^|[\W_])([A-Ga-g][#b]?)(-?\d+)(?:[\W_]|$)")
        wav_files = glob.glob(os.path.join(self.samples_dir, "*.wav")) + \
                    glob.glob(os.path.join(self.samples_dir, "**", "*.wav"), recursive=True)

        for filepath in wav_files:
            filename = os.path.basename(filepath)
            match = pattern.search(filename)
            if match:
                raw_note = match.group(1).upper()
                octave = int(match.group(2))
                normalized_note = self.ENHARMONIC_MAP.get(raw_note, raw_note)
                if normalized_note in self.CHROMATIC_NOTES:
                    key = (normalized_note, octave)
                    # Prefer close-mic or higher velocity if duplicates exist
                    if key not in self.native_samples or "Close" in filename:
                        self.native_samples[key] = filepath

    # -------------------------------------------------------------------------
    # Note Parsing & MIDI Helpers
    # -------------------------------------------------------------------------

    def _normalize_note_octave(self, note, octave=None):
        """
        Normalize note representation into (note_name, octave).
        Handles:
          - ("C", 4)
          - ("C4", None)
          - ("Db4", None) -> ("C#", 4)
          - (261.63, None) -> ("C", 4)
        """
        if isinstance(note, (int, float)):
            # Frequency input -> convert to nearest MIDI note
            freq = float(note)
            if freq <= 0:
                return ("C", 4)
            midi = int(round(69 + 12 * np.log2(freq / 440.0)))
            octave = (midi // 12) - 1
            note_name = self.CHROMATIC_NOTES[midi % 12]
            return (note_name, octave)

        note_str = str(note).strip()

        # Check if octave was embedded in note_str (e.g. "C4", "F#5", "Db3")
        m = re.match(r"^([A-Ga-g][#b]?)(-?\d+)$", note_str)
        if m:
            raw_note = m.group(1).upper()
            octave = int(m.group(2))
            normalized_note = self.ENHARMONIC_MAP.get(raw_note, raw_note)
            return (normalized_note, octave)

        # Standard (note, octave)
        raw_note = note_str.upper()
        normalized_note = self.ENHARMONIC_MAP.get(raw_note, raw_note)
        if octave is None:
            octave = 4
        return (normalized_note, int(octave))

    def _midi_number(self, note, octave):
        """Calculate MIDI note number for a given note and octave."""
        return 12 * (octave + 1) + self.CHROMATIC_NOTES.index(note)

    # -------------------------------------------------------------------------
    # WAV Audio Loader & Resampling Engine
    # -------------------------------------------------------------------------

    def _load_wav_file(self, filepath):
        """
        Read uncompressed PCM/IEEE WAV audio file into a float32 numpy array.
        Supports 16-bit, 24-bit, 32-bit int, and 32-bit float formats.
        Converts mono/stereo to self.channels and resamples to self.sample_rate if needed.
        """
        with wave.open(filepath, "rb") as wf:
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            n_channels = wf.getnnchannels() if hasattr(wf, 'getnnchannels') else wf.getnchannels()
            framerate = wf.getframerate()
            raw_bytes = wf.readframes(n_frames)

            # Decode bytes based on bit-depth
            if sampwidth == 2:
                # 16-bit signed PCM
                samples = np.frombuffer(raw_bytes, dtype="<i2").astype(np.float32) / 32768.0
            elif sampwidth == 3:
                # 24-bit signed PCM: unpack 3 bytes to 4 bytes with sign extension
                a = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
                sign = np.where(a[:, 2] & 0x80, 255, 0).astype(np.uint8)
                samples = np.column_stack((a, sign)).view("<i4").flatten().astype(np.float32) / (2**23)
            elif sampwidth == 4:
                # 32-bit float or 32-bit int PCM
                try:
                    samples = np.frombuffer(raw_bytes, dtype="<f4").copy()
                except Exception:
                    samples = np.frombuffer(raw_bytes, dtype="<i4").astype(np.float32) / (2**31)
            else:
                samples = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

            # Channel layout: ensure shape (N, channels)
            if n_channels == 1:
                if self.channels == 2:
                    audio_data = np.column_stack((samples, samples))
                else:
                    audio_data = samples.reshape(-1, 1)
            else:
                samples = samples.reshape(-1, n_channels)
                if self.channels == 1:
                    audio_data = samples.mean(axis=1, keepdims=True)
                else:
                    audio_data = samples[:, :self.channels]

            # Sample rate conversion if required
            if framerate != self.sample_rate and framerate > 0:
                ratio = self.sample_rate / framerate
                n_out = int(len(audio_data) * ratio)
                x_in = np.arange(len(audio_data))
                x_out = np.linspace(0, len(audio_data) - 1, n_out)
                resampled = np.empty((n_out, self.channels), dtype=np.float32)
                for ch in range(self.channels):
                    resampled[:, ch] = np.interp(x_out, x_in, audio_data[:, ch])
                audio_data = resampled

            return audio_data

    def _get_or_render_sample(self, note, octave):
        """
        Retrieve audio sample from memory cache.
        If not cached:
          - If native: load directly from disk.
          - If missing: find closest native note (within 1 semitone) and pitch-shift/resample.
        Caches result in self.sample_cache for instant future access.
        """
        key = (note, octave)
        if key in self.sample_cache:
            return self.sample_cache[key]

        if key in self.native_samples:
            sample_data = self._load_wav_file(self.native_samples[key])
            self.sample_cache[key] = sample_data
            return sample_data

        if not self.native_samples:
            # Fallback if no samples found at all
            t = np.linspace(0, 2.0, int(self.sample_rate * 2.0), endpoint=False)
            freq = self.NOTE_FREQUENCIES.get(note, 440.0) * (2 ** (octave - 4))
            wave_data = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.0) * 0.3).astype(np.float32)
            fallback = np.column_stack((wave_data, wave_data)) if self.channels == 2 else wave_data.reshape(-1, 1)
            self.sample_cache[key] = fallback
            return fallback

        # Intelligent Pitch Handling: find closest native note
        target_midi = self._midi_number(note, octave)
        best_native = min(
            self.native_samples.keys(),
            key=lambda k: (abs(self._midi_number(*k) - target_midi), abs(k[1] - octave))
        )
        src_midi = self._midi_number(*best_native)
        semitones = target_midi - src_midi

        # Load native source sample
        source_sample = self._get_or_render_sample(*best_native)

        # Resample for pitch shift: ratio > 1 means pitch up (shorter length)
        pitch_ratio = 2.0 ** (semitones / 12.0)
        n_in = len(source_sample)
        n_out = int(n_in / pitch_ratio)
        x_in = np.arange(n_in)
        x_out = np.arange(n_out) * pitch_ratio

        resampled = np.empty((n_out, self.channels), dtype=np.float32)
        for ch in range(self.channels):
            resampled[:, ch] = np.interp(x_out, x_in, source_sample[:, ch])

        self.sample_cache[key] = resampled
        return resampled

    def _precache_octaves(self, octaves):
        """Pre-cache common octaves into memory so live gesture triggers have 0ms latency."""
        for octv in octaves:
            for note in self.CHROMATIC_NOTES:
                self._get_or_render_sample(note, octv)

    # -------------------------------------------------------------------------
    # Public Note & Chord Trigger Interface
    # -------------------------------------------------------------------------

    def note_on(self, note, octave=4, velocity=1.0):
        """
        Play a real sampled acoustic piano note.
        
        Examples:
            audio.note_on("C", 4)
            audio.note_on("F#", 5)
            audio.note_on("Eb", 3)
        """
        normalized_note, normalized_octave = self._normalize_note_octave(note, octave)
        sample = self._get_or_render_sample(normalized_note, normalized_octave)

        note_id = f"{normalized_note}{normalized_octave}"

        # 80ms felt damper release time
        release_frames = int(0.08 * self.sample_rate)

        new_voice = {
            "note_id": note_id,
            "sample": sample,
            "pos": 0,
            "velocity": max(0.1, min(1.0, float(velocity))),
            "releasing": False,
            "release_remaining": release_frames,
            "release_total": release_frames,
        }

        with self.lock:
            # If the same key is re-struck, quickly fade out the older voice to avoid build-up
            for voice in self.active_voices:
                if voice["note_id"] == note_id and not voice["releasing"]:
                    voice["releasing"] = True
                    fade_frames = int(0.03 * self.sample_rate)
                    voice["release_remaining"] = fade_frames
                    voice["release_total"] = fade_frames

            self.active_voices.append(new_voice)

            # Limit total concurrent voices to 32 to conserve CPU
            if len(self.active_voices) > 32:
                oldest = self.active_voices[0]
                if not oldest["releasing"]:
                    oldest["releasing"] = True
                    fade_frames = int(0.02 * self.sample_rate)
                    oldest["release_remaining"] = fade_frames
                    oldest["release_total"] = fade_frames

    def note_off(self, note, octave=4):
        """
        Release a note smoothly with natural piano felt damper damping.
        Avoids clicks or pops.
        """
        normalized_note, normalized_octave = self._normalize_note_octave(note, octave)
        note_id = f"{normalized_note}{normalized_octave}"

        with self.lock:
            for voice in self.active_voices:
                if voice["note_id"] == note_id and not voice["releasing"]:
                    release_frames = int(0.08 * self.sample_rate)
                    voice["release_remaining"] = release_frames
                    voice["release_total"] = release_frames
                    voice["releasing"] = True

    def play_chord(self, notes):
        """
        Play multiple notes simultaneously as an acoustic piano chord.
        
        Accepts:
            - List of tuples: [("C", 4), ("E", 4), ("G", 4)]
            - List of note strings: ["C4", "E4", "G4"] or ["C", "E", "G"]
            - List of frequencies: [261.63, 329.63, 392.00]
        """
        self.stop_all()

        for item in notes:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                n, o = item[0], item[1]
                self.note_on(n, o)
            elif isinstance(item, str):
                self.note_on(item)
            elif isinstance(item, (int, float)):
                self.note_on(item)

    def stop_all(self):
        """Smoothly release all currently sounding notes over 40ms."""
        fade_frames = int(0.04 * self.sample_rate)
        with self.lock:
            for voice in self.active_voices:
                if not voice["releasing"]:
                    voice["releasing"] = True
                    voice["release_remaining"] = fade_frames
                    voice["release_total"] = fade_frames

    # -------------------------------------------------------------------------
    # Audio Output Stream Callback (Real-time Polyphonic Mixer)
    # -------------------------------------------------------------------------

    def _callback(self, outdata, frames, time_info, status):
        """SoundDevice real-time output stream callback."""
        buffer = np.zeros((frames, self.channels), dtype=np.float32)

        with self.lock:
            alive_voices = []

            for voice in self.active_voices:
                sample_data = voice["sample"]
                pos = voice["pos"]
                remaining_sample = len(sample_data) - pos

                if remaining_sample <= 0:
                    continue

                chunk_len = min(frames, remaining_sample)
                chunk = sample_data[pos : pos + chunk_len]

                if voice["releasing"]:
                    rel_total = max(1, voice["release_total"])
                    start_gain = max(0.0, voice["release_remaining"] / rel_total)
                    voice["release_remaining"] -= chunk_len
                    end_gain = max(0.0, voice["release_remaining"] / rel_total)

                    ramp = np.linspace(start_gain, end_gain, chunk_len, endpoint=False, dtype=np.float32)
                    chunk = chunk * ramp[:, np.newaxis]

                # Mix into buffer with note velocity
                buffer[:chunk_len] += chunk * voice["velocity"]
                voice["pos"] += chunk_len

                # Keep voice alive if not finished and not fully damped
                if voice["pos"] < len(sample_data):
                    if not (voice["releasing"] and voice["release_remaining"] <= 0):
                        alive_voices.append(voice)

            self.active_voices = alive_voices

        # Apply master volume and soft-knee saturation limiter to prevent digital clipping
        buffer *= self.master_volume
        outdata[:] = np.tanh(buffer)

    def close(self):
        """Stop and close the audio stream."""
        self.stop_all()
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass