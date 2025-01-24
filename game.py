import cv2
import numpy as np
import mediapipe as mp
import random
import time
from pygame import mixer
import os

class RockPaperScissors:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Load assets
        self.load_assets()
        
        # Game states
        self.page = "start"  # start, game, result
        self.game_state = "countdown"  # countdown, playing, break
        self.countdown_timer = 0
        self.break_timer = 0
        
        # Score tracking
        self.round = 0
        self.max_rounds = 3
        self.human_score = 0
        self.ai_score = 0
        
        # Move tracking
        self.human_move = None
        self.ai_move = None
        self.round_result = None

    def load_assets(self):
        # Load and resize images
        self.bg_image = cv2.imread('assets/bg.jpg')
        self.bg_image = cv2.resize(self.bg_image, (1580, 920))
        
        self.ai_images = {
            'rock': cv2.resize(cv2.imread('assets/rock.jpg'), (640, 480)),
            'paper': cv2.resize(cv2.imread('assets/paper.jpg'), (640, 480)),
            'scissors': cv2.resize(cv2.imread('assets/scissor.jpg'), (640, 480))
        }
        
        # Load videos
        self.win_video = cv2.VideoCapture('assets/win.mp4')
        self.lose_video = cv2.VideoCapture('assets/lose.mp4')

    def create_start_page(self):
        # Create start page with background and button
        start_frame = self.bg_image.copy()
        
        # Add game title
        cv2.putText(start_frame, "ROCK PAPER SCISSORS", 
                    (320, 200), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 5)
        
        # Create start button
        button_x, button_y = 490, 350
        button_w, button_h = 350, 80
        cv2.rectangle(start_frame, (button_x, button_y), 
                     (button_x + button_w, button_y + button_h), (0, 255, 0), -1)
        cv2.putText(start_frame, "START GAME", 
                    (button_x + 50, button_y + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        return start_frame

    def create_game_page(self, human_frame, show_ai=True):
        game_frame = self.bg_image.copy()
        
        # Add human frame
        human_frame = cv2.resize(human_frame, (640, 480))
        game_frame[120:600, 0:640] = human_frame
        
        # Add AI frame if needed
        if show_ai and self.ai_move:
            ai_frame = self.ai_images[self.ai_move]
            game_frame[120:600, 640:1280] = ai_frame
        
        # Add scores and round info
        cv2.putText(game_frame, f"Round: {self.round}/{self.max_rounds}", 
                    (550, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(game_frame, f"Human: {self.human_score} AI: {self.ai_score}", 
                    (550, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return game_frame

    def create_result_page(self):
        # Determine winner and play appropriate video
        is_human_winner = self.human_score > self.ai_score
        video = self.win_video if is_human_winner else self.lose_video
        
        result_frame = None
        if video.isOpened():
            ret, result_frame = video.read()
            if ret:
                result_frame = cv2.resize(result_frame, (1580, 920))
        
        if result_frame is None:
            result_frame = self.bg_image.copy()
        
        # Add final score
        cv2.putText(result_frame, "GAME OVER!", 
                    (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
        cv2.putText(result_frame, f"Final Score:", 
                    (500, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(result_frame, f"Human: {self.human_score} - AI: {self.ai_score}", 
                    (450, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        winner_text = "You Win!" if is_human_winner else "AI Wins!"
        if self.human_score == self.ai_score:
            winner_text = "It's a Tie!"
        cv2.putText(result_frame, winner_text, 
                    (500, 350), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
        
        cv2.putText(result_frame, "Press 'R' to Play Again", 
                    (450, 650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return result_frame

    def detect_gesture(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        if not results.multi_hand_landmarks:
            return None
            
        hand_landmarks = results.multi_hand_landmarks[0]
        self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        # Get landmark positions for gesture detection
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y])
        
        # Detect gestures
        if self.is_rock(landmarks):
            return "rock"
        elif self.is_paper(landmarks):
            return "paper"
        elif self.is_scissors(landmarks):
            return "scissors"
        return None

    def is_rock(self, landmarks):
        return (abs(landmarks[4][0] - landmarks[8][0]) < 0.1 and
                abs(landmarks[4][1] - landmarks[8][1]) < 0.1)

    def is_paper(self, landmarks):
        return (landmarks[8][1] < landmarks[6][1] and
                landmarks[12][1] < landmarks[10][1] and
                landmarks[16][1] < landmarks[14][1] and
                landmarks[20][1] < landmarks[18][1])

    def is_scissors(self, landmarks):
        return (landmarks[8][1] < landmarks[6][1] and
                landmarks[12][1] < landmarks[10][1] and
                landmarks[16][1] > landmarks[14][1] and
                landmarks[20][1] > landmarks[18][1])

    def check_button_click(self, event, x, y, flags, param):
        if self.page == "start" and event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is within start button bounds
            if 490 <= x <= 790 and 350 <= y <= 430:
                self.page = "game"
                self.game_state = "countdown"
                self.countdown_timer = time.time()

    def run(self):
        cv2.namedWindow('Rock Paper Scissors')
        cv2.setMouseCallback('Rock Paper Scissors', self.check_button_click)
        
        while True:
            if self.page == "start":
                frame = self.create_start_page()
                
            elif self.page == "game":
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                frame = cv2.flip(frame, 1)
                
                if self.game_state == "countdown":
                    game_frame = self.create_game_page(frame, False)
                    time_left = int(3 - (time.time() - self.countdown_timer))
                    
                    if time_left <= 0:
                        self.game_state = "playing"
                    else:
                        cv2.putText(game_frame, str(time_left), 
                                  (600, 400), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8)
                    frame = game_frame
                    
                elif self.game_state == "playing":
                    gesture = self.detect_gesture(frame)
                    game_frame = self.create_game_page(frame, False)
                    
                    if gesture:
                        self.human_move = gesture
                        self.ai_move = random.choice(['rock', 'paper', 'scissors'])
                        
                        # Determine winner
                        if self.human_move == self.ai_move:
                            self.round_result = "tie"
                        elif ((self.human_move == "rock" and self.ai_move == "scissors") or
                              (self.human_move == "paper" and self.ai_move == "rock") or
                              (self.human_move == "scissors" and self.ai_move == "paper")):
                            self.round_result = "human"
                            self.human_score += 1
                        else:
                            self.round_result = "ai"
                            self.ai_score += 1
                        
                        self.round += 1
                        self.game_state = "break"
                        self.break_timer = time.time()
                    
                    frame = game_frame
                    
                elif self.game_state == "break":
                    game_frame = self.create_game_page(frame, True)
                    time_left = int(2 - (time.time() - self.break_timer))
                    
                    if time_left <= 0:
                        if self.round >= self.max_rounds:
                            self.page = "result"
                        else:
                            self.game_state = "countdown"
                            self.countdown_timer = time.time()
                    else:
                        result_text = f"Round {self.round} Result: "
                        if self.round_result == "tie":
                            result_text += "Tie!"
                        elif self.round_result == "human":
                            result_text += "You Win!"
                        else:
                            result_text += "AI Wins!"
                        
                        cv2.putText(game_frame, result_text, (400, 360),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
                    frame = game_frame
                    
            elif self.page == "result":
                frame = self.create_result_page()
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('r'):
                    self.__init__()
                    
            cv2.imshow('Rock Paper Scissors', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    game = RockPaperScissors()
    game.run()