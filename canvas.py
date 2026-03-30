import tkinter as tk
import math
import time
import RPi.GPIO as GPIO

# --- 1. Physical Setup & Calibration ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
STEPS_PER_REV = 200
DELAY = 0.002 # Speed of the motors. Lower is faster, but too low will stall them.

# --- 2. Virtual Canvas ---
CANVAS_WIDTH_PX = 800
CANVAS_HEIGHT_PX = 600
PIXELS_PER_INCH = CANVAS_WIDTH_PX / MOTOR_DISTANCE_INCHES 

# --- 3. Motor Pins ---
M1_DIR, M1_STEP, M1_EN = 4, 17, 5 
M2_DIR, M2_STEP, M2_EN = 27, 22, 6

# --- Math Conversions ---
SPOOL_CIRCUMFERENCE = math.pi * SPOOL_DIAMETER_INCHES
INCHES_PER_STEP = SPOOL_CIRCUMFERENCE / STEPS_PER_REV

# --- Global State Variables ---
last_x, last_y = None, None
current_left_in = 0.0
current_right_in = 0.0

def setup_gpio():
    """Configures the Pi pins and locks the motors down"""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pins = [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    
    # Start with motors disabled (HIGH)
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

def calculate_string_lengths(x_px, y_px):
    """Translates screen pixels into target physical inches"""
    x_inches = x_px / PIXELS_PER_INCH
    y_inches = y_px / PIXELS_PER_INCH
    
    left_string_inches = math.sqrt(x_inches**2 + y_inches**2)
    right_string_inches = math.sqrt((MOTOR_DISTANCE_INCHES - x_inches)**2 + y_inches**2)
    
    return left_string_inches, right_string_inches

def move_motors(target_left_in, target_right_in):
    """The core engine: Translates inch differences into coordinated motor steps"""
    global current_left_in, current_right_in
    
    # 1. Find the Delta (How far do we need to move?)
    delta_left = target_left_in - current_left_in
    delta_right = target_right_in - current_right_in
    
    # 2. Convert Delta inches into absolute steps
    steps_left = int(round(delta_left / INCHES_PER_STEP))
    steps_right = int(round(delta_right / INCHES_PER_STEP))
    
    # 3. Set Directions
    # NOTE: You may need to flip True/False here depending on how your spools are wound!
    # We assume Positive steps = Release String (unwind). Negative steps = Pull String (wind up).
    GPIO.output(M1_DIR, True if steps_left > 0 else False) 
    GPIO.output(M2_DIR, True if steps_right > 0 else False)
    
    steps_left = abs(steps_left)
    steps_right = abs(steps_right)
    max_steps = max(steps_left, steps_right)
    
    if max_steps == 0:
        return # No movement needed
        
    # 4. Wake up motors
    GPIO.output(M1_EN, GPIO.LOW)
    GPIO.output(M2_EN, GPIO.LOW)
    
    # 5. Proportional Stepping Loop
    left_counter = 0
    right_counter = 0
    
    for _ in range(max_steps):
        left_counter += steps_left
        right_counter += steps_right
        
        step_L = False
        step_R = False
        
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

    # 6. Put motors back to sleep
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)

    # 7. Update memory so the bot knows where it is now
    current_left_in = target_left_in
    current_right_in = target_right_in

def start_draw(event):
    """Fires when you click to start a line"""
    global last_x, last_y, current_left_in, current_right_in
    last_x, last_y = event.x, event.y
    
    # If this is the absolute first click, we need to tell the robot
    # that its current physical position matches the mouse click.
    if current_left_in == 0.0:
        current_left_in, current_right_in = calculate_string_lengths(event.x, event.y)
        print("Robot position initialized to first click.")

def paint(event):
    """Fires as you drag the mouse"""
    global last_x, last_y
    
    # Draw on the UI
    canvas.create_line(last_x, last_y, event.x, event.y, width=4, fill="black", capstyle=tk.ROUND, smooth=tk.TRUE)
    last_x, last_y = event.x, event.y
    
    # Calculate target and physically move the motors
    target_left, target_right = calculate_string_lengths(event.x, event.y)
    move_motors(target_left, target_right)

def clear_canvas(event=None):
    """Wipes the UI clean"""
    canvas.delete("all")
    print("Canvas cleared.")

# --- Initialization ---
try:
    setup_gpio()
    
    root = tk.Tk()
    root.title("Whiteboard Robot - Live Control")

    canvas = tk.Canvas(root, width=CANVAS_WIDTH_PX, height=CANVAS_HEIGHT_PX, bg="white", cursor="crosshair")
    canvas.pack(padx=10, pady=10)

    canvas.bind("<Button-1>", start_draw) 
    canvas.bind("<B1-Motion>", paint)     
    root.bind('<c>', clear_canvas) # The 'c' key shortcut

    print("System Ready. Draw on the canvas. Press 'c' to clear.")
    print("WARNING: Draw slowly! The Pi needs time to physically pulse the motors.")
    
    root.mainloop()

except KeyboardInterrupt:
    print("\nForce quit by user.")

finally:
    # Force motors asleep, but do NOT cleanup to prevent the twitching ghost
    GPIO.output(M1_EN, GPIO.HIGH)
    GPIO.output(M2_EN, GPIO.HIGH)
    print("Motors locked safely.")
