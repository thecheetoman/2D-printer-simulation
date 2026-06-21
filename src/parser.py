import sys
from pathlib import Path
from printer import Printer

printer = Printer()

# Check if the .banana file was ever included
if len(sys.argv) < 2:
    print("Error: Please provide a file path.")
    print('Usage: python3 ./src/printer/parser.py "./examples/square.banana"')
    sys.exit(1)

#Store the file for later use
target_file = sys.argv[1]
#Debug print the inputted file
print(target_file)

try:
    with open(target_file, "r") as sliceimage:
        contents = sliceimage.readlines()
        print("Raw file contents " + str(contents))
        print("\n \n Processing PT 1(Fixing spacing)")
        
        commands = []

        # .banana processing
        for line in contents:
            #Strip line of unnecesary styff
            line = line.strip()
            #Null check
            if not line:
                continue
            #Process each command and seperate each value from text
            #EX MOVE 50 50 ["MOVE", "50", "50"]
            token = line.split()

            #Token processing
            if token[0] == "HOME":
                commands.append(("HOME",))
            elif token[0] == "MOVE":
                commands.append(("MOVE", int(token[1]), int(token[2])))
            elif token[0] == "START":
                commands.append(("START",))
            elif token[0] == "END":
                commands.append(("END"),)
            elif token[0] == "COLOR":
                commands.append(("COLOR", int(token[1]), int(token[2]), int(token[3])))
            #Print out each line
            print(token)
        print(commands)
        for command in commands:
            printer.execute(command)
except FileNotFoundError:
    print("Error: The .banana file does not exist")