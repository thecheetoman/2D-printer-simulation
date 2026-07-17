import svgelements as svg
import sys 
from tqdm import tqdm

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

def is_point_inside_polygon(point, polygon_points):
    """Ray casting algorithm to check if point is inside polygon"""
    x, y = point
    inside = False
    n = len(polygon_points)
    
    for i in range(n):
        p1_x, p1_y = polygon_points[i]
        p2_x, p2_y = polygon_points[(i + 1) % n]
        
        # Check if ray crosses the edge
        if ((p1_y > y) != (p2_y > y)):
            x_intersect = p1_x + (y - p1_y) * (p2_x - p1_x) / (p2_y - p1_y)
            if x < x_intersect:
                inside = not inside
    
    return inside

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
                
        # --- INFILL SPLICING (IMPROVED Y-AXIS SCANLINE) ---
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
                
                # Step 1: Convert path to high-resolution polygon
                path_length = path_element.length() * scaleFactor
                num_samples = max(100, int(path_length / 0.3))  # High resolution
                
                poly_points = []
                for i in range(num_samples + 1):
                    t = i / num_samples
                    pt = path_element.point(t)
                    poly_points.append((pt.x * scaleFactor, pt.y * scaleFactor))
                
                # Step 2: Scan along Y axis (more stable for star shapes)
                going_right = True
                
                # Scan from top to bottom
                for y in range(int(ymin) + 2, int(ymax) - 1, infill_spacing):
                    # Find all x intersections at this y level
                    intersections = []
                    
                    # Check each polygon edge for intersection with horizontal ray at y
                    for i in range(len(poly_points)):
                        p1 = poly_points[i]
                        p2 = poly_points[(i + 1) % len(poly_points)]
                        
                        # Check if horizontal ray crosses this edge
                        if (p1[1] > y) != (p2[1] > y):
                            # Calculate x at this y
                            x_intersect = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                            intersections.append(x_intersect)
                    
                    # Sort intersections
                    intersections.sort()
                    
                    # Remove duplicates (floating point precision)
                    unique_intersections = []
                    for x in intersections:
                        if not unique_intersections or abs(x - unique_intersections[-1]) > 0.5:
                            unique_intersections.append(x)
                    
                    # Need at least 2 intersections
                    if len(unique_intersections) < 2:
                        continue
                    
                    # Pair intersections: (0,1), (2,3), (4,5), etc.
                    for i in range(0, len(unique_intersections) - 1, 2):
                        x_start = unique_intersections[i]
                        x_end = unique_intersections[i + 1]
                        
                        # Make sure start < end
                        if x_start > x_end:
                            x_start, x_end = x_end, x_start
                        
                        # Add small buffer to avoid edge artifacts
                        x_start += 1
                        x_end -= 1
                        
                        # Only draw if we have a valid range
                        if x_end - x_start > 1:
                            offset_x_start = int(x_start + xOffset)
                            offset_x_end = int(x_end + xOffset)
                            offset_y_val = int(y + yOffset)
                            
                            # Draw horizontal line
                            if going_right:
                                instructions.append(f"MOVE {offset_x_start} {offset_y_val}")
                                instructions.append(f"MOVE {offset_x_end} {offset_y_val}")
                            else:
                                instructions.append(f"MOVE {offset_x_end} {offset_y_val}")
                                instructions.append(f"MOVE {offset_x_start} {offset_y_val}")
                            
                            going_right = not going_right
                    
                instructions.append("END")
                
    instructions.append("HOME")
    
    with open("sliced_output.txt", "w") as f:
        f.write("\n".join(instructions))
    print("\nSlicing complete! Output saved to sliced_output.txt.")

slice_svg(target_svg)