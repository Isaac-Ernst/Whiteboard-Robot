from PIL import Image, ImageDraw

# --- SET THIS TO TRUE TO SEE WHAT YOUR ROBOT ACTUALLY DRAWS ---
NO_PEN_LIFT_MODE = True 

DPI = 50 
canvas_size = int(36.0 * DPI)
img = Image.new("RGB", (canvas_size, canvas_size), "white")
draw = ImageDraw.Draw(img)

def run_simulation(filename):
    pen_down = False
    current_pos = (18.0 * DPI, 10.0 * DPI) 
    
    with open(filename, 'r') as file:
        for line in file:
            cmd = line.strip().upper()
            if cmd == "UP": pen_down = False
            elif cmd == "DOWN": pen_down = True
            elif cmd.startswith("MOVE"):
                parts = cmd.split()
                target_pos = (float(parts[1]) * DPI, float(parts[2]) * DPI)
                
                if NO_PEN_LIFT_MODE or pen_down:
                    draw.line([current_pos, target_pos], fill="black", width=2)
                else:
                    # Hidden travel lines (only visible if you have a servo!)
                    draw.line([current_pos, target_pos], fill=(230, 230, 230), width=1)
                
                current_pos = target_pos
    img.save("sim_result.png")
    img.show()

run_simulation("drawing.txt")
