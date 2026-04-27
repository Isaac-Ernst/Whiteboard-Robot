import RPi.GPIO as GPIO
import time

# --- Setup ---
SERVO_PIN = 18 
FREQUENCY = 50 

# Motor Pins (Latest Configuration) 
M1_DIR, M1_STEP, M1_EN = 4, 17, 5
M2_DIR, M2_STEP, M2_EN = 27, 22, 6

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup Servo
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PIN, FREQUENCY)
pwm.start(7.5) 

# Setup Motors 
motor_pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# --- ENGAGE MOTORS ---
# Setting EN to LOW locks the motors in place [cite: 12, 13]
GPIO.output(M1_EN, GPIO.LOW)
GPIO.output(M2_EN, GPIO.LOW)

print("--- MOTORS ENGAGED & LOCKED ---")
print("You can now hang your weights and pendulum.")
print("--- SHSS401P Calibration Utility ---")
print("Values: 2.5 (0°) to 12.5 (180°). 7.5 is Center.")
print("Type 'q' to quit (Motors will stay locked).")

try:
    while True:
        val = input("\nEnter Duty Cycle (e.g., 7.5): ")
        
        if val.lower() == 'q':
            break
            
        try:
            duty = float(val)
            # Safety range for SHSS401P 
            if 2.5 <= duty <= 12.5:
                pwm.ChangeDutyCycle(duty)
                print(f"Servo moving to: {duty}")
            else:
                print("!! ERROR: Use values between 2.5 and 12.5.")
        except ValueError:
            print("Invalid input. Please enter a number.")

except KeyboardInterrupt:
    pass

finally:
    print("\n--- SAFELY SHUTTING DOWN ---")
    
    # 1. Stop the Servo first to reduce electrical noise
    if pwm:
        pwm.stop()
    
    # 2. Force the Enable pins HIGH to cut power to the coils
    # This releases the holding torque so the weight doesn't "snap" the motor
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    
    # 3. Brief pause to let the magnetic fields in the motors collapse
    time.sleep(0.1)
    
    # 4. TARGETED CLEANUP 
    # Instead of cleaning up everything, only cleanup the Servo 
    # and EN pins. Keep the STEP pins as OUTPUTS held LOW.
    # This keeps the "antenna" grounded so it can't pick up noise.
    GPIO.setup(M1_STEP, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(M2_STEP, GPIO.OUT, initial=GPIO.LOW)
    
    # Optional: Only cleanup the servo pin to stop PWM
    GPIO.cleanup(SERVO_PIN) 
    
    print("Motors disabled and signal pins grounded. Shaking should stop.")