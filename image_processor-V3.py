import cv2
import numpy as np

# --- CALIBRATED DIMENSIONS ---
BOARD_WIDTH_INCHES = 36.0      
DRAW_WIDTH_INCHES = 24.0    
DRAW_START_Y = 10.0         
LINE_SPACING_INCHES = 0.05  

def get_line_segments(mask, pt1, pt2, reverse=False):
    h, w = mask.shape
    line_img = np.zeros((h, w), dtype=np.uint8)
    cv2.line(line_img, pt1, pt2, 255, 1)
    active_pixels = cv2.bitwise_and(line_img, mask)
    
    points = cv2.findNonZero(active_pixels)
    if points is None: return []

    points = points.reshape(-1, 2)
    # Sort points along the line axis
    points = points[np.lexsort((points[:, 1], points[:, 0]))]
    
    # If this is an 'even' line, we draw it backwards to stay close to the last end-point
    if reverse:
        points = points[::-1]

    segments = []
    if len(points) > 0:
        current_segment = [points[0]]
        for i in range(1, len(points)):
            dist = np.linalg.norm(points[i] - points[i-1])
            if dist < 3.0: # Gap tolerance
                current_segment.append(points[i])
            else:
                segments.append(current_segment)
                current_segment = [points[i]]
        segments.append(current_segment)
    return segments

def process_image_to_hatch(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return

    h_orig, w_orig = img.shape
    target_w = 1000 # Higher res for better detail
    img = cv2.resize(img, (target_w, int(h_orig * (target_w / w_orig))))
    h, w = img.shape
    
    phys_scale = DRAW_WIDTH_INCHES / w
    spacing_px = max(1, int(LINE_SPACING_INCHES / phys_scale))
    offset_x = (BOARD_WIDTH_INCHES - DRAW_WIDTH_INCHES) / 2.0

    thresholds = [200, 150, 100, 50]
    angles = [45, 135, 0, 90] 
    
    with open(output_path, 'w') as f:
        f.write("# Optimized Zig-Zag Instructions\nUP\n")
        
        for i in range(len(thresholds)):
            _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
            angle = angles[i]
            diag = int(np.sqrt(h**2 + w**2))
            
            print(f"Layer {i+1}...")
            
            line_count = 0
            for d in range(-diag, diag, spacing_px):
                line_count += 1
                x0, y0 = d * np.cos(np.radians(angle)), d * np.sin(np.radians(angle))
                vx, vy = np.cos(np.radians(angle + 90)), np.sin(np.radians(angle + 90))
                pt1 = (int(x0 - vx * diag), int(y0 - vy * diag))
                pt2 = (int(x0 + vx * diag), int(y0 + vy * diag))
                
                # Zig-zag: Reverse every other line
                do_reverse = (line_count % 2 == 0)
                segments = get_line_segments(mask, pt1, pt2, reverse=do_reverse)
                
                for seg in segments:
                    sx, sy = (seg[0][0] * phys_scale) + offset_x, (seg[0][1] * phys_scale) + DRAW_START_Y
                    ex, ey = (seg[-1][0] * phys_scale) + offset_x, (seg[-1][1] * phys_scale) + DRAW_START_Y
                    f.write(f"MOVE {sx:.2f} {sy:.2f}\nDOWN\nMOVE {ex:.2f} {ey:.2f}\nUP\n")

    print(f"Success! Optimized {output_path} generated.")
    