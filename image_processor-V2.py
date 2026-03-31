import cv2
import numpy as np

# --- CALIBRATED DIMENSIONS ---
BOARD_WIDTH_INCHES = 36.0      
DRAW_WIDTH_INCHES = 24.0    
DRAW_START_Y = 10.0         
LINE_SPACING_INCHES = 0.05  

def get_line_segments(mask, pt1, pt2):
    """
    Traces a line between two points and finds continuous segments 
    where the mask is active (black fur).
    """
    h, w = mask.shape
    # Create a temporary black canvas to draw one single line
    line_img = np.zeros((h, w), dtype=np.uint8)
    cv2.line(line_img, pt1, pt2, 255, 1)
    
    # Intersection of the grid line and the darkness mask
    active_pixels = cv2.bitwise_and(line_img, mask)
    
    # Get all points that should be drawn
    points = cv2.findNonZero(active_pixels)
    if points is None:
        return []

    points = points.reshape(-1, 2)
    # Sort points by X (or Y) to keep them in order along the line
    points = points[np.lexsort((points[:, 1], points[:, 0]))]
    
    segments = []
    if len(points) > 0:
        current_segment = [points[0]]
        for i in range(1, len(points)):
            # If the distance between pixels is > 2, it's a gap (white space)
            dist = np.linalg.norm(points[i] - points[i-1])
            if dist < 2.5:
                current_segment.append(points[i])
            else:
                segments.append(current_segment)
                current_segment = [points[i]]
        segments.append(current_segment)
        
    return segments

def process_image_to_hatch(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return

    # Resize to a manageable resolution for the algorithm
    h_orig, w_orig = img.shape
    target_w = 800 
    img = cv2.resize(img, (target_w, int(h_orig * (target_w / w_orig))))
    h, w = img.shape
    
    phys_scale = DRAW_WIDTH_INCHES / w
    spacing_px = max(1, int(LINE_SPACING_INCHES / phys_scale))
    offset_x = (BOARD_WIDTH_INCHES - DRAW_WIDTH_INCHES) / 2.0

    thresholds = [200, 150, 100, 50]
    angles = [45, 135, 0, 90] 
    
    with open(output_path, 'w') as f:
        f.write("# Segmented Crosshatch Instructions\nUP\n")
        
        for i in range(len(thresholds)):
            _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
            angle = angles[i]
            diag = int(np.sqrt(h**2 + w**2))
            
            print(f"Processing Layer {i+1} ({angle} degrees)...")
            
            for d in range(-diag, diag, spacing_px):
                # Calculate endpoints for the scanline
                x0 = d * np.cos(np.radians(angle))
                y0 = d * np.sin(np.radians(angle))
                vx, vy = np.cos(np.radians(angle + 90)), np.sin(np.radians(angle + 90))
                
                pt1 = (int(x0 - vx * diag), int(y0 - vy * diag))
                pt2 = (int(x0 + vx * diag), int(y0 + vy * diag))
                
                # Find only the segments that stay inside the black fur
                segments = get_line_segments(mask, pt1, pt2)
                
                for seg in segments:
                    # Move to start of segment
                    sx = (seg[0][0] * phys_scale) + offset_x
                    sy = (seg[0][1] * phys_scale) + DRAW_START_Y
                    f.write(f"MOVE {sx:.2f} {sy:.2f}\nDOWN\n")
                    
                    # Draw to end of segment
                    ex = (seg[-1][0] * phys_scale) + offset_x
                    ey = (seg[-1][1] * phys_scale) + DRAW_START_Y
                    f.write(f"MOVE {ex:.2f} {ey:.2f}\nUP\n")

    print(f"Success! {output_path} generated.")

process_image_to_hatch("test_image.jpg", "drawing.txt")
