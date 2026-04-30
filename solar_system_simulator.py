# Imports
import pygame # For window and graphics
import sys # For exiting the program properly
import random # For generating random numbers
import math # For any more complex mathematical functions

# Defining constants
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
COLOUR_BLACK = (0,0,0) # RGB tuple for black
COLOUR_WHITE = (255,255,255) # RGB tuple for white
MAXIMUM_TRAIL_LENGTH = 500 # Max number of trail positions
GRAVITATIONAL_CONSTANT = 6.67e-11 # Constant G for equations
MAXIMUM_NUMBER_OF_BODIES = 50 # Limit to 50 bodies simultaneously
TIME_STEP = 0.05 # Relatively small time step for accuracy

pygame.init() # Initialising pygame for future use

# Window set up
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE) # Set window size and the mode
pygame.display.set_caption("Solar System Simulator") # Add a name to the window created

# Setting up the clock before the main loop so that i can have consistent animation
clock = pygame.time.Clock()


#=======FUNCTIONS=======#

# Define function to calculate distance between bodies(r for equations)
def calculate_distance(body1, body2):
    delta_x = body2.position_x - body1.position_x # Change in x
    delta_y = body2.position_y - body1.position_y # Change in y
    distance = math.sqrt(delta_x**2 + delta_y**2) # Pythagoras rearanged

# Define a function to calculate gravitational force between two bodies
def calculate_gravitational_force(body1, body2):
    distance = calculate_distance(body1, body2) # Get distance from other function

    # Check if distance is 0
    if distance == 0:
        distance = 0.001 # Avoid a crash from division by 0

    force_magnitude = (GRAVITATIONAL_CONSTANT * body1.mass * body2.mass)/ (distance**2) # F = (m1m2G)/(r^2)

    delta_x = body2.position_x - body1.position_x # Change in x
    delta_y = body2.position_y - body1.position_y # Change in y

    scale_x = delta_x/distance
    scale_y = delta_y/distance
    
    force_vector_x = force_magnitude * scale_x
    force_vector_y = force_magnitude * scale_y

    return force_vector_x, force_vector_y

# Procedure to calculate all forces on bodies
def calculate_all_forces():
    # Reset accelerations
    for body in list_of_celestial_bodies:
        body.acceleration_x = 0
        body.acceleration_y = 0

    number_of_bodies = len(list_of_celestial_bodies)

    for i in range(number_of_bodies):
        for j in range(i + 1, number_of_bodies):
            body1 = list_of_celestial_bodies[i]
            body2 = list_of_celestial_bodies[j]

            # Calculate force on body1
            force_x, force_y = calculate_gravitational_force(body1, body2)

            # Calculate accelerations for body1 with Newtons 2nd law
            body1.acceleration_x += force_x / body1.mass
            body1.acceleration_y += force_y / body1.mass

            # Calculate accelerations for body2 with Newtons 3rd law
            body2.acceleration_x -= force_x / body2.mass
            body2.acceleration_y -= force_y / body2.mass

def calculate_orbital_velocity(distance, central_mass):
    orbital_velocity = math.sqrt((GRAVITATIONAL_CONSTANT * central_mass)/ distance) # Use derived equation for orbital velocity
    return orbital_velocity

# Function to calculate apply leapfrog method
def apply_symplectic_euler(dt): # Take time step
    for body in list_of_celestial_bodies: # Go through all bodies
        # Update velocity - v(n+1) = v(n) + (a(n) * dt)
        body.velocity_x += body.acceleration_x * dt
        body.velocity_y += body.acceleration_y * dt

        # Update position - p(n+1) = p(n) + (v(n+1) * dt)
        # Used NEW velocity (v(n+1)) as it is symplectic Euler
        body.position_x += body.velocity_x * dt
        body.position_y += body.velocity_y * dt

        body.update_trail() # Use new position to update trail


# Creating the main class
class CelestialBody:
    
    # Set up the constructor method
    def __init__(self, name, mass, position_x, position_y, velocity_x, velocity_y, radius, colour = None):
        self.name = name
        self.mass = mass
        self.position_x = position_x
        self.position_y = position_y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.radius = radius

        if colour is None: # Check for predefined colour
            self.colour = (random.randint(100,255), random.randint(100,255), random.randint(100,255))
        else:
            self.colour = colour

        # Define initial list for trail positions
        self.trail = []

        # Define initial x and y accelerations
        self.acceleration_x = 0
        self.acceleration_y = 0

    # Defining a static method for random colouring
    @staticmethod
    def generate_random_colour():
        return(random.randint(100,255),random.randint(100,255),random.randint(100,255))
    

    #=======TRAILS=======#
    
    # Defining method for updating trail
    def update_trail(self):
        trail = self.trail
        trail.append((self.position_x,self.position_y))
        if len(trail) > MAXIMUM_TRAIL_LENGTH: # Check length against constant
            trail.pop(0) # Remove oldest position
        self.trail = trail

    # Defining a method to clear the trail history
    def clear_trail(self):
        self.trail = []

    # Defining a method to put values into a dictionary format
    def to_dictionary(self):
        dictionary = {
            "name": self.name,
            "mass": self.mass,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "radius": self.radius,
            "colour": self.colour
        }
        return dictionary

    

# Create a camera offset system
camera_offset_x = SCREEN_WIDTH // 2 # Offset to the centre horizontally
camera_offset_y = SCREEN_HEIGHT // 2 # Offset to the centre vertically


# Create default font
font = pygame.font.Font(None, 24)


# Define main list for storing all celestial bodies
list_of_celestial_bodies = []


# Create a test body to verify drawing works
test_body = CelestialBody(
    name="Test",
    mass=100,
    position_x=0,  # At simulation centre (where Sun will be)
    position_y=0,
    velocity_x=0,
    velocity_y=0,
    radius=20,
    colour=(255, 100, 100)
)
list_of_celestial_bodies.append(test_body)


# Creating the flags
simulation_is_running = True
running = True
while running: # Using the flag as the condition for the program to run
    for event in pygame.event.get(): # Making a for loop to go through all events and check for specific ones
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_ESCAPE:
                running = False

    screen.fill(COLOUR_BLACK) # Fill the screen with black (the background)

    # Check if user has paused or not
    if simulation_is_running:
        calculate_all_forces() # Calculate gravitational forces on all bodies
        apply_symplectic_euler(TIME_STEP) # Calculate new v's and p's
    
    # DRAWING
    # Go through all celestial bodies
    for body in list_of_celestial_bodies:
        # convert simulation co-ordinates to screen co-ordinates
        screen_x = int(body.position_x + camera_offset_x)# Introduce x offset
        screen_y = int(body.position_y + camera_offset_y)# Introduce y offset

        # Draw the body
        pygame.draw.circle(screen, body.colour, (screen_x, screen_y), body.radius)

        # 1.Render text
        label = font.render(body.name, True, COLOUR_WHITE)
        # 2.Calculate position
        label_x = screen_x - label.get_width()
        label_y = screen_y + body.radius + 5
        # 3.Blit
        screen.blit(label, (label_x, label_y))

    pygame.display.flip() # Update the display
    clock.tick(60) # Limit FPS
    
                
# End the program
pygame.quit()
sys.exit() # Properly terminates the entire program


