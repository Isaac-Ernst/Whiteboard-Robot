from PIL import Image, ImageDraw
import os

# --- Simulation Settings ---
DPI = 50 
BOARD_SIZE_IN = 36.0
canvas_px = int(BOARD_SIZE_IN * DPI)

def run_ideal_simulation(filename):
    # Create high-res white canvas
    img = Image.new("RGB", (canvas_px, canvas_px), "white")
    draw = ImageDraw.Draw(img)
    
    current_pos = (18.0 * DPI, 0.0 * DPI) # Start at Home
    pen_down = False
    
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return

    print(f"Simulating {filename} in IDEAL (Servo) mode...")
    
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip().upper()
            if not line or line.startswith("#"): continue
            
            if line == "UP":
                pen_down = False
            elif line == "DOWN":
                pen_down = True
            elif line.startswith("MOVE"):
                parts = line.split()
                target_x = float(parts[1]) * DPI
                target_y = float(parts[2]) * DPI
                target_pos = (target_x, target_y)
                
                # ONLY draw if the pen is DOWN
                if pen_down:
                    # Draw solid black for the intended hatch
                    draw.line([current_pos, target_pos], fill="black", width=1)
                else:
                    # Travel lines are invisible (or use a very light cyan to see the path)
                    # draw.line([current_pos, target_pos], fill=(0, 255, 255, 50), width=1)
                    pass
                
                current_pos = target_pos
                
    output_path = "sim_result.png"
    img.save(output_path)
    print(f"Success! {output_path} generated.")
    img.show()

run_ideal_simulation("drawing.txt")
