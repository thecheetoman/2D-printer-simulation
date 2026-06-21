import pygame
import sys
from printer import Printer
from parser import parse_banana_file

WIDTH = 800
HEIGHT = 600

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Printer Simulator")

# makey printer
printer = Printer(WIDTH, HEIGHT)

# parse files so that i can eat dinner
if len(sys.argv) < 2:
    print("Error: Please provide a file path.")
    print('Usage: python3 ./src/renderer.py "./examples/square.banana"')
    sys.exit(1)

target_file = sys.argv[1]
commands = parse_banana_file(target_file)

# what command do when how many
current_command_index = 0

# intrepolation vroom
current_x = printer.center_x
current_y = printer.center_y
target_x = printer.center_x
target_y = printer.center_y
interpolation_speed = 300  # pixels per second

running = True
clock = pygame.time.Clock()

# start fist fomsnad
if commands:
    printer.execute(commands[current_command_index])
    target_x = printer.x
    target_y = printer.y
    current_command_index += 1
screen.fill((255, 255, 255))
while running:
    dt = clock.tick(60) / 1000.0  # delta airlines(delta time)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # interpolate or something
    dx = target_x - current_x
    dy = target_y - current_y
    distance = (dx**2 + dy**2)**0.5

    if distance > 0.1:  # prevent jitter
        # MOVEEE
        move_distance = interpolation_speed * dt
        if move_distance < distance:
            # normalize and move
            current_x += (dx / distance) * move_distance
            current_y += (dy / distance) * move_distance
        else:
            # reaching target store?
            current_x = target_x
            current_y = target_y
    else:
        # next cmd
        if current_command_index < len(commands):
            printer.execute(commands[current_command_index])
            target_x = printer.x
            target_y = printer.y
            current_command_index += 1


    # make it black
    pygame.draw.circle(screen, (0, 0, 0), (int(current_x), int(current_y)), 5)

    pygame.display.flip()

pygame.quit()