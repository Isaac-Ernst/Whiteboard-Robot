import RPi.GPIO as GPIO
import time

# --- Motor 1 Pins (Left Side) ---
M1_DIR = 4
M1_STEP = 17
M1_EN = 5 

# --- Motor 2 Pins (Right Side) ---
M2_DIR = 27
M2_STEP = 22
M2_EN = 6

STEPS_PER_REV = 200 
DELAY = 0.005 

def setup():
    GPIO.setmode(GPIO.BCM)
    
    # Setup all pins as outputs
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    # Start with both motors disabled (HIGH = OFF)
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

def spin_dual_motors(steps, delay):
    # Wake both motors up (LOW = ON)
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)
    time.sleep(0.01) # Brief pause to wake up
    
    # Set Motor 1 to Clockwise (True/HIGH)
    GPIO.output(M1_DIR, True)
    # Set Motor 2 to Counter-Clockwise (False/LOW)
    GPIO.output(M2_DIR, False) 
    
    # Pulse BOTH step pins at the exact same time
    for _ in range(steps):
        GPIO.output(M1_STEP, GPIO.HIGH)
        GPIO.output(M2_STEP, GPIO.HIGH)
        time.sleep(delay)
        
        GPIO.output(M1_STEP, GPIO.LOW)
        GPIO.output(M2_STEP, GPIO.LOW)
        time.sleep(delay)
        
    # Put both motors back to sleep when finished
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

try:
    setup()
    print("Motors are starting full rotation in opposite directions...")
    
    # Run the function for 1 full revolution
    spin_dual_motors(STEPS_PER_REV, DELAY)
    
    print("Rotation complete.")

except KeyboardInterrupt:
    print("Test stopped by user.")

finally:
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    
    print("GPIO Cleaned up. Motors disabled and safe.")
