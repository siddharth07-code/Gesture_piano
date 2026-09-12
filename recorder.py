import time


class Recorder:
    def __init__(self):
        self.recording = False
        self.events = []
        self.start_time = None

    def start(self):
        self.recording = True
        self.events = []
        self.start_time = time.time()

    def stop(self):
        self.recording = False

    def record(self, event_type, notes):
        if not self.recording:
            return

        current_time = time.time() - self.start_time

        self.events.append({
            "time": current_time,
            "type": event_type,
            "notes": notes
        })

    def add_event(self, event_type, notes):
        self.record(event_type, notes)

    def clear(self):
        self.events = []

    def get_events(self):
        return self.events

    def is_recording(self):
        return self.recording