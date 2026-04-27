import RPi.GPIO as GPIO
import time

# --- Setup ---
SERVO_PIN = 18  # Your assigned PWM pin
FREQUENCY = 50  # Standard 50Hz for micro servos

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, FREQUENCY)
pwm.start(7.5) # Start at neutral 90 degrees

print("--- SHSS401P Calibration Utility ---")
print("Enter values between 2.5 and 12.5.")
print("7.5 is usually the 90-degree center.")
print("Type 'q' to quit.")

try:
    while True:
        val = input("\nEnter Duty Cycle (e.g., 7.5): ")
        
        if val.lower() == 'q':
            break
            
        try:
            duty = float(val)
            # Safety check: 50.0 or 0.0 will stall/burn the motor
            if 2.0 <= duty <= 13.0:
                pwm.ChangeDutyCycle(duty)
                print(f"Moving to: {duty}")
            else:
                print("!! WARNING: Keep values between 2.5 and 12.5 to avoid damage.")
        except ValueError:
            print("Invalid input. Please enter a number.")

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    # GPIO.cleanup()
    print("\nGPIO Cleaned up. Calibration complete.")