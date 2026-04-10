import math
import time
import RPi.GPIO as GPIO
import sys

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0 
SPOOL_DIAMETER_INCHES = 1.0  
STEPS_PER_REV = 200          
DELAY = 0.002                

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5   
M2_DIR, M2_STEP, M2_EN = 27, 22, 6  
SERVO_PIN = 18                      

# --- Servo Angles ---
PEN_UP_ANGLE = 7.5    
PEN_DOWN_ANGLE = 11.0 

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

# Global state
current_left_in = 18.0 
current_right_in = 18.0
pwm = None 

def setup_gpio():
    global pwm
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50) 
    pwm.start(PEN_UP_ANGLE) 
    
    # Keep motors locked from the start
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)

def set_pen(state):
    global pwm
    if state == "UP":
        pwm.ChangeDutyCycle(PEN_UP_ANGLE)
        time.sleep(0.3) 
    elif state == "DOWN":
        pwm.ChangeDutyCycle(PEN_DOWN_ANGLE)
        time.sleep(0.3)

def move_motors(target_x, target_y):
    global current_left_in, current_right_in
    target_left_in = math.sqrt(target_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + target_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left = abs(steps_left)
    steps_right = abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0: return 
    
    # Ensure motors are engaged
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)
    
    left_counter, right_counter = 0, 0
    for _ in range(max_steps):
        left_counter += steps_left
        right_counter += steps_right
        step_L, step_R = False, False
        if left_counter >= max_steps:
            GPIO.output(M1_STEP, GPIO.HIGH)
            left_counter -= max_steps
            step_L = True
        if right_counter >= max_steps:
            GPIO.output(M2_STEP, GPIO.HIGH)
            right_counter -= max_steps
            step_R = True
        time.sleep(DELAY)
        if step_L: GPIO.output(M1_STEP, GPIO.LOW)
        if step_R: GPIO.output(M2_STEP, GPIO.LOW)
        time.sleep(DELAY)

    current_left_in = target_left_in
    current_right_in = target_right_in

def show_menu():
    """The interactive menu that keeps motors locked"""
    print("\n" + "="*30)
    print("      ROBOT PAUSED MENU")
    print("="*30)
    print("1. RESUME Drawing")
    print("2. RESTART from beginning")
    print("3. STOP and Disable Motors (Emergency)")
    print("="*30)
    
    while True:
        choice = input("Enter selection (1-3): ").strip()
        if choice == '1':
            print("--> Resuming...")
            return "RESUME"
        elif choice == '2':
            print("--> Restarting File...")
            return "RESTART"
        elif choice == '3':
            print("--> Shutting Down...")
            return "STOP"
        else:
            print("Invalid choice.")

def run_drawing_file(filename):
    while True: # Outer loop for Restarts
        try:
            with open(filename, 'r') as file:
                print(f"\nStarted drawing: {filename}")
                for line_num, line in enumerate(file, 1):
                    command = line.strip().upper()
                    if not command or command.startswith("#"): continue 
                    
                    try:
                        if command == "UP":
                            set_pen("UP")
                        elif command == "DOWN":
                            set_pen("DOWN")
                        elif command.startswith("MOVE"):
                            parts = command.split()
                            if len(parts) == 3:
                                move_motors(float(parts[1]), float(parts[2]))
                    
                    except KeyboardInterrupt:
                        # This catches Ctrl+C during a MOVE and opens the menu
                        action = show_menu()
                        if action == "RESUME":
                            continue # Just keep going with the next line
                        elif action == "RESTART":
                            break # Breaks inner loop to trigger outer loop restart
                        elif action == "STOP":
                            return # Exits the whole function

                else: # This runs if the 'for' loop finishes naturally
                    print("Drawing Complete!")
                    return

        except FileNotFoundError:
            print(f"Error: Could not find '{filename}'")
            return

# --- Execution ---
try:
    setup_gpio()
    print("System Initialized. Motors Locked.")
    print("Home the pen to (18,0) manually, then press Enter.")
    input("Press Enter to start drawing...")
    
    run_drawing_file("drawing.txt")

finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) # Release motors
    GPIO.output(M2_EN, GPIO.HIGH)
    GPIO.cleanup()
    print("\nMotors disabled. Hardware safe.")
    