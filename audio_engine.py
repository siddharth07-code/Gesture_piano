import threading

import numpy as np
import sounddevice as sd

from config import(
    SAMPLE_RATE,
    AUDIO_BLOCK_SIZE,
    NOTE_FREQUENCIES
)

class AudioEngine:
    def __init__(self):
        self.lock=threading.Lock()
        self.active_notes={}

        self.stream=sd.OutputStream(
            samplerate=SAMPLE_RATE,
            blocksize=AUDIO_BLOCK_SIZE,
            channels=1,
            dtype="float32",
            callback=self.audio_callback
        )

        self.stream.start()

    def note_on(
        self,
        note,
        octave=4
    ):
        key=f"{note}{octave}"
        frequency=(
            NOTE_FREQUENCIES[note]
            *(2 ** (octave-4))
        )

        with self.lock:
            if key not in self.active_notes:
                self.active_notes[key]={
                    "frequency":frequency,
                    "phase":0.0,
                    "amplitude":0.0
                } 
    def note_off(
        self,
        note,
        octave=4
    ): 
        
        key=f"{note}{octave}"
        with self.lock:
            if key in self.active_notes:
                del self.active_notes[key]
    
                
