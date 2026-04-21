import RPi.GPIO as GPIO
import time

# --- Setup ---
SERVO_PIN = 18  # BCM 18 (Physical Pin 12)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# 50Hz is standard for SG90 servos
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0) 

def set_angle(duty_cycle):
    """
    Standard SG90 values:
    7.5  -> Roughly Neutral (Your 'UP')
    11.0 -> Your 'DOWN'
    """
    print(f"Moving to Duty Cycle: {duty_cycle}")
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5) # Give it time to physically move

try:
    print("--- Servo Test Started ---")
    print("Testing your calibrated angles...")
    
    while True:
        print("\nOptions: [1] UP (7.5) | [2] DOWN (11.0) | [3] CUSTOM | [Q] Quit")
        choice = input("Select: ").strip().lower()
        
        if choice == '1':
            set_angle(7.5)  # From your drawing script
        elif choice == '2':
            set_angle(11.0) # From your drawing script
        elif choice == '3':
            val = input("Enter custom duty cycle (e.g., 5.0 to 12.0): ")
            try:
                set_angle(float(val))
            except ValueError:
                print("Invalid number.")
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")

finally:
    pwm.stop()
    GPIO.cleanup()
    print("\nGPIO cleaned up. Powering down.")