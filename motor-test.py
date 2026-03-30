import RPi.GPIO as GPIO
import time

DIR_PIN = 4
STEP_PIN = 17
EN_PIN = 5 # The new Enable pin

STEPS_PER_REV = 200 
DELAY = 0.005 

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    GPIO.setup(EN_PIN, GPIO.OUT)
    
    # Start with the motor disabled (HIGH = OFF)
    GPIO.output(EN_PIN, GPIO.HIGH) 

def spin_motor(direction, steps, delay):
    # Wake the motor up (LOW = ON)
    GPIO.output(EN_PIN, GPIO.LOW)
    time.sleep(0.01) # Give it a tiny fraction of a second to wake up
    
    GPIO.output(DIR_PIN, direction)
    
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)
        
    # Put the motor back to sleep when finished moving (HIGH = OFF)
    GPIO.output(EN_PIN, GPIO.HIGH)

try:
    setup()
    print("Spinning Clockwise...")
    spin_motor(True, STEPS_PER_REV, DELAY)

except KeyboardInterrupt:
    print("Test stopped by user.")

finally:
    GPIO.cleanup()
    print("GPIO Cleaned up. Motor disabled and safe.")
