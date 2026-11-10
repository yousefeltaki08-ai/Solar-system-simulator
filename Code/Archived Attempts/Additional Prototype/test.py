class Planet:
    # Changed 'color' parameter to 'image_file' string
    def __init__(self, name, image_file, distance, size, speed):
        self.name = name
        self.distance = distance
        # Ensure minimum size for visibility and store base size
        self.base_size = max(4, int(size))
        self.angle = 0.0
        # now interpret speed as degrees per simulation second (will be multiplied by dt)
        self.speed = float(speed)

        # NEW CODE: Load the initial image surface using the helper function
        # load original image (keep full resolution if available) and prepare cache
        orig = load_image_and_scale(image_file, None)  # pass None to get original size (see load helper below)
        self.original_image = orig  # may be None if file missing
        # create a small initial scaled image for default draw size (but don't overwrite original)
        if orig is not None:
            self.image = pygame.transform.smoothscale(orig, (self.base_size, self.base_size))
        else:
            self.image = None
        # cache for scaled images keyed by size (int)
        self._scaled_cache = {}

        self.image_file = image_file # Store the filename for dynamic scaling later

        # world coordinates (relative to sun at origin)
        self.x = 0.0
        self.y = 0.0

        # initialize position (call with dt=0)
        # call the class method (works because method is defined at class level)
        self.update_position(0.0, 1.0)

    def update_position(self, dt=None, time_multiplier=None):
        if dt is None:
            # legacy behaviour (degrees per frame)
            self.angle = (self.angle + self.speed) % 360.0
        else:
            if time_multiplier is None:
                time_multiplier = globals().get('SIM_TIME_MULTIPLIER', 1.0)
            # advance angle in degrees using simulated seconds = dt * time_multiplier
            self.angle = (self.angle + self.speed * dt * time_multiplier) % 360.0

        # compute world coords from angle and distance (sun at origin)
        theta = math.radians(self.angle)
        self.x = math.cos(theta) * self.distance
        self.y = math.sin(theta) * self.distance

    def draw(self, screen, cam_x, cam_y, zoom):
        # compute desired draw size
        desired_size = max(2, int(self.base_size * zoom))

        # world -> screen coords
        # Compute screen position based on camera center (camera_x, camera_y) and zoom
        sx = int(WIDTH // 2 + (self.x - cam_x) * zoom)
        sy = int(HEIGHT // 2 + (self.y - cam_y) * zoom)


        if desired_size < 1:
            return

        # choose source to scale from
        source = getattr(self, 'original_image', None) or self.image

        if source is not None:
            # if we have a cache entry, use it
            cached = self._scaled_cache.get(desired_size)
            if cached is None:
                # avoid scaling *above* the original size too much — it'll look blurry.
                # If source has a native size, prefer scaling from that using smoothscale.
                src_w = source.get_width()
                # If desired_size exceeds original width, we still smoothscale but note blurriness.
                try:
                    scaled = pygame.transform.smoothscale(source, (desired_size, desired_size))
                except Exception:
                    # fallback to transform.scale if smoothscale fails
                    scaled = pygame.transform.scale(source, (desired_size, desired_size))
                self._scaled_cache[desired_size] = scaled
                cached = scaled

            img_rect = cached.get_rect(center=(sx, sy))
            screen.blit(cached, img_rect)
        else:
            # no image available: fallback circle
            pygame.draw.circle(screen, YELLOW,
                   (int(WIDTH // 2 - camera_x * camera_zoom),int(HEIGHT // 2 - camera_y * camera_zoom)),int(15 * camera_zoom))

        # draw name tag as before
        try:
            self.name_tag_draw(screen, sx, sy, desired_size)
        except Exception:
            pass

    def name_tag_draw(self, screen, sx, sy, size):
        # Draw a small label under the planet if a font is available; otherwise do nothing.
        font = globals().get('FONT', None)
        if not font:
            return
        try:
            text_surf = font.render(self.name, True, WHITE)
            text_rect = text_surf.get_rect(center=(sx, sy + size//2 + 10))
            bg_rect = text_rect.inflate(4, 2)
            pygame.draw.rect(screen, BLACK, bg_rect)
            screen.blit(text_surf, text_rect)
        except Exception:
            # silently ignore rendering errors
            return
    def speed_up(self):
        self.speed = self.speed * 1.1

    def speed_down(self):
        self.speed = self.speed * 0.9090909091
