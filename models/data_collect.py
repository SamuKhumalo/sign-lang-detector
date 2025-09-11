# #data_collect.py
# import cv2
# import csv
# import time
# import os
# import numpy as np
# import mediapipe as mp
# from collections import deque

# # ====== SETTINGS ======
# LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")  # A–Z
# SAMPLES_PER_LABEL = 200
# DATA_CSV = "sign_data.csv"
# # ======================

# os.makedirs("data", exist_ok=True)

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# def extract_landmarks(landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark], dtype=np.float32)
#     wrist = pts[0].copy()
#     pts -= wrist
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist
#     return pts.flatten()

# def ensure_header(path):
#     if not os.path.exists(path):
#         with open(path, "w", newline="") as f:
#             writer = csv.writer(f)
#             header = [f"f{i}" for i in range(63)] + ["label"]
#             writer.writerow(header)

# def append_row(path, features, label):
#     with open(path, "a", newline="") as f:
#         writer = csv.writer(f)
#         writer.writerow(list(features) + [label])

# def main():
#     ensure_header(DATA_CSV)

#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("ERROR: Cannot access camera")
#         return

#     with mp_hands.Hands(
#         static_image_mode=False,
#         max_num_hands=1,
#         min_detection_confidence=0.6,
#         min_tracking_confidence=0.6
#     ) as hands:
#         for label in LABELS:
#             print(f"\n=== Collecting {SAMPLES_PER_LABEL} samples for: {label} ===")
#             print("Prepare your hand... Starting in 3 seconds...")
#             time.sleep(3)

#             collected = 0
#             cooldown = deque(maxlen=5)

#             while collected < SAMPLES_PER_LABEL:
#                 ok, frame = cap.read()
#                 if not ok: break
#                 frame = cv2.flip(frame, 1)
#                 rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 results = hands.process(rgb)

#                 h, w, _ = frame.shape
#                 status_text = f"Label: {label}  {collected}/{SAMPLES_PER_LABEL}"
#                 cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

#                 if results.multi_hand_landmarks:
#                     hand_landmarks = results.multi_hand_landmarks[0]
#                     feats = extract_landmarks(hand_landmarks)

#                     cooldown.append(feats.tobytes())
#                     if len(set(cooldown)) > 1:  # only save if not duplicate
#                         append_row(DATA_CSV, feats, label)
#                         collected += 1

#                     mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#                 cv2.imshow("Collecting Data (Q=quit)", frame)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     cap.release()
#                     cv2.destroyAllWindows()
#                     return

#             print(f"Done collecting for: {label}")

#     cap.release()
#     cv2.destroyAllWindows()
#     print("\n✅ Collection complete. Data saved to:", DATA_CSV)

# if __name__ == "__main__":
#     main()
























#2222222222222222222222222 WORDS + LETTERS
# data_collect.py
import cv2
import csv
import time
import os
import numpy as np
import mediapipe as mp
from collections import deque

# ========== SETTINGS ==========
LETTER_LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")  # A–Z
WORD_LABELS = ["HELLO", "THANKYOU", "YES", "NO", "PLEASE", "SORRY", "EAT", "DRINK", "SCHOOL", "LOVE"]
ALL_LABELS = LETTER_LABELS + WORD_LABELS
SAMPLES_PER_LABEL = 200   # adjust if you want fewer/more
DATA_CSV = "sign_data.csv"
# ==============================

os.makedirs("data", exist_ok=True)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def extract_landmarks(landmarks):
    """Normalize landmarks: wrist-centered & scale-invariant"""
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark], dtype=np.float32)
    wrist = pts[0].copy()
    pts -= wrist
    max_dist = np.linalg.norm(pts, axis=1).max()
    if max_dist > 0:
        pts /= max_dist
    return pts.flatten()

def ensure_header(path):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            header = [f"f{i}" for i in range(63)] + ["label"]
            writer.writerow(header)

def append_row(path, features, label):
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(list(features) + [label])

def main():
    ensure_header(DATA_CSV)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ ERROR: Cannot access camera")
        return

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as hands:
        for label in ALL_LABELS:
            print(f"\n=== Collecting {SAMPLES_PER_LABEL} samples for: {label} ===")
            print("Prepare your hand... Starting in 3 seconds...")
            time.sleep(3)

            collected = 0
            cooldown = deque(maxlen=5)

            while collected < SAMPLES_PER_LABEL:
                ok, frame = cap.read()
                if not ok: break
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                h, w, _ = frame.shape
                status_text = f"Label: {label}  {collected}/{SAMPLES_PER_LABEL}"
                cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    feats = extract_landmarks(hand_landmarks)

                    cooldown.append(feats.tobytes())
                    if len(set(cooldown)) > 1:  # avoid duplicates
                        append_row(DATA_CSV, feats, label)
                        collected += 1

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                cv2.imshow("Collecting Data (Q=quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return

            print(f"✅ Done collecting for: {label}")

    cap.release()
    cv2.destroyAllWindows()
    print("\n🎉 Collection complete. Data saved to:", DATA_CSV)

if __name__ == "__main__":
    main()
