import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import random
from cvzone.HandTrackingModule import HandDetector
import threading
import os
import logging
from PIL import Image, ImageTk
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
tf.get_logger().setLevel(logging.ERROR)

class RockPaperScissors:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rock Paper Scissors")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2C3E50')
        
        # Initialize variables
        self.game_active = False
        self.camera_active = False
        self.player_score = 0
        self.ai_score = 0
        self.countdown = 3
        self.round_number = 0  # Add round counter
        self.max_rounds = 5    # Set maximum rounds
        self.detector = HandDetector(maxHands=1)
        
        # Replace the choices dictionary with image paths
        self.choices = {
            "rock": self.load_image("assets/rock.png", (100, 100)),
            "paper": self.load_image("assets/paper.png", (100, 100)),
            "scissors": self.load_image("assets/scissors.png", (100, 100))
        }
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Game.TFrame', background='#34495E')
        self.style.configure('Game.TLabel', background='#34495E', foreground='white')
        self.style.configure('Game.TButton', 
                           background='#3498DB', 
                           foreground='white',
                           padding=10,
                           font=('Arial', 12, 'bold'))
        
        self.create_welcome_screen()
        
    def load_image(self, path, size):
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
        
    def create_welcome_screen(self):
        self.welcome_frame = ttk.Frame(self.root, style='Game.TFrame')
        self.welcome_frame.pack(expand=True, fill='both')
        
        # Title with fancy styling
        title_frame = ttk.Frame(self.welcome_frame, style='Game.TFrame')
        title_frame.pack(pady=50)
        
        title = ttk.Label(title_frame, 
                         text="ROCK PAPER SCISSORS",
                         font=("Arial", 36, "bold"),
                         style='Game.TLabel')
        title.pack()
        
        subtitle = ttk.Label(title_frame,
                           text="Human vs AI",
                           font=("Arial", 18),
                           style='Game.TLabel')
        subtitle.pack(pady=10)
        
        # Preview symbols
        preview_frame = ttk.Frame(self.welcome_frame, style='Game.TFrame')
        preview_frame.pack(pady=30)
        
        for image in self.choices.values():
            label = ttk.Label(preview_frame, 
                            image=image,
                            style='Game.TLabel')
            label.pack(side=tk.LEFT, padx=20)
        
        # Instructions
        instructions = ttk.Label(self.welcome_frame,
                               text="Show your hand gesture to the camera!\nRock: Closed fist | Paper: Open hand | Scissors: Victory sign",
                               font=("Arial", 14),
                               justify=tk.CENTER,
                               style='Game.TLabel')
        instructions.pack(pady=30)
        
        # Start button
        self.start_btn = tk.Button(self.welcome_frame,
                                 text="START GAME",
                                 font=("Arial", 16, "bold"),
                                 bg='#27AE60',
                                 fg='white',
                                 padx=30,
                                 pady=15,
                                 relief=tk.RAISED,
                                 command=self.start_game)
        self.start_btn.pack(pady=20)
        
        # Bind hover effects
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.configure(bg='#2ECC71'))
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.configure(bg='#27AE60'))
        
    def create_game_screen(self):
        self.game_frame = ttk.Frame(self.root, style='Game.TFrame')
        self.game_frame.pack(expand=True, fill='both')
        
        # Top section with scores and timer
        top_frame = ttk.Frame(self.game_frame, style='Game.TFrame')
        top_frame.pack(fill='x', pady=20)
        
        self.score_label = ttk.Label(top_frame,
                                   text="Player: 0  |  AI: 0",
                                   font=("Arial", 24, "bold"),
                                   style='Game.TLabel')
        self.score_label.pack()
        
        self.timer_label = ttk.Label(top_frame,
                                   text="Time: 3",
                                   font=("Arial", 20),
                                   style='Game.TLabel')
        self.timer_label.pack(pady=10)
        
        # Main game area
        game_area = ttk.Frame(self.game_frame, style='Game.TFrame')
        game_area.pack(expand=True, fill='both', padx=20)
        
        # Player camera feed
        player_frame = ttk.Frame(game_area, style='Game.TFrame')
        player_frame.pack(side=tk.LEFT, expand=True)
        
        player_label = ttk.Label(player_frame,
                               text="YOU",
                               font=("Arial", 18, "bold"),
                               style='Game.TLabel')
        player_label.pack(pady=10)
        
        self.camera_label = ttk.Label(player_frame)
        self.camera_label.pack()
        
        # VS label
        vs_label = ttk.Label(game_area,
                            text="VS",
                            font=("Arial", 36, "bold"),
                            style='Game.TLabel')
        vs_label.pack(side=tk.LEFT, padx=40)
        
        # AI choice
        ai_frame = ttk.Frame(game_area, style='Game.TFrame')
        ai_frame.pack(side=tk.LEFT, expand=True)
        
        ai_label = ttk.Label(ai_frame,
                            text="AI",
                            font=("Arial", 18, "bold"),
                            style='Game.TLabel')
        ai_label.pack(pady=10)
        
        # Update AI choice label to use a default image if robot.png is not available
        try:
            ai_default_image = self.load_image("assets/BG.png", (100, 100))
        except FileNotFoundError:
            # Use one of the existing images as a placeholder
            ai_default_image = list(self.choices.values())[0]
        
        self.ai_choice_label = ttk.Label(ai_frame,
                                       image=ai_default_image,
                                       style='Game.TLabel')
        self.ai_choice_label.pack()
        
        # Control buttons
        control_frame = ttk.Frame(self.game_frame, style='Game.TFrame')
        control_frame.pack(pady=20)
        
        self.pause_btn = tk.Button(control_frame,
                                 text="PAUSE",
                                 font=("Arial", 14),
                                 bg='#E67E22',
                                 fg='white',
                                 padx=20,
                                 pady=10,
                                 command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=10)
        
        self.quit_btn = tk.Button(control_frame,
                                text="QUIT",
                                font=("Arial", 14),
                                bg='#C0392B',
                                fg='white',
                                padx=20,
                                pady=10,
                                command=self.quit_game)
        self.quit_btn.pack(side=tk.LEFT, padx=10)

    def start_game(self):
        self.welcome_frame.destroy()
        self.create_game_screen()
        self.camera_active = True
        self.game_active = True
        self.cap = cv2.VideoCapture(0)
        self.update_camera()
        self.start_round()
        
    def update_camera(self):
        if self.camera_active:
            ret, frame = self.cap.read()
            if ret:
                hands, frame = self.detector.findHands(frame)
                
                if hands:
                    fingers = self.detector.fingersUp(hands[0])
                    player_choice = self.get_player_choice(fingers)
                    
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (400, 300))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
            
            self.root.after(10, self.update_camera)
            
    def get_player_choice(self, fingers):
        if sum(fingers) == 0:
            return "rock"
        elif sum(fingers) == 5:
            return "paper"
        elif sum(fingers) == 2 and fingers[1] and fingers[2]:
            return "scissors"
        return None
        
    def start_round(self):
        if self.game_active:
            self.countdown = 3
            self.update_timer()
            
    def update_timer(self):
        if self.countdown > 0 and self.game_active:
            self.timer_label.config(text=f"Time: {self.countdown}")
            self.countdown -= 1
            self.root.after(1000, self.update_timer)
        elif self.game_active:
            self.play_round()
            
    def play_round(self):
        if self.round_number >= self.max_rounds:
            self.show_final_results()
            return

        ai_choice = random.choice(list(self.choices.keys()))
        self.ai_choice_label.configure(image=self.choices[ai_choice])
        
        ret, frame = self.cap.read()
        hands, _ = self.detector.findHands(frame)
        
        if hands:
            fingers = self.detector.fingersUp(hands[0])
            player_choice = self.get_player_choice(fingers)
            
            if player_choice:
                self.determine_winner(player_choice, ai_choice)
                self.round_number += 1  # Increment round counter
                self.show_break_screen()
                return
        
        # If no valid choice was made, restart the round
        self.start_round()
        
    def determine_winner(self, player_choice, ai_choice):
        if player_choice == ai_choice:
            return
        
        winning_combinations = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if winning_combinations[player_choice] == ai_choice:
            self.player_score += 1
            result = "YOU WIN!"
        else:
            self.ai_score += 1
            result = "AI WINS!"
            
        # Update score at the top
        self.score_label.config(text=f"Player: {self.player_score}  |  AI: {self.ai_score}")
        
        # Show round result briefly
        result_label = ttk.Label(self.game_frame,
                               text=result,
                               font=("Arial", 36, "bold"),
                               style='Game.TLabel')
        result_label.place(relx=0.5, rely=0.4, anchor='center')
        self.root.after(800, result_label.destroy)  # Remove after 0.8 seconds
    
    def show_break_screen(self):
        if self.game_active:
            # Clear existing widgets in the center of the screen
            for widget in self.game_frame.winfo_children():
                if isinstance(widget, ttk.Label) and widget not in [self.score_label, self.timer_label]:
                    widget.destroy()
            
            # Create a break frame with background
            break_frame = ttk.Frame(self.game_frame, style='Game.TFrame')
            break_frame.place(relx=0.5, rely=0.5, anchor='center')
            
            # Break timer with minimal design
            self.break_countdown = 3
            self.break_timer_label = ttk.Label(break_frame,
                                             text=str(self.break_countdown),
                                             font=("Arial", 120, "bold"),
                                             style='Game.TLabel')
            self.break_timer_label.pack()
            
            self.update_break_timer(break_frame)
    
    def update_break_timer(self, break_frame):
        if self.break_countdown > 0:
            self.break_timer_label.configure(text=str(self.break_countdown))
            
            # Simple scale animation
            def scale_text(size):
                self.break_timer_label.configure(font=("Arial", size, "bold"))
            
            self.root.after(0, lambda: scale_text(120))
            self.root.after(100, lambda: scale_text(130))
            self.root.after(200, lambda: scale_text(120))
            
            self.break_countdown -= 1
            self.root.after(1000, lambda: self.update_break_timer(break_frame))
        else:
            break_frame.destroy()
            self.start_round()

    def show_final_results(self):
        self.game_active = False
        self.camera_active = False
        
        # Clear game frame
        for widget in self.game_frame.winfo_children():
            widget.destroy()
        
        # Show final results
        result_text = f"Game Over!\n\nFinal Score:\nPlayer: {self.player_score}\nAI: {self.ai_score}\n\n"
        if self.player_score > self.ai_score:
            result_text += "You Win! 🎉"
        elif self.player_score < self.ai_score:
            result_text += "AI Wins! 🤖"
        else:
            result_text += "It's a Tie! 🤝"
            
        results_label = ttk.Label(self.game_frame,
                                text=result_text,
                                font=("Arial", 24, "bold"),
                                style='Game.TLabel')
        results_label.pack(pady=50)
        
        # Add play again button
        play_again_btn = tk.Button(self.game_frame,
                                 text="Play Again",
                                 font=("Arial", 16, "bold"),
                                 bg='#27AE60',
                                 fg='white',
                                 padx=30,
                                 pady=15,
                                 command=self.restart_game)
        play_again_btn.pack(pady=20)
        
        quit_btn = tk.Button(self.game_frame,
                           text="Quit",
                           font=("Arial", 16, "bold"),
                           bg='#C0392B',
                           fg='white',
                           padx=30,
                           pady=15,
                           command=self.quit_game)
        quit_btn.pack(pady=20)

    def restart_game(self):
        # Reset game state
        self.player_score = 0
        self.ai_score = 0
        self.round_number = 0
        self.countdown = 3
        
        # Clear and recreate game screen
        self.game_frame.destroy()
        self.create_game_screen()
        
        # Restart game
        self.camera_active = True
        self.game_active = True
        self.start_round()

    def toggle_pause(self):
        self.game_active = not self.game_active
        if self.game_active:
            self.pause_btn.config(text="PAUSE")
            self.start_round()
        else:
            self.pause_btn.config(text="CONTINUE")
            
    def quit_game(self):
        self.camera_active = False
        self.game_active = False
        if hasattr(self, 'cap'):
            self.cap.release()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = RockPaperScissors()
    game.run()