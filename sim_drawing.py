import math
from PIL import Image, ImageDraw

# --- 1. Calibrated Dimensions (Must match your physical setup) ---
MOTOR_DISTANCE_INCHES = 36.0  
SPOOL_DIAMETER_INCHES = 1.0   
DPI = 50  # Pixels per inch. 50 DPI = 1800x1800 image for a 36" board.

# --- 2. Canvas Setup ---
canvas_size = int(MOTOR_DISTANCE_INCHES * DPI)
# Create a white background
img = Image.new("RGB", (canvas_size, canvas_size), "white")
draw = ImageDraw.Draw(img)

def run_simulation(filename):
    print(f"Simulating {filename}...")
    
    # State tracking
    pen_down = False
    # Start at the "Home" position (18, 0) 
    current_pos = (18.0 * DPI, 0.0 * DPI) 
    
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                command = line.strip().upper()
                if not command or command.startswith("#"):
                    continue
                
                if command == "UP":
                    pen_down = False
                elif command == "DOWN":
                    pen_down = True
                elif command.startswith("MOVE"):
                    parts = command.split()
                    if len(parts) == 3:
                        # Convert target inches to pixels
                        target_x = float(parts[1]) * DPI
                        target_y = float(parts[2]) * DPI
                        target_pos = (target_x, target_y)
                        
                        if pen_down:
                            # Draw a solid black line 
                            draw.line([current_pos, target_pos], fill="black", width=2)
                        else:
                            # Draw a faint grey line for 'Travel' movements
                            # This helps you see what the robot does when the pen is "UP"
                            draw.line([current_pos, target_pos], fill=(220, 220, 220), width=1)
                        
                        # Update current position
                        current_pos = target_pos
        
        # Save the result
        output_name = "sim_result.png"
        img.save(output_name)
        print(f"Simulation complete! Opening {output_name}")
        img.show()

    except FileNotFoundError:
        print(f"Error: {filename} not found.")

# Run it
run_simulation("drawing.txt")
