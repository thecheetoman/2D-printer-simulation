import svgelements as svg
import sys 
from tqdm import tqdm  # progress bar wizardry =D

# check if user provided a target file
if len(sys.argv) < 2:
    print("Please provide a valid target to an SVG")
    print("EX: python3 main.py testsubject.svg")
    sys.exit()

target_svg = sys.argv[1]

# check if target file is really an svg
if ".svg" not in target_svg:
    print("Please provide a valid target to an SVG")
    sys.exit()

def hex_to_rgb(hex_str):
    if not hex_str:
        return (120, 125, 130) # fallback grey
    hex_str = str(hex_str).lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# user inputs
xOffset = int(input("please enter an x offset(px): "))
yOffset = int(input("please enter a y offset(px): "))
scaleFactor = float(input("please enter a scale factor (ex: 1.0 = 100%, 0.5 = 50%): "))

def slice_svg(target):
    targetSvgInstance = svg.SVG.parse(target)
    instructions = ["HOME"]
    elements_list = list(targetSvgInstance.elements())
    
    for element in tqdm(elements_list, desc="Slicing SVG", unit="element"):
        if not isinstance(element, (svg.Rect, svg.Circle, svg.Path, svg.Polygon, svg.Polyline, svg.Line)):
            continue
            
        path_element = svg.Path(element)
        stroke_color = hex_to_rgb(element.stroke.hex) if element.stroke and element.stroke != "none" else None
        fill_color = hex_to_rgb(element.fill.hex) if element.fill and element.fill != "none" else None
        
        # --- PERIMETER SPLICING ---
        if stroke_color:
            path_length = path_element.length()
            num_points = max(2, int(path_length / 2.0))
            
            points = []
            for i in range(num_points):
                t = i / (num_points - 1)
                point = path_element.point(t)
                points.append((point.x * scaleFactor + xOffset, point.y * scaleFactor + yOffset))
            
            if len(points) > 1:
                instructions.append(f"COLOR {stroke_color[0]} {stroke_color[1]} {stroke_color[2]}")
                instructions.append(f"MOVE {int(points[0][0])} {int(points[0][1])}")
                instructions.append("START")
                for pt in points[1:]:
                    instructions.append(f"MOVE {int(pt[0])} {int(pt[1])}")
                instructions.append("END")
                
        # --- INFILL SPLICING (OPTIMIZED SCANLINE) ---
        if fill_color:
            instructions.append(f"COLOR {fill_color[0]} {fill_color[1]} {fill_color[2]}")
            
            bbox = path_element.bbox() 
            if bbox:
                # Scale boundaries upfront
                xmin = bbox[0] * scaleFactor
                ymin = bbox[1] * scaleFactor
                xmax = bbox[2] * scaleFactor
                ymax = bbox[3] * scaleFactor
                
                infill_spacing = 2 
                instructions.append("START")
                
                # Step 1: Flatten curves into high-fidelity line segments once
                path_length = path_element.length() * scaleFactor
                num_samples = max(30, int(path_length / 1.0))
                
                poly_points = []
                for i in range(num_samples + 1):
                    t = i / num_samples
                    pt = path_element.point(t)
                    poly_points.append((pt.x * scaleFactor, pt.y * scaleFactor))
                
                # Step 2: Build segments and pre-calculate min_x/max_x bounds
                segments = []
                for i in range(len(poly_points) - 1):
                    p1, p2 = poly_points[i], poly_points[i+1]
                    if p1[0] != p2[0]: # Skip vertical segments to avoid division by zero
                        segments.append({
                            'p1': p1,
                            'p2': p2,
                            'min_x': min(p1[0], p2[0]),
                            'max_x': max(p1[0], p2[0])
                        })
                
                # Sort segments globally by min_x
                segments.sort(key=lambda s: s['min_x'])
                
                going_down = True
                segment_idx = 0
                num_segments = len(segments)
                active_segments = []
                
                # Step 3: Scan horizontally across the shape
                for x in range(int(xmin) + 2, int(xmax) - 1, infill_spacing):
                    
                    # Add segments that have entered the active scanline area
                    while segment_idx < num_segments and segments[segment_idx]['min_x'] <= x:
                        active_segments.append(segments[segment_idx])
                        segment_idx += 1
                    
                    # Evict segments that the scanline has completely moved past
                    active_segments = [s for s in active_segments if s['max_x'] >= x]
                    
                    # Calculate vertical intersection points for ONLY active lines
                    intersections = []
                    for seg in active_segments:
                        p1, p2 = seg['p1'], seg['p2']
                        y_intersect = p1[1] + (x - p1[0]) * (p2[1] - p1[1]) / (p2[0] - p1[0])
                        intersections.append(y_intersect)
                    
                    intersections = sorted(list(set(intersections)))
                    if len(intersections) < 2:
                        continue
                        
                    y_start = intersections[0] + 1
                    y_end = intersections[-1] - 1
                    
                    # Apply translation offsets (yOffset used properly here!)
                    offset_x_val = x + xOffset
                    offset_y_start = int(y_start) + yOffset
                    offset_y_end = int(y_end) + yOffset
                    
                    if going_down:
                        instructions.append(f"MOVE {offset_x_val} {offset_y_start}")
                        instructions.append(f"MOVE {offset_x_val} {offset_y_end}")
                    else:
                        instructions.append(f"MOVE {offset_x_val} {offset_y_end}")
                        instructions.append(f"MOVE {offset_x_val} {offset_y_start}")
                        
                    going_down = not going_down
                    
                instructions.append("END")
                
    instructions.append("HOME")
    
    with open("sliced_output.txt", "w") as f:
        f.write("\n".join(instructions))
    print("\nSlicing complete! Output saved to sliced_output.txt.")

slice_svg(target_svg)