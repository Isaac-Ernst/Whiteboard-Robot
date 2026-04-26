import cv2
import numpy as np

# --- CALIBRATED CONSTANTS ---
BOARD_WIDTH_INCHES = 36.0      
MAX_DRAW_WIDTH = 24.0    # Horizontal limit
MAX_DRAW_HEIGHT = 18.0   # Vertical limit (to stay in the 'sweet spot')
DRAW_START_Y = 10.0      # Top margin
LINE_SPACING_INCHES = 0.15  

def get_clean_segments(mask, pt1, pt2, reverse=False):
    h, w = mask.shape
    line_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.line(line_mask, pt1, pt2, 255, 1)
    active = cv2.bitwise_and(line_mask, mask)
    pts = cv2.findNonZero(active)
    if pts is None: return []
    pts = pts.reshape(-1, 2)
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    if reverse: pts = pts[::-1]
    segments = []
    if len(pts) > 0:
        curr = [pts[0]]
        for i in range(1, len(pts)):
            if np.linalg.norm(pts[i] - pts[i-1]) < 3.5:
                curr.append(pts[i])
            else:
                segments.append(curr)
                curr = [pts[i]]
        segments.append(curr)
    return segments

def process_any_image(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Could not load {image_path}")
        return

    # 1. Pre-Processing (Gamma & CLAHE)
    gamma = 1.2
    lut = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img = cv2.LUT(img, lut)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    img = clahe.apply(img)

    # 2. Dynamic Scaling & Centering Logic
    h_px, w_px = img.shape
    
    # Calculate potential scales for both dimensions
    scale_w = MAX_DRAW_WIDTH / w_px
    scale_h = MAX_DRAW_HEIGHT / h_px
    
    # Use the smaller scale to ensure the image fits in BOTH directions
    phys_scale = min(scale_w, scale_h)
    
    # Final physical size in inches
    final_w_in = w_px * phys_scale
    final_h_in = h_px * phys_scale
    
    # Calculate offsets to center the image in the drawing area
    offset_x = (BOARD_WIDTH_INCHES - final_w_in) / 2.0
    offset_y = DRAW_START_Y + (MAX_DRAW_HEIGHT - final_h_in) / 2.0

    print(f"Image auto-scaled to {final_w_in:.2f}\" x {final_h_in:.2f}\"")
    print(f"Centering at X offset: {offset_x:.2f}, Y offset: {offset_y:.2f}")

    # 3. High-Res Internal Resize
    tw = 1000
    img = cv2.resize(img, (tw, int(h_px * (tw / w_px))))
    h, w = img.shape
    pixel_to_in_scale = final_w_in / w
    spacing_px = max(1, int(LINE_SPACING_INCHES / pixel_to_in_scale))

    # 4. Hatching Loop
    thresholds = [225, 170, 115, 60]
    angles = [45, 135, 0, 90]
    
    with open(output_path, 'w') as f:
        f.write(f"# Auto-Centered Instructions for {image_path}\nUP\n")
        
        for i in range(len(thresholds)):
            _, mask = cv2.threshold(img, thresholds[i], 255, cv2.THRESH_BINARY_INV)
            angle = angles[i]
            diag = int(np.sqrt(h**2 + w**2))
            
            line_idx = 0
            for d in range(-diag, diag, spacing_px):
                line_idx += 1
                x0, y0 = d * np.cos(np.radians(angle)), d * np.sin(np.radians(angle))
                vx, vy = np.cos(np.radians(angle + 90)), np.sin(np.radians(angle + 90))
                p1, p2 = (int(x0 - vx * diag), int(y0 - vy * diag)), (int(x0 + vx * diag), int(y0 + vy * diag))
                
                segs = get_clean_segments(mask, p1, p2, reverse=(line_idx % 2 == 0))
                for s in segs:
                    sx, sy = (s[0][0] * pixel_to_in_scale) + offset_x, (s[0][1] * pixel_to_in_scale) + offset_y
                    ex, ey = (s[-1][0] * pixel_to_in_scale) + offset_x, (s[-1][1] * pixel_to_in_scale) + offset_y
                    f.write(f"MOVE {sx:.2f} {sy:.2f}\nDOWN\nMOVE {ex:.2f} {ey:.2f}\nUP\n")

    print(f"Success! Instructions generated in {output_path}")

# You can now throw any image at it
process_any_image("tamu-final-final.jpg", "drawing.txt")
