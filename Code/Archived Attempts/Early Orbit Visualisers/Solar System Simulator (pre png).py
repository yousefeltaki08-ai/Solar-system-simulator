# ========================================================================================
#
#                                  Solar System Simulator - Pygame-based simulation of a scaled-down solar system
#
# ======================= INDEX / VARIABLE & FUNCTION EXPLANATIONS =======================
#
# --- General Setup ---
# pygame.init()                : Initializes all imported pygame modules.
# pygame.display.Info()        : Retrieves current screen resolution for fullscreen display.
#
# WIDTH, HEIGHT                : Screen width and height in pixels (based on current resolution).
# screen                       : The main pygame window surface.
# pygame.display.set_caption() : Sets the window title to "Solar System Simulator".
# clock                        : Pygame clock used to control frame rate.
# FPS                          : Frames per second (controls simulation speed).
#
# --- Colors ---
# BLACK, WHITE, YELLOW, etc.   : RGB tuples used to draw elements in the simulation.
#
# --- Camera ---
# camera_x, camera_y           : Track the camera's offset position, used for navigating space.
# camera_speed                 : Speed at which the camera moves using arrow keys or WASD.
#
# --- Scale ---
# scale                        : Global scale factor applied to all planet distances and sizes to make them fit on screen.
#
# --- Class: Planet ---
# Planet                       : Represents each planet with properties and orbital movement.
#   - name                     : Name of the planet (used for identification).
#   - color                    : RGB color of the planet for rendering.
#   - distance                 : Distance from the sun, scaled.
#   - size                     : Radius of the planet, scaled for screen.
#   - angle                    : Current angle of orbit (degrees).
#   - speed                    : Orbital speed — smaller = slower revolution.
#   - update_position()        : Calculates the planet’s current (x, y) position in orbit.
#   - draw()                   : Draws the planet to the screen, adjusting for camera offset.
#
# --- List: scaled_planets ---
# scaled_planets               : List containing instances of all the planets in the solar system,
#                                with scaled distances and sizes.
#
# --- Main Loop ---
# running                      : Boolean flag that keeps the main game loop active.
# pygame.event.get()           : Processes system/user events like quitting.
# pygame.key.get_pressed()     : Checks which keys are being held down for continuous input.
# planet.update_position()     : Updates each planet’s position for smooth orbital movement.
# planet.draw()                : Renders each planet to the screen at its current position.
#
# ========================================================================================


import pygame
import math
import sys
import ctypes # Allows me to put the window ontop of everything else

# Initialize pygame
pygame.init()

# Screen settings
Screen_info = pygame.display.Info()
WIDTH, HEIGHT = Screen_info.current_w, Screen_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Solar System Simulator")
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Camera offset
camera_x, camera_y = 0, 0
camera_speed = 10

# Camera zoom
camera_zoom = 1.0
camera_zoom_max = 10
camera_zoom_min = 0.1
# Planet class
class Planet:
    def __init__(self, name, color, distance, size, speed):
        self.name = name
        self.color = color
        self.distance = distance
        self.size = max(2, int(size))
        self.angle = 0
        self.speed = speed * 0.5  # Slower speed
        self.update_position()

    def update_position(self):
        self.angle += self.speed
        pixel_distance = self.distance * camera_zoom
        theta = math.radians(self.angle)
        self.x = WIDTH // 2 + int(pixel_distance * math.cos(theta))
        self.y = HEIGHT // 2 + int(pixel_distance * math.sin(theta))

    def draw(self, screen, cam_x, cam_y, zoom):
        pygame.draw.circle(screen, self.color, (self.x + cam_x, self.y + cam_y), (self.size * zoom))

# Global scale factor because i cant be bothered to keep changing everything
scale = 0.05

# Scaled planets
scaled_planets = [
    Planet("Mercury", RED, 253.4 * scale, 38.3 * scale, 10.0),
    Planet("Venus", GREEN, 474.2 * scale, 95.0 * scale, 7.3),
    Planet("Earth", BLUE, 654.2 * scale, 100.0 * scale, 6.2),
    Planet("Mars", RED, 999.1 * scale, 53.2 * scale, 5.0),
    Planet("Jupiter", ORANGE, 2060.2 * scale, 878.6 * scale, 1.3),
    Planet("Saturn", YELLOW, 3783.2 * scale, 735.7 * scale, 1.0),
    Planet("Uranus", CYAN, 7595.6 * scale, 312.7 * scale, 0.7),
    Planet("Neptune", BLUE, 11900.0 * scale, 303.6 * scale, 0.5),
]

# Main loop
running = True
while running:
    screen.fill(BLACK)

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # Checks if the last event was the x (the close window button) beinng pressed
            running = False
        elif event.type == pygame.KEYDOWN: # Checks if the last event was a key being pressed
            if event.key == pygame.K_ESCAPE: # Checks if the key pressed was the escape button
                running = False # Stops the code from running
        # Handle key presses for camera zoom
        elif event.type == pygame.MOUSEWHEEL: # Checks if the last event was the mouswheel
            if event.y > 0: 
                camera_zoom *= 1.1
            else:
                camera_zoom /= 1.1
        camera_zoom = max(camera_zoom_min, min(camera_zoom_max, camera_zoom)) # Avoid 0 or huge numbers
            
    # Handle key presses for camera movement
    keys = pygame.key.get_pressed() # Returns a list of boolean values for the state of every key on the keyboard and stores it in keys. I use this rather than for event in ... KEYDOWN because i want to handle the continuous movement of the camer arather than a single key press
    pan_speed = camera_speed * camera_zoom # Make panning look better (When zoomed in panning is slower and "more precise", vice versa)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]: # Checks for the left arrow or the A key (WASD)
        camera_x += pan_speed # Adds the pan speed to the x value of the camera (moves right)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: # Checks for the right arrow or the D key (WASD)
        camera_x -= pan_speed # Subtracts the pan speed from the x value of the camera (moves left)
    if keys[pygame.K_UP] or keys[pygame.K_w]: # Checks for the up arrow or the W key (WASD)
        camera_y += pan_speed # Adds the pan speed to the y value of the camera (moves up)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]: # checks for the down arrow or the S key (WASD)
        camera_y -= pan_speed # Subtracts the pan speed from the y value of the camera (moves down)

    # Draw Sun
    pygame.draw.circle(screen, YELLOW, (WIDTH // 2 + camera_x, HEIGHT // 2 + camera_y), (15 * camera_zoom))

    # Update and draw planets
    for planet in scaled_planets:
        planet.update_position()
        planet.draw(screen, camera_x, camera_y, camera_zoom)

    pygame.display.flip() # Pushes all drawn objects from the back buffer onto the screen for the user to avoid them seeing unfinished frames
    clock.tick(FPS) # Limits the FPS/ the game loop speed to the set FPS

pygame.quit()
sys.exit()
