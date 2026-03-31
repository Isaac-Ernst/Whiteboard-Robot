import cv2
import numpy as np

# --- Physical Setup (Matches your Board) ---
BOARD_WIDTH_INCHES = 36.0      
DRAWING_WIDTH_INCHES = 24.0    # Making it a bit bigger for detail
DRAWING_START_Y = 8.0         
LINE_SPACING_INCHES = 0.12     # Distance between hatch lines (Adjust for marker thickness)

def generate_hatch_lines(mask, angle, spacing_px):
    """Generates parallel lines only where the mask is white"""
    h, w = mask.shape
    lines = []
    
    # Create a larger canvas to rotate lines without clipping
    diagonal = int(np.sqrt(h**2 + w**2))
    for d in range(-diagonal, diagonal, spacing_px):
        # Math to create a long line at a specific angle
        x0 = d * np.cos(np.radians(angle))
        y0 = d * np.sin(np.radians(angle))
        
        # Line vector
        vx = np.cos(np.radians(angle + 90))
        vy = np.sin(np.radians(angle + 90))
        
        # Endpoints of a very long line
        pt1 = (int(x0 - vx * diagonal), int(y0 - vy * diagonal))
        pt2 = (int(x0 + vx * diagonal), int(y0 + vy * diagonal))
        
        # Create a blank slate to draw a single test line
        line_img = np.zeros((h, w), dtype=np.uint8)
        cv2.line(line_img, pt1, pt2, 255, 1)
        
        # Only keep the parts of the line that overlap the "darkness mask"
        active_line = cv2.bitwise_and(line_img, mask)
        
        # Find coordinates of active pixels
        points = cv2.findNonZero(active_line)
        if points is not None:
            # Sort points to ensure the motor moves in a continuous line
            points = points.reshape(-1, 2)
            lines.append(points)
            
    return lines

def process_image_to_hatch(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return

    # Resize for processing speed while maintaining aspect ratio
    h_orig, w_orig = img.shape
    scale_factor = 500 / w_orig
    img = cv2.resize(img, (500, int(h_orig * scale_factor)))
    h, w = img.shape
    
    # Calculate physical scaling
    phys_scale = DRAWING_WIDTH_INCHES / w
    spacing_px = int(LINE_SPACING_INCHES / phys_scale)
    offset_x = (BOARD_WIDTH_INCHES - DRAWING_WIDTH_INCHES) / 2.0

    # Define 4 darkness levels (0=black, 255=white)
    # Layer 1: Light shadows. Layer 2: Midtones. Layer 3: Dark. Layer 4: Deep Black.
    thresholds = [200, 150, 100, 50]
    angles = [45, 135, 0, 90] # Cross-hatched angles
    
    all_paths = []

    for i in range(len(thresholds)):
        # Create a mask of pixels DARKER than the threshold
        _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
        print(f"Processing Layer {i+1} at {angles[i]} degrees...")
        layer_lines = generate_hatch_lines(mask, angles[i], spacing_px)
        all_paths.extend(layer_lines)

    # Write to drawing.txt
    with open(output_path, 'w') as f:
        f.write("# Crosshatch Drawing\nUP\n")
        for path in all_paths:
            # Move to start of line
            start_x = (path[0][0] * phys_scale) + offset_x
            start_y = (path[0][1] * phys_scale) + DRAWING_START_Y
            f.write(f"MOVE {start_x:.2f} {start_y:.2f}\nDOWN\n")
            
            # Draw to end of line
            end_x = (path[-1][0] * phys_scale) + offset_x
            end_y = (path[-1][1] * phys_scale) + DRAWING_START_Y
            f.write(f"MOVE {end_x:.2f} {end_y:.2f}\nUP\n")

    print(f"Done! Instructions saved to {output_path}")

process_image_to_hatch("test_image.jpg", "drawing.txt")
