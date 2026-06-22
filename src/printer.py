class Printer:
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_x = 700
        self.center_y = 100
        self.x = self.center_x
        self.y = self.center_y
        self.r = 0
        self.g = 0                  
        self.b = 0
        self.pen_down = False

    def execute(self, command):
        if command[0] == "HOME":
            self.x = self.center_x
            self.y = self.center_y

        elif command[0] == "MOVE":
            if len(command) >= 3:
                self.x = command[1]
                self.y = command[2]
            else:
                print(f"Error: Invalid MOVE command format: {command}")

        elif command[0] == "START":
            self.pen_down = True

        elif command[0] == "END":
            self.pen_down = False
        elif command[0] == "COLOR":
            if len(command) >= 4:
                self.r = command[1]
                self.g = command[2]
                self.b = command[3]
            else:
                print(f"Error: Invalid COLOR command format: {command}")

        print(f"Position: ({self.x}, {self.y})")