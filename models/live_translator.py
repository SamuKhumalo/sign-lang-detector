# #11111111111111111111111111111111111111
# # live_translator.py
# import cv2
# import mediapipe as mp
# import numpy as np
# import joblib
# from collections import deque
# import pyttsx3
# import time
# import threading

# # Load trained model + encoder
# model = joblib.load("sign_model.pkl")
# label_encoder = joblib.load("label_encoder.pkl")

# # Mediapipe setup
# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils
# hands = mp_hands.Hands(max_num_hands=1,
#                        min_detection_confidence=0.7,
#                        min_tracking_confidence=0.7)

# # Buffers
# buffer = deque(maxlen=15)
# sentence = ""
# current_word = ""
# spoken_words = []  # subtitles

# # Voice engine
# engine = pyttsx3.init()

# def speak_async(text):
#     """Speak in a separate thread so UI doesn't freeze"""
#     def run():
#         try:
#             engine.say(text)
#             engine.runAndWait()
#         except Exception as e:
#             print("TTS error:", e)
#     threading.Thread(target=run, daemon=True).start()

# # Pause timers
# last_detected_time = time.time()
# short_pause = 1.5  # word separator
# long_pause = 3.0   # full sentence

# def extract_landmarks(hand_landmarks):
#     """ Normalize landmarks: wrist-centered & scale-invariant """
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
#     wrist = pts[0].copy()
#     pts -= wrist
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist
#     return pts.flatten()  # 63 features

# cap = cv2.VideoCapture(0)
# print("🎥 Real-Time Translator Started (press 'q' to quit, 's' to speak full sentence)...")

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame = cv2.flip(frame, 1)
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = hands.process(rgb)

#     detected_label = None

#     if results.multi_hand_landmarks:
#         hand_landmarks = results.multi_hand_landmarks[0]
#         features = extract_landmarks(hand_landmarks).reshape(1, -1)

#         pred = model.predict(features)[0]
#         detected_label = label_encoder.inverse_transform([pred])[0]

#         buffer.append(detected_label)

#         # Stable detection
#         if len(buffer) == buffer.maxlen and len(set(buffer)) == 1:
#             current_word += detected_label
#             sentence += detected_label
#             buffer.clear()

#         # Reset timer since hand is active
#         last_detected_time = time.time()

#         # Draw hand
#         mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#     else:
#         # No hand detected → check pause durations
#         elapsed = time.time() - last_detected_time

#         if elapsed > long_pause and sentence.strip():
#             # Speak full sentence and clear
#             print(f"🗣 Speaking full sentence: {sentence.strip()}")
#             speak_async(sentence.strip())
#             spoken_words.append(sentence.strip())
#             sentence = ""
#             current_word = ""
#             last_detected_time = time.time()

#         elif elapsed > short_pause and current_word:
#             # Speak last word and add space
#             print(f"🗣 Speaking word: {current_word}")
#             speak_async(current_word)
#             spoken_words.append(current_word)
#             sentence += " "
#             current_word = ""
#             last_detected_time = time.time()

#     # Draw labels
#     if detected_label:
#         cv2.putText(frame, f"Detected: {detected_label}", (10, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

#     # Sentence
#     cv2.putText(frame, f"Sentence: {sentence}", (10, 100),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

#     # Subtitles (all words spoken so far)
#     if spoken_words:
#         subtitle_text = " | ".join(spoken_words[-5:])  # show last 5 words max
#         cv2.putText(frame, f"Spoken: {subtitle_text}", (10, 150),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 200), 2)

#     cv2.imshow("Live Translator", frame)

#     key = cv2.waitKey(1) & 0xFF
#     if key == ord('q'):
#         break
#     elif key == ord('s'):  # Speak full sentence manually
#         if sentence.strip():
#             print(f"🗣 Speaking full sentence: {sentence.strip()}")
#             speak_async(sentence.strip())
#             spoken_words.append(sentence.strip())

# cap.release()
# cv2.destroyAllWindows()



#222222222222222222222222 WORDS + LETTERS

# live_translator.py
# import cv2
# import mediapipe as mp
# import numpy as np
# import joblib
# from collections import deque
# import pyttsx3
# import time
# import threading
# from collections import Counter

# # ===== CONFIG =====
# MODEL_PATH = "sign_model.pkl"
# ENCODER_PATH = "label_encoder.pkl"

# BUFFER_SIZE = 12          # frames kept in rolling buffer for stability
# STABLE_THRESHOLD = 0.75   # fraction in buffer required to accept a label
# WORD_PAUSE = 1.2          # pause (sec) with no hand -> finalize spelled word
# SENTENCE_PAUSE = 2.8      # longer pause -> speak full sentence
# TTS_COOLDOWN = 0.5
# # ===================

# # load model & encoder
# clf = joblib.load(MODEL_PATH)
# le = joblib.load(ENCODER_PATH)

# # infer which classes are words (multi-char) vs letters (single char)
# classes = [c.upper() for c in le.classes_]
# LETTER_LABELS = [c for c in classes if len(c) == 1]
# WORD_LABELS = [c for c in classes if len(c) > 1]
# print("Loaded classes. Letters:", len(LETTER_LABELS), "Words:", len(WORD_LABELS))

# # mediapipe
# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils
# hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)

# # TTS setup (background)
# engine = pyttsx3.init()
# engine.setProperty("rate", 160)
# _tts_lock = threading.Lock()
# _last_tts = 0.0

# def speak_async(text):
#     global _last_tts
#     def run(t):
#         try:
#             engine.say(t)
#             engine.runAndWait()
#         except Exception as e:
#             print("TTS error:", e)
#     now = time.time()
#     with _tts_lock:
#         if now - _last_tts < TTS_COOLDOWN:
#             return
#         _last_tts = now
#     threading.Thread(target=run, args=(text,), daemon=True).start()

# def extract_landmarks(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
#     wrist = pts[0].copy()
#     pts -= wrist
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist
#     return pts.flatten()

# def stable_label_from_buffer(buf):
#     if not buf:
#         return None, 0.0
#     cnt = Counter(buf)
#     label, count = cnt.most_common(1)[0]
#     return label, count / len(buf)

# # state
# pred_buf = deque(maxlen=BUFFER_SIZE)
# current_word = ""
# sentence = ""
# spoken_words = []
# last_hand_time = time.time()
# last_accepted = None

# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     raise RuntimeError("Cannot open webcam.")

# print("▶ Hybrid live translator started. Keys: [s]=speak sentence, [c]=clear, [q]=quit")

# try:
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             time.sleep(0.01)
#             continue

#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         realtime_label = None
#         stable_label = None
#         stable_conf = 0.0

#         if results.multi_hand_landmarks:
#             hand = results.multi_hand_landmarks[0]
#             feats = extract_landmarks(hand).reshape(1, -1)

#             pred_idx = clf.predict(feats)[0]
#             # pred_idx is encoded label index (int). Convert to string label via encoder
#             label_str = le.inverse_transform([pred_idx])[0].upper()
#             realtime_label = label_str
#             pred_buf.append(realtime_label)

#             mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
#             last_hand_time = time.time()

#             # check stability
#             lbl, conf = stable_label_from_buffer(pred_buf)
#             stable_conf = conf
#             if conf >= STABLE_THRESHOLD:
#                 stable_label = lbl

#         else:
#             # no hand in view
#             pass

#         # If stable label exists and not repeated immediately
#         if stable_label and stable_label != last_accepted:
#             last_accepted = stable_label
#             # handle word vs letter
#             if stable_label in WORD_LABELS:
#                 sentence += stable_label + " "
#                 spoken_words.append(stable_label)
#                 speak_async(stable_label)
#                 pred_buf.clear()
#                 current_word = ""  # clear any partial word
#             elif stable_label in LETTER_LABELS:
#                 current_word += stable_label
#                 pred_buf.clear()

#         # handle pauses -> finalize spelled word or speak sentence
#         elapsed = time.time() - last_hand_time
#         if elapsed > WORD_PAUSE and current_word:
#             # finalize spelled word
#             sentence += current_word + " "
#             spoken_words.append(current_word)
#             speak_async(current_word)
#             current_word = ""
#             # small cooldown to avoid immediate repeats
#             last_hand_time = time.time()

#         if elapsed > SENTENCE_PAUSE and sentence.strip():
#             # speak whole sentence
#             final = sentence.strip()
#             spoken_words.append(final)
#             speak_async(final)
#             sentence = ""
#             current_word = ""
#             pred_buf.clear()
#             last_accepted = None
#             last_hand_time = time.time()

#         # UI overlays
#         h, w, _ = frame.shape
#         if realtime_label:
#             cv2.rectangle(frame, (10, 10), (360, 60), (10,10,10), -1)
#             cv2.putText(frame, f"Realtime: {realtime_label} ({stable_conf:.2f})", (18, 44),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

#         cv2.rectangle(frame, (0, h-140), (w, h), (20,20,20), -1)
#         cv2.putText(frame, f"Current word: {current_word}", (18, h-100),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200,200,0), 2)
#         cv2.putText(frame, f"Sentence: {sentence}", (18, h-60),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,200,200), 2)

#         if spoken_words:
#             subtitle_text = " | ".join(spoken_words[-6:])
#             cv2.putText(frame, subtitle_text, (18, h-170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180,255,255), 2)

#         cv2.putText(frame, "Keys: S=speak C=clear Q=quit", (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

#         cv2.imshow("Hybrid Live Translator", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord('s'):
#             if sentence.strip():
#                 speak_async(sentence.strip())
#                 spoken_words.append(sentence.strip())
#                 sentence = ""
#                 current_word = ""
#         elif key == ord('c'):
#             sentence = ""
#             current_word = ""
#             pred_buf.clear()
#             last_accepted = None
#             spoken_words.clear()

# finally:
#     cap.release()
#     cv2.destroyAllWindows()
#     hands.close()





##333333333333333333

import cv2
import numpy as np
import mediapipe as mp
import joblib

# Load trained model + label encoder
model = joblib.load("sign_model.pkl")
le = joblib.load("label_encoder.pkl")

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ---------- FEATURE EXTRACTION ----------
def extract_features(hand_landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)

    # Normalize relative to wrist (index 0)
    wrist = pts[0].copy()
    pts -= wrist

    # Scale so largest distance = 1
    max_dist = np.linalg.norm(pts, axis=1).max()
    if max_dist > 0:
        pts /= max_dist

    return pts.flatten().reshape(1, -1)   # shape (1,63)

# ---------- LIVE TRANSLATOR ----------
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as hands:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            features = extract_features(hand_landmarks)

            # Debug check
            print("Feature shape:", features.shape, "| First 5:", features[0][:5])

            # Predict
            probs = model.predict_proba(features)[0]
            pred_idx = np.argmax(probs)
            pred_label = le.inverse_transform([pred_idx])[0]
            confidence = np.max(probs)

            print(f"Prediction: {pred_label} | Confidence: {confidence:.2f}")

            # Draw landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            cv2.putText(frame, f"{pred_label} ({confidence:.2f})",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2)

        cv2.imshow("Live Translator (press Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
