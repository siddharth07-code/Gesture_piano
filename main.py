# main.py

import cv2
import time

from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    MODEL_PATH,
    NOTES,
    CHORD_INTERVALS,
    NOTE_INDEX
)

from hand_tracker import HandTracker

from gesture_detector import (
    get_fingers,
    get_gesture,
    chord_type_from_gesture
)

from piano import Piano

from audio_engine import AudioEngine

from recorder import Recorder


FIXED_OCTAVE = 4


def get_root_chord(
    root,
    chord_type,
    octave=FIXED_OCTAVE
):

    root_index = NOTE_INDEX[root]

    intervals = CHORD_INTERVALS[
        chord_type
    ]

    result = []

    note_names = list(
        NOTE_INDEX.keys()
    )

    for interval in intervals:

        target = (
            root_index +
            interval
        )

        octave_offset = (
            target // 12
        )

        target_note_index = (
            target % 12
        )

        # Find note
        for name, index in NOTE_INDEX.items():

            if index == target_note_index:

                result.append(
                    (
                        name,
                        octave +
                        octave_offset
                    )
                )

                break

    return result


def draw_landmarks(
    frame,
    landmarks
):

    connections = [

        # Thumb
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),

        # Index
        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),

        # Middle
        (5, 9),
        (9, 10),
        (10, 11),
        (11, 12),

        # Ring
        (9, 13),
        (13, 14),
        (14, 15),
        (15, 16),

        # Pinky
        (13, 17),
        (17, 18),
        (18, 19),
        (19, 20),

        # Palm
        (0, 17)
    ]

    h, w = frame.shape[:2]

    points = []

    for landmark in landmarks:

        x = int(
            landmark.x * w
        )

        y = int(
            landmark.y * h
        )

        points.append(
            (x, y)
        )

        cv2.circle(
            frame,
            (x, y),
            4,
            (0, 255, 0),
            -1
        )

    for a, b in connections:

        cv2.line(
            frame,
            points[a],
            points[b],
            (255, 255, 255),
            2
        )


def main():

    # -------------------------
    # Camera
    # -------------------------

    cap = cv2.VideoCapture(0)

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    if not cap.isOpened():

        print(
            "Could not open camera."
        )

        return

    # -------------------------
    # Systems
    # -------------------------

    tracker = HandTracker(
        MODEL_PATH
    )

    audio = AudioEngine()

    piano = Piano(
        CAMERA_WIDTH
    )

    recorder = Recorder()

    # -------------------------
    # State
    # -------------------------

    # Right hand melody state
    current_note = None
    pending_note = None
    pending_note_frames = 0
    right_hand_absent_frames = 0

    # Left hand chord state
    current_chord = None
    current_chord_root = None
    current_chord_notes = []
    pending_chord = None
    pending_chord_frames = 0
    left_hand_absent_frames = 0

    # Debounce threshold (consecutive frames needed to confirm a key/chord change)
    DEBOUNCE_FRAMES = 2

    # -------------------------
    # Main loop
    # -------------------------

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(
            frame,
            1
        )

        result = tracker.process(
            frame
        )

        active_note = None
        detected_gesture = "NONE"

        left_hand = None
        right_hand = None

        # -------------------------
        # Identify hands
        # -------------------------

        if result.hand_landmarks:

            for i, landmarks in enumerate(
                result.hand_landmarks
            ):

                draw_landmarks(
                    frame,
                    landmarks
                )

                fingers = get_fingers(
                    landmarks
                )

                gesture = get_gesture(
                    fingers
                )

                # Use center X to separate
                # left and right sides
                wrist_x = landmarks[0].x

                if wrist_x < 0.5:

                    left_hand = (
                        landmarks,
                        gesture
                    )

                else:

                    right_hand = (
                        landmarks,
                        gesture
                    )

        # =================================================
        # RIGHT HAND → MELODY
        # =================================================

        if right_hand:

            landmarks, gesture = right_hand

            detected_gesture = gesture

            index_tip = landmarks[8]

            x = int(
                index_tip.x *
                CAMERA_WIDTH
            )

            y = int(
                index_tip.y *
                CAMERA_HEIGHT
            )

            piano.draw_pointer(
                frame,
                x,
                y
            )

            # -------------------------
            # Note
            # -------------------------

            if gesture in (
                "INDEX",
                "TWO"
            ):
                right_hand_absent_frames = 0

                note = piano.get_key(
                    x
                )

                if note:
                    active_note = note

                    if current_note is None:
                        # No previously active melody note -> trigger immediately
                        audio.note_on(
                            note,
                            FIXED_OCTAVE
                        )

                        recorder.add_event(
                            "NOTE",
                            [
                                (
                                    note,
                                    FIXED_OCTAVE
                                )
                            ]
                        )

                        current_note = note
                        pending_note = None
                        pending_note_frames = 0

                    elif note == current_note:
                        # Still pointing at the same piano key -> keep existing voice playing
                        # Do not call note_on() again
                        pending_note = None
                        pending_note_frames = 0

                    else:
                        # Detected piano key changed -> debounce before switching
                        if note == pending_note:
                            pending_note_frames += 1
                            if pending_note_frames >= DEBOUNCE_FRAMES:
                                audio.note_off(
                                    current_note,
                                    FIXED_OCTAVE
                                )

                                audio.note_on(
                                    note,
                                    FIXED_OCTAVE
                                )

                                recorder.add_event(
                                    "NOTE",
                                    [
                                        (
                                            note,
                                            FIXED_OCTAVE
                                        )
                                    ]
                                )

                                current_note = note
                                pending_note = None
                                pending_note_frames = 0
                        else:
                            pending_note = note
                            pending_note_frames = 1

            elif gesture == "FIST":
                right_hand_absent_frames = 0
                pending_note = None
                pending_note_frames = 0

                if current_note:
                    audio.note_off(
                        current_note,
                        FIXED_OCTAVE
                    )
                    current_note = None
                piano.clear_active_note()

            else:
                pending_note = None
                pending_note_frames = 0
                right_hand_absent_frames += 1
                if right_hand_absent_frames > 15:
                    if current_note:
                        audio.note_off(
                            current_note,
                            FIXED_OCTAVE
                        )
                        current_note = None
                    piano.clear_active_note()

        else:
            pending_note = None
            pending_note_frames = 0
            right_hand_absent_frames += 1
            if right_hand_absent_frames > 15:
                if current_note:
                    audio.note_off(
                        current_note,
                        FIXED_OCTAVE
                    )
                    current_note = None
                piano.clear_active_note()

        # =================================================
        # LEFT HAND → CHORD
        # =================================================

        if left_hand:

            landmarks, gesture = left_hand

            x = int(
                landmarks[0].x *
                CAMERA_WIDTH
            )

            root = piano.get_key(
                x
            )

            chord_type = (
                chord_type_from_gesture(
                    gesture
                )
            )

            if (
                root
                and chord_type
            ):
                left_hand_absent_frames = 0
                detected_chord = (root, chord_type)

                if current_chord_root is None or current_chord is None:
                    # No previous chord active -> trigger immediately
                    chord_notes = (
                        get_root_chord(
                            root,
                            chord_type,
                            FIXED_OCTAVE
                        )
                    )

                    for note, note_octave in chord_notes:
                        audio.note_on(
                            note,
                            note_octave
                        )

                    recorder.add_event(
                        "CHORD",
                        chord_notes
                    )

                    current_chord = chord_type
                    current_chord_root = root
                    current_chord_notes = chord_notes
                    pending_chord = None
                    pending_chord_frames = 0

                elif detected_chord == (current_chord_root, current_chord):
                    # Same chord and root -> keep playing, do NOT restart
                    pending_chord = None
                    pending_chord_frames = 0

                else:
                    # Chord or root changed -> debounce before switching
                    if detected_chord == pending_chord:
                        pending_chord_frames += 1
                        if pending_chord_frames >= DEBOUNCE_FRAMES:
                            # Release previous chord notes smoothly without cutting off melody
                            for note, note_octave in current_chord_notes:
                                audio.note_off(
                                    note,
                                    note_octave
                                )

                            chord_notes = (
                                get_root_chord(
                                    root,
                                    chord_type,
                                    FIXED_OCTAVE
                                )
                            )

                            for note, note_octave in chord_notes:
                                audio.note_on(
                                    note,
                                    note_octave
                                )

                            recorder.add_event(
                                "CHORD",
                                chord_notes
                            )

                            current_chord = chord_type
                            current_chord_root = root
                            current_chord_notes = chord_notes
                            pending_chord = None
                            pending_chord_frames = 0
                    else:
                        pending_chord = detected_chord
                        pending_chord_frames = 1

            elif gesture == "FIST":
                left_hand_absent_frames = 0
                pending_chord = None
                pending_chord_frames = 0

                if current_chord_notes:
                    for note, note_octave in current_chord_notes:
                        audio.note_off(
                            note,
                            note_octave
                        )
                    current_chord_notes = []

                current_chord = None
                current_chord_root = None

            else:
                pending_chord = None
                pending_chord_frames = 0
                left_hand_absent_frames += 1
                if left_hand_absent_frames > 15:
                    if current_chord_notes:
                        for note, note_octave in current_chord_notes:
                            audio.note_off(
                                note,
                                note_octave
                            )
                        current_chord_notes = []
                    current_chord = None
                    current_chord_root = None

        else:
            pending_chord = None
            pending_chord_frames = 0
            left_hand_absent_frames += 1
            if left_hand_absent_frames > 15:
                if current_chord_notes:
                    for note, note_octave in current_chord_notes:
                        audio.note_off(
                            note,
                            note_octave
                        )
                    current_chord_notes = []
                current_chord = None
                current_chord_root = None

        # =================================================
        # UI
        # =================================================

        cv2.rectangle(
            frame,
            (0, 0),
            (CAMERA_WIDTH, 140),
            (20, 20, 20),
            -1
        )

        cv2.putText(
            frame,
            "GESTURE PIANO",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Gesture: {detected_gesture}",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        if current_chord:

            cv2.putText(
                frame,
                f"Chord: {current_chord}",
                (350, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        if current_note:

            cv2.putText(
                frame,
                f"Note: {current_note}",
                (350, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        # Piano
        piano.draw(
            frame,
            active_note
        )

        # Controls
        cv2.putText(
            frame,
            "Q: Quit | R: Record | S: Stop Recording",
            (30, 460),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "Gesture Piano",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        # Quit
        if key == ord("q"):

            break

        # Record
        elif key == ord("r"):

            recorder.start()

            print(
                "Recording started."
            )

        # Stop recording
        elif key == ord("s"):

            recorder.stop()

            print(
                "Recording stopped."
            )

    # -------------------------
    # Cleanup
    # -------------------------

    audio.close()

    tracker.close()

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()