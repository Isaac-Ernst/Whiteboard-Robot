import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200           
DELAY = 0.004                 

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 27, 22, 6    
M2_DIR, M2_STEP, M2_EN = 4, 17, 5
SERVO_PIN = 18                      

# --- Servo Angles (Adjust these for your marker holder) ---
PEN_UP_ANGLE = 7.5    
PEN_DOWN_ANGLE = 11.0 

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES   
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV   

# Global state for string lengths
current_left_in = 18.0   
current_right_in = 18.0  
pwm = None 

def setup_gpio():
    global pwm
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Motor Pins
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    # Servo Setup
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50) 
    pwm.start(PEN_UP_ANGLE) 
    
    # Start with motors disabled
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 

def set_pen(state):
    """Moves the servo to lift or drop the pen"""
    global pwm
    if state == "UP":
        print("--> LIFTING PEN")
        pwm.ChangeDutyCycle(PEN_UP_ANGLE)
        time.sleep(0.3) 
    elif state == "DOWN":
        print("--> DROPPING PEN")
        pwm.ChangeDutyCycle(PEN_DOWN_ANGLE)
        time.sleep(0.3)

def move_motors(target_x, target_y):
    """Calculates lengths and moves the motors proportionally"""
    global current_left_in, current_right_in
    
    # --- THE IMAGE FLIP FIX ---
    # Inverts the X-axis to mirror the drawing horizontally
    target_x = MOTOR_DISTANCE_INCHES - target_x
    # --------------------------
    
    # Calculate target physical lengths
    target_left_in = math.sqrt(target_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + target_y**2)
    
    # Find the Delta
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # Set Directions
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left = abs(steps_left)
    steps_right = abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0:
        return 
        
    # Wake up motors
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)
    
    # Proportional Stepping Algorithm
    left_counter = 0
    right_counter = 0
    
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

    # Update memory
    current_left_in = target_left_in
    current_right_in = target_right_in

def run_drawing_file(filename):
    """Reads the text file and executes commands"""
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                command = line.strip().upper()
                if not command or command.startswith("#"):
                    continue 
                
                if command == "UP":
                    set_pen("UP")
                elif command == "DOWN":
                    set_pen("DOWN")
                elif command.startswith("MOVE"):
                    parts = command.split()
                    if len(parts) == 3:
                        x = float(parts[1])
                        y = float(parts[2])
                        move_motors(x, y)
    except FileNotFoundError:
        print(f"Error: Could not find '{filename}'")

# --- Execution ---
try:
    setup_gpio()
    print("System Ready. Pen Homing to (18,0).")
    time.sleep(1)
    
    run_drawing_file("drawing.txt")
    
    # Finish up
    set_pen("UP")
    move_motors(18.0, 0.0)  # Returning to center will still work perfectly
    print("Drawing Complete! Returned to Home.")

except KeyboardInterrupt:
    print("\nEmergency Stop.")

finally:
    if pwm:
        pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 
    print("Motors disabled and safe.")
    