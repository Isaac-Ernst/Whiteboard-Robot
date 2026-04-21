import math
import time
import sys
import tty
import termios
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200           
DELAY = 0.003  # Your updated delay for torque

# --- Motor & Servo Pins (Updated Pins) ---
M1_DIR, M1_STEP, M1_EN = 27, 22, 6    #
M2_DIR, M2_STEP, M2_EN = 4, 17, 5     #
SERVO_PIN = 18                        

# --- Servo Angles ---
PEN_UP_ANGLE = 7.5    
PEN_DOWN_ANGLE = 11.0 

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES   
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV   

# Global state
current_x = 18.0   # Current logical X position
current_y = 0.0    # Current logical Y position
current_left_in = 18.0   
current_right_in = 18.0  
pwm = None 

def getch():
    """Captures a single keypress without needing Enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

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
    global current_left_in, current_right_in, current_x, current_y
    
    # Mirroring Fix
    logical_x = MOTOR_DISTANCE_INCHES - target_x
    
    # Inverse Kinematics
    target_left_in = math.sqrt(logical_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - logical_x)**2 + target_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
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

    current_left_in, current_right_in = target_left_in, target_right_in
    current_x, current_y = target_x, target_y

def manual_setup():
    """WASD Controls to position the gondola before drawing"""
    global current_x, current_y
    print("\n--- MANUAL SETUP PHASE ---")
    print("Use WASD to move (0.25\" increments).")
    print("Space: Toggle Pen | Enter: Start Drawing | Q: Quit")
    
    pen_state = "UP"
    step_size = 0.25 # Inches per keypress

    while True:
        print(f"Current Position: ({current_x:.2f}, {current_y:.2f}) | Pen: {pen_state}", end='\r')
        char = getch().lower()
        
        if char == 'w': move_motors(current_x, current_y - step_size)
        elif char == 's': move_motors(current_x, current_y + step_size)
        elif char == 'a': move_motors(current_x - step_size, current_y)
        elif char == 'd': move_motors(current_x + step_size, current_y)
        elif char == ' ':
            pen_state = "DOWN" if pen_state == "UP" else "UP"
            set_pen(pen_state)
        elif char == '\r' or char == '\n': # Enter key
            print("\nSetup Locked. Starting File...")
            break
        elif char == 'q':
            sys.exit("\nSetup Cancelled.")

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
    manual_setup() # Runs WASD phase first
    run_drawing_file("drawing.txt")
    set_pen("UP")
    move_motors(18.0, 0.0)
    print("Drawing Complete!")
except KeyboardInterrupt:
    print("\nEmergency Stop.")
finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) 
    GPIO.output(M2_EN, GPIO.HIGH) 
    # GPIO.cleanup()
    