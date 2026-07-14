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
        #check if the shape is a rectangle or circle
        isRect = isinstance(element, svg.Rect)
        isCircle = isinstance(element, svg.Circle)

        if isRect or isCircle:

            fillObject = element.fill
            #check if the fill value is not present, otherwise, put it into fillInfo string
            if fillObject is None or fillObject == "none" or fillObject.opacity == 0:
                fillInfo = "transparent or something"
            else:
                fillInfo = "infill: " + str(fillObject.hex) + "(printer doesnt support opacity, so it will ignore it)"

            #similar check to see if there is a stroke(border)
            strokeObject = element.stroke
            strokeWidthPreProcess = element.stroke_width

            if strokeObject is None or strokeObject == "none" or strokeWidthPreProcess == 0:
                strokeInfo = "no stroke"
            else:
                strokeInfo = "stroke color: " + str(strokeObject.hex) + "stroke width: " + str(strokeWidthPreProcess) + "px"
            
            # printing the information
            #                
            # check if the image has a rectangle
            if isinstance(element, svg.Rect):
                print("\nrectangle present:")
                print(f"position: x={element.x}, y={element.y}")
                print(f"dimensions: width={element.width}, height={element.height}")
                print(fillInfo)
                print(strokeInfo)

            # check if there is a circle
            elif isinstance(element, svg.Circle):
                print("\ncircle present")
                print(f"center: cx={element.cx}, cy={element.cy}")
                print(f"radius: r={element.rx}")
                print(fillInfo)
                print(strokeInfo)

dumpSvg(target_svg)
extractShapes(target_svg)