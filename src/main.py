import pygame
import sys
import os
from printer import Printer
from parser import parse_banana_file

WIDTH = 800
HEIGHT = 600

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Printer Simulator")

# Load background image
background_path = os.path.join(os.path.dirname(__file__), "../assets/printbed.png")
background = pygame.image.load(background_path)
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# makey printer
printer = Printer(WIDTH, HEIGHT)

# parse files so that i can eat dinner
if len(sys.argv) < 2:
    print("Error: Please provide a file path.")
    print('Usage: python3 ./src/main.py "./examples/square.banana"')
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

#intrepolation speeds
interpolation_speed = 300  # The actual variable
nozzleup = 500
nozzledown = 100

running = True
clock = pygame.time.Clock()
shift_pressed = False
started = False
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 32
button_rect = pygame.Rect(
    20,
    HEIGHT - BUTTON_HEIGHT - 10,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
)
button_font = pygame.font.SysFont(None, 22)

while running:
    dt = clock.tick(60) / 1000.0  # delta airlines(delta time)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LSHIFT:
                shift_pressed = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT:
                shift_pressed = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if button_rect.collidepoint(event.pos) and not started:
                started = True
                if commands:
                    printer.execute(commands[current_command_index])
                    target_x = printer.x
                    target_y = printer.y
                    current_command_index += 1

    # interpolate or something
    dx = target_x - current_x
    dy = target_y - current_y
    distance = (dx**2 + dy**2)**0.5
    if printer.pen_down:
        interpolation_speed = nozzledown
    else:
        interpolation_speed = nozzleup

    if started:
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


    # background image i epically created
    screen.blit(background, (0, 0))

    # draw start button with transparency
    button_color = (40, 130, 35, 180) if not started else (80, 80, 80, 180)
    button_surface = pygame.Surface((BUTTON_WIDTH, BUTTON_HEIGHT), pygame.SRCALPHA)
    button_surface.fill(button_color)
    pygame.draw.rect(button_surface, (255, 255, 255, 220), button_surface.get_rect(), width=2, border_radius=00)
    screen.blit(button_surface, button_rect.topleft)
    button_text = button_font.render("START", True, (255, 255, 255))
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    # slightly transparent if shit is pressed
    if shift_pressed:
        nozzle_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(nozzle_surface, (0, 0, 0, 100), (5, 5), 5)
        screen.blit(nozzle_surface, (int(current_x) - 5, int(current_y) - 5))
    else:
        pygame.draw.circle(screen, (0, 0, 0), (int(current_x), int(current_y)), 5)

    pygame.display.flip()

pygame.quit()
