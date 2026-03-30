import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200
DELAY = 0.002 # Speed of the motors

# --- Motor Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5 
M2_DIR, M2_STEP, M2_EN = 27, 22, 6

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

# --- Global Memory ---
# We assume the robot starts perfectly homed at top-center
current_left_in = MOTOR_DISTANCE_INCHES / 2.0
current_right_in = MOTOR_DISTANCE_INCHES / 2.0

def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    # Disable motors while sitting
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

def set_pen(state):
    """Dummy function for future servo implementation"""
    if state == "UP":
        print("--> PEN LIFTED (Servo moving to safe angle)")
        # Future: pwm.ChangeDutyCycle(lift_angle)
        time.sleep(0.5) 
    elif state == "DOWN":
        print("--> PEN DROPPED (Servo moving to drawing angle)")
        # Future: pwm.ChangeDutyCycle(draw_angle)
        time.sleep(0.5)

def move_motors(target_x, target_y):
    """Calculates lengths and moves the motors proportionally"""
    global current_left_in, current_right_in
    
    # Calculate target physical lengths
    target_left_in = math.sqrt(target_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + target_y**2)
    
    # Find the Delta
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # Set Directions (Modify True/False if motors spin the wrong way)
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left = abs(steps_left)
    steps_right = abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0:
        return 
        
    print(f"Moving to X:{target_x} Y:{target_y} | L-Steps: {steps_left} R-Steps: {steps_right}")
    
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

    # Update robot memory
    current_left_in = target_left_in
    current_right_in = target_right_in

def run_drawing_file(filename):
    """Reads the text file and executes commands"""
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                command = line.strip().upper()
                if not command or command.startswith("#"):
                    continue # Skip empty lines and comments
                
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
                    else:
                        print(f"Error on line {line_num}: Invalid MOVE format. Use 'MOVE X Y'")
    except FileNotFoundError:
        print(f"Error: Could not find '{filename}'")

# --- Main Execution ---
try:
    setup_gpio()
    print("System Initialized.")
    print("Manually pull your strings to top center before drawing!")
    time.sleep(2) # Give you a moment to read the terminal
    
    run_drawing_file("drawing.txt")
    
    print("Drawing Complete!")

except KeyboardInterrupt:
    print("\nEmergency Stop Triggered.")

finally:
    # Lock motors down
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    print("Motors disabled and safe.")
