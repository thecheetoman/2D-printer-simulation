import svgelements as svg
import sys 
import numpy
from tqdm import tqdm  # Imported tqdm for the progress bar

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
    # hex to rgb since the 2d printer can only 
    if not hex_str:
        return (120, 125, 130) # fallback grey
    hex_str = str(hex_str).lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# offsets so you dont have it clipped into the corner
xOffset = int(input("please enter an x offset(px): "))
yOffset = int(input("please enter a y offset(px): "))


def slice_svg(target):
    targetSvgInstance = svg.SVG.parse(target)
    
    # list of instructions(.banana file)
    instructions = ["HOME"]
    
    # Convert elements to a list so tqdm can calculate the total count and ETA
    elements_list = list(targetSvgInstance.elements())
    
    # Wrap the loop in tqdm to display the progress bar
    for element in tqdm(elements_list, desc="Slicing SVG", unit="element"):
        # ignore svg structure stuff(<svg></svg> tags and more stuff. this is irrelevant to priting)
        if not isinstance(element, (svg.Rect, svg.Circle, svg.Path, svg.Polygon, svg.Polyline, svg.Line)):
            continue
            
        # basically turn into lines and stuff, which the printer can print
        path_element = svg.Path(element)
        
        # extract colors
        stroke_color = hex_to_rgb(element.stroke.hex) if element.stroke and element.stroke != "none" else None
        fill_color = hex_to_rgb(element.fill.hex) if element.fill and element.fill != "none" else None
        
        # make a perimeter
        if stroke_color:
            # get the total length of the path
            path_length = path_element.length()
            
            # determine the amount of points we need.
            # minimum 2(start and an end)
            num_points = max(2, int(path_length / 2.0))
            
            # generate points along that path
            points = []
            for i in range(num_points):
                t = i / (num_points - 1)
                point = path_element.point(t)
                points.append((point.x + xOffset, point.y + yOffset))
            
            if len(points) > 1:
                instructions.append(f"COLOR {stroke_color[0]} {stroke_color[1]} {stroke_color[2]}")
                
                # move to the beginning of the shape
                instructions.append(f"MOVE {int(points[0][0])} {int(points[0][1])}")
                instructions.append("START")
                for pt in points[1:]:
                    instructions.append(f"MOVE {int(pt[0])} {int(pt[1])}")
                instructions.append("END")
                
        # infill
        if fill_color:
            instructions.append(f"COLOR {fill_color[0]} {fill_color[1]} {fill_color[2]}")
            
            bbox = path_element.bbox() # (xmin, ymin, xmax, ymax)
            if bbox:
                xmin, ymin, xmax, ymax = bbox
                
                infill_spacing = 2 
                instructions.append("START")
                
                # --- OPTIMIZATION 1: PRE-GENERATE FLAT PERIMETER LINES ---
                path_length = path_element.length()
                num_samples = max(30, int(path_length / 1.0)) # 1 sample per pixel
                
                # Pre-calculate points to avoid generating them dynamically inside the loop
                poly_points = []
                for i in range(num_samples + 1):
                    t = i / num_samples
                    pt = path_element.point(t)
                    poly_points.append((pt.x, pt.y))
                
                # Group them into segments once, storing min/max X for lightning fast filtering
                segments = []
                for i in range(len(poly_points) - 1):
                    p1 = poly_points[i]
                    p2 = poly_points[i+1]
                    if p1[0] != p2[0]: # Ignore perfectly vertical lines to prevent division by zero
                        segments.append({
                            'p1': p1,
                            'p2': p2,
                            'min_x': min(p1[0], p2[0]),
                            'max_x': max(p1[0], p2[0])
                        })
                
                going_down = True
                
                # Move horizontally along the shape
                for x in range(int(xmin) + 2, int(xmax) - 1, infill_spacing):
                    intersections = []
                    
                    # --- OPTIMIZATION 2: FAST REJECTION FILTERING ---
                    for seg in segments:
                        # Instantly skip segments that don't cross this column
                        if x < seg['min_x'] or x > seg['max_x']:
                            continue
                            
                        # Quick linear interpolation since we already know it crosses
                        p1, p2 = seg['p1'], seg['p2']
                        y_intersect = p1[1] + (x - p1[0]) * (p2[1] - p1[1]) / (p2[0] - p1[0])
                        intersections.append(y_intersect)
                                
                    # Remove duplicates and sort top to bottom
                    intersections = sorted(list(set(intersections)))
                    
                    # If the vertical line doesn't cleanly enter and exit the shape, skip it
                    if len(intersections) < 2:
                        continue
                        
                    # Get precise top and bottom boundaries for this specific column
                    y_start = intersections[0] + 1
                    y_end = intersections[-1] - 1
                    
                    # Apply offsets
                    offset_x_val = x + xOffset
                    offset_y_start = int(y_start) + yOffset
                    offset_y_end = int(y_end) + yOffset
                    
                    if going_down:
                        instructions.append(f"MOVE {offset_x_val} {offset_y_start}")
                        instructions.append(f"MOVE {offset_x_val} {offset_y_end}")
                    else:
                        instructions.append(f"MOVE {offset_x_val} {offset_y_end}")
                        instructions.append(f"MOVE {offset_x_val} {offset_y_start}")
                        
                    going_down = not going_down # switch direction
                    
                instructions.append("END")
                                    
    instructions.append("HOME")
    
    # Save to file
    print("\nSaving sliced instructions to sliced_output.txt...")
    with open("sliced_output.txt", "w") as f:
        f.write("\n".join(instructions))
    print("Slicing complete!")

slice_svg(target_svg)