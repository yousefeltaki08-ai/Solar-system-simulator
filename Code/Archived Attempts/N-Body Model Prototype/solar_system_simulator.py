"""
==============================================================================
SOLAR SYSTEM SIMULATOR - N-BODY GRAVITY SIMULATION
==============================================================================
Author: Yousef El-Taki
Purpose: NEA Computer Science Project - Educational Physics Simulation
Target Audience: GCSE and A-Level Physics Students

This program creates an interactive N-body gravity simulation that allows
students to explore orbital mechanics, gravitational interactions, and
celestial body dynamics in real-time. The simulation addresses the gap in
educational physics tools by providing customisable, interactive experiences
that static textbooks and videos cannot offer.

Key Features:
- Real-time N-body gravitational physics using Newton's Inverse Square Law
- Customisable celestial bodies with adjustable mass, position, and velocity
- Collision detection and handling between bodies
- Save/Load simulation states to/from JSON files
- Interactive camera controls (zoom, pan)
- Simulation speed control
- Visual trails showing orbital paths
- FPS monitoring for performance awareness

Physics Concepts Covered:
- Gravitational force (Newton's Law of Universal Gravitation)
- Orbital mechanics and stability
- Centripetal force balance
- Numerical integration (Euler method)
- Vector mathematics
==============================================================================
"""

# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
# Import pygame library for graphics rendering, event handling, and display
# This provides the GUI framework for the simulation
import pygame

# Import sys for system-specific parameters and functions
# Used for proper program termination
import sys

# Import math for mathematical operations
# Used for square root, trigonometric functions, and power calculations
import math

# Import json for JSON file handling
# Used for saving and loading simulation states (data persistence)
import json

# Import os for operating system interface
# Used for file path operations and directory management
import os

# Import random for random number generation
# Used for generating random colours and initial conditions
import random

# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================
# Gravitational constant (G) in simulation units
# In the real universe, G = 6.674 × 10^-11 N⋅m²/kg²
# For simulation purposes, we use a scaled value that produces stable orbits
# This value is calibrated to work with our distance scale (1 AU = 100 units)
GRAVITATIONAL_CONSTANT = 200

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================
# Time step (dt) for numerical integration
# This represents the small increment of time used in each calculation cycle
# Smaller values increase accuracy but decrease performance
# Larger values decrease accuracy but increase performance
# This is a fundamental concept in numerical integration - the Euler method
# divides continuous time into discrete steps of size dt
TIME_STEP = 0.05

# Maximum number of bodies allowed in the simulation
# This limit exists due to O(N²) computational complexity
# For N bodies, we need N×(N-1)/2 pairwise force calculations
# This scales quadratically: 10 bodies = 45 calculations, 100 bodies = 4950 calculations
# Limited to maintain acceptable performance on school computers
MAXIMUM_NUMBER_OF_BODIES = 50

# Maximum length of orbital trails (number of position points stored)
# Trails help students visualize orbital paths and understand elliptical orbits
# Longer trails show more orbital history but use more memory
MAXIMUM_TRAIL_LENGTH = 500

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================
# Screen dimensions in pixels
# These dimensions are chosen to be compatible with typical school laptop screens
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900

# Default scale factor for converting simulation units to pixels
# Higher values zoom in (bodies appear larger/further apart on screen)
# Lower values zoom out (bodies appear smaller/closer together on screen)
DEFAULT_ZOOM_SCALE = 1.0

# Minimum and maximum zoom levels to prevent extreme views
MINIMUM_ZOOM_SCALE = 0.1
MAXIMUM_ZOOM_SCALE = 10.0

# Frame rate (frames per second) for the simulation
# 60 FPS provides smooth animation while being achievable on most hardware
TARGET_FRAMES_PER_SECOND = 60

# =============================================================================
# COLOUR DEFINITIONS (RGB Values)
# =============================================================================
# Colours are defined as RGB (Red, Green, Blue) tuples
# Each value ranges from 0 (none) to 255 (maximum intensity)
COLOUR_BLACK = (0, 0, 0)           # Background colour for space
COLOUR_WHITE = (255, 255, 255)     # Text and UI elements
COLOUR_YELLOW = (255, 255, 0)      # Sun and highlights
COLOUR_GRAY = (100, 100, 100)      # UI borders and inactive elements
COLOUR_DARK_GRAY = (40, 40, 40)    # UI panel backgrounds
COLOUR_RED = (255, 100, 100)       # Warning indicators
COLOUR_GREEN = (100, 255, 100)     # Positive indicators
COLOUR_BLUE = (100, 150, 255)      # Information displays


# =============================================================================
# CELESTIAL BODY CLASS
# =============================================================================
class CelestialBody:
    """
    Represents a celestial body (planet, moon, star, or any massive object)
    in the N-body simulation.
    
    This class models each body as a point mass - a simplification that
    ignores shape, composition, rotation, and other physical properties,
    focusing only on mass, position, and velocity for gravitational calculations.
    
    Attributes:
        name (str): The display name of the body
        mass (float): The mass of the body (determines gravitational influence)
        position_x (float): X-coordinate position in simulation space
        position_y (float): Y-coordinate position in simulation space
        velocity_x (float): X-component of velocity
        velocity_y (float): Y-component of velocity
        radius (int): Display radius in pixels (visual representation only)
        colour (tuple): RGB colour tuple for rendering
        image (pygame.Surface): Loaded image for the body (optional)
        trail (list): List of previous positions for drawing orbital trails
        acceleration_x (float): X-component of current acceleration
        acceleration_y (float): Y-component of current acceleration
    """
    
    def __init__(self, name, mass, position_x, position_y, velocity_x, velocity_y, 
                 radius, colour=None, image_surface=None):
        """
        Initialize a new CelestialBody with the given properties.
        
        Parameters:
            name (str): Display name for the body (e.g., "Earth", "Mars")
            mass (float): Mass of the body in simulation units
            position_x (float): Initial X position in simulation coordinates
            position_y (float): Initial Y position in simulation coordinates
            velocity_x (float): Initial X velocity in simulation units/time
            velocity_y (float): Initial Y velocity in simulation units/time
            radius (int): Display radius in pixels for rendering
            colour (tuple): RGB colour tuple (optional, random if not provided)
            image_surface (pygame.Surface): Pre-loaded image surface (optional)
        """
        # Store the body's name for display purposes
        self.name = name
        
        # Store the mass - this determines the gravitational force the body exerts
        # According to Newton's Law: F = G * m1 * m2 / r²
        # Larger mass = stronger gravitational pull
        self.mass = mass
        
        # Store position as separate x and y components
        # Position represents the location in 2D simulation space
        # These values will be updated every frame during numerical integration
        self.position_x = position_x
        self.position_y = position_y
        
        # Store velocity as separate x and y components
        # Velocity represents the rate of change of position
        # These values are updated based on acceleration during integration
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        
        # Store the display radius (visual size only, does not affect physics)
        # In reality, planets have different radii, but for point mass physics,
        # the radius is purely for visualisation
        self.radius = radius
        
        # Set colour - use provided colour or generate a random one
        # Colour helps distinguish different bodies visually
        if colour is None:
            self.colour = self.generate_random_colour()
        else:
            self.colour = colour
        
        # Store the image surface if an image is provided
        # This allows using actual planet images from the Images folder
        self.image = image_surface
        
        # Initialize the trail as an empty list
        # The trail stores previous positions to draw the orbital path
        # This helps students visualize elliptical orbits and orbital mechanics
        self.trail = []
        
        # Initialize acceleration components to zero
        # Acceleration is calculated each frame from gravitational forces
        # Using Newton's Second Law: a = F/m
        self.acceleration_x = 0
        self.acceleration_y = 0
    
    @staticmethod
    def generate_random_colour():
        """
        Generate a random RGB colour that is visually distinguishable.
        
        Returns:
            tuple: RGB colour tuple with values between 100-255 for brightness
        
        Note:
            We avoid dark colours (values below 100) to ensure visibility
            against the black space background.
        """
        return (
            random.randint(100, 255),  # Red component
            random.randint(100, 255),  # Green component
            random.randint(100, 255)   # Blue component
        )
    
    def update_trail(self):
        """
        Add the current position to the trail history.
        
        The trail stores a history of positions that the body has passed through,
        allowing us to draw the orbital path. This is essential for visualising
        elliptical orbits and understanding orbital mechanics.
        
        The trail is limited to MAXIMUM_TRAIL_LENGTH points to manage memory usage.
        """
        # Add current position to the trail list
        self.trail.append((self.position_x, self.position_y))
        
        # If trail exceeds maximum length, remove the oldest point
        # This creates a "fade" effect where old trail points disappear
        if len(self.trail) > MAXIMUM_TRAIL_LENGTH:
            self.trail.pop(0)
    
    def clear_trail(self):
        """
        Clear all trail history.
        
        Useful when resetting the simulation or when a collision occurs
        and the trail is no longer relevant.
        """
        self.trail = []
    
    def to_dictionary(self):
        """
        Convert the celestial body's state to a dictionary for JSON serialization.
        
        This method is used for saving simulation states to JSON files,
        allowing students to save and reload their simulations later.
        
        Returns:
            dict: Dictionary containing all essential body properties
        """
        return {
            'name': self.name,
            'mass': self.mass,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'velocity_x': self.velocity_x,
            'velocity_y': self.velocity_y,
            'radius': self.radius,
            'colour': self.colour
        }
    
    @classmethod
    def create_from_dictionary(cls, data, image_surface=None):
        """
        Create a CelestialBody instance from a dictionary (loaded from JSON).
        
        This class method is used when loading saved simulation states.
        
        Parameters:
            data (dict): Dictionary containing body properties
            image_surface (pygame.Surface): Optional pre-loaded image
            
        Returns:
            CelestialBody: New instance with properties from the dictionary
        """
        return cls(
            name=data['name'],
            mass=data['mass'],
            position_x=data['position_x'],
            position_y=data['position_y'],
            velocity_x=data['velocity_x'],
            velocity_y=data['velocity_y'],
            radius=data['radius'],
            colour=tuple(data['colour']) if 'colour' in data else None,
            image_surface=image_surface
        )


# =============================================================================
# SOLAR SYSTEM SIMULATOR CLASS
# =============================================================================
class SolarSystemSimulator:
    """
    Main simulation class that manages the N-body gravity simulation.
    
    This class handles:
    - Physics calculations (force calculations, numerical integration)
    - Collision detection and handling
    - Rendering and visualization
    - User input handling
    - State persistence (save/load)
    
    The simulation uses Euler integration to calculate positions and velocities
    over discrete time steps, applying Newton's Law of Universal Gravitation
    to calculate forces between all pairs of bodies.
    """
    
    def __init__(self):
        """
        Initialize the Solar System Simulator with default settings.
        
        This sets up the display window, loads resources, and initializes
        the simulation state.
        """
        # Initialize Pygame library
        # This must be called before using any pygame functionality
        pygame.init()
        
        # Set up the display window with the specified dimensions
        # The window is resizable and can be maximized
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), 
            pygame.RESIZABLE
        )
        
        # Set the window title
        pygame.display.set_caption("Solar System N-Body Simulator - Educational Physics Tool")
        
        # Create a clock object to control frame rate
        # This ensures the simulation runs at a consistent speed
        self.clock = pygame.time.Clock()
        
        # Initialize font for text rendering
        # We use the default system font for compatibility
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.large_font = pygame.font.Font(None, 36)
        
        # Initialize the list of celestial bodies
        # This list will contain all bodies in the simulation
        self.list_of_celestial_bodies = []
        
        # Initialize camera/view settings
        # The camera offset allows panning around the simulation
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        
        # Zoom scale for magnification
        self.zoom_scale = DEFAULT_ZOOM_SCALE
        
        # Simulation speed multiplier
        # 1.0 = normal speed, 2.0 = double speed, 0.5 = half speed
        self.simulation_speed_multiplier = 1.0
        
        # Flag to control simulation running state
        # When True, the simulation advances; when False, it is paused
        self.is_simulation_running = True
        
        # Flag to show/hide orbital trails
        self.show_trails = True
        
        # Flag to show/hide body labels
        self.show_labels = True
        
        # Flag to show/hide force vectors
        self.show_force_vectors = False
        
        # Flag to show/hide velocity vectors
        self.show_velocity_vectors = False
        
        # FPS tracking variables
        self.current_fps = 0
        self.fps_update_timer = 0
        
        # Dragging state for camera panning
        self.is_mouse_dragging = False
        self.drag_start_position = (0, 0)
        self.drag_start_camera_offset = (0, 0)
        
        # Selected body for user interaction
        self.selected_body = None
        
        # UI panel rectangle for the control panel
        self.control_panel_rect = pygame.Rect(10, 10, 280, 450)
        
        # Load images for planets
        # This dictionary stores loaded pygame surfaces for each planet
        self.planet_images = self.load_planet_images()
        
        # Create default solar system
        self.create_default_solar_system()
        
        # Store the path for saving/loading simulations
        self.save_directory = os.path.dirname(os.path.abspath(__file__))
    
    def load_planet_images(self):
        """
        Load planet images from the 'Images' folder.
        
        This method attempts to load PNG images for each planet from the
        Images folder. Images should be named with capitalised first letter
        (e.g., 'Sun.png', 'Earth.png', 'Mars.png').
        
        Returns:
            dict: Dictionary mapping planet names to pygame.Surface objects
        """
        # Dictionary to store loaded images
        loaded_images = {}
        
        # Construct the path to the Images folder
        # The Images folder exists in the same directory as this Python file
        images_folder_path = os.path.join(os.path.dirname(__file__), 'Images')
        
        # List of common planet/celestial body names to try loading
        # These are the base names without file extension
        body_names = [
            'Sun', 'Mercury', 'Venus', 'Earth', 'Mars', 
            'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Moon',
            'Asteroid', 'Comet', 'Star', 'Planet'
        ]
        
        # Check if the Images folder exists
        if os.path.exists(images_folder_path):
            # Attempt to load each image
            for name in body_names:
                # Construct the full file path using the capitalised name
                # e.g., 'Images/Sun.png', 'Images/Earth.png'
                image_path = os.path.join(images_folder_path, f'{name}.png')
                
                # Check if the file exists
                if os.path.exists(image_path):
                    try:
                        # Load the image using pygame
                        loaded_image = pygame.image.load(image_path)
                        
                        # Enable alpha channel for transparency support
                        # This allows PNG images with transparent backgrounds
                        loaded_image = loaded_image.convert_alpha()
                        
                        # Store the loaded image in the dictionary
                        # Use lowercase key for case-insensitive matching
                        loaded_images[name.lower()] = loaded_image
                        
                    except pygame.error as error:
                        # If loading fails, print a warning and continue
                        print(f"Warning: Could not load image '{image_path}': {error}")
        
        return loaded_images
    
    def get_planet_image(self, name, radius):
        """
        Get a scaled planet image for a given body name and radius.
        
        This method looks up a pre-loaded image from the planet_images dictionary
        and scales it to the specified radius. The image files should be stored
        in the 'Images' folder with capitalised names (e.g., 'Sun.png', 'Earth.png').
        
        Parameters:
            name (str): Name of the planet (e.g., 'Sun', 'Earth', 'Mars')
                        Can be passed as lowercase or with capital - matching is case-insensitive
            radius (int): Desired radius in pixels
            
        Returns:
            pygame.Surface or None: Scaled image surface, or None if not found
        """
        # Convert name to lowercase for case-insensitive matching
        # This allows both 'Sun' and 'sun' to match the stored image
        name_lower = name.lower()
        
        # Check if we have an image for this body
        if name_lower in self.planet_images:
            # Get the original image from the dictionary
            original_image = self.planet_images[name_lower]
            
            # Scale the image to match the desired radius
            # The diameter is 2 * radius for the full width/height
            diameter = radius * 2
            scaled_image = pygame.transform.scale(
                original_image, 
                (diameter, diameter)
            )
            
            return scaled_image
        
        # Return None if no matching image was found
        return None
    
    def calculate_orbital_velocity_for_circular_orbit(self, distance_from_sun, sun_mass):
        """
        Calculate the required orbital velocity for a stable circular orbit.
        
        For a circular orbit, the centripetal force equals the gravitational force:
        mv²/r = GMm/r²
        
        Solving for v:
        v = √(G × M / r)
        
        This is a key concept in A-Level physics - the balance between
        gravitational attraction and centripetal acceleration.
        
        Parameters:
            distance_from_sun (float): Distance from the Sun in simulation units
            sun_mass (float): Mass of the Sun in simulation units
            
        Returns:
            float: Required orbital velocity for a circular orbit
        """
        # Calculate orbital velocity using v = sqrt(G * M / r)
        orbital_velocity = math.sqrt(GRAVITATIONAL_CONSTANT * sun_mass / distance_from_sun)
        return orbital_velocity
    
    def create_default_solar_system(self):
        """
        Create a default solar system with the Sun and major planets.
        
        This method creates a scientifically accurate representation of our solar system
        with correct relative distances (using 1 AU = 100 distance units).
        
        Real distance ratios from NASA data:
        - Mercury: 0.39 AU
        - Venus: 0.72 AU
        - Earth: 1.00 AU
        - Mars: 1.52 AU
        - Jupiter: 5.20 AU
        - Saturn: 9.58 AU
        - Uranus: 19.22 AU
        - Neptune: 30.05 AU
        
        The initial velocities are calculated using the formula for circular orbits:
        v = √(G × M / r)
        
        Planet masses are kept very small compared to the Sun to prevent
        gravitational perturbations between planets, ensuring stable orbits.
        The Sun contains 99.86% of the solar system's mass in reality.
        """
        # Clear any existing bodies
        self.list_of_celestial_bodies = []
        
        # =====================================================================
        # SCALE DEFINITION
        # =====================================================================
        # 1 Astronomical Unit (AU) = 100 distance units in simulation
        # This scale allows inner planets to be visible while maintaining
        # accurate relative distances
        AU_SCALE = 200  # 1 AU = 200 distance units (larger scale prevents Mercury collision)
        
        # =====================================================================
        # CREATE THE SUN
        # =====================================================================
        # The Sun is the central star of our solar system
        # In reality, the Sun contains 99.86% of the solar system's total mass
        # Mass set to 20000 to dominate gravitational field completely
        # This ensures planets orbit the Sun without perturbing each other
        SUN_MASS = 20000
        sun_image = self.get_planet_image('Sun', 15)  # Small visual size to avoid Mercury collision
        sun = CelestialBody(
            name="Sun",
            mass=SUN_MASS,              # Dominant mass for gravity
            position_x=0,               # Centered at origin
            position_y=0,
            velocity_x=0,               # Stationary at centre
            velocity_y=0,
            radius=15,                  # Small visual size to avoid collision with Mercury
            colour=(255, 255, 0),       # Yellow colour
            image_surface=sun_image
        )
        self.list_of_celestial_bodies.append(sun)
        
        # =====================================================================
        # CREATE MERCURY
        # =====================================================================
        # Mercury: Closest planet to the Sun at 0.39 AU
        # Real mass ratio: 0.055 Earth masses (very small)
        # Orbital period: 88 Earth days (fastest orbit)
        mercury_distance = 0.39 * AU_SCALE  # 78 units
        mercury_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            mercury_distance, SUN_MASS
        )
        mercury_image = self.get_planet_image('Mercury', 4)
        mercury = CelestialBody(
            name="Mercury",
            mass=1,                     # Small mass (relative)
            position_x=mercury_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=mercury_orbital_velocity,
            radius=4,                   # Smallest planet
            colour=(169, 169, 169),     # Gray colour
            image_surface=mercury_image
        )
        self.list_of_celestial_bodies.append(mercury)
        
        # =====================================================================
        # CREATE VENUS
        # =====================================================================
        # Venus: Second planet at 0.72 AU
        # Real mass ratio: 0.815 Earth masses
        # Similar size to Earth but much hotter surface
        venus_distance = 0.72 * AU_SCALE  # 144 units
        venus_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            venus_distance, SUN_MASS
        )
        venus_image = self.get_planet_image('Venus', 6)
        venus = CelestialBody(
            name="Venus",
            mass=1,                     # Small mass to prevent perturbations
            position_x=venus_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=venus_orbital_velocity,
            radius=6,                   # Similar size to Earth
            colour=(255, 198, 73),      # Orange-yellow colour
            image_surface=venus_image
        )
        self.list_of_celestial_bodies.append(venus)
        
        # =====================================================================
        # CREATE EARTH
        # =====================================================================
        # Earth: Third planet at 1.00 AU (reference distance)
        # Real mass: 1 Earth mass (reference)
        # Our home planet - students can relate to this
        earth_distance = 1.00 * AU_SCALE  # 200 units
        earth_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            earth_distance, SUN_MASS
        )
        earth_image = self.get_planet_image('Earth', 6)
        earth = CelestialBody(
            name="Earth",
            mass=1,                     # Reference mass
            position_x=earth_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=earth_orbital_velocity,
            radius=6,                  # Visual size
            colour=(100, 149, 237),     # Blue colour (oceans)
            image_surface=earth_image
        )
        self.list_of_celestial_bodies.append(earth)
        
        # =====================================================================
        # CREATE MARS
        # =====================================================================
        # Mars: Fourth planet at 1.52 AU
        # Real mass ratio: 0.107 Earth masses
        # Known as the Red Planet
        mars_distance = 1.52 * AU_SCALE  # 304 units
        mars_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            mars_distance, SUN_MASS
        )
        mars_image = self.get_planet_image('Mars', 5)
        mars = CelestialBody(
            name="Mars",
            mass=1,                     # Small mass
            position_x=mars_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=mars_orbital_velocity,
            radius=5,                   # Smaller than Earth
            colour=(193, 68, 14),       # Red-orange colour
            image_surface=mars_image
        )
        self.list_of_celestial_bodies.append(mars)
        
        # =====================================================================
        # CREATE JUPITER
        # =====================================================================
        # Jupiter: Fifth planet at 5.20 AU (first gas giant)
        # Real mass ratio: 318 Earth masses (largest planet)
        # Has strong gravitational influence in real solar system
        jupiter_distance = 5.20 * AU_SCALE  # 1040 units
        jupiter_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            jupiter_distance, SUN_MASS
        )
        jupiter_image = self.get_planet_image('Jupiter', 12)
        jupiter = CelestialBody(
            name="Jupiter",
            mass=5,                     # Kept small for stability
            position_x=jupiter_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=jupiter_orbital_velocity,
            radius=12,                  # Largest visual size
            colour=(255, 166, 99),      # Orange-brown colour
            image_surface=jupiter_image
        )
        self.list_of_celestial_bodies.append(jupiter)
        
        # =====================================================================
        # CREATE SATURN
        # =====================================================================
        # Saturn: Sixth planet at 9.58 AU
        # Real mass ratio: 95.2 Earth masses
        # Famous for its prominent ring system
        saturn_distance = 9.58 * AU_SCALE  # 1916 units
        saturn_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            saturn_distance, SUN_MASS
        )
        saturn_image = self.get_planet_image('Saturn', 10)
        saturn = CelestialBody(
            name="Saturn",
            mass=5,                     # Kept small for stability
            position_x=saturn_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=saturn_orbital_velocity,
            radius=10,                  # Second largest
            colour=(210, 180, 140),     # Tan colour
            image_surface=saturn_image
        )
        self.list_of_celestial_bodies.append(saturn)
        
        # =====================================================================
        # CREATE URANUS
        # =====================================================================
        # Uranus: Seventh planet at 19.22 AU
        # Real mass ratio: 14.5 Earth masses
        # Ice giant, rotates on its side
        uranus_distance = 19.22 * AU_SCALE  # 3844 units
        uranus_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            uranus_distance, SUN_MASS
        )
        uranus_image = self.get_planet_image('Uranus', 8)
        uranus = CelestialBody(
            name="Uranus",
            mass=3,                     # Small mass
            position_x=uranus_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=uranus_orbital_velocity,
            radius=8,                   # Medium size
            colour=(173, 216, 230),     # Light blue colour
            image_surface=uranus_image
        )
        self.list_of_celestial_bodies.append(uranus)
        
        # =====================================================================
        # CREATE NEPTUNE
        # =====================================================================
        # Neptune: Eighth planet at 30.05 AU (farthest from Sun)
        # Real mass ratio: 17.1 Earth masses
        # Ice giant, has the strongest winds in solar system
        neptune_distance = 30.05 * AU_SCALE  # 6010 units
        neptune_orbital_velocity = self.calculate_orbital_velocity_for_circular_orbit(
            neptune_distance, SUN_MASS
        )
        neptune_image = self.get_planet_image('Neptune', 8)
        neptune = CelestialBody(
            name="Neptune",
            mass=3,                     # Small mass
            position_x=neptune_distance,
            position_y=0,
            velocity_x=0,
            velocity_y=neptune_orbital_velocity,
            radius=8,                   # Similar to Uranus
            colour=(30, 144, 255),      # Deep blue colour
            image_surface=neptune_image
        )
        self.list_of_celestial_bodies.append(neptune)
        
        # Center the camera on the Sun initially
        self.camera_offset_x = SCREEN_WIDTH // 2
        self.camera_offset_y = SCREEN_HEIGHT // 2
    
    def calculate_distance_between_bodies(self, body1, body2):
        """
        Calculate the Euclidean distance between two celestial bodies.
        
        This uses the Pythagorean theorem:
        distance = √((x2-x1)² + (y2-y1)²)
        
        Parameters:
            body1 (CelestialBody): First body
            body2 (CelestialBody): Second body
            
        Returns:
            float: Distance between the two bodies in simulation units
        """
        # Calculate the difference in x-coordinates
        delta_x = body2.position_x - body1.position_x
        
        # Calculate the difference in y-coordinates
        delta_y = body2.position_y - body1.position_y
        
        # Calculate and return the Euclidean distance
        # Using the formula: distance = √(Δx² + Δy²)
        distance = math.sqrt(delta_x**2 + delta_y**2)
        
        return distance
    
    def calculate_gravitational_force(self, body1, body2):
        """
        Calculate the gravitational force between two celestial bodies.
        
        This implements Newton's Law of Universal Gravitation:
        F = G * m1 * m2 / r²
        
        Where:
        - F is the gravitational force
        - G is the gravitational constant
        - m1 and m2 are the masses of the two bodies
        - r is the distance between the centres of the two bodies
        
        Parameters:
            body1 (CelestialBody): First body
            body2 (CelestialBody): Second body
            
        Returns:
            tuple: (force_x, force_y) - Force components acting on body1 from body2
        """
        # Calculate the distance between the two bodies
        distance = self.calculate_distance_between_bodies(body1, body2)
        
        # Prevent division by zero when bodies overlap
        # This can happen during collisions or when bodies are created at the same position
        if distance < 1:
            distance = 1
        
        # Calculate the direction vector from body1 to body2
        delta_x = body2.position_x - body1.position_x
        delta_y = body2.position_y - body1.position_y
        
        # Calculate the magnitude of gravitational force using Newton's Law
        # F = G * m1 * m2 / r²
        force_magnitude = (GRAVITATIONAL_CONSTANT * body1.mass * body2.mass) / (distance ** 2)
        
        # Calculate the unit vector components
        # The unit vector points from body1 to body2
        unit_vector_x = delta_x / distance
        unit_vector_y = delta_y / distance
        
        # Calculate the force components
        # Force on body1 points towards body2 (attractive force)
        force_x = force_magnitude * unit_vector_x
        force_y = force_magnitude * unit_vector_y
        
        return force_x, force_y
    
    def calculate_all_forces(self):
        """
        Calculate all gravitational forces between all pairs of bodies.
        
        This method implements the N-body force calculation using decomposition:
        1. For each unique pair of bodies, calculate the gravitational force
        2. Sum all forces acting on each body to get the net force
        3. Convert net force to acceleration using Newton's Second Law (a = F/m)
        
        The computational complexity is O(N²) because for N bodies,
        we need to calculate N×(N-1)/2 unique pairwise interactions.
        
        This is a critical concept for students to understand why N-body
        simulations become computationally expensive with many bodies.
        """
        # Reset acceleration for all bodies to zero
        # We will accumulate the accelerations from all forces
        for body in self.list_of_celestial_bodies:
            body.acceleration_x = 0
            body.acceleration_y = 0
        
        # Get the total number of bodies
        number_of_bodies = len(self.list_of_celestial_bodies)
        
        # Iterate through all unique pairs of bodies
        # We use nested loops where the inner loop starts at i+1 to avoid:
        # 1. Calculating forces between a body and itself
        # 2. Calculating the same pair twice (symmetry)
        for i in range(number_of_bodies):
            for j in range(i + 1, number_of_bodies):
                # Get the two bodies in this pair
                body_i = self.list_of_celestial_bodies[i]
                body_j = self.list_of_celestial_bodies[j]
                
                # Calculate the gravitational force between this pair
                force_x, force_y = self.calculate_gravitational_force(body_i, body_j)
                
                # Apply Newton's Third Law: For every action, there is an equal and opposite reaction
                # The force on body_i from body_j is equal and opposite to the force on body_j from body_i
                
                # Calculate acceleration for body_i using Newton's Second Law: a = F/m
                # The force on body_i points towards body_j (attractive gravity)
                body_i.acceleration_x += force_x / body_i.mass
                body_i.acceleration_y += force_y / body_i.mass
                
                # Calculate acceleration for body_j using Newton's Second Law: a = F/m
                # The force on body_j points towards body_i (equal magnitude, opposite direction)
                body_j.acceleration_x -= force_x / body_j.mass
                body_j.acceleration_y -= force_y / body_j.mass
    
    def apply_numerical_integration(self, time_step):
        """
        Apply Symplectic Euler (semi-implicit Euler) integration to update positions and velocities.
        
        The Symplectic Euler method is a first-order numerical integration technique
        that conserves energy much better than standard Euler integration:
        1. v(t+dt) = v(t) + a(t) * dt
        2. x(t+dt) = x(t) + v(t+dt) * dt  (uses the UPDATED velocity)
        
        This small change makes orbits stable over long time periods, unlike
        standard Euler which causes orbits to spiral inward.
        
        This is important for students to understand that numerical methods
        have different properties - some conserve energy better than others.
        
        Parameters:
            time_step (float): The time increment (dt) for this integration step
        """
        # Iterate through all bodies and update their velocities and positions
        for body in self.list_of_celestial_bodies:
            # Update velocity using acceleration
            # v_new = v_old + a * dt
            # This comes from the definition of acceleration: a = dv/dt
            body.velocity_x += body.acceleration_x * time_step
            body.velocity_y += body.acceleration_y * time_step
            
            # Update position using the NEW velocity (Symplectic Euler)
            # x_new = x_old + v_new * dt
            # Using the updated velocity instead of old velocity conserves energy
            # and keeps orbits stable over long simulation times
            body.position_x += body.velocity_x * time_step
            body.position_y += body.velocity_y * time_step
            
            # Update the trail with the new position
            body.update_trail()
    
    def check_for_collisions(self):
        """
        Check for collisions between all pairs of bodies.
        
        Collision detection uses a simple distance-based check:
        If the distance between two bodies is less than the sum of their radii,
        they are considered to have collided.
        
        When a collision is detected, the bodies are merged according to
        conservation of momentum.
        """
        # Create a list to track bodies to remove after collisions
        bodies_to_remove = []
        
        # Get the number of bodies
        number_of_bodies = len(self.list_of_celestial_bodies)
        
        # Check all unique pairs for collisions
        for i in range(number_of_bodies):
            # Skip if this body is already marked for removal
            if self.list_of_celestial_bodies[i] in bodies_to_remove:
                continue
                
            for j in range(i + 1, number_of_bodies):
                # Skip if this body is already marked for removal
                if self.list_of_celestial_bodies[j] in bodies_to_remove:
                    continue
                
                body_i = self.list_of_celestial_bodies[i]
                body_j = self.list_of_celestial_bodies[j]
                
                # Calculate distance between bodies
                distance = self.calculate_distance_between_bodies(body_i, body_j)
                
                # Calculate the sum of radii (collision threshold)
                combined_radii = body_i.radius + body_j.radius
                
                # Check if bodies have collided
                if distance < combined_radii:
                    # Merge the two bodies
                    # Conservation of momentum: m1*v1 + m2*v2 = (m1+m2)*v_final
                    merged_body = self.merge_bodies(body_i, body_j)
                    
                    # Mark the original bodies for removal
                    bodies_to_remove.append(body_i)
                    bodies_to_remove.append(body_j)
                    
                    # Add the merged body to the simulation
                    self.list_of_celestial_bodies.append(merged_body)
        
        # Remove collided bodies from the simulation
        for body in bodies_to_remove:
            if body in self.list_of_celestial_bodies:
                self.list_of_celestial_bodies.remove(body)
    
    def merge_bodies(self, body1, body2):
        """
        Merge two colliding bodies into one.
        
        This uses conservation of momentum to determine the new velocity:
        m1*v1 + m2*v2 = (m1+m2)*v_final
        
        Parameters:
            body1 (CelestialBody): First body to merge
            body2 (CelestialBody): Second body to merge
            
        Returns:
            CelestialBody: New merged body
        """
        # Calculate total mass
        total_mass = body1.mass + body2.mass
        
        # Calculate new position (centre of mass)
        # The centre of mass is the weighted average of positions
        new_position_x = (body1.mass * body1.position_x + body2.mass * body2.position_x) / total_mass
        new_position_y = (body1.mass * body1.position_y + body2.mass * body2.position_y) / total_mass
        
        # Calculate new velocity using conservation of momentum
        # p = m*v, total momentum is conserved
        new_velocity_x = (body1.mass * body1.velocity_x + body2.mass * body2.velocity_y) / total_mass
        new_velocity_y = (body1.mass * body1.velocity_y + body2.mass * body2.velocity_y) / total_mass
        
        # Calculate new radius (preserve volume approximately)
        # Volume of sphere: V = (4/3)πr³
        # Combined volume: V_total = V1 + V2
        # New radius: r_new = (r1³ + r2³)^(1/3)
        new_radius = int((body1.radius**3 + body2.radius**3) ** (1/3))
        
        # Create a name for the merged body
        new_name = f"{body1.name}-{body2.name} (Merged)"
        
        # Blend colours
        new_colour = (
            (body1.colour[0] + body2.colour[0]) // 2,
            (body1.colour[1] + body2.colour[1]) // 2,
            (body1.colour[2] + body2.colour[2]) // 2
        )
        
        # Create and return the merged body
        return CelestialBody(
            name=new_name,
            mass=total_mass,
            position_x=new_position_x,
            position_y=new_position_y,
            velocity_x=new_velocity_x,
            velocity_y=new_velocity_y,
            radius=new_radius,
            colour=new_colour
        )
    
    def convert_simulation_to_screen_coordinates(self, simulation_x, simulation_y):
        """
        Convert simulation coordinates to screen pixel coordinates.
        
        This transformation accounts for:
        1. Camera offset (panning)
        2. Zoom scale (magnification)
        
        Parameters:
            simulation_x (float): X position in simulation space
            simulation_y (float): Y position in simulation space
            
        Returns:
            tuple: (screen_x, screen_y) - Pixel coordinates on screen
        """
        # Apply zoom scale and camera offset transformation
        screen_x = simulation_x * self.zoom_scale + self.camera_offset_x
        screen_y = simulation_y * self.zoom_scale + self.camera_offset_y
        
        return int(screen_x), int(screen_y)
    
    def convert_screen_to_simulation_coordinates(self, screen_x, screen_y):
        """
        Convert screen pixel coordinates to simulation coordinates.
        
        This is the inverse transformation of convert_simulation_to_screen_coordinates,
        used when the user clicks to add a new body.
        
        Parameters:
            screen_x (int): X position in screen pixels
            screen_y (int): Y position in screen pixels
            
        Returns:
            tuple: (simulation_x, simulation_y) - Position in simulation space
        """
        simulation_x = (screen_x - self.camera_offset_x) / self.zoom_scale
        simulation_y = (screen_y - self.camera_offset_y) / self.zoom_scale
        
        return simulation_x, simulation_y
    
    def draw_orbital_trail(self, body):
        """
        Draw the orbital trail for a celestial body.
        
        The trail shows the path the body has taken, helping students
        visualize orbital shapes (elliptical, circular, parabolic, hyperbolic).
        
        Parameters:
            body (CelestialBody): The body whose trail to draw
        """
        # Only draw if there are enough points and trails are enabled
        if not self.show_trails or len(body.trail) < 2:
            return
        
        # Convert trail points to screen coordinates
        trail_points = []
        for position in body.trail:
            screen_x, screen_y = self.convert_simulation_to_screen_coordinates(
                position[0], position[1]
            )
            trail_points.append((screen_x, screen_y))
        
        # Draw the trail as a series of connected line segments
        # The trail fades from dim to bright (older to newer positions)
        number_of_points = len(trail_points)
        
        for i in range(1, number_of_points):
            # Calculate alpha (brightness) based on position in trail
            # Older points are dimmer, newer points are brighter
            alpha_ratio = i / number_of_points
            
            # Create a faded colour
            faded_colour = (
                int(body.colour[0] * alpha_ratio),
                int(body.colour[1] * alpha_ratio),
                int(body.colour[2] * alpha_ratio)
            )
            
            # Draw line segment
            pygame.draw.line(
                self.screen, 
                faded_colour, 
                trail_points[i-1], 
                trail_points[i], 
                1
            )
    
    def draw_celestial_body(self, body):
        """
        Draw a celestial body on the screen.
        
        This method handles drawing the body itself, including:
        - Image (if available) or coloured circle
        - Name label (if enabled)
        - Velocity vector (if enabled)
        
        Parameters:
            body (CelestialBody): The body to draw
        """
        # Convert body position to screen coordinates
        screen_x, screen_y = self.convert_simulation_to_screen_coordinates(
            body.position_x, body.position_y
        )
        
        # Calculate scaled radius based on zoom
        scaled_radius = int(body.radius * self.zoom_scale)
        scaled_radius = max(2, scaled_radius)  # Minimum size of 2 pixels
        
        # Check if body is within screen bounds
        if -scaled_radius < screen_x < SCREEN_WIDTH + scaled_radius and \
           -scaled_radius < screen_y < SCREEN_HEIGHT + scaled_radius:
            
            # Try to draw using image if available
            if body.image is not None:
                # Scale image to current zoom level
                scaled_image = pygame.transform.scale(
                    body.image, 
                    (scaled_radius * 2, scaled_radius * 2)
                )
                # Draw image centered on body position
                self.screen.blit(
                    scaled_image, 
                    (screen_x - scaled_radius, screen_y - scaled_radius)
                )
            else:
                # Draw a filled circle for the body
                pygame.draw.circle(
                    self.screen, 
                    body.colour, 
                    (screen_x, screen_y), 
                    scaled_radius
                )
                # Draw a darker outline
                pygame.draw.circle(
                    self.screen, 
                    (50, 50, 50), 
                    (screen_x, screen_y), 
                    scaled_radius, 
                    1
                )
            
            # Draw name label if enabled
            if self.show_labels:
                label_surface = self.small_font.render(body.name, True, COLOUR_WHITE)
                label_x = screen_x - label_surface.get_width() // 2
                label_y = screen_y + scaled_radius + 5
                self.screen.blit(label_surface, (label_x, label_y))
            
            # Draw velocity vector if enabled
            if self.show_velocity_vectors:
                # Scale velocity for visibility
                vector_scale = 5 * self.zoom_scale
                velocity_end_x = screen_x + body.velocity_x * vector_scale
                velocity_end_y = screen_y + body.velocity_y * vector_scale
                
                pygame.draw.line(
                    self.screen,
                    COLOUR_GREEN,
                    (screen_x, screen_y),
                    (velocity_end_x, velocity_end_y),
                    2
                )
    
    def draw_all_bodies(self):
        """
        Draw all celestial bodies and their trails.
        """
        # Draw trails first (so they appear behind bodies)
        for body in self.list_of_celestial_bodies:
            self.draw_orbital_trail(body)
        
        # Draw bodies on top of trails
        for body in self.list_of_celestial_bodies:
            self.draw_celestial_body(body)
    
    def draw_control_panel(self):
        """
        Draw the control panel with simulation information and controls.
        
        The control panel displays:
        - Simulation status (running/paused)
        - Number of bodies
        - Current simulation speed
        - Zoom level
        - FPS
        - Control instructions
        """
        # Draw semi-transparent background for control panel
        panel_surface = pygame.Surface(
            (self.control_panel_rect.width, self.control_panel_rect.height)
        )
        panel_surface.set_alpha(200)
        panel_surface.fill(COLOUR_DARK_GRAY)
        self.screen.blit(panel_surface, self.control_panel_rect.topleft)
        
        # Draw panel border
        pygame.draw.rect(self.screen, COLOUR_GRAY, self.control_panel_rect, 2)
        
        # Starting position for text
        text_y = self.control_panel_rect.top + 10
        text_x = self.control_panel_rect.left + 10
        
        # Draw title
        title = self.font.render("Solar System Simulator", True, COLOUR_YELLOW)
        self.screen.blit(title, (text_x, text_y))
        text_y += 30
        
        # Draw separator line
        pygame.draw.line(
            self.screen, 
            COLOUR_GRAY, 
            (text_x, text_y), 
            (self.control_panel_rect.right - 10, text_y)
        )
        text_y += 10
        
        # Display simulation status
        status_text = "RUNNING" if self.is_simulation_running else "PAUSED"
        status_colour = COLOUR_GREEN if self.is_simulation_running else COLOUR_RED
        status = self.small_font.render(f"Status: {status_text}", True, status_colour)
        self.screen.blit(status, (text_x, text_y))
        text_y += 20
        
        # Display number of bodies
        bodies_text = self.small_font.render(
            f"Bodies: {len(self.list_of_celestial_bodies)}/{MAXIMUM_NUMBER_OF_BODIES}", 
            True, 
            COLOUR_WHITE
        )
        self.screen.blit(bodies_text, (text_x, text_y))
        text_y += 20
        
        # Display simulation speed
        speed_text = self.small_font.render(
            f"Speed: {self.simulation_speed_multiplier:.1f}x", 
            True, 
            COLOUR_WHITE
        )
        self.screen.blit(speed_text, (text_x, text_y))
        text_y += 20
        
        # Display zoom level
        zoom_text = self.small_font.render(
            f"Zoom: {self.zoom_scale:.2f}x", 
            True, 
            COLOUR_WHITE
        )
        self.screen.blit(zoom_text, (text_x, text_y))
        text_y += 20
        
        # Display FPS
        fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, COLOUR_WHITE)
        self.screen.blit(fps_text, (text_x, text_y))
        text_y += 30
        
        # Draw separator line
        pygame.draw.line(
            self.screen, 
            COLOUR_GRAY, 
            (text_x, text_y), 
            (self.control_panel_rect.right - 10, text_y)
        )
        text_y += 10
        
        # Draw controls header
        controls_header = self.small_font.render("Controls:", True, COLOUR_YELLOW)
        self.screen.blit(controls_header, (text_x, text_y))
        text_y += 20
        
        # Draw control instructions
        controls = [
            "SPACE - Pause/Resume",
            "+/- - Change Speed",
            "Scroll - Zoom In/Out",
            "Right-Click Drag - Pan",
            "R - Reset Simulation",
            "T - Toggle Trails",
            "L - Toggle Labels",
            "V - Toggle Velocity Vectors",
            "S - Save Simulation",
            "O - Load Simulation",
            "A - Add Random Body",
            "C - Clear All Bodies",
            "ESC - Quit"
        ]
        
        for control in controls:
            control_text = self.small_font.render(control, True, COLOUR_WHITE)
            self.screen.blit(control_text, (text_x, text_y))
            text_y += 18
    
    def draw_body_info_panel(self):
        """
        Draw information panel showing details of selected body.
        
        This panel shows mass, position, velocity, and other properties
        of a body that the user clicks on.
        """
        if self.selected_body is None:
            return
        
        # Create panel rectangle
        info_panel_rect = pygame.Rect(SCREEN_WIDTH - 260, 10, 250, 200)
        
        # Draw semi-transparent background
        panel_surface = pygame.Surface(
            (info_panel_rect.width, info_panel_rect.height)
        )
        panel_surface.set_alpha(200)
        panel_surface.fill(COLOUR_DARK_GRAY)
        self.screen.blit(panel_surface, info_panel_rect.topleft)
        
        # Draw border
        pygame.draw.rect(self.screen, COLOUR_GRAY, info_panel_rect, 2)
        
        # Draw body name as title
        text_y = info_panel_rect.top + 10
        text_x = info_panel_rect.left + 10
        
        name_text = self.font.render(self.selected_body.name, True, COLOUR_YELLOW)
        self.screen.blit(name_text, (text_x, text_y))
        text_y += 30
        
        # Draw body properties
        properties = [
            f"Mass: {self.selected_body.mass:.1f}",
            f"Position: ({self.selected_body.position_x:.1f}, {self.selected_body.position_y:.1f})",
            f"Velocity: ({self.selected_body.velocity_x:.2f}, {self.selected_body.velocity_y:.2f})",
            f"Speed: {math.sqrt(self.selected_body.velocity_x**2 + self.selected_body.velocity_y**2):.2f}",
            f"Radius: {self.selected_body.radius} px",
            f"Acceleration: ({self.selected_body.acceleration_x:.4f}, {self.selected_body.acceleration_y:.4f})"
        ]
        
        for prop in properties:
            prop_text = self.small_font.render(prop, True, COLOUR_WHITE)
            self.screen.blit(prop_text, (text_x, text_y))
            text_y += 20
    
    def handle_keyboard_input(self, event):
        """
        Handle keyboard input events.
        
        This method processes key presses for simulation control.
        
        Parameters:
            event (pygame.event): The keyboard event to process
        """
        # Space bar - Toggle pause/resume
        if event.key == pygame.K_SPACE:
            self.is_simulation_running = not self.is_simulation_running
        
        # Plus key - Increase simulation speed
        elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
            self.simulation_speed_multiplier = min(
                self.simulation_speed_multiplier + 0.5, 
                10.0
            )
        
        # Minus key - Decrease simulation speed
        elif event.key == pygame.K_MINUS:
            self.simulation_speed_multiplier = max(
                self.simulation_speed_multiplier - 0.5, 
                0.1
            )
        
        # R key - Reset simulation to default solar system
        elif event.key == pygame.K_r:
            self.create_default_solar_system()
        
        # T key - Toggle orbital trails
        elif event.key == pygame.K_t:
            self.show_trails = not self.show_trails
            # Clear trails when toggling off
            if not self.show_trails:
                for body in self.list_of_celestial_bodies:
                    body.clear_trail()
        
        # L key - Toggle body labels
        elif event.key == pygame.K_l:
            self.show_labels = not self.show_labels
        
        # V key - Toggle velocity vectors
        elif event.key == pygame.K_v:
            self.show_velocity_vectors = not self.show_velocity_vectors
        
        # S key - Save simulation to JSON file
        elif event.key == pygame.K_s:
            self.save_simulation_to_json()
        
        # O key - Load simulation from JSON file
        elif event.key == pygame.K_o:
            self.load_simulation_from_json()
        
        # A key - Add a random body
        elif event.key == pygame.K_a:
            self.add_random_body()
        
        # C key - Clear all bodies
        elif event.key == pygame.K_c:
            self.list_of_celestial_bodies = []
        
        # ESC key - Quit the application
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
    
    def handle_mouse_input(self, event):
        """
        Handle mouse input events.
        
        This method processes mouse clicks and movements for:
        - Panning the camera (right-click drag)
        - Selecting bodies (left-click)
        - Zooming (scroll wheel)
        
        Parameters:
            event (pygame.event): The mouse event to process
        """
        # Mouse button down - Start drag or select body
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Right mouse button - Start panning
            if event.button == 3:
                self.is_mouse_dragging = True
                self.drag_start_position = event.pos
                self.drag_start_camera_offset = (
                    self.camera_offset_x, 
                    self.camera_offset_y
                )
            
            # Left mouse button - Select body
            elif event.button == 1:
                self.select_body_at_position(event.pos)
            
            # Scroll wheel up - Zoom in
            elif event.button == 4:
                self.zoom_scale = min(
                    self.zoom_scale * 1.1, 
                    MAXIMUM_ZOOM_SCALE
                )
            
            # Scroll wheel down - Zoom out
            elif event.button == 5:
                self.zoom_scale = max(
                    self.zoom_scale / 1.1, 
                    MINIMUM_ZOOM_SCALE
                )
        
        # Mouse button up - End drag
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.is_mouse_dragging = False
        
        # Mouse motion - Perform drag
        elif event.type == pygame.MOUSEMOTION:
            if self.is_mouse_dragging:
                # Calculate how far the mouse has moved
                delta_x = event.pos[0] - self.drag_start_position[0]
                delta_y = event.pos[1] - self.drag_start_position[1]
                
                # Update camera offset
                self.camera_offset_x = self.drag_start_camera_offset[0] + delta_x
                self.camera_offset_y = self.drag_start_camera_offset[1] + delta_y
    
    def select_body_at_position(self, mouse_position):
        """
        Select a celestial body at the given mouse position.
        
        This allows users to click on bodies to view their properties.
        
        Parameters:
            mouse_position (tuple): (x, y) screen coordinates of mouse click
        """
        # Convert mouse position to simulation coordinates
        sim_x, sim_y = self.convert_screen_to_simulation_coordinates(
            mouse_position[0], 
            mouse_position[1]
        )
        
        # Check each body to see if the click is within its radius
        for body in self.list_of_celestial_bodies:
            # Calculate distance from click to body centre
            distance = math.sqrt(
                (body.position_x - sim_x)**2 + 
                (body.position_y - sim_y)**2
            )
            
            # Check if click is within body's radius (scaled for zoom)
            if distance < body.radius / self.zoom_scale + 10:  # +10 for easier selection
                self.selected_body = body
                return
        
        # If no body was clicked, deselect
        self.selected_body = None
    
    def add_random_body(self):
        """
        Add a random celestial body to the simulation.
        
        This is useful for students to experiment with different configurations
        and observe how new bodies affect orbital stability.
        """
        # Check if we've reached the maximum number of bodies
        if len(self.list_of_celestial_bodies) >= MAXIMUM_NUMBER_OF_BODIES:
            return
        
        # Generate random position (within view)
        random_x = random.uniform(-300, 300)
        random_y = random.uniform(-300, 300)
        
        # Generate random velocity
        random_vx = random.uniform(-3, 3)
        random_vy = random.uniform(-3, 3)
        
        # Generate random mass and radius
        random_mass = random.uniform(10, 200)
        random_radius = int(random.uniform(5, 20))
        
        # Create the body
        new_body = CelestialBody(
            name=f"Body_{len(self.list_of_celestial_bodies) + 1}",
            mass=random_mass,
            position_x=random_x,
            position_y=random_y,
            velocity_x=random_vx,
            velocity_y=random_vy,
            radius=random_radius
        )
        
        # Add to simulation
        self.list_of_celestial_bodies.append(new_body)
    
    def save_simulation_to_json(self):
        """
        Save the current simulation state to a JSON file.
        
        This implements state persistence, allowing students to save their
        custom simulations and load them later for further experimentation.
        
        The JSON format is human-readable, making it educational for students
        to understand how data can be structured and stored.
        """
        # Create a dictionary to store the simulation state
        simulation_data = {
            'simulation_settings': {
                'camera_offset_x': self.camera_offset_x,
                'camera_offset_y': self.camera_offset_y,
                'zoom_scale': self.zoom_scale,
                'simulation_speed_multiplier': self.simulation_speed_multiplier,
                'show_trails': self.show_trails,
                'show_labels': self.show_labels,
                'show_velocity_vectors': self.show_velocity_vectors
            },
            'celestial_bodies': []
        }
        
        # Add each body's data to the dictionary
        for body in self.list_of_celestial_bodies:
            simulation_data['celestial_bodies'].append(body.to_dictionary())
        
        # Define the save file path
        save_file_path = os.path.join(self.save_directory, 'saved_simulation.json')
        
        # Write the data to a JSON file
        try:
            with open(save_file_path, 'w') as json_file:
                json.dump(simulation_data, json_file, indent=4)
            print(f"Simulation saved to: {save_file_path}")
        except Exception as error:
            print(f"Error saving simulation: {error}")
    
    def load_simulation_from_json(self):
        """
        Load a simulation state from a JSON file.
        
        This method reads a previously saved simulation and restores all
        bodies and settings to their saved state.
        """
        # Define the load file path
        load_file_path = os.path.join(self.save_directory, 'saved_simulation.json')
        
        # Check if the save file exists
        if not os.path.exists(load_file_path):
            print(f"No saved simulation found at: {load_file_path}")
            return
        
        # Read and parse the JSON file
        try:
            with open(load_file_path, 'r') as json_file:
                simulation_data = json.load(json_file)
            
            # Restore simulation settings
            settings = simulation_data['simulation_settings']
            self.camera_offset_x = settings['camera_offset_x']
            self.camera_offset_y = settings['camera_offset_y']
            self.zoom_scale = settings['zoom_scale']
            self.simulation_speed_multiplier = settings['simulation_speed_multiplier']
            self.show_trails = settings['show_trails']
            self.show_labels = settings['show_labels']
            self.show_velocity_vectors = settings['show_velocity_vectors']
            
            # Clear existing bodies
            self.list_of_celestial_bodies = []
            
            # Load each body from the saved data
            for body_data in simulation_data['celestial_bodies']:
                # Try to get an image for this body
                body_image = self.get_planet_image(body_data['name'], body_data['radius'])
                
                # Create the body from saved data
                body = CelestialBody.create_from_dictionary(body_data, body_image)
                
                # Add to simulation
                self.list_of_celestial_bodies.append(body)
            
            print(f"Simulation loaded from: {load_file_path}")
            
        except Exception as error:
            print(f"Error loading simulation: {error}")
    
    def update_fps_counter(self, delta_time):
        """
        Update the FPS counter display.
        
        Parameters:
            delta_time (float): Time since last frame in milliseconds
        """
        self.fps_update_timer += delta_time
        
        # Update FPS display every 500ms
        if self.fps_update_timer >= 500:
            if delta_time > 0:
                self.current_fps = int(1000 / delta_time)
            self.fps_update_timer = 0
    
    def run_main_loop(self):
        """
        Run the main simulation loop.
        
        This is the core of the simulation, containing:
        1. Event handling (user input)
        2. Physics updates (force calculations, integration)
        3. Collision detection
        4. Rendering (drawing everything to screen)
        5. Frame rate control
        
        The loop continues until the user closes the window or presses ESC.
        """
        # Main loop flag
        is_running = True
        
        # Main simulation loop
        while is_running:
            # =================================================================
            # EVENT HANDLING
            # =================================================================
            # Process all events in the pygame event queue
            for event in pygame.event.get():
                # Window close button clicked
                if event.type == pygame.QUIT:
                    is_running = False
                
                # Keyboard key pressed
                elif event.type == pygame.KEYDOWN:
                    self.handle_keyboard_input(event)
                
                # Mouse events
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                    self.handle_mouse_input(event)
                
                # Window resize
                elif event.type == pygame.VIDEORESIZE:
                    global SCREEN_WIDTH, SCREEN_HEIGHT
                    SCREEN_WIDTH = event.w
                    SCREEN_HEIGHT = event.h
                    self.screen = pygame.display.set_mode(
                        (SCREEN_WIDTH, SCREEN_HEIGHT), 
                        pygame.RESIZABLE
                    )
            
            # =================================================================
            # PHYSICS UPDATE
            # =================================================================
            # Only update physics if simulation is running (not paused)
            if self.is_simulation_running:
                # Calculate effective time step with speed multiplier
                effective_time_step = TIME_STEP * self.simulation_speed_multiplier
                
                # Step 1: Calculate all gravitational forces
                # This updates acceleration for each body
                self.calculate_all_forces()
                
                # Step 2: Apply numerical integration (Euler method)
                # This updates velocities and positions
                self.apply_numerical_integration(effective_time_step)
                
                # Step 3: Check for and handle collisions
                self.check_for_collisions()
            
            # =================================================================
            # RENDERING
            # =================================================================
            # Clear the screen with black (empty space)
            self.screen.fill(COLOUR_BLACK)
            
            # Draw all celestial bodies and their trails
            self.draw_all_bodies()
            
            # Draw the control panel (left side)
            self.draw_control_panel()
            
            # Draw body info panel if a body is selected
            self.draw_body_info_panel()
            
            # Update the display
            pygame.display.flip()
            
            # =================================================================
            # FRAME RATE CONTROL
            # =================================================================
            # Control frame rate and get delta time
            delta_time = self.clock.tick(TARGET_FRAMES_PER_SECOND)
            
            # Update FPS counter
            self.update_fps_counter(delta_time)
        
        # Clean up and exit
        pygame.quit()
        sys.exit()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """
    Main entry point for the Solar System Simulator.
    
    This function creates and runs the simulation when the script is executed.
    """
    print("=" * 60)
    print("SOLAR SYSTEM N-BODY SIMULATOR")
    print("Educational Physics Tool for GCSE and A-Level Students")
    print("=" * 60)
    print("\nInitializing simulation...")
    
    # Create the simulator instance
    simulator = SolarSystemSimulator()
    
    print("Simulation initialized successfully!")
    print("\nStarting main loop...")
    print("Press ESC or close the window to exit.\n")
    
    # Run the main simulation loop
    simulator.run_main_loop()


# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
# This block ensures the main() function is only called when the script
# is run directly (not when imported as a module)
if __name__ == "__main__":
    main()
