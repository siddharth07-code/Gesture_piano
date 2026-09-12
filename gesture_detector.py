import math

def distance(a,b):

  return math.sqrt(
    (a.x-b.x) ** 2 +
    (a.y-b.y) ** 2
  )

def finger_up(landmarks,tip,pip):
  return (
    landmarks[tip].y <
    landmarks[pip].y
  )

def get_fingers(landmarks):
  index=finger_up(
    landmarks,
    8,
    6
  )

  middle=finger_up(
    landmarks,
    12,
    10
  )
  ring=finger_up(
    landmarks,
    16,
    14
  )

  pinky = finger_up(
    landmarks,
    20,
    18
    )

  thumb = (
     distance(
        landmarks[4],
        landmarks[5]
        )
        >
        distance(
        landmarks[3],
         landmarks[5]
        )
    )
  return [
      thumb,
      index,
      middle,
      ring,
      pinky
    ]

def get_gesture(fingers):
  thumb,index,middle,ring,pinky=fingers

  if index and not middle and not ring and not pinky:
    return "INDEX"

  if index and middle and not ring and not pinky:
    return "TWO"

  if index and middle and ring and not pinky:
    return "THREE"

  if(
    index
    and middle
    and ring
    and pinky
  ):
    return "OPEN"

  if(
    thumb
    and not index
    and not middle
    and not ring
    and not pinky
  ):
    return "THUMB"

  if not any(fingers):
    return "FIST"

  return "UNKNOWN"

def chord_type_from_gesture(gesture):

  mapping={
    "INDEX":"MAJOR",
    "TWO":"MINOR",
    "THREE":"7TH",
    "OPEN":"SUS4",
  }          
  return mapping.get(
    gesture,
    None
  )

