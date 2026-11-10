import pygame
import math

# Constants

#(screen size and framerate)
WIDTH, HEIGHT = 800, 600
FPS = 60

# Set the colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Planet Class
class Planet:
    def __init__(self, name, color, distance, size, speed):
        self.name = name
        self.color = color
        self.distance = distance
        self.size = size
        self.angle = 0
        self.speed = speed

    def update_position(self):
        self.angle += self.speed
        self.x = WIDTH // 2 + int(self.distance * math.cos(math.radians(self.angle)))
        self.y = HEIGHT // 2 + int(self.distance * math.sin(math.radians(self.angle)))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Solar System Simulator")
clock = pygame.time.Clock()

# Create Sun as a rectangle to help draw it and Planets
sun = pygame.Rect(WIDTH // 2 - 30, HEIGHT // 2 - 30, 60, 60)
planets = [
    Planet("Mercury", RED, 70, 5, 4),
    Planet("Venus", GREEN, 100, 7, 2.5),
    Planet("Earth", BLUE, 130, 8, 2),
    Planet("Mars", RED, 160, 6, 1.5),
]

# Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw Sun
    pygame.draw.circle(screen, YELLOW, (WIDTH // 2, HEIGHT // 2), 30)

    # Update and Draw Planets
    for planet in planets:
        planet.update_position()
        planet.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
