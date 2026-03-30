import RPi.GPIO as GPIO
import time

# --- Setup Your Pins Here ---
DIR_PIN = 4   # Connect to A4988 DIR pin
STEP_PIN = 17  # Connect to A4988 STEP pin

# NEMA 17 motors have 200 steps per full revolution (1.8 degrees per step)
STEPS_PER_REV = 200 
DELAY = 0.005 # Delay between steps controls the speed (lower is faster)

def setup():
    # Use BCM GPIO numbering
    GPIO.setmode(GPIO.BCM)
    # Set the pins as outputs
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)

def spin_motor(direction, steps, delay):
    # Set the direction (True = Clockwise, False = Counter-Clockwise)
    GPIO.output(DIR_PIN, direction)
    
    # Pulse the STEP pin to move the motor
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

try:
    setup()
    print("Spinning Clockwise...")
    spin_motor(True, STEPS_PER_REV, DELAY)
    
    time.sleep(1) # Pause for 1 second
    
    print("Spinning Counter-Clockwise...")
    spin_motor(False, STEPS_PER_REV, DELAY)

except KeyboardInterrupt:
    print("Test stopped by user.")

finally:
    # Always clean up GPIO pins when the script exits to prevent damage
    GPIO.cleanup()
    print("GPIO Cleaned up. Test Complete.")