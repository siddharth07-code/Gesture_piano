import cv2


class Piano:
    def __init__(self, width, top=500, bottom=700):
        self.width = width
        self.top = top
        self.bottom = bottom

        self.notes = ["C", "D", "E", "F", "G", "A", "B"]

        self.active_note = None

    def set_active_note(self, note):
        self.active_note = note

    def clear_active_note(self):
        self.active_note = None

    def draw(self, frame, active_note=None):
        if active_note is not None:
            self.active_note = active_note

        key_width = self.width // len(self.notes)

        for i, note in enumerate(self.notes):
            x1 = i * key_width
            x2 = (i + 1) * key_width

            # Highlight active key
            if note == self.active_note:
                color = (0, 255, 0)
            else:
                color = (255, 255, 255)

            cv2.rectangle(
                frame,
                (x1, self.top),
                (x2, self.bottom),
                color,
                -1
            )

            cv2.rectangle(
                frame,
                (x1, self.top),
                (x2, self.bottom),
                (0, 0, 0),
                2
            )

            # Note name
            text_x = x1 + key_width // 2 - 10
            text_y = self.bottom - 30

            cv2.putText(
                frame,
                note,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 0),
                2
            )

    def get_note_from_x(self, x):
        key_width = self.width / len(self.notes)

        index = int(x / key_width)

        if 0 <= index < len(self.notes):
            return self.notes[index]

        return None

    def get_key(self, x):
        return self.get_note_from_x(x)

    def draw_pointer(self, frame, x, y):
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
        cv2.circle(frame, (x, y), 12, (255, 255, 255), 2)