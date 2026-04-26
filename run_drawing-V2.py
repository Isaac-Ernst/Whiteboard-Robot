import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.1   
STEPS_PER_REV = 200           
DELAY = 0.002                 

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5
M2_DIR, M2_STEP, M2_EN = 27, 22, 6
SERVO_PIN = 18                      

# --- Servo Angles ---
PEN_UP_ANGLE = 10.0    # Approximately 90 degrees
PEN_DOWN_ANGLE = 9.0 # Slightly further to press the pen

# --- Positioning & Flip Fixes ---
Y_OFFSET = 5.0              # Pushes drawing down 5" to prevent jamming
DRAWING_HEIGHT_INCHES = 20.0 # Adjust this to the height of your image
FLIP_VERTICAL = False        # Set to False if you want to undo the Y-flip
FLIP_HORIZONTAL = True      # Re-adding the X-flip fix

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES   
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV   

# Homing: Starting at (18, 5)
# L = sqrt(18^2 + 5^2) = 18.68
current_left_in = 18.68   
current_right_in = 18.68  
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
        pwm.ChangeDutyCycle(PEN_UP_ANGLE)
    elif state == "DOWN":
        pwm.ChangeDutyCycle(PEN_DOWN_ANGLE)
    time.sleep(0.3)

def move_motors(target_x, target_y):
    global current_left_in, current_right_in
    
    # --- VERTICAL FLIP FIX ---
    if FLIP_VERTICAL:
        target_y = DRAWING_HEIGHT_INCHES - target_y
    
    # --- HORIZONTAL FLIP FIX ---
    if FLIP_HORIZONTAL:
        target_x = MOTOR_DISTANCE_INCHES - target_x
        
    # Apply safety offset
    physical_y = target_y + Y_OFFSET
    
    # Calculate target physical lengths
    target_left_in = math.sqrt(target_x**2 + physical_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + physical_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    # GPIO.output(M2_DIR, True if steps_right > 0 else False)

    # Reversed Logic
    GPIO.output(M1_DIR, False if steps_left > 0 else True) 
    GPIO.output(M2_DIR, False if steps_right > 0 else True)
    
    steps_left, steps_right = abs(steps_left), abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps > 0:
        GPIO.output(M1_EN, GPIO.LOW)
        GPIO.output(M2_EN, GPIO.LOW)
        l_cnt, r_cnt = 0, 0
        for _ in range(max_steps):
            l_cnt += steps_left
            r_cnt += steps_right
            s_L, s_R = False, False
            if l_cnt >= max_steps:
                GPIO.output(M1_STEP, GPIO.HIGH)
                l_cnt -= max_steps
                s_L = True
            if r_cnt >= max_steps:
                GPIO.output(M2_STEP, GPIO.HIGH)
                r_cnt -= max_steps
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
                    p = command.split()
                    move_motors(float(p[1]), float(p[2]))
    except FileNotFoundError:
        print(f"Error: Could not find '{filename}'")

# --- Execution ---
try:
    setup_gpio()
    print(f"Homing... Ensure pen is at (18, {Y_OFFSET})")
    time.sleep(1)
    
    run_drawing_file("drawing.txt")
    
    set_pen("UP")
    move_motors(18.0, 0.0) # Return to home position
    print("Drawing Complete!")

except KeyboardInterrupt:
    print("\nEmergency Stop.")

finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 
    print("Motors disabled.")
