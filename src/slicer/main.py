import svgelements as svg
import sys 

#check it user provided a target svg
if len(sys.argv) < 2:
    print("Please provide a valid target to an SVG")
    print("EX: python3 main.py testsubject.svg")
    sys.exit()

#check if user provided actually provided an svg or a random file
target_svg = sys.argv[1]
if ".svg" not in target_svg:
    print("Please provide a valid target to an SVG")
    print("EX: python3 main.py testsubject.svg")
    sys.exit()

#function used to dump svg(remove this later if not used)
def dumpSvg(target):
    targetSvgInstance = svg.SVG.parse(target)
    stringDump = targetSvgInstance.string_xml()
    print(stringDump)

#function used to extract shapes from an SVG
def extractShapes(target):
    targetSvgInstance = svg.SVG.parse(target)
    for element in targetSvgInstance.elements():
        # check if the image has a rectangle
        if isinstance(element, svg.Rect):
            print("\nrectangle present:")
            print(f"position: x={element.x}, y={element.y}")
            print(f"dimensions: width={element.width}, height={element.height}")
            
        # check if there is a circle
        elif isinstance(element, svg.Circle):
            print("\ncircle present")
            print(f"center: cx={element.cx}, cy={element.cy}")
            print(f"radius: r={element.r}")

dumpSvg(target_svg)
extractShapes(target_svg)