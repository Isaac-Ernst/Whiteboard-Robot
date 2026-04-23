import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.1   # Updated per your latest code
STEPS_PER_REV = 200           
DELAY = 0.003                 # Slightly slower for better torque

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 27, 22, 6   # Left Motor
M2_DIR, M2_STEP, M2_EN = 4, 17, 5    # Right Motor
SERVO_PIN = 18                      

# --- Servo Angles ---
PEN_UP_ANGLE = 7.5    
PEN_DOWN_ANGLE = 11.0 

# --- Positioning & Flip Fixes ---
# This pushes the logo 10 inches down so (18, 0) in your file 
# is physically 10 inches below the motors
Y_OFFSET = 10.0              
# Set this to True to flip the image vertically if it's still upside down
FLIP_VERTICAL = True        

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES   
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV   

# --- Homing Calculation ---
# Starting at physical (18, 10). 
# L = sqrt(18^2 + 10^2) = 20.5912 inches
current_left_in = 20.5912   
current_right_in = 20.5912  
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
    # Disable motors initially
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
    
    # --- FLIP & OFFSET LOGIC ---
    if FLIP_VERTICAL:
        # Subtract from 15 because your file goes from Y=10 to Y=27
        # This keeps the logo oriented correctly
        target_y = 28.0 - target_y 
    
    # Add the safety buffer so it doesn't hit the motors
    physical_y = target_y + Y_OFFSET
    
    # Mirror the X-axis
    target_x = MOTOR_DISTANCE_INCHES - target_x
    
    # Calculate target physical lengths (Pythagorean Theorem)
    # $$L = \sqrt{x^2 + y^2}$$
    target_left_in = math.sqrt(target_x**2 + physical_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + physical_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # Set Directions
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
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
                cmd = line.strip().upper()
                if not cmd or cmd.startswith("#"): continue
                if cmd == "UP": set_pen("UP")
                elif cmd == "DOWN": set_pen("DOWN")
                elif cmd.startswith("MOVE"):
                    p = cmd.split()
                    move_motors(float(p[1]), float(p[2]))
    except FileNotFoundError:
        print(f"Error: {filename} not found.")

# --- Execution ---
try:
    setup_gpio()
    print(f"--- READY ---")
    print(f"1. Physically hang pen exactly 10 inches below center.")
    print(f"2. Ensure strings are 20.59 inches long.")
    input("Press Enter to begin the draw...")
    
    run_drawing_file("drawing.txt")
    
    # Return to home safely
    set_pen("UP")
    move_motors(18.0, 0.0) 
    print("TAMU Logo Complete!")

except KeyboardInterrupt:
    print("\nEmergency Stop.")

finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 
