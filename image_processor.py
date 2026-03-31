import cv2
import numpy as np

# --- CALIBRATED DIMENSIONS ---
BOARD_WIDTH_INCHES = 36.0      
DRAW_WIDTH_INCHES = 24.0    
DRAW_START_Y = 10.0         
LINE_SPACING_INCHES = 0.05  # Higher resolution for dog detail

def generate_hatch_lines(mask, angle, spacing_px):
    h, w = mask.shape
    lines = []
    diagonal = int(np.sqrt(h**2 + w**2))
    
    for d in range(-diagonal, diagonal, spacing_px):
        x0 = d * np.cos(np.radians(angle))
        y0 = d * np.sin(np.radians(angle))
        vx = np.cos(np.radians(angle + 90))
        vy = np.sin(np.radians(angle + 90))
        
        pt1 = (int(x0 - vx * diagonal), int(y0 - vy * diagonal))
        pt2 = (int(x0 + vx * diagonal), int(y0 + vy * diagonal))
        
        line_img = np.zeros((h, w), dtype=np.uint8)
        cv2.line(line_img, pt1, pt2, 255, 1)
        active_line = cv2.bitwise_and(line_img, mask)
        
        points = cv2.findNonZero(active_line)
        if points is not None:
            points = points.reshape(-1, 2)
            lines.append(points)
    return lines

def process_image_to_hatch(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Error: Could not load image.")
        return

    h_orig, w_orig = img.shape
    scale_factor = 1000 / w_orig
    img = cv2.resize(img, (1000, int(h_orig * scale_factor)))
    h, w = img.shape
    
    phys_scale = DRAW_WIDTH_INCHES / w
    spacing_px = int(LINE_SPACING_INCHES / phys_scale)
    offset_x = (BOARD_WIDTH_INCHES - DRAW_WIDTH_INCHES) / 2.0

    thresholds = [200, 150, 100, 50]
    angles = [45, 135, 0, 90] 
    
    # FIXED: Using 'f' consistently here
    with open(output_path, 'w') as f:
        f.write("# Calibrated Crosshatch Instructions\nUP\n")
        
        for i in range(len(thresholds)):
            _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
            print(f"Processing Layer {i+1}...")
            layer_lines = generate_hatch_lines(mask, angles[i], spacing_px)
            
            for path in layer_lines:
                start_x = (path[0][0] * phys_scale) + offset_x
                start_y = (path[0][1] * phys_scale) + DRAW_START_Y
                f.write(f"MOVE {start_x:.2f} {start_y:.2f}\nDOWN\n")
                
                end_x = (path[-1][0] * phys_scale) + offset_x
                end_y = (path[-1][1] * phys_scale) + DRAW_START_Y
                f.write(f"MOVE {end_x:.2f} {end_y:.2f}\nUP\n")

    print(f"Success! {output_path} generated.")

process_image_to_hatch("test_image.jpg", "drawing.txt")
