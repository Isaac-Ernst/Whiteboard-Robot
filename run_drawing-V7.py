import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200           
DELAY = 0.003                 

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 27, 22, 6    
M2_DIR, M2_STEP, M2_EN = 4, 17, 5
SERVO_PIN = 18                      

# --- Servo Angles ---
PEN_UP_ANGLE = 7.5    
PEN_DOWN_ANGLE = 11.0 

# --- Offset Settings ---
# This pushes the entire drawing 5 inches down to prevent jamming
Y_OFFSET = 5.0 

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES   
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV   

# --- Homing Calculation ---
# Starting at (18, 5) instead of (18, 0)
# L = sqrt(18^2 + 5^2) = 18.6815
HOME_X = 18.0
HOME_Y = 0.0 # This is "logical" 0, which will be physically at 5.0
current_left_in = 18.6815   
current_right_in = 18.6815  
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
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 

def set_pen(state):
    global pwm
    if state == "UP":
        print("--> LIFTING PEN")
        pwm.ChangeDutyCycle(PEN_UP_ANGLE)
    elif state == "DOWN":
        print("--> DROPPING PEN")
        pwm.ChangeDutyCycle(PEN_DOWN_ANGLE)
    time.sleep(0.3)

def move_motors(target_x, target_y):
    global current_left_in, current_right_in
    
    # Apply the Safety Offset to push the drawing down the board
    physical_y = target_y + Y_OFFSET
    
    # Image Flip Fix
    target_x = MOTOR_DISTANCE_INCHES - target_x
    
    # Calculate target physical lengths
    target_left_in = math.sqrt(target_x**2 + physical_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + physical_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left, steps_right = abs(steps_left), abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0: return 
        
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)
    
    l_counter, r_counter = 0, 0
    for _ in range(max_steps):
        l_counter += steps_left
        r_counter += steps_right
        s_L, s_R = False, False
        if l_counter >= max_steps:
            GPIO.output(M1_STEP, GPIO.HIGH)
            l_counter -= max_steps
            s_L = True
        if r_counter >= max_steps:
            GPIO.output(M2_STEP, GPIO.HIGH)
            r_counter -= max_steps
            s_R = True
        time.sleep(DELAY)
        if s_L: GPIO.output(M1_STEP, GPIO.LOW)
        if s_R: GPIO.output(M2_STEP, GPIO.LOW)
        time.sleep(DELAY)

    current_left_in = target_left_in
    current_right_in = target_right_in

def run_drawing_file(filename):
    try:
        with open(filename, 'r') as file:
            for line in file:
                command = line.strip().upper()
                if not command or command.startswith("#"): continue 
                if command == "UP": set_pen("UP")
                elif command == "DOWN": set_pen("DOWN")
                elif command.startswith("MOVE"):
                    parts = command.split()
                    move_motors(float(parts[1]), float(parts[2]))
    except FileNotFoundError:
        print(f"Error: {filename} not found")

# --- Execution ---
try:
    setup_gpio()
    print(f"System Ready. PHYSICALLY HANG PEN AT (18, {Y_OFFSET}) before starting.")
    time.sleep(2)
    
    run_drawing_file("drawing.txt")
    
    # Finish up safely
    set_pen("UP")
    move_motors(HOME_X, HOME_Y)  # Returns to the 5-inch safety mark
    print("Drawing Complete! Returned to Home.")

except KeyboardInterrupt:
    print("\nEmergency Stop.")

finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 
    print("Motors disabled and safe.")
    