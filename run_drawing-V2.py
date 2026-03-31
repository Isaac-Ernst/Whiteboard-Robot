import math
import time
import RPi.GPIO as GPIO

# --- Physical Dimensions ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200
DELAY = 0.002 

# --- Motor & Servo Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5 
M2_DIR, M2_STEP, M2_EN = 27, 22, 6
SERVO_PIN = 18  # NEW: Connect your SG90 orange/yellow wire here

# --- Servo Angles (Calibrate these for your bracket) ---
PEN_UP_ANGLE = 7.5    # Duty cycle for "Lifted"
PEN_DOWN_ANGLE = 11.0 # Duty cycle for "Touching Board"

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

current_left_in = 18.0 
current_right_in = 18.0
pwm = None # Global PWM object

def setup_gpio():
    global pwm
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Motor Setup
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    # Servo Setup
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50) # 50Hz frequency for SG90
    pwm.start(PEN_UP_ANGLE) # Start in UP position
    
    # Disable motors while sitting
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

def set_pen(state):
    """Physically moves the SG90 servo"""
    global pwm
    if state == "UP":
        print("--> LIFTING PEN")
        pwm.ChangeDutyCycle(PEN_UP_ANGLE)
        time.sleep(0.3) # Wait for servo to move
    elif state == "DOWN":
        print("--> DROPPING PEN")
        pwm.ChangeDutyCycle(PEN_DOWN_ANGLE)
        time.sleep(0.3)

# ... (move_motors function remains the same) ...

def run_drawing_file(filename):
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

# --- Main Execution ---
try:
    setup_gpio()
    print("System Initialized at Home (18,0).")
    time.sleep(1)
    
    run_drawing_file("drawing.txt")
    
    # Return to home after finishing
    set_pen("UP")
    move_motors(18.0, 0.0)
    print("Drawing Complete! Returned to Home.")

except KeyboardInterrupt:
    print("\nEmergency Stop.")

finally:
    if pwm:
        pwm.stop()
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    GPIO.cleanup()
    