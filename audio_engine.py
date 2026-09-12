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
    
    def play_chord(
        self,
        notes,
        octave=4
    ):
        for note in notes:
            self.note_on(
                note,
                octave
            )
    def stop_all(self):
        with self.lock:
             self.active_notes.clear()

    def audio_callback(
        self,
        outdata,
        frames,
        time,
        status
    ):
        output=np.zeroes(
            frames,
            dtype=np.float32
        )        
        with self.lock:

             for key,data in self.active_notes.items():

                 frequency=data["frequency"]
                 phase=data["phase"]

                 t=(
                    np.arrange(frames)
                    + phase
                 )

                 wave=np.sin(
                    2*np.pi*
                    frequency*
                    t/
                    SAMPLE_RATE
                 )

                 wave += (
                    0.30*
                    np.sin(
                        2*np.pi*
                        frequency*
                        2*
                        t/
                        SAMPLE_RATE
                    )
                 )

                 wave += (
                    0.12*
                    np.sin(
                        2*np.pi*
                        frequency*
                        3*
                        t/
                        SAMPLE_RATE
                    )
                 )

                 output += (
                    wave*0.12
                 )

                 data["phase"]=(
                    phase+frames
                 ) % SAMPLE_RATE

        output =np.clip(
            output,
            -1,
            1
        )       
        outdata[:,0]=output

    def close(self):
         self.stop_all()

         self.stream.stop()
         self.stream.close()
                
