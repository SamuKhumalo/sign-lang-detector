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

# import cv2
# import numpy as np
# import mediapipe as mp
# import joblib

# # Load trained model + label encoder
# model = joblib.load("sign_model.pkl")
# le = joblib.load("label_encoder.pkl")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# # ---------- FEATURE EXTRACTION ----------
# def extract_features(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)

#     # Normalize relative to wrist (index 0)
#     wrist = pts[0].copy()
#     pts -= wrist

#     # Scale so largest distance = 1
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist

#     return pts.flatten().reshape(1, -1)   # shape (1,63)

# # ---------- LIVE TRANSLATOR ----------
# cap = cv2.VideoCapture(0)

# with mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.6,
#     min_tracking_confidence=0.6
# ) as hands:
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         if results.multi_hand_landmarks:
#             hand_landmarks = results.multi_hand_landmarks[0]
#             features = extract_features(hand_landmarks)

#             # Debug check
#             print("Feature shape:", features.shape, "| First 5:", features[0][:5])

#             # Predict
#             probs = model.predict_proba(features)[0]
#             pred_idx = np.argmax(probs)
#             pred_label = le.inverse_transform([pred_idx])[0]
#             confidence = np.max(probs)

#             print(f"Prediction: {pred_label} | Confidence: {confidence:.2f}")

#             # Draw landmarks
#             mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#             cv2.putText(frame, f"{pred_label} ({confidence:.2f})",
#                         (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
#                         1, (0, 255, 0), 2)

#         cv2.imshow("Live Translator (press Q to quit)", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# cap.release()
# cv2.destroyAllWindows()



#=================================================================================================

# import cv2
# import numpy as np
# import mediapipe as mp
# import joblib
# import pyttsx3

# # Load trained model + label encoder
# model = joblib.load("sign_model.pkl")
# le = joblib.load("label_encoder.pkl")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# # ---------- FEATURE EXTRACTION ----------
# def extract_features(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)

#     # Normalize relative to wrist (index 0)
#     wrist = pts[0].copy()
#     pts -= wrist

#     # Scale so largest distance = 1
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist

#     return pts.flatten().reshape(1, -1)   # shape (1,63)

# # ---------- VOICE ENGINE ----------
# engine = pyttsx3.init()
# engine.setProperty("rate", 160)   # speaking speed
# engine.setProperty("volume", 1.0) # max volume

# # ---------- LIVE TRANSLATOR ----------
# cap = cv2.VideoCapture(0)

# sentence = []   # store detected words

# with mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.6,
#     min_tracking_confidence=0.6
# ) as hands:
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         if results.multi_hand_landmarks:
#             hand_landmarks = results.multi_hand_landmarks[0]
#             features = extract_features(hand_landmarks)

#             # Predict
#             probs = model.predict_proba(features)[0]
#             pred_idx = np.argmax(probs)
#             pred_label = le.inverse_transform([pred_idx])[0]
#             confidence = np.max(probs)

#             # Append detected word if confident enough
#             if confidence > 0.75:  
#                 sentence.append(pred_label)

#             print(f"Prediction: {pred_label} | Confidence: {confidence:.2f}")

#             # Draw landmarks
#             mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#             cv2.putText(frame, f"{pred_label} ({confidence:.2f})",
#                         (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
#                         1, (0, 255, 0), 2)

#         # Show sentence on screen
#         cv2.putText(frame, "Sentence: " + " ".join(sentence),
#                     (10, 80), cv2.FONT_HERSHEY_SIMPLEX,
#                     1, (255, 0, 0), 2)

#         cv2.imshow("Live Translator (press Q to quit, SPACE to speak)", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):  # quit
#             break
#         elif key == 32:  # SPACE pressed
#             if sentence:
#                 text_to_speak = " ".join(sentence)
#                 engine.say(text_to_speak)
#                 engine.runAndWait()
#                 print(f"🔊 Speaking: {text_to_speak}")
#                 sentence = []  # clear after speaking

# cap.release()
# cv2.destroyAllWindows()




#Code with a voice engine after stopped using gestures for 2 seconds

# import cv2
# import numpy as np
# import mediapipe as mp
# import joblib
# import pyttsx3
# import time

# # Load trained model + label encoder
# model = joblib.load("sign_model.pkl")
# le = joblib.load("label_encoder.pkl")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# # ---------- FEATURE EXTRACTION ----------
# def extract_features(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)

#     # Normalize relative to wrist (index 0)
#     wrist = pts[0].copy()
#     pts -= wrist

#     # Scale so largest distance = 1
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist

#     return pts.flatten().reshape(1, -1)   # shape (1,63)

# # ---------- VOICE ENGINE ----------
# engine = pyttsx3.init()
# engine.setProperty("rate", 160)   # speaking speed
# engine.setProperty("volume", 1.0) # max volume

# # ---------- LIVE TRANSLATOR ----------
# cap = cv2.VideoCapture(0)

# sentence = []   # store detected words
# last_seen_time = time.time()
# pause_threshold = 2.0  # seconds of no hands = pause

# with mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.6,
#     min_tracking_confidence=0.6
# ) as hands:
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         if results.multi_hand_landmarks:
#             hand_landmarks = results.multi_hand_landmarks[0]
#             features = extract_features(hand_landmarks)

#             # Predict
#             probs = model.predict_proba(features)[0]
#             pred_idx = np.argmax(probs)
#             pred_label = le.inverse_transform([pred_idx])[0]
#             confidence = np.max(probs)

#             if confidence > 0.75:  
#                 sentence.append(pred_label)

#             print(f"Prediction: {pred_label} | Confidence: {confidence:.2f}")

#             # Draw landmarks
#             mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#             cv2.putText(frame, f"{pred_label} ({confidence:.2f})",
#                         (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
#                         1, (0, 255, 0), 2)

#             last_seen_time = time.time()  # reset timer when hands visible

#         else:
#             # If no hands detected for pause_threshold seconds
#             if sentence and (time.time() - last_seen_time > pause_threshold):
#                 text_to_speak = " ".join(sentence)
#                 engine.say(text_to_speak)
#                 engine.runAndWait()
#                 print(f"🔊 Speaking: {text_to_speak}")
#                 sentence = []  # clear after speaking
#                 last_seen_time = time.time()

#         # Show sentence on screen
#         cv2.putText(frame, "Sentence: " + " ".join(sentence),
#                     (10, 80), cv2.FONT_HERSHEY_SIMPLEX,
#                     1, (255, 0, 0), 2)

#         cv2.imshow("Live Translator (press Q to quit)", frame)

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# cap.release()
# cv2.destroyAllWindows()














#####################################   27 Sept 2025  ######################################

# # live_translator.py  (pause = word boundary + speech)
# import cv2
# import numpy as np
# import mediapipe as mp
# import joblib
# import pyttsx3
# import time
# from collections import deque, Counter

# # ---------- LOAD MODEL ----------
# model = joblib.load("sign_model.pkl")
# le = joblib.load("label_encoder.pkl")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# # ---------- FEATURES ----------
# def extract_features(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
#     wrist = pts[0].copy()
#     pts -= wrist
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist
#     return pts.flatten().reshape(1, -1)   # (1,63)

# # ---------- CONFIG (tweak these if needed) ----------
# CONF_THRESH       = 0.40  # only count frames above this probability
# VOTE_WINDOW       = 20    # frames considered for majority vote
# STABLE_NEED       = 7      # min count of same label in the window to accept
# LETTER_DEBOUNCE   = 0.50   # min seconds between two accepted labels
# WORD_PAUSE        = 1.60   # if no new accepted label for this long -> finalize word (+space) + speak
# DRAW_CONFIDENCE   = True

# # ---------- TTS ----------
# engine = pyttsx3.init()
# engine.setProperty("rate", 160)
# engine.setProperty("volume", 1.0)

# def tts_say(text: str):
#     if not text or not text.strip():
#         return
#     try:
#         engine.stop()           # clear any stuck/queued utterances
#     except Exception:
#         pass
#     engine.say(text)
#     engine.runAndWait()

# # ---------- STATE ----------
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     raise RuntimeError("❌ Cannot open webcam")

# pred_buf = deque(maxlen=VOTE_WINDOW)

# current_word = []     # list of letters being built
# transcript   = ""     # full string with spaces between words

# last_accept_time   = 0.0  # when we last appended a letter/word
# last_word_close_ts = 0.0  # when we last auto-finalized a word

# def accept_label(label: str):
#     """Accept a stable label (letter or whole-word). Updates timers & buffers."""
#     global last_accept_time, current_word, transcript
#     now = time.time()
#     if now - last_accept_time < LETTER_DEBOUNCE:
#         return

#     # Treat multi-char labels as whole words (HELLO, PLEASE, ...)
#     if len(label) > 1:  # likely a whole word class
#         if current_word:
#             # finalize current word first
#             word = "".join(current_word)
#             transcript += (word + " ")
#             tts_say(word)
#             current_word = []
#         transcript += (label + " ")
#         tts_say(label)
#     else:
#         # single character (A–Z etc.)
#         current_word.append(label)

#     last_accept_time = now

# def maybe_finalize_word_on_pause():
#     """If no new letter for WORD_PAUSE seconds, finalize the word, add space, and speak it."""
#     global current_word, transcript, last_word_close_ts, last_accept_time
#     if not current_word:
#         return
#     now = time.time()
#     idle = now - last_accept_time
#     if idle >= WORD_PAUSE and (now - last_word_close_ts) >= 0.3:
#         word = "".join(current_word)
#         transcript += (word + " ")
#         tts_say(word)
#         current_word = []
#         last_word_close_ts = now

# # ---------- MAIN ----------
# with mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.65,
#     min_tracking_confidence=0.65
# ) as hands:

#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         if results.multi_hand_landmarks:
#             hand_landmarks = results.multi_hand_landmarks[0]
#             features = extract_features(hand_landmarks)

#             # Predict with probabilities
#             probs = model.predict_proba(features)[0]
#             pred_idx = int(np.argmax(probs))
#             conf = float(np.max(probs))
#             pred_label = le.inverse_transform([pred_idx])[0].upper()

#             # use only confident frames for voting
#             if conf >= CONF_THRESH:
#                 pred_buf.append(pred_label)

#             # majority vote & stability check
#             stable_label, count = (None, 0)
#             if pred_buf:
#                 c = Counter(pred_buf)
#                 stable_label, count = c.most_common(1)[0]

#             if stable_label and count >= STABLE_NEED:
#                 # handle explicit SPACE/END/DEL if those exist as model classes
#                 if stable_label == "SPACE":
#                     maybe_finalize_word_on_pause()  # ensures any partial letters become a word
#                     # add an extra space only if last char not already space
#                     if not transcript.endswith(" "):
#                         transcript += " "
#                     # speak last word already handled above
#                 elif stable_label == "END":
#                     maybe_finalize_word_on_pause()
#                     final = transcript.strip()
#                     if final:
#                         tts_say(final)
#                     transcript = ""
#                 elif stable_label == "DEL":
#                     # delete last letter if in word, else trim last word
#                     if current_word:
#                         current_word.pop()
#                     else:
#                         transcript = transcript.rstrip()
#                         if transcript.endswith(" "):
#                             transcript = transcript[:-1]
#                         # remove last word
#                         pieces = transcript.split(" ")
#                         if pieces:
#                             pieces = pieces[:-1]
#                         transcript = (" ".join(pieces) + " ") if pieces else ""
#                 else:
#                     accept_label(stable_label)

#                 pred_buf.clear()  # avoid rapid repeats

#             # Draw landmarks + HUD
#             mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#             if DRAW_CONFIDENCE:
#                 cv2.putText(
#                     frame,
#                     f"{pred_label} ({conf:.2f})",
#                     (10, 40),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     1,
#                     (0, 255, 0) if conf >= CONF_THRESH else (0, 200, 200),
#                     2,
#                 )
#         else:
#             # Even if the hand is still “seen”, we rely on inactivity of accepted labels.
#             pass

#         # finalize word on inactivity (SPACE-by-pause)
#         maybe_finalize_word_on_pause()

#         # Build display text
#         display_current = "".join(current_word)
#         display_text = (transcript + display_current).strip()

#         # Overlay UI
#         cv2.putText(frame, f"Text: {display_text}", (10, 80),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
#         cv2.putText(frame, f"[Q] quit  [V] voice  [C] clear   Pause>{WORD_PAUSE:.1f}s => space+speech",
#                     (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)

#         cv2.imshow("Live Translator (pause = space + speech)", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord('v'):
#             msg = (transcript + "".join(current_word)).strip()
#             if msg:
#                 tts_say(msg)
#         elif key == ord('c'):
#             pred_buf.clear()
#             current_word.clear()
#             transcript = ""
#             last_accept_time = time.time()

# cap.release()
# cv2.destroyAllWindows()



############ 22222222222222222222222222222222222  ###################

# # live_translator.py  (per-utterance TTS threads + reliable spacing)
# import cv2
# import numpy as np
# import mediapipe as mp
# import joblib
# import time
# import threading
# from collections import deque, Counter
# import pyttsx3

# # ---------- LOAD MODEL ----------
# model = joblib.load("sign_model.pkl")
# le = joblib.load("label_encoder.pkl")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# # ---------- FEATURES ----------
# def extract_features(hand_landmarks):
#     pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
#     wrist = pts[0].copy()
#     pts -= wrist
#     max_dist = np.linalg.norm(pts, axis=1).max()
#     if max_dist > 0:
#         pts /= max_dist
#     return pts.flatten().reshape(1, -1)   # (1,63)

# # ---------- CONFIG ----------
# CONF_THRESH       = 0.50   # min probability to count a frame
# VOTE_WINDOW       = 12     # frames for majority vote
# STABLE_NEED       = 7      # min same-label votes in window to accept
# LETTER_DEBOUNCE   = 0.50   # seconds between accepted labels
# WORD_PAUSE        = 1.60   # inactivity => finalize word + space + speak
# NO_HAND_PAUSE     = 1.80   # no hand => finalize word + space
# DRAW_CONFIDENCE   = True

# # ---------- PER-UTTERANCE TTS (fresh engine each time) ----------
# _last_tts_thread = None
# _tts_lock = threading.Lock()

# def _speak_once(text: str, rate=160, volume=1.0, voice_id=None):
#     try:
#         eng = pyttsx3.init()
#         eng.setProperty("rate", rate)
#         eng.setProperty("volume", volume)
#         if voice_id is not None:
#             try: eng.setProperty("voice", voice_id)
#             except Exception: pass
#         eng.say(text)
#         eng.runAndWait()
#         try: eng.stop()
#         except Exception: pass
#     except Exception as e:
#         print("TTS error:", e)

# def tts_say(text: str):
#     """Fire-and-forget speech that never blocks the main loop and never reuses a stale engine."""
#     global _last_tts_thread
#     text = (text or "").strip()
#     if not text: return
#     with _tts_lock:
#         # prevent overlapping utterances: wait the previous a little if still running
#         if _last_tts_thread and _last_tts_thread.is_alive():
#             # don't block – just let them overlap if you prefer; otherwise join(timeout)
#             pass
#         th = threading.Thread(target=_speak_once, args=(text,), daemon=True)
#         th.start()
#         _last_tts_thread = th
#     print("SAY ->", text)  # debug

# # ---------- STATE ----------
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     raise RuntimeError("❌ Cannot open webcam")

# pred_buf = deque(maxlen=VOTE_WINDOW)

# current_word = []     # list of letters being built
# transcript   = ""     # full string with spaces between words

# last_accept_time   = time.time()  # last time a letter/word/boundary was accepted
# last_word_close_ts = 0.0          # when we last auto-finalized a word
# last_hand_seen     = time.time()
# was_hand_present   = False

# def _append_space_once():
#     """Ensure transcript ends with a single space (no double spaces)."""
#     global transcript
#     transcript = transcript.rstrip() + " "

# def accept_label(label: str):
#     """Accept a stable label (letter or whole-word)."""
#     global last_accept_time, current_word, transcript
#     now = time.time()
#     if now - last_accept_time < LETTER_DEBOUNCE:
#         return

#     # Treat multi-char labels as whole words (HELLO, PLEASE, etc.)
#     if len(label) > 1:
#         if current_word:
#             word = "".join(current_word)
#             if word:
#                 transcript += word + " "
#                 tts_say(word)
#                 current_word = []
#         transcript += label + " "
#         tts_say(label)
#     else:
#         current_word.append(label)

#     last_accept_time = now

# def finalize_current_word(force: bool = False):
#     """Finalize current letters into a word and speak it."""
#     global current_word, transcript, last_word_close_ts, last_accept_time
#     if not current_word:
#         return
#     now = time.time()
#     if not force:
#         idle = now - last_accept_time
#         if idle < WORD_PAUSE:
#             return
#         if (now - last_word_close_ts) < 0.3:
#             return
#     word = "".join(current_word)
#     if word:
#         transcript += word + " "
#         tts_say(word)
#     current_word = []
#     last_word_close_ts = now
#     last_accept_time = now  # reset inactivity timer after finalizing

# def finalize_on_no_hand(hand_present: bool):
#     """If no hand for NO_HAND_PAUSE seconds, force a word boundary."""
#     global last_hand_seen, was_hand_present, last_accept_time
#     now = time.time()
#     if hand_present:
#         last_hand_seen = now
#     else:
#         if was_hand_present and (now - last_hand_seen) >= NO_HAND_PAUSE:
#             finalize_current_word(force=True)
#             _append_space_once()
#             last_accept_time = now
#             last_hand_seen = now

# # ---------- MAIN LOOP ----------
# with mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.65,
#     min_tracking_confidence=0.65
# ) as hands:

#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         hand_present = results.multi_hand_landmarks is not None
#         if hand_present:
#             last_hand_seen = time.time()

#             hand_landmarks = results.multi_hand_landmarks[0]
#             features = extract_features(hand_landmarks)

#             # Predict with probabilities
#             probs = model.predict_proba(features)[0]
#             pred_idx = int(np.argmax(probs))
#             conf = float(np.max(probs))
#             pred_label = le.inverse_transform([pred_idx])[0].upper()

#             # use only confident frames for voting
#             if conf >= CONF_THRESH:
#                 pred_buf.append(pred_label)

#             # majority vote & stability check
#             stable_label, count = (None, 0)
#             if pred_buf:
#                 c = Counter(pred_buf)
#                 stable_label, count = c.most_common(1)[0]

#             if stable_label and count >= STABLE_NEED:
#                 if stable_label == "SPACE":
#                     finalize_current_word(force=True)
#                     _append_space_once()
#                     last_accept_time = time.time()
#                 elif stable_label == "END":
#                     finalize_current_word(force=True)
#                     final = transcript.strip()
#                     if final:
#                         tts_say(final)
#                     transcript = ""
#                     last_accept_time = time.time()
#                 elif stable_label == "DEL":
#                     if current_word:
#                         current_word.pop()
#                     else:
#                         transcript = transcript.rstrip()
#                         parts = transcript.split()
#                         if parts:
#                             parts = parts[:-1]
#                         transcript = (" ".join(parts) + " ") if parts else ""
#                     last_accept_time = time.time()
#                 else:
#                     accept_label(stable_label)

#                 pred_buf.clear()  # avoid rapid repeats

#             # Draw landmarks + HUD
#             mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#             if DRAW_CONFIDENCE:
#                 cv2.putText(
#                     frame,
#                     f"{pred_label} ({conf:.2f})",
#                     (10, 40),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     1,
#                     (0, 255, 0) if conf >= CONF_THRESH else (0, 200, 200),
#                     2,
#                 )

#         # word boundaries
#         finalize_on_no_hand(hand_present)
#         finalize_current_word(force=False)

#         # UI text
#         display_current = "".join(current_word)
#         display_text = (transcript + display_current).strip()
#         cv2.putText(frame, f"Text: {display_text}", (10, 80),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
#         cv2.putText(frame, f"[Q] quit  [V] voice  [C] clear   Pause>{WORD_PAUSE:.1f}s => space+speech",
#                     (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)

#         cv2.imshow("Live Translator (per-utterance TTS)", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord('v'):
#             msg = (transcript + "".join(current_word)).strip()
#             if msg:
#                 tts_say(msg)
#         elif key == ord('c'):
#             pred_buf.clear()
#             current_word.clear()
#             transcript = ""
#             last_accept_time = time.time()

#         was_hand_present = hand_present

# # ---------- CLEANUP ----------
# cap.release()
# cv2.destroyAllWindows()











#############   33333333333333333333333333333333333333333   ############################

import cv2
import numpy as np
import mediapipe as mp
import joblib
import time
import threading
from collections import deque, Counter
import pyttsx3

# ---------- LOAD MODEL ----------
model = joblib.load("sign_model.pkl")
le = joblib.load("label_encoder.pkl")

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ---------- FEATURES ----------
def extract_features(hand_landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
    wrist = pts[0].copy()
    pts -= wrist
    max_dist = np.linalg.norm(pts, axis=1).max()
    if max_dist > 0:
        pts /= max_dist
    return pts.flatten().reshape(1, -1)   # (1,63)

# ---------- CONFIG ----------
CONF_THRESH       = 0.50   # min probability to count a frame
VOTE_WINDOW       = 12     # frames for majority vote
STABLE_NEED       = 7      # min same-label votes in window to accept
LETTER_DEBOUNCE   = 0.50   # seconds between accepted labels
WORD_PAUSE        = 1.60   # inactivity => finalize word + space + speak (per word)
NO_HAND_PAUSE     = 1.80   # no hand => finalize word + space
SENTENCE_PAUSE    = 4.00   # long idle => speak WHOLE sentence and clear
DRAW_CONFIDENCE   = True

# ---------- PER-UTTERANCE TTS (fresh engine each time) ----------
_last_tts_thread = None
_tts_lock = threading.Lock()

def _speak_once(text: str, rate=160, volume=1.0, voice_id=None):
    try:
        eng = pyttsx3.init()
        eng.setProperty("rate", rate)
        eng.setProperty("volume", volume)
        if voice_id is not None:
            try:
                eng.setProperty("voice", voice_id)
            except Exception:
                pass
        eng.say(text)
        eng.runAndWait()
        try:
            eng.stop()
        except Exception:
            pass
    except Exception as e:
        print("TTS error:", e)

def tts_say(text: str):
    """Fire-and-forget speech that never blocks the main loop and never reuses a stale engine."""
    global _last_tts_thread
    text = (text or "").strip()
    if not text:
        return
    with _tts_lock:
        if _last_tts_thread and _last_tts_thread.is_alive():
            # allow overlap; or join(timeout) to serialize if you prefer
            pass
        th = threading.Thread(target=_speak_once, args=(text,), daemon=True)
        th.start()
        _last_tts_thread = th
    print("SAY ->", text)  # debug

# ---------- STATE ----------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("❌ Cannot open webcam")

pred_buf = deque(maxlen=VOTE_WINDOW)

current_word = []     # list of letters being built
transcript   = ""     # full string with spaces between words

last_accept_time   = time.time()  # last time a letter/word/boundary was accepted
last_word_close_ts = 0.0          # when we last auto-finalized a word
last_hand_seen     = time.time()
was_hand_present   = False

def _append_space_once():
    """Ensure transcript ends with a single space (no double spaces)."""
    global transcript
    transcript = transcript.rstrip() + " "

def accept_label(label: str):
    """Accept a stable label (letter or whole-word)."""
    global last_accept_time, current_word, transcript
    now = time.time()
    if now - last_accept_time < LETTER_DEBOUNCE:
        return

    # Treat multi-char labels as whole words (HELLO, PLEASE, etc.)
    if len(label) > 1:
        if current_word:
            word = "".join(current_word)
            if word:
                transcript += word + " "
                tts_say(word)
                current_word = []
        transcript += label + " "
        tts_say(label)
    else:
        current_word.append(label)

    last_accept_time = now

def finalize_current_word(force: bool = False):
    """Finalize current letters into a word and speak it."""
    global current_word, transcript, last_word_close_ts, last_accept_time
    if not current_word:
        return
    now = time.time()
    if not force:
        idle = now - last_accept_time
        if idle < WORD_PAUSE:
            return
        if (now - last_word_close_ts) < 0.3:
            return
    word = "".join(current_word)
    if word:
        transcript += word + " "
        tts_say(word)
    current_word = []
    last_word_close_ts = now
    last_accept_time = now  # reset inactivity timer after finalizing

def finalize_on_no_hand(hand_present: bool):
    """If no hand for NO_HAND_PAUSE seconds, force a word boundary."""
    global last_hand_seen, was_hand_present, last_accept_time
    now = time.time()
    if hand_present:
        last_hand_seen = now
    else:
        if was_hand_present and (now - last_hand_seen) >= NO_HAND_PAUSE:
            finalize_current_word(force=True)
            _append_space_once()
            last_accept_time = now
            last_hand_seen = now

def maybe_speak_sentence_on_long_pause():
    """
    If there has been no activity for SENTENCE_PAUSE seconds,
    speak the entire sentence (including any partial word) and clear buffers.
    """
    global transcript, current_word, last_accept_time
    now = time.time()
    if (now - last_accept_time) >= SENTENCE_PAUSE:
        full_text = (transcript + "".join(current_word)).strip()
        if full_text:
            tts_say(full_text)
            # Clear buffers to start a fresh sentence after speaking
            transcript = ""
            current_word.clear()
            last_accept_time = now  # prevent immediate retrigger

# ---------- MAIN LOOP ----------
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
) as hands:

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_present = results.multi_hand_landmarks is not None
        if hand_present:
            last_hand_seen = time.time()

            hand_landmarks = results.multi_hand_landmarks[0]
            features = extract_features(hand_landmarks)

            # Predict with probabilities
            probs = model.predict_proba(features)[0]
            pred_idx = int(np.argmax(probs))
            conf = float(np.max(probs))
            pred_label = le.inverse_transform([pred_idx])[0].upper()

            # use only confident frames for voting
            if conf >= CONF_THRESH:
                pred_buf.append(pred_label)

            # majority vote & stability check
            stable_label, count = (None, 0)
            if pred_buf:
                c = Counter(pred_buf)
                stable_label, count = c.most_common(1)[0]

            if stable_label and count >= STABLE_NEED:
                if stable_label == "SPACE":
                    finalize_current_word(force=True)
                    _append_space_once()
                    last_accept_time = time.time()
                elif stable_label == "END":
                    # Speak whole sentence immediately on END
                    final = (transcript + "".join(current_word)).strip()
                    if final:
                        tts_say(final)
                    transcript = ""
                    current_word.clear()
                    last_accept_time = time.time()
                elif stable_label == "DEL":
                    if current_word:
                        current_word.pop()
                    else:
                        transcript = transcript.rstrip()
                        parts = transcript.split()
                        if parts:
                            parts = parts[:-1]
                        transcript = (" ".join(parts) + " ") if parts else ""
                    last_accept_time = time.time()
                else:
                    accept_label(stable_label)

                pred_buf.clear()  # avoid rapid repeats

            # Draw landmarks + HUD
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            if DRAW_CONFIDENCE:
                cv2.putText(
                    frame,
                    f"{pred_label} ({conf:.2f})",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0) if conf >= CONF_THRESH else (0, 200, 200),
                    2,
                )

        # word boundaries + sentence on long pause
        finalize_on_no_hand(hand_present)
        finalize_current_word(force=False)
        maybe_speak_sentence_on_long_pause()

        # UI text
        display_current = "".join(current_word)
        display_text = (transcript + display_current).strip()
        cv2.putText(frame, f"Text: {display_text}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        cv2.putText(
            frame,
            f"[Q] quit  [V] voice  [C] clear   Word pause>{WORD_PAUSE:.1f}s | Sentence pause>{SENTENCE_PAUSE:.1f}s",
            (10, 115),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1
        )

        cv2.imshow("Live Translator (per-utterance TTS + sentence pause)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('v'):
            msg = (transcript + "".join(current_word)).strip()
            if msg:
                tts_say(msg)
        elif key == ord('c'):
            pred_buf.clear()
            current_word.clear()
            transcript = ""
            last_accept_time = time.time()

        was_hand_present = hand_present

# ---------- CLEANUP ----------
cap.release()
cv2.destroyAllWindows()
