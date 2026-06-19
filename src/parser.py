import sys
from pathlib import Path

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
        print(contents)
except FileNotFoundError:
    print("Error: The .banana file does not exist")