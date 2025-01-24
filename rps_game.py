import streamlit as st
import cv2
import mediapipe as mp
import random
import time
import numpy as np
from PIL import Image

# Initialize Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialize game variables
if "page" not in st.session_state:
    st.session_state.page = "start"
if "game_state" not in st.session_state:
    st.session_state.game_state = "countdown"
if "countdown_timer" not in st.session_state:
    st.session_state.countdown_timer = 0
if "break_timer" not in st.session_state:
    st.session_state.break_timer = 0
if "round" not in st.session_state:
    st.session_state.round = 0
if "human_score" not in st.session_state:
    st.session_state.human_score = 0
if "ai_score" not in st.session_state:
    st.session_state.ai_score = 0
if "human_move" not in st.session_state:
    st.session_state.human_move = None
if "ai_move" not in st.session_state:
    st.session_state.ai_move = None
if "round_result" not in st.session_state:
    st.session_state.round_result = None

# Load assets
def load_assets():
    assets = {
        "bg": Image.open("assets/bg.jpg").resize((800, 600)),
        "rock": Image.open("assets/rock.jpg").resize((300, 300)),
        "paper": Image.open("assets/paper.jpg").resize((300, 300)),
        "scissors": Image.open("assets/scissor.jpg").resize((300, 300)),
    }
    return assets

assets = load_assets()

# Gesture detection
def detect_gesture(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if not results.multi_hand_landmarks:
        return None

    hand_landmarks = results.multi_hand_landmarks[0]
    landmarks = [[lm.x, lm.y] for lm in hand_landmarks.landmark]

    # Gesture recognition logic
    if is_rock(landmarks):
        return "rock"
    elif is_paper(landmarks):
        return "paper"
    elif is_scissors(landmarks):
        return "scissors"
    return None

def is_rock(landmarks):
    return abs(landmarks[4][0] - landmarks[8][0]) < 0.1 and abs(landmarks[4][1] - landmarks[8][1]) < 0.1

def is_paper(landmarks):
    return (
        landmarks[8][1] < landmarks[6][1]
        and landmarks[12][1] < landmarks[10][1]
        and landmarks[16][1] < landmarks[14][1]
        and landmarks[20][1] < landmarks[18][1]
    )

def is_scissors(landmarks):
    return (
        landmarks[8][1] < landmarks[6][1]
        and landmarks[12][1] < landmarks[10][1]
        and landmarks[16][1] > landmarks[14][1]
        and landmarks[20][1] > landmarks[18][1]
    )

# Pages
def start_page():
    st.image(assets["bg"])
    st.title("Rock Paper Scissors")
    if st.button("Start Game"):
        st.session_state.page = "game"
        st.session_state.game_state = "countdown"
        st.session_state.countdown_timer = time.time()

def game_page():
    st.title("Rock Paper Scissors - Game")
    # Camera input
    frame = st.camera_input("Show your move")
    if frame is not None:
        frame = cv2.imdecode(np.frombuffer(frame.read(), np.uint8), cv2.IMREAD_COLOR)
        frame = cv2.flip(frame, 1)

        if st.session_state.game_state == "countdown":
            time_left = int(3 - (time.time() - st.session_state.countdown_timer))
            if time_left <= 0:
                st.session_state.game_state = "playing"
            st.subheader(f"Game starts in: {time_left} seconds")

        elif st.session_state.game_state == "playing":
            gesture = detect_gesture(frame)
            if gesture:
                st.session_state.human_move = gesture
                st.session_state.ai_move = random.choice(["rock", "paper", "scissors"])

                # Determine round result
                if st.session_state.human_move == st.session_state.ai_move:
                    st.session_state.round_result = "tie"
                elif (
                    (st.session_state.human_move == "rock" and st.session_state.ai_move == "scissors")
                    or (st.session_state.human_move == "paper" and st.session_state.ai_move == "rock")
                    or (st.session_state.human_move == "scissors" and st.session_state.ai_move == "paper")
                ):
                    st.session_state.round_result = "human"
                    st.session_state.human_score += 1
                else:
                    st.session_state.round_result = "ai"
                    st.session_state.ai_score += 1

                st.session_state.round += 1
                st.session_state.game_state = "break"
                st.session_state.break_timer = time.time()

        elif st.session_state.game_state == "break":
            time_left = int(2 - (time.time() - st.session_state.break_timer))
            if time_left <= 0:
                if st.session_state.round >= 3:  # End game after 3 rounds
                    st.session_state.page = "result"
                else:
                    st.session_state.game_state = "countdown"
                    st.session_state.countdown_timer = time.time()
            else:
                st.subheader(f"Round {st.session_state.round} Result: {st.session_state.round_result}")

        # Display game status
        st.text(f"Round: {st.session_state.round}/3")
        st.text(f"Human: {st.session_state.human_score} | AI: {st.session_state.ai_score}")

def result_page():
    st.title("Game Over")
    st.text(f"Final Score: Human {st.session_state.human_score} - AI {st.session_state.ai_score}")
    if st.session_state.human_score > st.session_state.ai_score:
        st.subheader("You Win!")
    elif st.session_state.human_score < st.session_state.ai_score:
        st.subheader("AI Wins!")
    else:
        st.subheader("It's a Tie!")
    if st.button("Play Again"):
        for key in st.session_state.keys():
            del st.session_state[key]

# Main App
if st.session_state.page == "start":
    start_page()
elif st.session_state.page == "game":
    game_page()
elif st.session_state.page == "result":
    result_page()
