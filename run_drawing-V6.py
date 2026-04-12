import math
import time
import RPi.GPIO as GPIO
import sys

# ==========================================
# --- PHYSICAL DIMENSIONS & CONSTANTS ---
# ==========================================
MOTOR_DISTANCE_INCHES = 36.0 
SPOOL_DIAMETER_INCHES = 1.0  
STEPS_PER_REV = 200          

# ==========================================
# --- GLOBAL SETTINGS (Tunable at runtime) ---
# ==========================================
DELAY = 0.002           # Lower is faster (0.001 to 0.003 is typical)
PEN_UP_ANGLE = 7.5      # Duty cycle for lifted pen
PEN_DOWN_ANGLE = 11.0   # Duty cycle for drawing

# ==========================================
# --- MOTOR & SERVO PINS (Swapped M1/M2) ---
# ==========================================
M1_DIR, M1_STEP, M1_EN = 27, 22, 6  # Left Motor (Swapped to fix reverse issue)
M2_DIR, M2_STEP, M2_EN = 4, 17, 5   # Right Motor (Swapped to fix reverse issue)
SERVO_PIN = 18                      # Hardware PWM Pin

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

# --- Global State ---
current_left_in = 18.0 
current_right_in = 18.0
pwm = None 
current_line_index = 0

# ==========================================
# --- CORE FUNCTIONS ---
# ==========================================

def print_help():
    """Prints a reference guide for the operator"""
    print("\n" + "="*55)
    print("      WHITEBOARD ROBOT COMMAND CENTER")
    print("="*55)
    print("KEYBOARD CONTROLS:")
    print(" - [Ctrl + C] : Pause drawing and open the Pro Menu.")
    print(" - [Enter]    : Confirm menu selections.")
    print("\nPRO MENU FEATURES:")
    print(" - Jump       : Skip forward/backward in the text file.")
    print(" - Tweak      : Change servo lift/drop height mid-draw.")
    print(" - Speed      : Change motor step delay mid-draw.")
    print(" - Manual Jog : Nudge the pen using W/A/S/D coordinates.")
    print("="*55 + "\n")

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
    
    # Lock motors immediately to hold gondola weight
    GPIO.output(M1_EN, GPIO.LOW) 
    GPIO.output(M2_EN, GPIO.LOW)

def set_pen(state):
    global pwm, PEN_UP_ANGLE, PEN_DOWN_ANGLE
    angle = PEN_UP_ANGLE if state == "UP" else PEN_DOWN_ANGLE
    pwm.ChangeDutyCycle(angle)
    time.sleep(0.3)

def move_motors(target_x, target_y):
    global current_left_in, current_right_in, DELAY
    
    # Calculate physical string lengths required for target coordinate
    target_left_in = math.sqrt(target_x**2 + target_y**2)
    target_right_in = math.sqrt((MOTOR_DISTANCE_INCHES - target_x)**2 + target_y**2)
    
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # Flip True/False here if a specific motor is spooling backward
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left, steps_right = abs(steps_left), abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0: 
        return 
    
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
            
        time.sleep(DELAY)
        
        if step_L: GPIO.output(M1_STEP, GPIO.LOW)
        if step_R: GPIO.output(M2_STEP, GPIO.LOW)
        
        time.sleep(DELAY)
        
    current_left_in, current_right_in = target_left_in, target_right_in

def get_current_xy():
    """Converts current string lengths back to Cartesian X/Y for jogging"""
    L = current_left_in
    R = current_right_in
    D = MOTOR_DISTANCE_INCHES
    x = (L**2 - R**2 + D**2) / (2 * D)
    val = L**2 - x**2
    y = math.sqrt(val) if val > 0 else 0
    return x, y

def manual_jog():
    """Allows precise physical nudging of the pen"""
    print("\n--- MANUAL JOG MODE ---")
    print("Format: [WASD] [Distance] (e.g., 'W 0.5' moves UP 0.5 inches)")
    print("Enter 'Q' to return to menu.")
    
    while True:
        cmd = input("Jog Command: ").strip().upper()
        if cmd == 'Q': break
        
        try:
            parts = cmd.split()
            direction = parts[0]
            dist = float(parts[1])
            
            curr_x, curr_y = get_current_xy()
            target_x, target_y = curr_x, curr_y
            
            if direction == 'W': target_y -= dist # Up is negative Y in our math
            elif direction == 'S': target_y += dist
            elif direction == 'A': target_x -= dist
            elif direction == 'D': target_x += dist
            else:
                print("Use W, A, S, or D.")
                continue
                
            print(f"Moving to X:{target_x:.2f}, Y:{target_y:.2f}")
            move_motors(target_x, target_y)
        except Exception as e:
            print("Invalid format. Use 'W 1.0'")

def show_menu(total_lines):
    global DELAY, PEN_UP_ANGLE, PEN_DOWN_ANGLE, current_line_index
    print("\n" + "!"*50)
    print(f" PAUSED | Line: {current_line_index}/{total_lines} | Speed: {DELAY}s")
    print("!"*50)
    print("1. RESUME (Motors locked)")
    print("2. JUMP to Line Number")
    print("3. CHANGE SPEED (Step Delay)")
    print("4. TWEAK SERVO (Up/Down Angles)")
    print("5. MANUAL JOG (Nudge Pen X/Y)")
    print("6. RESTART File from Line 1")
    print("7. EXIT & DISABLE MOTORS")
    print("!"*50)
    
    while True:
        c = input("Selection: ").strip()
        if c == '1': 
            return "RESUME"
        if c == '2':
            val = input(f"Jump to line (1-{total_lines}): ")
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
                set_pen("UP") # Test the new lift height instantly
            except: print("Invalid entry.")
            return "RESUME"
        if c == '5':
            manual_jog()
            return "RESUME"
        if c == '6': 
            current_line_index = 0
            return "RESTART"
        if c == '7': 
            return "STOP"

def run_drawing_file(filename):
    global current_line_index
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            total = len(lines)
            
            while current_line_index < total:
                line = lines[current_line_index].strip().upper()
                current_line_index += 1
                
                if not line or line.startswith("#"): 
                    continue
                
                try:
                    if line == "UP": 
                        set_pen("UP")
                    elif line == "DOWN": 
                        set_pen("DOWN")
                    elif line.startswith("MOVE"):
                        parts = line.split()
                        if len(parts) == 3:
                            move_motors(float(parts[1]), float(parts[2]))
                
                except KeyboardInterrupt:
                    # Traps Ctrl+C to open the menu without crashing
                    action = show_menu(total)
                    if action == "STOP": 
                        return
                    if action == "RESTART": 
                        break # Exits the while loop to allow external loop/exit
            
            if current_line_index >= total:
                print("Finished Drawing!")
                
    except FileNotFoundError: 
        print(f"Error: Could not find '{filename}'")

# ==========================================
# --- MAIN EXECUTION ---
# ==========================================
print_help()

try:
    setup_gpio()
    print("System Online. Motors are LOCKED.")
    input("Manually pull strings to home (18, 0) and press ENTER to start...")
    
    run_drawing_file("drawing.txt")
    
    # Return home sequence
    set_pen("UP")
    move_motors(18.0, 0.0)
    print("Returned to Home.")

except KeyboardInterrupt:
    print("\nEmergency Stop Triggered.")

finally:
    if pwm: 
        pwm.stop()
    # Release the holding torque so motors don't overheat when idle
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    # GPIO.cleanup()
    print("System safe. Motors released.")
    