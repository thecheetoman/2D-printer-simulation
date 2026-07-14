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

def dumpSvg(target):
    targetSvgInstance = svg.SVG.parse(target)
    stringDump = targetSvgInstance.string_xml()
    print(stringDump)

dumpSvg(target_svg)