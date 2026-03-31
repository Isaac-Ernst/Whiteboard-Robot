import cv2
import numpy as np

# --- CALIBRATED CONSTANTS ---
BOARD_WIDTH_INCHES = 36.0      
DRAW_WIDTH_INCHES = 24.0    
DRAW_START_Y = 10.0         
LINE_SPACING_INCHES = 0.05  

def get_clean_segments(mask, pt1, pt2, reverse=False):
    h, w = mask.shape
    line_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.line(line_mask, pt1, pt2, 255, 1)
    
    # Extract only the pixels on this line that are "Dark"
    active = cv2.bitwise_and(line_mask, mask)
    pts = cv2.findNonZero(active)
    
    if pts is None: return []
    
    pts = pts.reshape(-1, 2)
    # Sort along the line's primary axis
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    if reverse: pts = pts[::-1]
    
    segments = []
    if len(pts) > 0:
        curr = [pts[0]]
        for i in range(1, len(pts)):
            # If gap > 3 pixels, it's a "white" area; break the segment
            if np.linalg.norm(pts[i] - pts[i-1]) < 3.5:
                curr.append(pts[i])
            else:
                segments.append(curr)
                curr = [pts[i]]
        segments.append(curr)
    return segments

def process_dog_image(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return

    # Scale image to 1000px width for high-fidelity processing
    h_orig, w_orig = img.shape
    tw = 1000
    img = cv2.resize(img, (tw, int(h_orig * (tw / w_orig))))
    h, w = img.shape
    
    phys_scale = DRAW_WIDTH_INCHES / w
    spacing_px = max(1, int(LINE_SPACING_INCHES / phys_scale))
    offset_x = (BOARD_WIDTH_INCHES - DRAW_WIDTH_INCHES) / 2.0

    # 4 layers of hatching for deep tonal range
    thresholds = [210, 160, 110, 60]
    angles = [45, 135, 0, 90]
    
    with open(output_path, 'w') as f:
        f.write("# Perfected CSCE 462 Instructions\nUP\n")
        
        for i in range(len(thresholds)):
            _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
            angle = angles[i]
            diag = int(np.sqrt(h**2 + w**2))
            
            line_idx = 0
            for d in range(-diag, diag, spacing_px):
                line_idx += 1
                # Calculate scanline vector
                x0, y0 = d * np.cos(np.radians(angle)), d * np.sin(np.radians(angle))
                vx, vy = np.cos(np.radians(angle + 90)), np.sin(np.radians(angle + 90))
                p1 = (int(x0 - vx * diag), int(y0 - vy * diag))
                p2 = (int(x0 + vx * diag), int(y0 + vy * diag))
                
                # Snake pathing for efficiency
                segs = get_clean_segments(mask, p1, p2, reverse=(line_idx % 2 == 0))
                
                for s in segs:
                    sx, sy = (s[0][0] * phys_scale) + offset_x, (s[0][1] * phys_scale) + DRAW_START_Y
                    ex, ey = (s[-1][0] * phys_scale) + offset_x, (s[-1][1] * phys_scale) + DRAW_START_Y
                    f.write(f"MOVE {sx:.2f} {sy:.2f}\nDOWN\nMOVE {ex:.2f} {ey:.2f}\nUP\n")

    print(f"Instructions perfected in {output_path}")

process_dog_image("test_image.jpg", "drawing.txt")
