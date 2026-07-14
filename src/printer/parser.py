import sys
from pathlib import Path
from printer import Printer

def parse_banana_file(target_file):
    # Parse a sliced .banana file
    commands = []
    try:
        with open(target_file, "r") as sliceimage:
            contents = sliceimage.readlines()
            
            for line in contents:
                line = line.strip()
                if not line:
                    continue
                token = line.split()

                if token[0] == "HOME":
                    commands.append(("HOME",))
                elif token[0] == "MOVE":
                    commands.append(("MOVE", int(token[1]), int(token[2])))
                elif token[0] == "START":
                    commands.append(("START",))
                elif token[0] == "END":
                    commands.append(("END",))
                elif token[0].upper() == "INFILL":
                    commands.append(("INFILL",))
                elif token[0].upper() == "DRAW":
                    commands.append(("DRAW",))
                elif token[0] == "COLOR":
                    commands.append(("COLOR", int(token[1]), int(token[2]), int(token[3])))
                elif token[0] == "BED":
                    commands.append(("BED", int(token[1]), int(token[2])))
        
        return commands
    except FileNotFoundError:
        print("Error: The .banana file does not exist")
        sys.exit(1)

# run directly = go vrooom
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a file path.")
        print('Usage: python3 ./src/parser.py "./examples/square.banana"')
        sys.exit(1)

    printer = Printer()
    target_file = sys.argv[1]
    commands = parse_banana_file(target_file)
    
    for command in commands:
        printer.execute(command)