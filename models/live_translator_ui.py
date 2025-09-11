#live_translator_ui.py
# models/live_translator_ui.py
import cv2
import mediapipe as mp
import numpy as np
import joblib
import pyttsx3
from collections import deque, Counter
import time
import os

# ---------- CONFIG ----------
MODEL_PATH = "sign_model.pkl"
ENCODER_PATH = "label_encoder.pkl"

# Buffer and stability
BUFFER_LEN = 15
STABLE_RATIO = 0.6           # label considered stable if it occupies >= 60% of buffer
COOLDOWN_SECONDS = 0.8       # wait this long after accepting a stable label before accepting again

# Keyboard layout (rows of keys)
KEY_ROWS = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
    ["SPACE", "DEL", "END"]
]
# Normalize keys to the labels your model uses (uppercase strings)
ALL_KEYS = [k for row in KEY_ROWS for k in row]

# ---------- Sanity check files ----------
if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
    raise FileNotFoundError("Model or encoder not found. Train your model first (sign_model.pkl, label_encoder.pkl).")

# ---------- Load model ----------
model = joblib.load(MODEL_PATH)
le = joblib.load(ENCODER_PATH)

# ---------- Mediapipe & TTS init ----------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.65, min_tracking_confidence=0.6)

engine = pyttsx3.init()
engine.setProperty("rate", 160)

# ---------- State ----------
pred_buf = deque(maxlen=BUFFER_LEN)
last_accept_time = 0.0

current_word = ""
sentence = ""
detected_label_realtime = None
stable_label = None

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open webcam (VideoCapture failed). Try changing the camera index.")

print("▶ Starting Real-Time Translator with UI (press 'q' to quit).")

def majority_label(buffer):
    if not buffer:
        return None, 0
    cnt = Counter(buffer)
    label, cnt_val = cnt.most_common(1)[0]
    return label, cnt_val

def draw_keyboard(frame, highlight=None, stable=False):
    """Draw keyboard grid at bottom of frame. highlight is the key string to highlight."""
    h, w, _ = frame.shape
    margin = 10
    key_h = 60
    spacing = 8
    start_y = h - (len(KEY_ROWS) * (key_h + spacing)) - 20

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2

    for r_idx, row in enumerate(KEY_ROWS):
        row_len = len(row)
        # compute width per key to center row
        total_key_width = (row_len * 90) + ((row_len - 1) * spacing)
        start_x = (w - total_key_width) // 2
        y1 = start_y + r_idx * (key_h + spacing)
        for k_idx, key in enumerate(row):
            x1 = start_x + k_idx * (90 + spacing)
            x2 = x1 + 90
            y2 = y1 + key_h

            # default color / fill
            fill_color = (40, 40, 40)   # dark gray
            border_color = (200, 200, 200)
            text_color = (255, 255, 255)

            # highlight if matches
            if highlight and key == highlight:
                if stable:
                    fill_color = (0, 180, 0)      # green for stable
                    border_color = (0, 255, 0)
                    text_color = (0, 0, 0)
                else:
                    fill_color = (0, 200, 200)    # yellow/cyan-ish for unstable
                    border_color = (0, 255, 255)
                    text_color = (0, 0, 0)

            # draw rectangle and text
            cv2.rectangle(frame, (x1, y1), (x2, y2), fill_color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)

            # draw label centered
            text_size = cv2.getTextSize(key, font, font_scale, thickness)[0]
            text_x = x1 + (90 - text_size[0]) // 2
            text_y = y1 + (key_h + text_size[1]) // 2
            cv2.putText(frame, key, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

def safe_say(text):
    """Run TTS without raising errors."""
    if not text or text.strip() == "":
        return
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

# ---------- Main loop ----------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame read failed; skipping frame.")
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    detected_label_realtime = None

    if results.multi_hand_landmarks:
        # take first hand only (single-hand model)
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # extract flattened landmarks (21 * 3)
        feats = []
        for lm in hand_landmarks.landmark:
            feats.extend([lm.x, lm.y, lm.z])
        feats = np.array(feats).reshape(1, -1)

        # predict using model
        try:
            pred_idx = model.predict(feats)[0]
            detected_label_realtime = le.inverse_transform([pred_idx])[0].upper()
            pred_buf.append(detected_label_realtime)
        except Exception as e:
            # prediction error fallback
            detected_label_realtime = None

    # determine majority and stability
    maj_label, maj_count = majority_label(pred_buf)
    stable = False
    now = time.time()
    if maj_label:
        if maj_count >= max(1, int(BUFFER_LEN * STABLE_RATIO)) and (now - last_accept_time) > COOLDOWN_SECONDS:
            stable = True
        else:
            stable = False

    # If stable and not cooldown, accept the label
    if stable and maj_label:
        # Accept label action
        k = maj_label
        # control labels
        if k == "SPACE":
            if current_word:
                sentence += current_word + " "
                current_word = ""
        elif k == "DEL":
            if current_word:
                current_word = current_word[:-1]
            elif sentence:
                sentence = sentence.rstrip()
                # remove last word if any
                sentence = " ".join(sentence.split(" ")[:-1])
                if sentence and not sentence.endswith(" "):
                    sentence += " "
        elif k == "END":
            if current_word:
                sentence += current_word
                current_word = ""
            final = sentence.strip()
            if final:
                print("✅ Spoken:", final)
                safe_say(final)
            sentence = ""
        else:
            # letter - append to current word
            current_word += k

        last_accept_time = now
        pred_buf.clear()  # reset buffer after accepting

    # Overlay sentence and current word
    display_text = (sentence + current_word).strip()
    if display_text == "":
        display_text = "[typing...]"

    # Draw top-left small box for detected realtime label
    if detected_label_realtime:
        cv2.rectangle(frame, (10, 10), (230, 70), (10, 10, 10), -1)
        cv2.putText(frame, f"Realtime: {detected_label_realtime}", (18, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

    # Draw big sentence bar at bottom
    h, w, _ = frame.shape
    cv2.rectangle(frame, (0, h - 110), (w, h), (15, 15, 15), -1)
    cv2.putText(frame, display_text, (20, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)

    # Draw keyboard UI (highlight detected label; green if stable else yellow)
    draw_keyboard(frame, highlight=maj_label if maj_label else detected_label_realtime, stable=stable)

    # help text
    cv2.putText(frame, "Press V=voice, C=clear, Q=quit", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

    cv2.imshow("Sign Language - Live Translator (UI)", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('v'):
        text = (sentence + current_word).strip()
        if text:
            print("🔊 Voice:", text)
            safe_say(text)
            # clear after speaking if you prefer
            # sentence = ""; current_word = ""
    elif key == ord('c'):
        sentence = ""
        current_word = ""
        pred_buf.clear()

# cleanup
cap.release()
cv2.destroyAllWindows()
