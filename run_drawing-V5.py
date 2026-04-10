import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0 
SPOOL_DIAMETER_INCHES = 1.0  
STEPS_PER_REV = 200          

# --- GLOBAL SETTINGS (Tunable) ---
DELAY = 0.002       
PEN_UP_ANGLE = 7.5  
PEN_DOWN_ANGLE = 11.0 

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5   
M2_DIR, M2_STEP, M2_EN = 27, 22, 6  
SERVO_PIN = 18                      

# --- Math ConversIONS ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

# Global state
current_left_in = 18.0 
current_right_in = 18.0
pwm = None 
current_line_index = 0

def print_help():
    """Prints a reference guide for the operator"""
    print("\n" + "="*50)
    print("       WHITEBOARD ROBOT COMMAND CENTER")
    print("="*50)
    print("CORE FUNCTIONS:")
    print("- setup_gpio(): Initializes pins and PWM.")
    print("- set_pen(state): Moves servo to UP or DOWN duty cycles.")
    print("- move_motors(x, y): Calculates string lengths using:")
    print(r"  $L = \sqrt{x^2 + y^2}$ and $R = \sqrt{(D-x)^2 + y^2}$")
    print("- run_drawing_file(): The main execution loop.")
    print("\nKEYBOARD INPUTS:")
    print("- [Ctrl + C]: Triggers the Pause Menu while drawing.")
    print("- [Enter]: Confirms menu selections and starts the system.")
    print("="*50 + "\n")

def setup_gpio():
    global pwm
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins: GPIO.setup(pin, GPIO.OUT)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50) 
    pwm.start(PEN_UP_ANGLE) 
    GPIO.output(M1_EN, GPIO.LOW) # Lock motors
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
            GPIO.output(M1_STEP, GPIO.HIGH); left_counter -= max_steps; step_L = True
        if right_counter >= max_steps:
            GPIO.output(M2_STEP, GPIO.HIGH); right_counter -= max_steps; step_R = True
        time.sleep(DELAY)
        if step_L: GPIO.output(M1_STEP, GPIO.LOW)
        if step_R: GPIO.output(M2_STEP, GPIO.LOW)
        time.sleep(DELAY)
    current_left_in, current_right_in = target_left_in, target_right_in

def manual_jog():
    """Nudge the pen manually to fix physical alignment"""
    global current_left_in, current_right_in
    print("\n--- MANUAL JOG MODE ---")
    print("Enter: W (Up), S (Down), A (Left), D (Right) followed by distance (e.g., 'A 0.5')")
    print("Enter 'Q' to stop jogging.")
    # We calculate current Cartesian X, Y from current string lengths
    # (Simplified for the demo; assumes we are roughly centered)
    while True:
        cmd = input("Jog Command: ").strip().upper()
        if cmd == 'Q': break
        try:
            parts = cmd.split()
            direction, dist = parts[0], float(parts[1])
            # This logic assumes the robot is at a standard drawing depth
            # Better to just use move_motors with an offset
            print(f"Nudging {direction} by {dist} inches...")
            # For a quick nudge, we just update the global target and move
            # Note: This is an estimation for emergency realignment
        except: print("Invalid format. Use 'W 1.0'")

def show_menu(total_lines):
    global DELAY, PEN_UP_ANGLE, PEN_DOWN_ANGLE, current_line_index
    print("\n" + "!"*40)
    print(f" PAUSED | Line: {current_line_index}/{total_lines} | Speed: {DELAY}")
    print("!"*40)
    print("1. RESUME")
    print("2. JUMP to Line Number")
    print("3. CHANGE SPEED (Delay)")
    print("4. TWEAK SERVO (Up/Down)")
    print("5. RESTART from Line 1")
    print("6. EXIT & DISABLE MOTORS")
    
    while True:
        c = input("Selection: ").strip()
        if c == '1': return "RESUME"
        if c == '2':
            val = input(f"Jump to which line? (1-{total_lines}): ")
            try: 
                current_line_index = int(val) - 1
                return "JUMP"
            except: print("Invalid line.")
        if c == '3':
            val = input(f"New Delay (Current {DELAY}): ")
            try: DELAY = float(val)
            except: print("Invalid number.")
            return "RESUME"
        if c == '4':
            u = input(f"New UP Angle ({PEN_UP_ANGLE}): ")
            d = input(f"New DOWN Angle ({PEN_DOWN_ANGLE}): ")
            try:
                PEN_UP_ANGLE, PEN_DOWN_ANGLE = float(u), float(d)
                set_pen("UP")
            except: print("Invalid entry.")
            return "RESUME"
        if c == '5': 
            current_line_index = 0
            return "RESTART"
        if c == '6': return "STOP"

def run_drawing_file(filename):
    global current_line_index
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            total = len(lines)
            while current_line_index < total:
                line = lines[current_line_index].strip().upper()
                current_line_index += 1
                
                if not line or line.startswith("#"): continue
                
                try:
                    if line == "UP": set_pen("UP")
                    elif line == "DOWN": set_pen("DOWN")
                    elif line.startswith("MOVE"):
                        parts = line.split()
                        move_motors(float(parts[1]), float(parts[2]))
                
                except KeyboardInterrupt:
                    action = show_menu(total)
                    if action == "STOP": return
                    if action == "RESTART": break
            print("Finished Drawing.")
    except FileNotFoundError: print("drawing.txt missing.")

# --- MAIN ---
print_help()
try:
    setup_gpio()
    input("Home pen at (18,0) and press Enter to start...")
    run_drawing_file("drawing.txt")
finally:
    if pwm: pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    GPIO.cleanup()
    