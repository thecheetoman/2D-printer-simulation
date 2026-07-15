import svgelements as svg
import sys 

#check if user provided a target file
if len(sys.argv) < 2:
    print("Please provide a valid target to an SVG")
    print("EX: python3 main.py testsubject.svg")
    sys.exit()

target_svg = sys.argv[1]

#check if target file is really an svg
if ".svg" not in target_svg:
    print("Please provide a valid target to an SVG")
    sys.exit()

def hex_to_rgb(hex_str):
    # hex to rgb since the 2d printer can only 
    if not hex_str:
        return (120, 125, 130) # fallback grey
    hex_str = str(hex_str).lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def slice_svg(target):
    targetSvgInstance = svg.SVG.parse(target)
    
    # list of instructions(.banana file)
    instructions = ["HOME"]
    
    for element in targetSvgInstance.elements():
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
                points.append((point.x, point.y))
            
            if len(points) > 1:
                instructions.append(f"COLOR {stroke_color[0]} {stroke_color[1]} {stroke_color[2]}")
                
                # move to the beginning of the shape
                instructions.append(f"MOVE {int(points[0][0])} {int(points[0][1])}")
                instructions.append("START")
                for pt in points[1:]:
                    instructions.append(f"MOVE {int(pt[0])} {int(pt[1])}")
                instructions.append("END")
                
        # infil
        if fill_color:
            
            instructions.append(f"COLOR {fill_color[0]} {fill_color[1]} {fill_color[2]}")
            
            # get the shapes boundaries
            bbox = path_element.bbox() # (xmin, ymin, xmax, ymax)
            if bbox:
                xmin, ymin, xmax, ymax = bbox
                
                # infill spacing, i forgot how much the printer needs so imma start with 4
                infill_spacing = 2 
                
                # we need vertical zig zags to make infil
                instructions.append("START")
                
                going_down = True
                # move horizontally along the shape
                for x in range(int(xmin), int(xmax), infill_spacing):
                    # constraint to x max and minimum
                    # MAKE THIS LATER: calculating precise values
                    y_start = int(ymin)
                    y_end = int(ymax)
                    
                    if going_down:
                        instructions.append(f"MOVE {x} {y_start}")
                        instructions.append(f"MOVE {x} {y_end}")
                    else:
                        instructions.append(f"MOVE {x} {y_end}")
                        instructions.append(f"MOVE {x} {y_start}")
                        
                    going_down = not going_down # switch direction
                    
                instructions.append("END")
                
    instructions.append("HOME")
    
    # output sliced file
    print("\n".join(instructions))
    
    # saving to file
    with open("sliced_output.txt", "w") as f:
        f.write("\n".join(instructions))

slice_svg(target_svg)