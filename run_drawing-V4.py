import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0 
SPOOL_DIAMETER_INCHES = 1.0  
STEPS_PER_REV = 200          

# --- GLOBAL SETTINGS (Tunable at Runtime) ---
DELAY = 0.002       # Speed: Lower = Faster
PEN_UP_ANGLE = 7.5  # Servo duty cycle for UP
PEN_DOWN_ANGLE = 11.0 # Servo duty cycle for DOWN

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5   
M2_DIR, M2_STEP, M2_EN = 27, 22, 6  
SERVO_PIN = 18                      

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
    for pin in pins: GPIO.setup(pin, GPIO.OUT)
    
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50) 
    pwm.start(PEN_UP_ANGLE) 
    
    # Keep motors energized
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)

def set_pen(state):
    global pwm, PEN_UP_ANGLE, PEN_DOWN_ANGLE
    angle = PEN_UP_ANGLE if state == "UP" else PEN_DOWN_ANGLE
    pwm.ChangeDutyCycle(angle)
    time.sleep(0.3)

def move_motors(target_x, target_y):
    global current_left_in, current_right_in, DELAY
    
    target_left_in = math.sqrt(target_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + target_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left, steps_right = abs(steps_left), abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0: return 
    
    left_counter, right_counter = 0, 0
    for _ in range(max_steps):
        left_counter += steps_left
        right_counter += steps_right
        
        step_L = step_R = False
        if left_counter >= max_steps:
            GPIO.output(M1_STEP, GPIO.HIGH)
            left_counter -= max_steps
            step_L = True
        if right_counter >= max_steps:
            GPIO.output(M2_STEP, GPIO.HIGH)
            right_counter -= max_steps
            step_R = True
            
        time.sleep(DELAY) # Uses the global DELAY variable
        
        if step_L: GPIO.output(M1_STEP, GPIO.LOW)
        if step_R: GPIO.output(M2_STEP, GPIO.LOW)
        time.sleep(DELAY)

    current_left_in, current_right_in = target_left_in, target_right_in

def show_menu():
    global DELAY, PEN_UP_ANGLE, PEN_DOWN_ANGLE
    print("\n" + "="*40)
    print(f" PAUSED | Speed: {DELAY} | UP: {PEN_UP_ANGLE} | DOWN: {PEN_DOWN_ANGLE}")
    print("="*40)
    print("1. RESUME")
    print("2. CHANGE SPEED (Current Delay: {})".format(DELAY))
    print("3. TWEAK SERVO (Calibration)")
    print("4. RESTART FILE")
    print("5. EXIT (Emergency Stop)")
    print("="*40)
    
    while True:
        c = input("Choice: ").strip()
        if c == '1': return "RESUME"
        if c == '2':
            val = input(f"New Delay (current {DELAY}, try 0.001): ")
            try: DELAY = float(val)
            except: print("Invalid number.")
            return "RESUME"
        if c == '3':
            u = input(f"New UP Angle (current {PEN_UP_ANGLE}): ")
            d = input(f"New DOWN Angle (current {PEN_DOWN_ANGLE}): ")
            try:
                PEN_UP_ANGLE = float(u)
                PEN_DOWN_ANGLE = float(d)
                set_pen("UP") # Test the new up position immediately
            except: print("Invalid entry.")
            return "RESUME"
        if c == '4': return "RESTART"
        if c == '5': return "STOP"

def run_drawing_file(filename):
    while True:
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip().upper()
                    i += 1
                    if not line or line.startswith("#"): continue
                    
                    try:
                        if line == "UP": set_pen("UP")
                        elif line == "DOWN": set_pen("DOWN")
                        elif line.startswith("MOVE"):
                            parts = line.split()
                            move_motors(float(parts[1]), float(parts[2]))
                    
                    except KeyboardInterrupt:
                        action = show_menu()
                        if action == "RESUME": continue
                        if action == "RESTART": break
                        if action == "STOP": return
                else:
                    print("Drawing Complete!")
                    return
        except FileNotFoundError:
            print("File not found.")
            return

# --- Main ---
try:
    setup_gpio()
    input("Home pen at (18,0) and press Enter...")
    run_drawing_file("drawing.txt")
finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH) # Relax motors
    GPIO.output(M2_EN, GPIO.HIGH)
    GPIO.cleanup()
    