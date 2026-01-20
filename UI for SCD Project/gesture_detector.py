import cv2
import mediapipe as mp
import pyautogui
import time

class GestureDetector:
    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False

        # Mediapipe hand detector
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.drawing_utils = mp.solutions.drawing_utils

        # Screen size
        self.screen_width, self.screen_height = pyautogui.size()

        # Variables for gestures
        self.index_x = 0
        self.index_y = 0
        self.last_click_time = 0
        self.prev_index_y = None           # <-- ADDED for scrolling

    def start(self):
        """Starts webcam detection in a loop."""
        self.running = True
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ ERROR: Cannot open webcam")
            return

        print("🎥 Gesture detector started")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame_h, frame_w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)
            hands = result.multi_hand_landmarks

            gesture = "None"

            if hands:
                for hand in hands:
                    self.drawing_utils.draw_landmarks(frame, hand)
                    landmarks = hand.landmark

                    # Loop through landmarks
                    for id, lm in enumerate(landmarks):
                        x = int(lm.x * frame_w)
                        y = int(lm.y * frame_h)

                        # INDEX FINGER TIP (ID 8)
                        if id == 8:
                            cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
                            self.index_x = (x / frame_w) * self.screen_width
                            self.index_y = (y / frame_h) * self.screen_height

                        # THUMB TIP (ID 4)
                        if id == 4:
                            cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
                            thumb_x = (x / frame_w) * self.screen_width
                            thumb_y = (y / frame_h) * self.screen_height

                            distance = abs(self.index_y - thumb_y)

                            # ----- PINCH CLICK -----
                            if distance < 20:
                                gesture = "Click"
                                current_time = time.time()
                                if current_time - self.last_click_time > 0.8:
                                    pyautogui.click()
                                    self.last_click_time = current_time

                            # ----- MOUSE MOVE -----
                            elif distance < 120:
                                gesture = "Move"
                                pyautogui.moveTo(self.index_x, self.index_y)

                            else:
                                gesture = "Hand Open"

                    # ---------------------------------------------------------
                    # 🚀 OPEN PALM SCROLL FEATURE
                    # ---------------------------------------------------------
                    try:
                        fingers_up = 0
                        # tips: 8(index),12(middle),16(ring),20(pinky)
                        for tip_idx in (8, 12, 16, 20):
                            if landmarks[tip_idx].y < landmarks[tip_idx - 2].y:
                                fingers_up += 1
                    except Exception:
                        fingers_up = 0

                    # If all 4 fingers are up → Open Palm
                    if fingers_up == 4:
                        index_frame_y = int(landmarks[8].y * frame_h)

                        if self.prev_index_y is not None:
                            diff = index_frame_y - self.prev_index_y

                            if diff > 15:
                                pyautogui.scroll(-40)
                                gesture = "Scroll Down"

                            elif diff < -15:
                                pyautogui.scroll(40)
                                gesture = "Scroll Up"

                        self.prev_index_y = index_frame_y
                    else:
                        self.prev_index_y = None
                    # ---------------------------------------------------------

            # Emit to frontend
            self.socketio.emit("gesture_update", {"gesture": gesture})

            cv2.imshow("Gesture Mode", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        print("🛑 Gesture detector stopped")

    def stop(self):
        """Stops the gesture loop."""
        print("Stopping detector...")
        self.running = False
