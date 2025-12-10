import pygame

black = (0, 0, 0)
gray = (100, 100, 100)

def DrawText(text, Textcolor, Rectcolor, x, y, fsize):
    font = pygame.font.Font('Roboto.ttf', fsize)
    text = font.render(text, True, Textcolor, Rectcolor)
    textRect = text.get_rect()
    textRect.center = (x, y)
    screen.blit(text, textRect)

def rectangle(display, color, x, y, w, h):
    pygame.draw.rect(display, color, (x, y, w, h))
nozzleX = 400
nozzleY = 300
speed = 1
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('2D printer simulation')
token = input("First X>  ")
toX = int(token)
token = input("First Y>  ")
toY = int(token)
clock = pygame.time.Clock()
dt = clock.tick(60)



#Initial frame so pygame dont shit itself gawha!
rectangle(screen, gray, nozzleX, nozzleY, 80, 60)
pygame.display.update()
while True:
    # Process player inputs.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        screen.fill('black')
        if nozzleX != toX:
            if nozzleX > toX:
                nozzleX = nozzleX - round((speed*dt)/17)
            if nozzleX < toX:
                nozzleX = nozzleX + round((speed*dt)/17)
        if nozzleY != toY:
            if nozzleY > toY:
                nozzleY = nozzleY - round((speed*dt)/17)
            if nozzleY < toY:
                nozzleY = nozzleY + round((speed*dt)/17)

        rectangle(screen, gray, nozzleX, nozzleY, 80, 60)
        pygame.display.update()
    
