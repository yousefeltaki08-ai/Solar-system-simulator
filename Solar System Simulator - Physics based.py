import math
import pygame
import os

# Initializing pygame
pygame.init()

# Screen settings
Screen_info = pygame.display.Info()
WIDTH, HEIGHT = Screen_info.current_w, Screen_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Solar System Simulator")
clock = pygame.time.Clock()
FPS = 60

# Font
try:
    FONT = pygame.font.SysFont(None, 18)
except Exception:
    FONT = None

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)


# ================================= Helper Functions ================================= #
def load_image_and_scale(name, size):
    full_file_path = os.path.join('Images', name)
    try:
        loaded_image = pygame.image.load(full_file_path)
        if loaded_image.get_alpha() is None:
            loaded_image = loaded_image.convert()
        else:
            loaded_image = loaded_image.convert_alpha()
        if size is None:
            return loaded_image
        else:
            return pygame.transform.smoothscale(loaded_image, (size, size))
    except Exception as error_message:
        print(f"[Warning] Cannot load image: {full_file_path} -> {error_message}")
        return None


# Physical constants
# 1 Unit Distance = 1 billion meters
# 1 Unit Mass = 10^24 kg
# 1 Unit Time = 1 Day (86400 seconds)
GRAVITATIONAL_CONSTANT = 6.67430e-11
SCALE_DISTANCE = 1e9
SCALE_MASS = 1e24
SCALE_TIME = 86400

# Derived G for the simulation units (Distance Units / Time Unit^2)
# G_sim = G_real * (M_scale * T_scale^2 / D_scale^3)
G = GRAVITATIONAL_CONSTANT * (SCALE_MASS * SCALE_TIME ** 2 / SCALE_DISTANCE ** 3)

# Camera variables
camera_x, camera_y = 0, 0
camera_speed = 300
camera_zoom = 1.0
camera_zoom_max = 20
camera_zoom_min = 0.05

# Time management
SIM_TIME_MULTIPLIER = 1.0
simulation_time = 0.0

# FIX: Removed hard-coded physics_substeps = 50
# This allows the simulation to use fewer steps when at low speeds, improving FPS.
# Increased MAX_SUBSTEP_DT to 0.5.
# 0.5 days per step is accurate enough for visual orbits and significantly improves performance.
MAX_SUBSTEP_DT = 0.5


# ================================= Classes ================================= #

class Planet:
    def __init__(self, name, image_file, mass, position, velocity, size, color_fallback):
        self.name = name
        self.mass = mass
        self.color_fallback = color_fallback

        self.position = list(position)
        self.velocity = list(velocity)
        self.acceleration = [0.0, 0.0]
        self.prev_acceleration = [0.0, 0.0]

        self.trail = []
        self.max_trail_length = 500

        self.base_size = max(4, int(size))
        self.image_file = image_file

        original_loaded_image = load_image_and_scale(image_file, None)
        self.original_image = original_loaded_image
        self._scaled_cache = {}
        if original_loaded_image is not None:
            self.image = pygame.transform.smoothscale(original_loaded_image, (self.base_size, self.base_size))
        else:
            self.image = None

    def calculate_acceleration_from_all(self, all_planets):
        ax, ay = 0.0, 0.0
        for planet in all_planets:
            if planet is not self:
                dx = planet.position[0] - self.position[0]
                dy = planet.position[1] - self.position[1]
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < 0.01:  # Avoid division by zero
                    continue
                force_mag = (G * planet.mass) / (distance * distance)
                ax += force_mag * (dx / distance)
                ay += force_mag * (dy / distance)
        return [ax, ay]

    def update_physics(self, all_planets, dt):
        # Velocity Verlet integration
        half_dt_sq = 0.5 * dt * dt
        self.position[0] += self.velocity[0] * dt + self.acceleration[0] * half_dt_sq
        self.position[1] += self.velocity[1] * dt + self.acceleration[1] * half_dt_sq

        new_acc = self.calculate_acceleration_from_all(all_planets)

        avg_ax = 0.5 * (self.acceleration[0] + new_acc[0])
        avg_ay = 0.5 * (self.acceleration[1] + new_acc[1])
        self.velocity[0] += avg_ax * dt
        self.velocity[1] += avg_ay * dt

        self.acceleration = new_acc

        # Trail update
        # Only add point if moved significantly (prevents bunching up)
        if len(self.trail) == 0 or (
                (self.position[0] - self.trail[-1][0]) ** 2 +
                (self.position[1] - self.trail[-1][1]) ** 2 > 0.1
        ):
            self.trail.append((self.position[0], self.position[1]))

        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def draw(self, screen, camera_offset_x, camera_offset_y, zoom_level, draw_trail=True):
        # Calculate screen position
        screen_x = int(WIDTH // 2 + (self.position[0] - camera_offset_x) * zoom_level)
        screen_y = int(HEIGHT // 2 + (self.position[1] - camera_offset_y) * zoom_level)

        # Calculate display size
        desired_planet_size = max(2, int(self.base_size * zoom_level))

        # OPTIMIZATION: Don't draw if off-screen
        margin = desired_planet_size + self.max_trail_length if draw_trail else desired_planet_size
        if (screen_x < -margin or screen_x > WIDTH + margin or
                screen_y < -margin or screen_y > HEIGHT + margin):
            return

        # Draw trail
        if draw_trail and len(self.trail) > 2:
            trail_points = []
            # Only transform points that are likely on screen to save CPU
            for trail_x, trail_y in self.trail:
                tx = int(WIDTH // 2 + (trail_x - camera_offset_x) * zoom_level)
                ty = int(HEIGHT // 2 + (trail_y - camera_offset_y) * zoom_level)
                trail_points.append((tx, ty))

            if len(trail_points) > 1:
                try:
                    pygame.draw.lines(screen, self.color_fallback, False, trail_points, 1)
                except:
                    pass

        # Draw body
        image_source = self.original_image if self.original_image is not None else self.image

        if image_source is not None:
            # OPTIMIZATION: Switched to transform.scale
            # smoothscale is very CPU intensive when called every frame (e.g. while zooming).
            # scale is much faster and prevents the "simulation speeds up when zooming" lag.
            cache_key = desired_planet_size
            if cache_key not in self._scaled_cache:
                try:
                    self._scaled_cache[cache_key] = pygame.transform.scale(image_source, (desired_planet_size,
                                                                                         desired_planet_size))
                except Exception:
                    self._scaled_cache[cache_key] = pygame.transform.scale(image_source,
                                                                           (desired_planet_size, desired_planet_size))

            planet_image_rect = self._scaled_cache[cache_key].get_rect(center=(screen_x, screen_y))
            screen.blit(self._scaled_cache[cache_key], planet_image_rect)
        else:
            pygame.draw.circle(screen, self.color_fallback, (screen_x, screen_y), max(2, desired_planet_size // 2))

        # Name tag
        try:
            if FONT:
                text_surface = FONT.render(self.name, True, WHITE)
                text_rectangle = text_surface.get_rect(center=(screen_x, screen_y + desired_planet_size // 2 + 10))
                background_rectangle = text_rectangle.inflate(4, 2)
                pygame.draw.rect(screen, BLACK, background_rectangle)
                screen.blit(text_surface, text_rectangle)
        except Exception:
            pass


# ================================= External functions ================================= #
def calculate_circular_orbit_velocity(distance_from_sun, sun_mass):
    return math.sqrt(G * sun_mass / distance_from_sun)


# ================================= Solar system data ================================= #

SUN_MASS_KG = 1.989e30
SUN_RADIUS_KM = 696000

PLANET_DATA = {
    "Mercury": [3.285e23, 0.387, 2439.7, (169, 169, 169)],
    "Venus": [4.867e24, 0.723, 6051.8, (255, 198, 73)],
    "Earth": [5.972e24, 1.000, 6371.0, (100, 149, 237)],
    "Mars": [6.39e23, 1.524, 3389.5, (193, 68, 14)],
    "Jupiter": [1.898e27, 5.203, 69911, (201, 176, 55)],
    "Saturn": [5.683e26, 9.537, 58232, (249, 214, 46)],
    "Uranus": [8.681e25, 19.19, 25362, (79, 208, 231)],
    "Neptune": [1.024e26, 30.07, 24622, (63, 84, 186)],
}

AU_TO_METERS = 1.496e11

sun_mass_sim = SUN_MASS_KG / SCALE_MASS
sun_size_pixels = 20

sun = Planet(name="Sun", image_file="sun.png", mass=sun_mass_sim, position=[0, 0], velocity=[0, 0],
             size=sun_size_pixels, color_fallback=YELLOW)

celestial_bodies = [sun]
planets_only = []

for planet_name, (mass_kg, distance_au, radius_km, color) in PLANET_DATA.items():
    mass_sim = mass_kg / SCALE_MASS
    distance_sim = (distance_au * AU_TO_METERS) / SCALE_DISTANCE
    size_pixels = max(4, int(5 * math.log10(radius_km / 1000)))
    orbital_speed = calculate_circular_orbit_velocity(distance_sim, sun_mass_sim)
    initial_position = [distance_sim, 0]
    initial_velocity = [0, orbital_speed]

    planet = Planet(
        name=planet_name,
        image_file=f"{planet_name}.png",
        mass=mass_sim,
        position=initial_position,
        velocity=initial_velocity,
        size=size_pixels,
        color_fallback=color
    )

    planet.acceleration = planet.calculate_acceleration_from_all([sun])

    celestial_bodies.append(planet)
    planets_only.append(planet)

mercury = planets_only[0]
venus = planets_only[1]
earth = planets_only[2]
mars = planets_only[3]
jupiter = planets_only[4]
saturn = planets_only[5]
uranus = planets_only[6]
neptune = planets_only[7]

# ================================= Main Game Loop ================================= #
running = True
paused_multiplier = SIM_TIME_MULTIPLIER

while running:
    screen.fill(BLACK)

    # OPTIMIZATION: Cap delta time to prevent "spiral of death" where lag causes massive time jumps
    # We also use a smaller clamp (0.1s) to ensure the simulation doesn't jump too far ahead if a frame hangs
    raw_delta_time = clock.tick(FPS) / 1000.0
    delta_time = min(raw_delta_time, 0.1)

    simulation_time += delta_time * SIM_TIME_MULTIPLIER

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                SIM_TIME_MULTIPLIER *= 1.5
            elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                SIM_TIME_MULTIPLIER /= 1.5
            elif event.key == pygame.K_SPACE:
                if SIM_TIME_MULTIPLIER > 0:
                    paused_multiplier = SIM_TIME_MULTIPLIER
                    SIM_TIME_MULTIPLIER = 0
                else:
                    SIM_TIME_MULTIPLIER = paused_multiplier
            elif event.key == pygame.K_t:
                for planet in planets_only:
                    planet.trail.clear()
            elif event.key == pygame.K_1:
                camera_x, camera_y = mercury.position[0], mercury.position[1]
            elif event.key == pygame.K_2:
                camera_x, camera_y = venus.position[0], venus.position[1]
            elif event.key == pygame.K_3:
                camera_x, camera_y = earth.position[0], earth.position[1]
            elif event.key == pygame.K_4:
                camera_x, camera_y = mars.position[0], mars.position[1]
            elif event.key == pygame.K_5:
                camera_x, camera_y = jupiter.position[0], jupiter.position[1]
            elif event.key == pygame.K_6:
                camera_x, camera_y = saturn.position[0], saturn.position[1]
            elif event.key == pygame.K_7:
                camera_x, camera_y = uranus.position[0], uranus.position[1]
            elif event.key == pygame.K_8:
                camera_x, camera_y = neptune.position[0], neptune.position[1]
            elif event.key == pygame.K_0:
                camera_x, camera_y = 0, 0
        elif event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x_before = camera_x + (mouse_x - WIDTH // 2) / camera_zoom
            world_y_before = camera_y + (mouse_y - HEIGHT // 2) / camera_zoom

            if event.y > 0:
                camera_zoom *= 1.1
            else:
                camera_zoom /= 1.1
            camera_zoom = max(camera_zoom_min, min(camera_zoom_max, camera_zoom))

            camera_x = world_x_before - (mouse_x - WIDTH // 2) / camera_zoom
            camera_y = world_y_before - (mouse_y - HEIGHT // 2) / camera_zoom

    camera_zoom = max(camera_zoom_min, min(camera_zoom_max, camera_zoom))

    keys = pygame.key.get_pressed()
    adjusted_pan_speed = camera_speed / camera_zoom

    if keys[pygame.K_LEFT] or keys[pygame.K_a]: camera_x -= adjusted_pan_speed * delta_time
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: camera_x += adjusted_pan_speed * delta_time
    if keys[pygame.K_UP] or keys[pygame.K_w]: camera_y -= adjusted_pan_speed * delta_time
    if keys[pygame.K_DOWN] or keys[pygame.K_s]: camera_y += adjusted_pan_speed * delta_time

    # Physics substepping
    total_sim_dt = delta_time * SIM_TIME_MULTIPLIER

    if total_sim_dt > 0:
        # FIX: Removed hardcoded 'physics_substeps = 50'.
        # We now rely entirely on MAX_SUBSTEP_DT to determine accuracy.
        # This prevents the CPU from doing 50 calculations per frame when only 1 is needed.
        required_substeps = int(math.ceil(total_sim_dt / MAX_SUBSTEP_DT))
        substep_dt = total_sim_dt / required_substeps
    else:
        required_substeps = 1
        substep_dt = 0.0

    for _ in range(required_substeps):
        for planet in planets_only:
            planet.update_physics(celestial_bodies, substep_dt)

    for body in celestial_bodies:
        body.draw(screen, camera_x, camera_y, camera_zoom, draw_trail=True)

    # Time display
    if FONT:
        speed_scale_factor = SIM_TIME_MULTIPLIER

        time_days = round(simulation_time, 2)
        time_years = round(time_days / 365.25, 2)

        time_display_text = [
            f"Days:    {time_days}",
            f"Years:   {time_years}",
            f"Speed:   {round(speed_scale_factor, 2)} days/sec"
        ]

        text_position = 20
        for line in time_display_text:
            text_surf = FONT.render(line, True, BLACK)
            text_rect = text_surf.get_rect(center=(70, text_position))
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (200, 200, 200), bg_rect)
            screen.blit(text_surf, text_rect)
            text_position += 25

    pygame.display.flip()

pygame.quit()