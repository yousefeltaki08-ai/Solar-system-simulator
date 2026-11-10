"""
================================================================================
                ORBITAL MECHANICS N-BODY SIMULATION
                    OCR NEA Project - A-Level Computer Science
================================================================================

PROJECT OVERVIEW:
This simulation addresses the difficulty GCSE and A-Level students face when
learning orbital mechanics, gravitational interactions, and N-body dynamics.

KEY FEATURES:
    - Real-time N-body gravitational simulation (all bodies affect each other)
    - Customizable celestial body creation and modification
    - Collision detection and handling
    - Save/Load simulation states to JSON files
    - Educational overlays showing forces, orbital data, and escape conditions
    - Interactive camera controls for full exploration

EDUCATIONAL VALUE:
    - Visualizes concepts: circular motion, centripetal force, gravitational fields
    - Demonstrates orbital stability and escape velocity
    - Shows how small changes lead to significant outcomes
    - Allows experimentation with body properties

CONTROLS:
    - WASD/Arrow Keys: Move camera
    - Mouse Wheel: Zoom in/out
    - Left Click: Select body
    - Right Click: Deselect
    - C: Create new body
    - E: Edit selected body
    - DELETE: Delete selected body
    - SPACE: Pause/Resume
    - +/-: Adjust simulation speed
    - F: Toggle force vectors
    - I: Toggle info panel
    - S: Save simulation
    - L: Load simulation
    - R: Reset camera
    - ESC: Quit

AUTHOR: OCR NEA Candidate
================================================================================
"""

# ==============================================================================
# SECTION 1: IMPORTS AND DEPENDENCIES
# ==============================================================================

import pygame                    # Graphics and user input handling
import math                      # Mathematical functions for physics calculations
import json                      # JSON file handling for save/load functionality
import os                        # File system operations
from dataclasses import dataclass, field    # Structured data classes
from typing import List, Dict, Tuple, Optional, Any  # Type hints
from datetime import datetime    # Timestamps for save files

# ==============================================================================
# SECTION 2: SIMULATION CONSTANTS AND CONFIGURATION
# ==============================================================================

# ------------------------------------------------------------------------------
# 2.1: Display Configuration
# ------------------------------------------------------------------------------
SCREEN_WIDTH = 1400              # Window width in pixels
SCREEN_HEIGHT = 900              # Window height in pixels
FPS = 60                         # Target frames per second
BACKGROUND_COLOR = (5, 5, 15)    # Deep space background color

# ------------------------------------------------------------------------------
# 2.2: Physics Constants
# ------------------------------------------------------------------------------
# Gravitational constant in SI units: m³/(kg·s²)
GRAVITATIONAL_CONSTANT_SI = 6.67430e-11

# Astronomical Unit in meters (average Earth-Sun distance)
AU_IN_METERS = 1.496e11

# Number of meters per pixel at zoom level 1 (for scaling)
METERS_PER_PIXEL_BASE = 1.0e9    # 1 billion meters per pixel

# Base time step in seconds (how much simulation time passes per frame at 1x speed)
BASE_TIME_STEP_SECONDS = 3600 * 24  # One day per frame at 1x speed

# Minimum distance for collision detection (in simulation units/meters)
COLLISION_DISTANCE_FACTOR = 1.5   # Bodies collide when distance < sum of radii * factor

# ------------------------------------------------------------------------------
# 2.3: Visual Configuration
# ------------------------------------------------------------------------------
MAX_TRAIL_LENGTH = 300           # Maximum points in orbital trail
TRAIL_LINE_WIDTH = 1             # Width of trail lines
INFO_PANEL_WIDTH = 300           # Width of side information panel
MIN_DISPLAY_RADIUS = 3           # Minimum pixel size for rendering bodies
MAX_DISPLAY_RADIUS = 50          # Maximum pixel size for rendering bodies

# Color definitions (RGB tuples)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (255, 220, 50)
COLOR_ORANGE = (255, 150, 50)
COLOR_RED = (220, 60, 60)
COLOR_BLUE = (70, 130, 220)
COLOR_GREEN = (70, 200, 70)
COLOR_PURPLE = (150, 70, 200)
COLOR_CYAN = (70, 200, 200)
COLOR_GRAY = (150, 150, 150)
COLOR_DARK_GRAY = (80, 80, 80)

# Default colors for newly created bodies
DEFAULT_BODY_COLORS = [
    (255, 100, 100),   # Light red
    (100, 255, 100),   # Light green
    (100, 100, 255),   # Light blue
    (255, 255, 100),   # Yellow
    (255, 100, 255),   # Magenta
    (100, 255, 255),   # Cyan
    (255, 180, 100),   # Orange
    (180, 100, 255),   # Purple
]

# ------------------------------------------------------------------------------
# 2.4: Educational Constants
# ------------------------------------------------------------------------------
# Mass of Earth in kg (for reference in body creation)
EARTH_MASS_KG = 5.972e24

# Mass of Sun in kg (for reference)
SUN_MASS_KG = 1.989e30

# Radius of Earth in meters (for reference)
EARTH_RADIUS_METERS = 6.371e6

# Radius of Sun in meters (for reference)
SUN_RADIUS_METERS = 6.96e8

# Standard gravitational parameter for the Sun (GM) in m³/s²
SUN_GRAVITATIONAL_PARAMETER = 1.327e20

# ==============================================================================
# SECTION 3: DATA STRUCTURES
# ==============================================================================

@dataclass
class Vector2D:
    """
    Two-dimensional vector for representing positions, velocities, and forces.
    
    This class provides the fundamental mathematical operations needed for
    orbital mechanics calculations including vector addition, subtraction,
    scalar multiplication, and magnitude calculations.
    
    Attributes:
        x: The x-component of the vector
        y: The y-component of the vector
    """
    x: float = 0.0
    y: float = 0.0
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """Vector addition: returns a new vector (x1+x2, y1+y2)"""
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        """Vector subtraction: returns a new vector (x1-x2, y1-y2)"""
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        """Scalar multiplication: returns a new vector (x*s, y*s)"""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        """Scalar division: returns a new vector (x/s, y/s)"""
        if scalar == 0:
            raise ValueError("Cannot divide vector by zero")
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __neg__(self) -> 'Vector2D':
        """Negation: returns a new vector (-x, -y)"""
        return Vector2D(-self.x, -self.y)
    
    def calculate_magnitude(self) -> float:
        """
        Calculate the magnitude (length) of the vector.
        
        Returns:
            The Euclidean length sqrt(x² + y²)
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def calculate_magnitude_squared(self) -> float:
        """
        Calculate the squared magnitude of the vector.
        
        This is more efficient than calculate_magnitude() when only comparing
        distances, as it avoids the square root operation.
        
        Returns:
            The squared length (x² + y²)
        """
        return self.x ** 2 + self.y ** 2
    
    def normalize(self) -> 'Vector2D':
        """
        Return a unit vector pointing in the same direction.
        
        A unit vector has magnitude 1.0 and is useful for calculating
        directions without affecting magnitude in subsequent calculations.
        
        Returns:
            A new vector with magnitude 1.0, or zero vector if magnitude is 0
        """
        magnitude = self.calculate_magnitude()
        if magnitude == 0:
            return Vector2D(0, 0)
        return self / magnitude
    
    def calculate_distance_to(self, other: 'Vector2D') -> float:
        """
        Calculate the Euclidean distance between two vectors.
        
        Args:
            other: The other vector to measure distance to
            
        Returns:
            The distance between this vector and the other
        """
        return (self - other).calculate_magnitude()
    
    def copy(self) -> 'Vector2D':
        """Create a copy of this vector"""
        return Vector2D(self.x, self.y)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple format (x, y)"""
        return (self.x, self.y)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization"""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Vector2D':
        """Create a Vector2D from a dictionary"""
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass
class CelestialBody:
    """
    Represents a celestial body in the simulation with physical properties.
    
    Each body has mass, position, velocity, and visual properties. Bodies
    interact gravitationally with all other bodies in the simulation (N-body).
    
    Attributes:
        name: Unique identifier for the body
        mass: Mass in kilograms
        radius: Physical radius in meters (for collision detection)
        position: Current position in meters (from origin)
        velocity: Current velocity in meters per second
        color: RGB tuple for rendering
        display_radius: Pixel radius for rendering (scaled for visibility)
        is_fixed: If True, body does not move (like a central star)
        orbital_trail: List of previous positions for trail rendering
        current_acceleration: Acceleration calculated each physics step
        gravitational_force: Total gravitational force acting on body
    """
    name: str
    mass: float
    radius: float
    position: Vector2D
    velocity: Vector2D
    color: Tuple[int, int, int] = (255, 255, 255)
    display_radius: int = 10
    is_fixed: bool = False
    orbital_trail: List[Tuple[float, float]] = field(default_factory=list)
    current_acceleration: Vector2D = field(default_factory=Vector2D)
    gravitational_force: Vector2D = field(default_factory=Vector2D)
    
    def calculate_kinetic_energy(self) -> float:
        """
        Calculate the kinetic energy of the body.
        
        KE = 0.5 * m * v²
        
        Returns:
            Kinetic energy in Joules
        """
        speed_squared = self.velocity.calculate_magnitude_squared()
        return 0.5 * self.mass * speed_squared
    
    def calculate_momentum(self) -> Vector2D:
        """
        Calculate the linear momentum of the body.
        
        p = m * v
        
        Returns:
            Momentum as a Vector2D (kg⋅m/s)
        """
        return self.velocity * self.mass
    
    def calculate_orbital_speed(self) -> float:
        """
        Get the current orbital speed (magnitude of velocity).
        
        Returns:
            Speed in m/s
        """
        return self.velocity.calculate_magnitude()
    
    def add_trail_point(self):
        """Add current position to the orbital trail"""
        self.orbital_trail.append(self.position.to_tuple())
        
        # Remove old points to maintain maximum length
        while len(self.orbital_trail) > MAX_TRAIL_LENGTH:
            self.orbital_trail.pop(0)
    
    def clear_trail(self):
        """Clear the orbital trail"""
        self.orbital_trail.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert body to dictionary for JSON serialization.
        
        Returns:
            Dictionary containing all body properties
        """
        return {
            "name": self.name,
            "mass": self.mass,
            "radius": self.radius,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "color": list(self.color),
            "display_radius": self.display_radius,
            "is_fixed": self.is_fixed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CelestialBody':
        """
        Create a CelestialBody from a dictionary.
        
        Args:
            data: Dictionary containing body properties
            
        Returns:
            A new CelestialBody instance
        """
        return cls(
            name=data["name"],
            mass=data["mass"],
            radius=data["radius"],
            position=Vector2D.from_dict(data["position"]),
            velocity=Vector2D.from_dict(data["velocity"]),
            color=tuple(data["color"]),
            display_radius=data.get("display_radius", 10),
            is_fixed=data.get("is_fixed", False)
        )


@dataclass
class SimulationState:
    """
    Represents the complete state of the simulation for save/load.
    
    Contains all information needed to exactly restore a simulation
    including time, camera position, and all celestial bodies.
    """
    simulation_time_seconds: float
    speed_multiplier: float
    camera_position_x: float
    camera_position_y: float
    camera_zoom: float
    bodies: List[CelestialBody]
    save_timestamp: str = ""
    save_name: str = "Untitled Simulation"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "simulation_time_seconds": self.simulation_time_seconds,
            "speed_multiplier": self.speed_multiplier,
            "camera_position_x": self.camera_position_x,
            "camera_position_y": self.camera_position_y,
            "camera_zoom": self.camera_zoom,
            "bodies": [body.to_dict() for body in self.bodies],
            "save_timestamp": self.save_timestamp,
            "save_name": self.save_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationState':
        """Create SimulationState from dictionary"""
        return cls(
            simulation_time_seconds=data["simulation_time_seconds"],
            speed_multiplier=data["speed_multiplier"],
            camera_position_x=data["camera_position_x"],
            camera_position_y=data["camera_position_y"],
            camera_zoom=data["camera_zoom"],
            bodies=[CelestialBody.from_dict(b) for b in data["bodies"]],
            save_timestamp=data.get("save_timestamp", ""),
            save_name=data.get("save_name", "Loaded Simulation")
        )


# ==============================================================================
# SECTION 4: PHYSICS ENGINE
# ==============================================================================

class GravitationalPhysicsEngine:
    """
    Handles all gravitational physics calculations for the simulation.
    
    This engine implements N-body gravitational simulation where every body
    exerts gravitational force on every other body. It uses Newton's law of
    universal gravitation and numerical integration for position updates.
    
    Educational Focus:
        - Newton's Law of Gravitation: F = G * m1 * m2 / r²
        - Superposition principle for forces
        - Numerical integration (Euler method)
        - Conservation of momentum and energy
    """
    
    def __init__(self, gravitational_constant: float = GRAVITATIONAL_CONSTANT_SI):
        """
        Initialize the physics engine.
        
        Args:
            gravitational_constant: The gravitational constant to use (default SI)
        """
        self.gravitational_constant = gravitational_constant
    
    def calculate_gravitational_force(self, body1: CelestialBody, 
                                       body2: CelestialBody) -> Vector2D:
        """
        Calculate the gravitational force exerted by body2 on body1.
        
        Using Newton's Law of Universal Gravitation:
            F = G * m1 * m2 / r²
        
        The force direction points from body1 toward body2 (attractive).
        
        Args:
            body1: The body experiencing the force
            body2: The body exerting the force
            
        Returns:
            Force vector pointing from body1 toward body2
        """
        # Calculate displacement vector from body1 to body2
        displacement = body2.position - body1.position
        
        # Calculate distance between bodies
        distance = displacement.calculate_magnitude()
        
        # Prevent division by zero and numerical instability at very close distances
        if distance < 1e6:  # Minimum distance of 1000 km
            return Vector2D(0, 0)
        
        # Calculate force magnitude using Newton's law
        # F = G * m1 * m2 / r²
        force_magnitude = (self.gravitational_constant * 
                          body1.mass * body2.mass / 
                          (distance ** 2))
        
        # Calculate unit vector pointing from body1 to body2
        direction = displacement.normalize()
        
        # Return force vector (magnitude * direction)
        return direction * force_magnitude
    
    def calculate_all_forces(self, bodies: List[CelestialBody]) -> Dict[str, Vector2D]:
        """
        Calculate the total gravitational force on each body from all others.
        
        This implements the superposition principle: the total force on a body
        is the vector sum of all individual forces from other bodies.
        
        Args:
            bodies: List of all celestial bodies in simulation
            
        Returns:
            Dictionary mapping body names to their total force vectors
        """
        forces = {}
        
        for body in bodies:
            total_force = Vector2D(0, 0)
            
            if not body.is_fixed:
                for other_body in bodies:
                    if body != other_body:
                        force = self.calculate_gravitational_force(body, other_body)
                        total_force = total_force + force
            
            forces[body.name] = total_force
            body.gravitational_force = total_force
        
        return forces
    
    def calculate_acceleration(self, body: CelestialBody, 
                               total_force: Vector2D) -> Vector2D:
        """
        Calculate acceleration from force using Newton's Second Law.
        
        F = ma, therefore a = F/m
        
        Args:
            body: The body to calculate acceleration for
            total_force: The total force acting on the body
            
        Returns:
            Acceleration vector (m/s²)
        """
        if body.mass == 0:
            return Vector2D(0, 0)
        
        return total_force / body.mass
    
    def update_body_physics(self, body: CelestialBody, 
                           acceleration: Vector2D, 
                           time_step: float):
        """
        Update body's velocity and position using Euler integration.
        
        Euler integration is a simple numerical method:
            v(t+dt) = v(t) + a * dt
            x(t+dt) = x(t) + v * dt
        
        For educational purposes, this method is easy to understand but
        less accurate than more advanced methods (Runge-Kutta, Verlet).
        
        Args:
            body: The body to update
            acceleration: Current acceleration
            time_step: Time step in seconds
        """
        if body.is_fixed:
            return
        
        # Store acceleration for display purposes
        body.current_acceleration = acceleration
        
        # Update velocity: v_new = v_old + a * dt
        body.velocity = body.velocity + (acceleration * time_step)
        
        # Update position: x_new = x_old + v * dt
        body.position = body.position + (body.velocity * time_step)
    
    def check_collision(self, body1: CelestialBody, 
                        body2: CelestialBody) -> bool:
        """
        Check if two bodies are colliding.
        
        Collision occurs when the distance between centers is less than
        the sum of their radii multiplied by a collision factor.
        
        Args:
            body1: First body
            body2: Second body
            
        Returns:
            True if bodies are colliding
        """
        distance = body1.position.calculate_distance_to(body2.position)
        collision_threshold = (body1.radius + body2.radius) * COLLISION_DISTANCE_FACTOR
        return distance < collision_threshold
    
    def handle_collision(self, body1: CelestialBody, 
                         body2: CelestialBody) -> CelestialBody:
        """
        Handle collision between two bodies using inelastic collision physics.
        
        When two bodies collide, they merge into one larger body conserving:
            - Total momentum: m1*v1 + m2*v2 = (m1+m2)*v_new
            - Total mass: m_new = m1 + m2
            - Volume (for radius): r_new = (r1³ + r2³)^(1/3)
        
        Args:
            body1: First colliding body
            body2: Second colliding body
            
        Returns:
            The merged body resulting from the collision
        """
        # Calculate combined mass
        combined_mass = body1.mass + body2.mass
        
        # Calculate combined momentum to get new velocity
        # p_total = m1*v1 + m2*v2
        combined_momentum = (body1.calculate_momentum() + 
                           body2.calculate_momentum())
        new_velocity = combined_momentum / combined_mass
        
        # Calculate combined radius (assuming spherical bodies)
        # Volume = 4/3 * π * r³, so r_new = (r1³ + r2³)^(1/3)
        combined_radius = (body1.radius ** 3 + body2.radius ** 3) ** (1/3)
        
        # New position is weighted average (center of mass)
        new_position = (body1.position * body1.mass + 
                       body2.position * body2.mass) / combined_mass
        
        # Determine properties of merged body
        # Keep the name of the larger body
        merged_name = body1.name if body1.mass >= body2.mass else body2.name
        merged_name += "_Merged"
        
        # Blend colors based on mass ratio
        mass_ratio1 = body1.mass / combined_mass
        mass_ratio2 = body2.mass / combined_mass
        merged_color = tuple(
            int(body1.color[i] * mass_ratio1 + body2.color[i] * mass_ratio2)
            for i in range(3)
        )
        
        # Calculate display radius (scaled for visibility)
        merged_display_radius = max(
            MIN_DISPLAY_RADIUS,
            min(MAX_DISPLAY_RADIUS, int((body1.display_radius ** 3 + 
                                         body2.display_radius ** 3) ** (1/3)))
        )
        
        # Create merged body
        merged_body = CelestialBody(
            name=merged_name,
            mass=combined_mass,
            radius=combined_radius,
            position=new_position,
            velocity=new_velocity,
            color=merged_color,
            display_radius=merged_display_radius,
            is_fixed=False
        )
        
        return merged_body
    
    def calculate_orbital_parameters(self, body: CelestialBody, 
                                      central_body: CelestialBody) -> Dict[str, float]:
        """
        Calculate orbital parameters for a body orbiting a central body.
        
        This is useful for educational purposes, showing students how
        orbital mechanics relates to observable quantities.
        
        Parameters calculated:
            - Orbital radius (distance from central body)
            - Orbital speed
            - Orbital period (using Kepler's third law)
            - Escape velocity at current distance
            - Specific orbital energy
        
        Args:
            body: The orbiting body
            central_body: The body being orbited (usually the largest)
            
        Returns:
            Dictionary of orbital parameters
        """
        distance = body.position.calculate_distance_to(central_body.position)
        speed = body.velocity.calculate_magnitude()
        
        # Standard gravitational parameter (GM) of central body
        gm = self.gravitational_constant * central_body.mass
        
        # Orbital period using Kepler's third law: T = 2π * sqrt(a³/GM)
        # Assuming circular orbit for simplicity
        if distance > 0:
            orbital_period = 2 * math.pi * math.sqrt(distance ** 3 / gm)
        else:
            orbital_period = 0
        
        # Escape velocity: v_escape = sqrt(2GM/r)
        escape_velocity = math.sqrt(2 * gm / distance) if distance > 0 else 0
        
        # Specific orbital energy: E = v²/2 - GM/r
        specific_energy = (speed ** 2 / 2) - (gm / distance) if distance > 0 else 0
        
        return {
            "orbital_radius_meters": distance,
            "orbital_radius_au": distance / AU_IN_METERS,
            "orbital_speed_ms": speed,
            "orbital_period_seconds": orbital_period,
            "orbital_period_days": orbital_period / (24 * 3600),
            "escape_velocity_ms": escape_velocity,
            "specific_energy": specific_energy,
            "is_bound": specific_energy < 0  # Bound orbit if energy is negative
        }
    
    def calculate_total_energy(self, bodies: List[CelestialBody]) -> float:
        """
        Calculate total mechanical energy of the system.
        
        Total energy = Kinetic Energy + Potential Energy
        E_total = Σ(0.5 * m * v²) + Σ(-G * m1 * m2 / r)
        
        This is useful for demonstrating energy conservation (or lack thereof
        with numerical integration).
        
        Args:
            bodies: All bodies in the simulation
            
        Returns:
            Total energy in Joules
        """
        kinetic_energy = sum(body.calculate_kinetic_energy() for body in bodies)
        
        potential_energy = 0
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                distance = body1.position.calculate_distance_to(body2.position)
                if distance > 0:
                    potential_energy -= (self.gravitational_constant * 
                                        body1.mass * body2.mass / distance)
        
        return kinetic_energy + potential_energy
    
    def calculate_total_momentum(self, bodies: List[CelestialBody]) -> Vector2D:
        """
        Calculate total linear momentum of the system.
        
        p_total = Σ(m * v)
        
        This should be conserved in an isolated system.
        
        Args:
            bodies: All bodies in the simulation
            
        Returns:
            Total momentum as a Vector2D
        """
        total_momentum = Vector2D(0, 0)
        for body in bodies:
            total_momentum = total_momentum + body.calculate_momentum()
        return total_momentum


# ==============================================================================
# SECTION 5: CAMERA AND VIEW MANAGEMENT
# ==============================================================================

class CameraController:
    """
    Manages the viewport for exploring the simulation space.
    
    Provides zoom and pan functionality allowing users to explore
    different scales of the simulation from full solar system view
    to detailed close-ups of individual bodies.
    """
    
    def __init__(self):
        """Initialize camera with default position and zoom"""
        self.position = Vector2D(0, 0)      # Position offset in meters
        self.zoom_level = 1.0               # Current zoom (1.0 = default scale)
        self.target_zoom = 1.0              # Target zoom for smooth transitions
        self.pan_speed_pixels = 15          # Camera pan speed in pixels per frame
        self.zoom_speed_factor = 0.15       # How fast zoom changes
        self.min_zoom = 0.05                # Maximum zoom out
        self.max_zoom = 20.0                # Maximum zoom in
    
    def handle_keyboard_input(self, keys_pressed: pygame.key.ScancodeWrapper,
                              zoom_adjusted_speed: bool = True):
        """
        Process keyboard input for camera panning.
        
        Args:
            keys_pressed: Current state of all keyboard keys
            zoom_adjusted_speed: If True, pan speed scales with zoom level
        """
        # Calculate effective pan speed (slower when zoomed in, faster when out)
        effective_speed = self.pan_speed_pixels
        if zoom_adjusted_speed:
            effective_speed = self.pan_speed_pixels / self.zoom_level
        
        # Convert pixel speed to simulation distance
        meters_per_pixel = METERS_PER_PIXEL_BASE / self.zoom_level
        pan_distance = effective_speed * meters_per_pixel
        
        # Handle WASD and arrow keys for panning
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            self.position.y += pan_distance
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            self.position.y -= pan_distance
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            self.position.x += pan_distance
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            self.position.x -= pan_distance
    
    def adjust_zoom(self, delta: float):
        """
        Adjust zoom level (positive = zoom in, negative = zoom out).
        
        Args:
            delta: Change in zoom level
        """
        self.target_zoom += delta * self.zoom_speed_factor
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom))
    
    def set_zoom(self, zoom: float):
        """Directly set zoom level"""
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, zoom))
    
    def update(self):
        """Update camera state (smooth zoom transitions)"""
        # Smoothly interpolate current zoom toward target zoom
        zoom_difference = self.target_zoom - self.zoom_level
        self.zoom_level += zoom_difference * 0.12
    
    def reset_to_default(self):
        """Reset camera to default position and zoom"""
        self.position = Vector2D(0, 0)
        self.target_zoom = 1.0
    
    def focus_on_position(self, target_position: Vector2D):
        """Move camera to center on a specific position"""
        self.position = target_position.copy()
    
    def world_to_screen(self, world_position: Vector2D) -> Tuple[int, int]:
        """
        Convert world coordinates (meters) to screen coordinates (pixels).
        
        Args:
            world_position: Position in simulation space
            
        Returns:
            Tuple (x, y) of screen pixel coordinates
        """
        # Calculate pixels per meter at current zoom
        pixels_per_meter = self.zoom_level / METERS_PER_PIXEL_BASE
        
        # Convert world position to screen position
        # Note: Screen y-axis is inverted (positive y is down)
        screen_x = int((world_position.x - self.position.x) * pixels_per_meter + 
                       SCREEN_WIDTH / 2)
        screen_y = int((self.position.y - world_position.y) * pixels_per_meter + 
                       SCREEN_HEIGHT / 2)
        
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_position: Tuple[int, int]) -> Vector2D:
        """
        Convert screen coordinates (pixels) to world coordinates (meters).
        
        Args:
            screen_position: (x, y) pixel coordinates on screen
            
        Returns:
            Position in simulation space (meters)
        """
        pixels_per_meter = self.zoom_level / METERS_PER_PIXEL_BASE
        
        world_x = (screen_position[0] - SCREEN_WIDTH / 2) / pixels_per_meter + self.position.x
        world_y = self.position.y - (screen_position[1] - SCREEN_HEIGHT / 2) / pixels_per_meter
        
        return Vector2D(world_x, world_y)


# ==============================================================================
# SECTION 6: USER INTERFACE COMPONENTS
# ==============================================================================

class UserInterfaceManager:
    """
    Manages all user interface elements including panels, buttons, and inputs.
    
    Provides the interactive elements that allow students to:
        - View simulation information
        - Create and edit celestial bodies
        - Access educational data about orbits
        - Save and load simulations
    """
    
    def __init__(self):
        """Initialize UI manager with fonts and panel states"""
        # Initialize fonts for different text sizes
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 22)
        self.font_large = pygame.font.Font(None, 28)
        self.font_title = pygame.font.Font(None, 36)
        
        # UI state flags
        self.show_info_panel = True
        self.show_force_vectors = False
        self.show_velocity_vectors = False
        self.show_orbital_data = True
        
        # Panel positions
        self.info_panel_rect = pygame.Rect(SCREEN_WIDTH - INFO_PANEL_WIDTH - 10, 10, 
                                           INFO_PANEL_WIDTH, SCREEN_HEIGHT - 20)
        
        # Colors for UI elements
        self.panel_bg_color = (20, 20, 35)
        self.panel_border_color = (60, 60, 90)
        self.text_color = (220, 220, 220)
        self.highlight_color = (100, 150, 255)
        self.warning_color = (255, 150, 50)
        self.error_color = (255, 80, 80)
        
        # Input handling state
        self.active_input_field = None
        self.input_text = ""
    
    def render_info_panel(self, screen: pygame.Surface, 
                          simulation_time: float,
                          speed_multiplier: float,
                          camera_zoom: float,
                          bodies: List[CelestialBody],
                          selected_body: Optional[CelestialBody],
                          physics_engine: GravitationalPhysicsEngine,
                          is_paused: bool,
                          total_energy: float):
        """
        Render the main information panel on the right side of screen.
        
        This panel displays:
            - Simulation time and speed
            - List of all bodies
            - Selected body details
            - Orbital parameters (if applicable)
            - Energy conservation data
        
        Args:
            screen: Pygame surface to render on
            simulation_time: Current simulation time in seconds
            speed_multiplier: Current time speed multiplier
            camera_zoom: Current camera zoom level
            bodies: List of all celestial bodies
            selected_body: Currently selected body (or None)
            physics_engine: Physics engine for calculations
            is_paused: Whether simulation is paused
            total_energy: Total system energy
        """
        if not self.show_info_panel:
            return
        
        # Draw panel background
        panel_surface = pygame.Surface((self.info_panel_rect.width, 
                                       self.info_panel_rect.height), 
                                      pygame.SRCALPHA)
        panel_surface.fill((*self.panel_bg_color, 230))
        screen.blit(panel_surface, self.info_panel_rect.topleft)
        
        # Draw panel border
        pygame.draw.rect(screen, self.panel_border_color, self.info_panel_rect, 2)
        
        # Calculate text positioning
        current_y = self.info_panel_rect.top + 15
        left_margin = self.info_panel_rect.left + 15
        text_width = self.info_panel_rect.width - 30
        
        # ------------------------------------------------------------------
        # Simulation Status Section
        # ------------------------------------------------------------------
        self._render_section_header(screen, "SIMULATION STATUS", left_margin, current_y)
        current_y += 30
        
        # Pause indicator
        if is_paused:
            pause_text = self.font_large.render("PAUSED", True, self.warning_color)
            screen.blit(pause_text, (left_margin, current_y))
            current_y += 25
        
        # Time display
        time_days = simulation_time / (24 * 3600)
        time_years = time_days / 365.25
        time_text = f"Time: {time_years:.2f} years ({time_days:.0f} days)"
        self._render_text_line(screen, time_text, left_margin, current_y)
        current_y += 22
        
        # Speed and zoom
        speed_text = f"Speed: {speed_multiplier:.2f}x"
        zoom_text = f"Zoom: {camera_zoom:.2f}x"
        self._render_text_line(screen, speed_text, left_margin, current_y)
        current_y += 20
        self._render_text_line(screen, zoom_text, left_margin, current_y)
        current_y += 25
        
        # Energy display (for conservation verification)
        energy_text = f"Total Energy: {total_energy:.2e} J"
        self._render_text_line(screen, energy_text, left_margin, current_y, 
                              self.font_small)
        current_y += 35
        
        # ------------------------------------------------------------------
        # Bodies List Section
        # ------------------------------------------------------------------
        self._render_section_header(screen, f"CELESTIAL BODIES ({len(bodies)})", 
                                   left_margin, current_y)
        current_y += 30
        
        for body in bodies[:8]:  # Limit to first 8 for space
            # Highlight selected body
            text_color = self.highlight_color if body == selected_body else self.text_color
            
            # Body name and mass
            name_text = f"• {body.name}"
            mass_text = f"  Mass: {body.mass:.2e} kg"
            
            self._render_text_line(screen, name_text, left_margin, current_y, 
                                  self.font_medium, text_color)
            current_y += 18
            self._render_text_line(screen, mass_text, left_margin + 10, current_y, 
                                  self.font_small, COLOR_GRAY)
            current_y += 20
        
        if len(bodies) > 8:
            more_text = f"  ... and {len(bodies) - 8} more"
            self._render_text_line(screen, more_text, left_margin, current_y, 
                                  self.font_small, COLOR_GRAY)
            current_y += 25
        
        current_y += 10
        
        # ------------------------------------------------------------------
        # Selected Body Details Section
        # ------------------------------------------------------------------
        if selected_body:
            self._render_section_header(screen, "SELECTED BODY", left_margin, current_y)
            current_y += 30
            
            current_y = self._render_body_details(screen, selected_body, 
                                                  left_margin, current_y, 
                                                  physics_engine, bodies)
        
        # ------------------------------------------------------------------
        # Controls Reminder Section
        # ------------------------------------------------------------------
        current_y = self.info_panel_rect.bottom - 150
        self._render_section_header(screen, "CONTROLS", left_margin, current_y)
        current_y += 25
        
        controls = [
            "WASD/Arrows: Move camera",
            "Mouse Wheel: Zoom",
            "Click: Select body",
            "C: Create new body",
            "E: Edit selected",
            "DEL: Delete selected",
            "F: Toggle force vectors",
            "I: Toggle this panel",
            "S/L: Save/Load",
            "SPACE: Pause"
        ]
        
        for control in controls:
            self._render_text_line(screen, control, left_margin, current_y, 
                                  self.font_small, COLOR_GRAY)
            current_y += 16
    
    def _render_section_header(self, screen: pygame.Surface, text: str, 
                               x: int, y: int):
        """Render a section header with underline"""
        header_surface = self.font_medium.render(text, True, self.highlight_color)
        screen.blit(header_surface, (x, y))
        pygame.draw.line(screen, self.panel_border_color, (x, y + 22), 
                        (x + INFO_PANEL_WIDTH - 40, y + 22), 1)
    
    def _render_text_line(self, screen: pygame.Surface, text: str, 
                         x: int, y: int, font: pygame.font.Font = None,
                         color: Tuple[int, int, int] = None):
        """Render a single line of text"""
        if font is None:
            font = self.font_medium
        if color is None:
            color = self.text_color
        
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x, y))
    
    def _render_body_details(self, screen: pygame.Surface, body: CelestialBody,
                             x: int, y: int, 
                             physics_engine: GravitationalPhysicsEngine,
                             all_bodies: List[CelestialBody]) -> int:
        """
        Render detailed information about a selected body.
        
        Returns the updated y position after rendering.
        """
        # Basic properties
        self._render_text_line(screen, f"Name: {body.name}", x, y)
        y += 20
        
        self._render_text_line(screen, f"Mass: {body.mass:.3e} kg", x, y, 
                              self.font_small)
        y += 18
        
        self._render_text_line(screen, f"Radius: {body.radius:.3e} m", x, y, 
                              self.font_small)
        y += 18
        
        # Position
        pos_au_x = body.position.x / AU_IN_METERS
        pos_au_y = body.position.y / AU_IN_METERS
        self._render_text_line(screen, f"Position: ({pos_au_x:.2f}, {pos_au_y:.2f}) AU", 
                              x, y, self.font_small)
        y += 18
        
        # Velocity
        speed_kms = body.velocity.calculate_magnitude() / 1000
        self._render_text_line(screen, f"Speed: {speed_kms:.2f} km/s", x, y, 
                              self.font_small)
        y += 18
        
        # Acceleration
        accel = body.current_acceleration.calculate_magnitude()
        self._render_text_line(screen, f"Acceleration: {accel:.3e} m/s²", x, y, 
                              self.font_small)
        y += 18
        
        # Force
        force = body.gravitational_force.calculate_magnitude()
        self._render_text_line(screen, f"Grav Force: {force:.3e} N", x, y, 
                              self.font_small)
        y += 18
        
        # Kinetic energy
        ke = body.calculate_kinetic_energy()
        self._render_text_line(screen, f"Kinetic Energy: {ke:.3e} J", x, y, 
                              self.font_small)
        y += 18
        
        # Fixed status
        if body.is_fixed:
            self._render_text_line(screen, "[FIXED - No motion]", x, y, 
                                  self.font_small, self.warning_color)
            y += 18
        
        y += 10
        
        # Orbital parameters (if there's a central body)
        if not body.is_fixed and len(all_bodies) > 1:
            # Find the most massive body as the "central" body
            central_body = max(all_bodies, key=lambda b: b.mass if b != body else 0)
            
            if central_body.mass > body.mass:
                self._render_text_line(screen, "Orbital Data:", x, y, 
                                      self.font_medium, self.highlight_color)
                y += 22
                
                orbital = physics_engine.calculate_orbital_parameters(body, central_body)
                
                self._render_text_line(screen, 
                    f"  Distance: {orbital['orbital_radius_au']:.3f} AU", 
                    x, y, self.font_small)
                y += 16
                
                self._render_text_line(screen, 
                    f"  Period: {orbital['orbital_period_days']:.1f} days", 
                    x, y, self.font_small)
                y += 16
                
                self._render_text_line(screen, 
                    f"  Escape vel: {orbital['escape_velocity_ms']/1000:.2f} km/s", 
                    x, y, self.font_small)
                y += 16
                
                bound_status = "BOUND" if orbital['is_bound'] else "UNBOUND"
                status_color = COLOR_GREEN if orbital['is_bound'] else self.error_color
                self._render_text_line(screen, f"  Status: {bound_status}", 
                                      x, y, self.font_small, status_color)
                y += 20
        
        return y
    
    def render_force_vectors(self, screen: pygame.Surface, 
                            bodies: List[CelestialBody],
                            camera: CameraController):
        """
        Render force and velocity vectors for all bodies.
        
        Educational visualization showing the direction and relative
        magnitude of forces acting on each body.
        """
        for body in bodies:
            if body.is_fixed:
                continue
            
            screen_pos = camera.world_to_screen(body.position)
            
            # Draw velocity vector (blue)
            if self.show_velocity_vectors:
                velocity_scale = 1e-5 / camera.zoom_level
                vel_end_x = screen_pos[0] + body.velocity.x * velocity_scale
                vel_end_y = screen_pos[1] - body.velocity.y * velocity_scale
                
                pygame.draw.line(screen, COLOR_BLUE, screen_pos, 
                               (int(vel_end_x), int(vel_end_y)), 2)
                
                # Arrowhead
                self._draw_arrowhead(screen, screen_pos, 
                                    (int(vel_end_x), int(vel_end_y)), COLOR_BLUE)
            
            # Draw gravitational force vector (red)
            if self.show_force_vectors:
                force_scale = 1e-15 / camera.zoom_level
                force_end_x = screen_pos[0] + body.gravitational_force.x * force_scale
                force_end_y = screen_pos[1] - body.gravitational_force.y * force_scale
                
                pygame.draw.line(screen, COLOR_RED, screen_pos, 
                               (int(force_end_x), int(force_end_y)), 2)
                
                # Arrowhead
                self._draw_arrowhead(screen, screen_pos, 
                                    (int(force_end_x), int(force_end_y)), COLOR_RED)
    
    def _draw_arrowhead(self, screen: pygame.Surface, start: Tuple[int, int], 
                        end: Tuple[int, int], color: Tuple[int, int, int]):
        """Draw an arrowhead at the end of a vector"""
        # Calculate direction
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 10:  # Too short for arrowhead
            return
        
        # Normalize and create arrowhead points
        dx /= length
        dy /= length
        
        arrow_size = 8
        perp_x, perp_y = -dy, dx
        
        p1 = (end[0] - dx * arrow_size + perp_x * arrow_size / 2,
              end[1] - dy * arrow_size + perp_y * arrow_size / 2)
        p2 = (end[0] - dx * arrow_size - perp_x * arrow_size / 2,
              end[1] - dy * arrow_size - perp_y * arrow_size / 2)
        
        pygame.draw.polygon(screen, color, [end, p1, p2])


# ==============================================================================
# SECTION 7: BODY CREATION AND EDITING
# ==============================================================================

class BodyEditor:
    """
    Handles creation and modification of celestial bodies.
    
    Provides a form-based interface for students to set body properties
    including mass, position, velocity, and visual appearance.
    """
    
    def __init__(self, ui_manager: UserInterfaceManager):
        """
        Initialize the body editor.
        
        Args:
            ui_manager: Reference to the UI manager for rendering
        """
        self.ui_manager = ui_manager
        self.is_active = False
        self.edit_mode = False  # True for edit, False for create
        self.body_being_edited: Optional[CelestialBody] = None
        
        # Form fields with default values
        self.form_fields = {
            "name": "NewBody",
            "mass": f"{EARTH_MASS_KG:.2e}",
            "radius": f"{EARTH_RADIUS_METERS:.2e}",
            "pos_x": "1.0",      # In AU
            "pos_y": "0.0",
            "vel_x": "0.0",      # In km/s
            "vel_y": "29.78",    # Earth's orbital velocity
            "is_fixed": "False"
        }
        
        self.active_field = None
        self.color_index = 0
    
    def open_for_creation(self):
        """Open editor in creation mode"""
        self.is_active = True
        self.edit_mode = False
        self.body_being_edited = None
        self._reset_form_defaults()
    
    def open_for_editing(self, body: CelestialBody):
        """Open editor in edit mode with body's current values"""
        self.is_active = True
        self.edit_mode = True
        self.body_being_edited = body
        
        # Populate form with body's current values
        self.form_fields["name"] = body.name
        self.form_fields["mass"] = f"{body.mass:.2e}"
        self.form_fields["radius"] = f"{body.radius:.2e}"
        self.form_fields["pos_x"] = f"{body.position.x / AU_IN_METERS:.4f}"
        self.form_fields["pos_y"] = f"{body.position.y / AU_IN_METERS:.4f}"
        self.form_fields["vel_x"] = f"{body.velocity.x / 1000:.2f}"
        self.form_fields["vel_y"] = f"{body.velocity.y / 1000:.2f}"
        self.form_fields["is_fixed"] = str(body.is_fixed)
    
    def close(self):
        """Close the editor"""
        self.is_active = False
        self.body_being_edited = None
        self.active_field = None
    
    def _reset_form_defaults(self):
        """Reset form to default values for a new Earth-like body"""
        self.form_fields = {
            "name": f"Body_{datetime.now().strftime('%H%M%S')}",
            "mass": f"{EARTH_MASS_KG:.2e}",
            "radius": f"{EARTH_RADIUS_METERS:.2e}",
            "pos_x": "1.0",
            "pos_y": "0.0",
            "vel_x": "0.0",
            "vel_y": "29.78",
            "is_fixed": "False"
        }
    
    def create_body_from_form(self) -> Optional[CelestialBody]:
        """
        Create a new celestial body from the current form values.
        
        Returns:
            A new CelestialBody instance, or None if values are invalid
        """
        try:
            name = self.form_fields["name"]
            mass = float(self.form_fields["mass"])
            radius = float(self.form_fields["radius"])
            pos_x = float(self.form_fields["pos_x"]) * AU_IN_METERS
            pos_y = float(self.form_fields["pos_y"]) * AU_IN_METERS
            vel_x = float(self.form_fields["vel_x"]) * 1000  # km/s to m/s
            vel_y = float(self.form_fields["vel_y"]) * 1000
            is_fixed = self.form_fields["is_fixed"].lower() == "true"
            
            # Validate values
            if mass <= 0 or radius <= 0:
                return None
            
            # Get color
            color = DEFAULT_BODY_COLORS[self.color_index % len(DEFAULT_BODY_COLORS)]
            
            # Calculate display radius (log scale for visibility)
            display_radius = max(MIN_DISPLAY_RADIUS, 
                                min(MAX_DISPLAY_RADIUS, 
                                    int(5 + math.log10(radius / EARTH_RADIUS_METERS) * 3)))
            
            return CelestialBody(
                name=name,
                mass=mass,
                radius=radius,
                position=Vector2D(pos_x, pos_y),
                velocity=Vector2D(vel_x, vel_y),
                color=color,
                display_radius=display_radius,
                is_fixed=is_fixed
            )
        
        except (ValueError, KeyError):
            return None
    
    def update_body_from_form(self) -> bool:
        """
        Update the body being edited with form values.
        
        Returns:
            True if update successful, False otherwise
        """
        if self.body_being_edited is None:
            return False
        
        try:
            self.body_being_edited.name = self.form_fields["name"]
            self.body_being_edited.mass = float(self.form_fields["mass"])
            self.body_being_edited.radius = float(self.form_fields["radius"])
            self.body_being_edited.position.x = float(self.form_fields["pos_x"]) * AU_IN_METERS
            self.body_being_edited.position.y = float(self.form_fields["pos_y"]) * AU_IN_METERS
            self.body_being_edited.velocity.x = float(self.form_fields["vel_x"]) * 1000
            self.body_being_edited.velocity.y = float(self.form_fields["vel_y"]) * 1000
            self.body_being_edited.is_fixed = self.form_fields["is_fixed"].lower() == "true"
            return True
        
        except (ValueError, KeyError):
            return False
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """
        Handle input events for the editor form.
        
        Returns True if the event was consumed by the editor.
        """
        if not self.is_active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            
            elif event.key == pygame.K_RETURN:
                # Submit form
                if self.edit_mode:
                    self.update_body_from_form()
                self.close()
                return True
            
            elif event.key == pygame.K_TAB:
                # Cycle through fields
                field_names = list(self.form_fields.keys())
                if self.active_field:
                    current_index = field_names.index(self.active_field)
                    self.active_field = field_names[(current_index + 1) % len(field_names)]
                else:
                    self.active_field = field_names[0]
                return True
            
            elif self.active_field and event.unicode:
                if event.key == pygame.K_BACKSPACE:
                    self.form_fields[self.active_field] = self.form_fields[self.active_field][:-1]
                else:
                    self.form_fields[self.active_field] += event.unicode
                return True
        
        return False
    
    def render(self, screen: pygame.Surface):
        """Render the body editor form"""
        if not self.is_active:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Editor panel
        panel_width = 400
        panel_height = 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (30, 30, 50), panel_rect)
        pygame.draw.rect(screen, (80, 80, 120), panel_rect, 2)
        
        # Title
        title = "EDIT BODY" if self.edit_mode else "CREATE NEW BODY"
        title_surface = self.ui_manager.font_title.render(title, True, 
                                                          self.ui_manager.highlight_color)
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))
        
        # Form fields
        y_offset = panel_y + 60
        field_labels = {
            "name": "Name:",
            "mass": "Mass (kg):",
            "radius": "Radius (m):",
            "pos_x": "Position X (AU):",
            "pos_y": "Position Y (AU):",
            "vel_x": "Velocity X (km/s):",
            "vel_y": "Velocity Y (km/s):",
            "is_fixed": "Fixed (True/False):"
        }
        
        for field_name, label in field_labels.items():
            # Label
            label_surface = self.ui_manager.font_small.render(label, True, 
                                                               self.ui_manager.text_color)
            screen.blit(label_surface, (panel_x + 20, y_offset))
            
            # Input field
            field_rect = pygame.Rect(panel_x + 150, y_offset - 2, 230, 22)
            field_color = (60, 60, 80) if self.active_field == field_name else (40, 40, 60)
            pygame.draw.rect(screen, field_color, field_rect)
            pygame.draw.rect(screen, (100, 100, 140), field_rect, 1)
            
            # Field value
            value_surface = self.ui_manager.font_small.render(
                self.form_fields[field_name], True, self.ui_manager.text_color)
            screen.blit(value_surface, (panel_x + 155, y_offset))
            
            y_offset += 35
        
        # Instructions
        instructions = "TAB: Next field | ENTER: Save | ESC: Cancel"
        inst_surface = self.ui_manager.font_small.render(instructions, True, COLOR_GRAY)
        screen.blit(inst_surface, (panel_x + 20, panel_y + panel_height - 35))


# ==============================================================================
# SECTION 8: SAVE/LOAD MANAGER
# ==============================================================================

class SaveLoadManager:
    """
    Handles saving and loading simulation states to/from JSON files.
    
    Allows students to save their custom simulations and reload them later,
    enabling experimentation and sharing of interesting configurations.
    """
    
    def __init__(self, save_directory: str = "saved_simulations"):
        """
        Initialize the save/load manager.
        
        Args:
            save_directory: Directory to store save files
        """
        self.save_directory = save_directory
        self._ensure_save_directory_exists()
    
    def _ensure_save_directory_exists(self):
        """Create the save directory if it doesn't exist"""
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
    
    def save_simulation(self, state: SimulationState, 
                        filename: str = None) -> Tuple[bool, str]:
        """
        Save the current simulation state to a JSON file.
        
        Args:
            state: The simulation state to save
            filename: Optional filename (will auto-generate if not provided)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"simulation_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith(".json"):
                filename += ".json"
            
            # Add timestamp to state
            state.save_timestamp = datetime.now().isoformat()
            
            # Full path
            filepath = os.path.join(self.save_directory, filename)
            
            # Write to file
            with open(filepath, 'w') as file:
                json.dump(state.to_dict(), file, indent=2)
            
            return True, f"Saved to {filename}"
        
        except Exception as e:
            return False, f"Save failed: {str(e)}"
    
    def load_simulation(self, filename: str) -> Tuple[bool, SimulationState, str]:
        """
        Load a simulation state from a JSON file.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            Tuple of (success: bool, state: SimulationState, message: str)
        """
        try:
            # Ensure .json extension
            if not filename.endswith(".json"):
                filename += ".json"
            
            filepath = os.path.join(self.save_directory, filename)
            
            with open(filepath, 'r') as file:
                data = json.load(file)
            
            state = SimulationState.from_dict(data)
            
            return True, state, f"Loaded {filename}"
        
        except FileNotFoundError:
            return False, None, f"File not found: {filename}"
        except json.JSONDecodeError:
            return False, None, f"Invalid JSON format in {filename}"
        except Exception as e:
            return False, None, f"Load failed: {str(e)}"
    
    def list_saved_simulations(self) -> List[str]:
        """
        List all saved simulation files.
        
        Returns:
            List of filenames (without path)
        """
        try:
            files = os.listdir(self.save_directory)
            return [f for f in files if f.endswith(".json")]
        except Exception:
            return []


# ==============================================================================
# SECTION 9: MAIN SIMULATION CLASS
# ==============================================================================

class OrbitalMechanicsSimulation:
    """
    Main simulation class that orchestrates all components.
    
    This is the central class that brings together:
        - Physics engine for gravitational calculations
        - Camera controller for view management
        - UI manager for user interface
        - Body editor for creating/editing bodies
        - Save/load manager for persistence
    
    The simulation loop handles:
        - Event processing (input, window events)
        - Physics updates (gravitational forces, collisions)
        - Rendering (bodies, trails, UI)
    """
    
    def __init__(self):
        """Initialize all simulation components"""
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Orbital Mechanics N-Body Simulation - OCR NEA")
        
        # Create display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize components
        self.physics_engine = GravitationalPhysicsEngine()
        self.camera = CameraController()
        self.ui_manager = UserInterfaceManager()
        self.body_editor = BodyEditor(self.ui_manager)
        self.save_load_manager = SaveLoadManager()
        
        # Simulation state
        self.bodies: List[CelestialBody] = []
        self.selected_body: Optional[CelestialBody] = None
        self.simulation_time = 0.0
        self.speed_multiplier = 1.0
        self.is_paused = False
        self.is_running = True
        
        # Trail update counter (for performance)
        self.trail_update_counter = 0
        self.trail_update_interval = 3  # Update every N frames
        
        # Background stars (pre-generated for performance)
        self.background_stars = self._generate_background_stars(300)
        
        # Initialize with a default solar system
        self._create_default_solar_system()
    
    def _generate_background_stars(self, count: int) -> List[Tuple[int, int, int]]:
        """
        Generate random background star positions.
        
        Args:
            count: Number of stars to generate
            
        Returns:
            List of (x, y, brightness) tuples
        """
        import random
        stars = []
        for i in range(count):
            x = (i * 7919 + 1234) % SCREEN_WIDTH
            y = (i * 6271 + 5678) % SCREEN_HEIGHT
            brightness = 80 + (i * 13) % 120
            stars.append((x, y, brightness))
        return stars
    
    def _create_default_solar_system(self):
        """
        Create a default solar system for demonstration.
        
        This includes the Sun and inner planets with realistic parameters,
        providing a starting point for student exploration.
        """
        # Create the Sun
        sun = CelestialBody(
            name="Sun",
            mass=SUN_MASS_KG,
            radius=SUN_RADIUS_METERS,
            position=Vector2D(0, 0),
            velocity=Vector2D(0, 0),
            color=(255, 220, 50),
            display_radius=25,
            is_fixed=True
        )
        self.bodies.append(sun)
        
        # Planetary data: (name, mass, radius, distance_AU, velocity_km_s, color)
        planets_data = [
            ("Mercury", 3.285e23, 2.44e6, 0.387, 47.87, (169, 169, 169), 4),
            ("Venus", 4.867e24, 6.05e6, 0.723, 35.02, (255, 198, 73), 6),
            ("Earth", 5.972e24, 6.37e6, 1.0, 29.78, (100, 149, 237), 7),
            ("Mars", 6.39e23, 3.39e6, 1.524, 24.07, (188, 39, 50), 5),
            ("Jupiter", 1.898e27, 6.99e7, 5.203, 13.07, (201, 144, 57), 15),
            ("Saturn", 5.683e26, 5.82e7, 9.537, 9.69, (234, 214, 184), 13),
            ("Uranus", 8.681e25, 2.54e7, 19.19, 6.81, (175, 238, 238), 10),
            ("Neptune", 1.024e26, 2.46e7, 30.07, 5.43, (65, 105, 225), 9),
        ]
        
        for name, mass, radius, distance_au, velocity_kms, color, display_size in planets_data:
            # Place planet on positive x-axis with velocity in positive y direction
            # This creates a counter-clockwise orbit
            body = CelestialBody(
                name=name,
                mass=mass,
                radius=radius,
                position=Vector2D(distance_au * AU_IN_METERS, 0),
                velocity=Vector2D(0, velocity_kms * 1000),  # Convert km/s to m/s
                color=color,
                display_radius=display_size,
                is_fixed=False
            )
            self.bodies.append(body)
    
    def handle_events(self):
        """Process all Pygame events"""
        # Handle body editor input first if active
        if self.body_editor.is_active:
            for event in pygame.event.get():
                if not self.body_editor.handle_input(event):
                    if event.type == pygame.QUIT:
                        self.is_running = False
            return
        
        # Normal event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.adjust_zoom(event.y)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
    
    def _handle_keydown(self, event: pygame.event.Event):
        """Handle keyboard key press events"""
        key = event.key
        
        # Pause/Resume
        if key == pygame.K_SPACE:
            self.is_paused = not self.is_paused
        
        # Speed adjustment
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.speed_multiplier = min(100.0, self.speed_multiplier * 2)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed_multiplier = max(0.125, self.speed_multiplier / 2)
        
        # Camera reset
        elif key == pygame.K_r:
            self.camera.reset_to_default()
        
        # Toggle UI elements
        elif key == pygame.K_i:
            self.ui_manager.show_info_panel = not self.ui_manager.show_info_panel
        elif key == pygame.K_f:
            self.ui_manager.show_force_vectors = not self.ui_manager.show_force_vectors
        elif key == pygame.K_v:
            self.ui_manager.show_velocity_vectors = not self.ui_manager.show_velocity_vectors
        
        # Body management
        elif key == pygame.K_c:
            self.body_editor.open_for_creation()
        elif key == pygame.K_e and self.selected_body:
            self.body_editor.open_for_editing(self.selected_body)
        elif key == pygame.K_DELETE and self.selected_body:
            if self.selected_body in self.bodies:
                self.bodies.remove(self.selected_body)
                self.selected_body = None
        
        # Save simulation
        elif key == pygame.K_s:
            self._save_current_simulation()
        
        # Load simulation
        elif key == pygame.K_l:
            self._load_simulation_prompt()
        
        # Quit
        elif key == pygame.K_ESCAPE:
            self.is_running = False
    
    def _handle_mouse_click(self, event: pygame.event.Event):
        """Handle mouse click events"""
        if event.button == 1:  # Left click - select body
            mouse_pos = pygame.mouse.get_pos()
            clicked_body = self._find_body_at_screen_position(mouse_pos)
            self.selected_body = clicked_body
            
            if clicked_body:
                print(f"Selected: {clicked_body.name}")
        
        elif event.button == 3:  # Right click - deselect
            self.selected_body = None
    
    def _find_body_at_screen_position(self, screen_pos: Tuple[int, int]) -> Optional[CelestialBody]:
        """
        Find a celestial body at the given screen position.
        
        Args:
            screen_pos: (x, y) pixel coordinates on screen
            
        Returns:
            The body at that position, or None
        """
        for body in reversed(self.bodies):  # Check front-to-back
            body_screen_pos = self.camera.world_to_screen(body.position)
            distance_pixels = math.sqrt(
                (screen_pos[0] - body_screen_pos[0]) ** 2 +
                (screen_pos[1] - body_screen_pos[1]) ** 2
            )
            
            # Use larger click radius for easier selection
            click_radius = max(body.display_radius, 15)
            if distance_pixels <= click_radius:
                return body
        
        return None
    
    def _save_current_simulation(self):
        """Save the current simulation state"""
        state = SimulationState(
            simulation_time_seconds=self.simulation_time,
            speed_multiplier=self.speed_multiplier,
            camera_position_x=self.camera.position.x,
            camera_position_y=self.camera.position.y,
            camera_zoom=self.camera.zoom_level,
            bodies=self.bodies,
            save_name="User Save"
        )
        
        success, message = self.save_load_manager.save_simulation(state)
        print(message)
    
    def _load_simulation_prompt(self):
        """Load a simulation (loads most recent for simplicity)"""
        saved_files = self.save_load_manager.list_saved_simulations()
        
        if not saved_files:
            print("No saved simulations found")
            return
        
        # Load the most recent file
        saved_files.sort(reverse=True)
        success, state, message = self.save_load_manager.load_simulation(saved_files[0])
        
        if success and state:
            self.bodies = state.bodies
            self.simulation_time = state.simulation_time_seconds
            self.speed_multiplier = state.speed_multiplier
            self.camera.position = Vector2D(state.camera_position_x, state.camera_position_y)
            self.camera.zoom_level = state.camera_zoom
            self.camera.target_zoom = state.camera_zoom
            print(message)
    
    def update(self):
        """Update simulation state"""
        # Handle continuous keyboard input for camera
        keys = pygame.key.get_pressed()
        self.camera.handle_keyboard_input(keys)
        self.camera.update()
        
        # Skip physics if paused
        if self.is_paused:
            return
        
        # Calculate time step
        time_step = BASE_TIME_STEP_SECONDS * self.speed_multiplier / FPS
        
        # Update simulation time
        self.simulation_time += time_step
        
        # Calculate gravitational forces
        self.physics_engine.calculate_all_forces(self.bodies)
        
        # Update each body's physics
        for body in self.bodies:
            acceleration = self.physics_engine.calculate_acceleration(
                body, body.gravitational_force)
            self.physics_engine.update_body_physics(body, acceleration, time_step)
        
        # Check for collisions
        self._handle_collisions()
        
        # Update orbital trails
        self.trail_update_counter += 1
        if self.trail_update_counter >= self.trail_update_interval:
            self.trail_update_counter = 0
            for body in self.bodies:
                if not body.is_fixed:
                    body.add_trail_point()
    
    def _handle_collisions(self):
        """Detect and handle collisions between bodies"""
        bodies_to_remove = []
        bodies_to_add = []
        
        for i, body1 in enumerate(self.bodies):
            for body2 in self.bodies[i+1:]:
                if self.physics_engine.check_collision(body1, body2):
                    # Skip if either body is already marked for removal
                    if body1 in bodies_to_remove or body2 in bodies_to_remove:
                        continue
                    
                    # Handle the collision
                    merged_body = self.physics_engine.handle_collision(body1, body2)
                    
                    bodies_to_remove.append(body1)
                    bodies_to_remove.append(body2)
                    bodies_to_add.append(merged_body)
                    
                    print(f"Collision! {body1.name} and {body2.name} merged into {merged_body.name}")
        
        # Remove collided bodies
        for body in bodies_to_remove:
            if body in self.bodies:
                self.bodies.remove(body)
            if body == self.selected_body:
                self.selected_body = None
        
        # Add merged bodies
        self.bodies.extend(bodies_to_add)
    
    def render(self):
        """Render the simulation"""
        # Clear screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw background stars
        for x, y, brightness in self.background_stars:
            color = (brightness, brightness, brightness)
            size = 1 if brightness < 150 else 2
            pygame.draw.circle(self.screen, color, (x, y), size)
        
        # Draw orbital trails
        self._render_trails()
        
        # Draw celestial bodies
        self._render_bodies()
        
        # Draw force/velocity vectors
        self.ui_manager.render_force_vectors(self.screen, self.bodies, self.camera)
        
        # Draw UI panel
        total_energy = self.physics_engine.calculate_total_energy(self.bodies)
        self.ui_manager.render_info_panel(
            self.screen,
            self.simulation_time,
            self.speed_multiplier,
            self.camera.zoom_level,
            self.bodies,
            self.selected_body,
            self.physics_engine,
            self.is_paused,
            total_energy
        )
        
        # Draw body editor if active
        self.body_editor.render(self.screen)
        
        # Update display
        pygame.display.flip()
    
    def _render_trails(self):
        """Render orbital trails for all bodies"""
        for body in self.bodies:
            if len(body.orbital_trail) < 2:
                continue
            
            # Convert trail points to screen coordinates
            screen_points = []
            for world_x, world_y in body.orbital_trail:
                screen_pos = self.camera.world_to_screen(Vector2D(world_x, world_y))
                screen_points.append(screen_pos)
            
            # Draw trail with fading effect
            for i in range(1, len(screen_points)):
                alpha = int(255 * i / len(screen_points) * 0.5)
                color = (
                    min(255, body.color[0]),
                    min(255, body.color[1]),
                    min(255, body.color[2])
                )
                pygame.draw.line(self.screen, color, 
                               screen_points[i-1], screen_points[i], 
                               TRAIL_LINE_WIDTH)
    
    def _render_bodies(self):
        """Render all celestial bodies"""
        for body in self.bodies:
            screen_pos = self.camera.world_to_screen(body.position)
            
            # Check if on screen
            if (-50 < screen_pos[0] < SCREEN_WIDTH + 50 and
                -50 < screen_pos[1] < SCREEN_HEIGHT + 50):
                
                # Draw selection highlight
                if body == self.selected_body:
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                      screen_pos, body.display_radius + 5, 2)
                
                # Draw body
                display_radius = max(MIN_DISPLAY_RADIUS, 
                                    int(body.display_radius * self.camera.zoom_level))
                display_radius = min(MAX_DISPLAY_RADIUS, display_radius)
                
                pygame.draw.circle(self.screen, body.color, screen_pos, display_radius)
                
                # Draw name label
                label = self.ui_manager.font_small.render(body.name, True, (255, 255, 255))
                label_rect = label.get_rect(center=(screen_pos[0], 
                                                    screen_pos[1] - display_radius - 10))
                self.screen.blit(label, label_rect)
    
    def run(self):
        """Main simulation loop"""
        print("\n" + "=" * 70)
        print("        ORBITAL MECHANICS N-BODY SIMULATION")
        print("              OCR NEA - A-Level Computer Science")
        print("=" * 70)
        print("\nEducational simulation for GCSE/A-Level orbital mechanics.")
        print("Features: N-body gravity, collision detection, save/load, customization")
        print("\nControls:")
        print("  WASD/Arrows: Pan camera")
        print("  Mouse Wheel: Zoom in/out")
        print("  Left Click: Select body")
        print("  Right Click: Deselect")
        print("  C: Create new body")
        print("  E: Edit selected body")
        print("  DEL: Delete selected body")
        print("  SPACE: Pause/Resume")
        print("  +/-: Adjust speed")
        print("  F: Toggle force vectors")
        print("  V: Toggle velocity vectors")
        print("  I: Toggle info panel")
        print("  S: Save simulation")
        print("  L: Load simulation")
        print("  R: Reset camera")
        print("  ESC: Quit")
        print("\n" + "=" * 70 + "\n")
        
        # Main loop
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        # Cleanup
        pygame.quit()
        print("\nSimulation ended. Thank you for exploring orbital mechanics!")


# ==============================================================================
# SECTION 10: ENTRY POINT
# ==============================================================================

def main():
    """
    Main entry point for the simulation.
    
    Creates and runs the orbital mechanics simulation.
    """
    simulation = OrbitalMechanicsSimulation()
    simulation.run()


# Execute when run directly
if __name__ == "__main__":
    main()
