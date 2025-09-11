#run_translator.py
import cv2
import time
import joblib
import numpy as np
import mediapipe as mp
import pyttsx3
from collections import deque, Counter

MODEL_PATH = "models/sign_rf.pkl"
ENC_PATH = "models/label_encoder.pkl"

# smoothing / stability
VOTE_WINDOW = 7          # majority vote over last N predictions
CONFIRM_FRAMES = 8       # require same prediction this many frames before accepting
SPEAK_ON_SPACE = True    # speak the word when SPACE is confirmed

def extract_landmarks(landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark], dtype=np.float32)
    wrist = pts[0].copy()
    pts -= wrist
    norms = np.linalg.norm(pts, axis=1)
    max_norm = norms.max()
    if max_norm > 0:
        pts /= max_norm
    return pts.flatten()

def main():
    clf = joblib.load(MODEL_PATH)
    le  = joblib.load(ENC_PATH)

    engine = pyttsx3.init()
    engine.setProperty('rate', 175)   # adjust if speech is too fast/slow

    mp_hands = mp.solutions.hands
    mp_draw  = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot access camera.")
        return

    vote_buf = deque(maxlen=VOTE_WINDOW)
    stable_label = None
    stable_count = 0
    text_buffer = []   # collected characters

    last_spoken_at = 0

    with mp_hands.Hands(
        static_image_mode=False, max_num_hands=1,
        min_detection_confidence=0.6, min_tracking_confidence=0.6
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            pred_label = None

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                feats = extract_landmarks(hand).reshape(1, -1)
                pred_idx = clf.predict(feats)[0]
                pred_label = le.inverse_transform([pred_idx])[0]
                vote_buf.append(pred_label)

                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                # voting + stability
                if len(vote_buf) == VOTE_WINDOW:
                    most = Counter(vote_buf).most_common(1)[0][0]
                    if most == stable_label:
                        stable_count += 1
                    else:
                        stable_label = most
                        stable_count = 1

                    # accept a character only after it remains stable for CONFIRM_FRAMES
                    if stable_count == CONFIRM_FRAMES:
                        if stable_label == "SPACE":
                            # speak the current word if any
                            if SPEAK_ON_SPACE:
                                word = "".join(text_buffer).strip()
                                if word:
                                    print("SAY:", word)
                                    engine.say(word)
                                    engine.runAndWait()
                                    last_spoken_at = time.time()
                            text_buffer.append(" ")
                        else:
                            text_buffer.append(stable_label)
            else:
                vote_buf.clear()
                stable_label = None
                stable_count = 0

            # overlay UI
            ui_text = f"Buffer: {''.join(text_buffer)[-40:]}"
            cv2.putText(frame, ui_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            hint = "[V]oice now  [B]ackspace  [C]lear  [Q]uit"
            cv2.putText(frame, hint, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

            if pred_label:
                cv2.putText(frame, f"Pred: {pred_label}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

            cv2.imshow("Sign → Speech (MVP)", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('v'):  # voice the whole buffer on demand
                msg = "".join(text_buffer).strip()
                if msg:
                    print("SAY:", msg)
                    engine.say(msg)
                    engine.runAndWait()
            elif key == ord('b'):  # backspace
                if text_buffer:
                    text_buffer.pop()
            elif key == ord('c'):  # clear
                text_buffer.clear()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
