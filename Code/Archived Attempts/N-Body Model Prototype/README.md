# Solar System N-Body Simulator

## Educational Physics Tool for GCSE and A-Level Students

### Overview
This Python program creates an interactive N-body gravity simulation that allows students to explore orbital mechanics, gravitational interactions, and celestial body dynamics in real-time.

### Features
- **Real-time N-body gravitational physics** using Newton's Inverse Square Law
- **Customisable celestial bodies** with adjustable mass, position, and velocity
- **Collision detection and handling** between bodies
- **Save/Load simulation states** to/from JSON files
- **Interactive camera controls** (zoom, pan)
- **Simulation speed control**
- **Visual trails** showing orbital paths
- **FPS monitoring** for performance awareness

### Physics Concepts Covered
- Gravitational force (Newton's Law of Universal Gravitation)
- Orbital mechanics and stability
- Centripetal force balance
- Numerical integration (Euler method)
- Vector mathematics
- Conservation of momentum (collisions)

### Requirements
- Python 3.x
- Pygame library

### Installation
```bash
pip install pygame
```

### Running the Simulator
```bash
python solar_system_simulator.py
```

### Controls
| Key/Action | Function |
|------------|----------|
| SPACE | Pause/Resume simulation |
| + / = | Increase simulation speed |
| - | Decrease simulation speed |
| Mouse Scroll | Zoom In/Out |
| Right-Click Drag | Pan camera |
| R | Reset to default solar system |
| T | Toggle orbital trails |
| L | Toggle body labels |
| V | Toggle velocity vectors |
| S | Save simulation to JSON |
| O | Load simulation from JSON |
| A | Add random body |
| C | Clear all bodies |
| Left-Click | Select body (view properties) |
| ESC | Quit application |

### Images Folder
Place planet images in the `Images` folder with the naming convention:
- `Sun.png`
- `Mercury.png`
- `Venus.png`
- `Earth.png`
- `Mars.png`
- `Jupiter.png`
- `Saturn.png`
- `Uranus.png`
- `Neptune.png`
- `Moon.png`

Note: Image names should have the first letter capitalised (e.g., "Sun.png", not "sun.png").

Images should be in PNG format with transparency support.

### Computational Methods Used

1. **Numerical Integration (Euler Method)**
   - Divides continuous time into discrete steps (dt)
   - Updates velocity: v(t+dt) = v(t) + a(t) × dt
   - Updates position: x(t+dt) = x(t) + v(t) × dt

2. **Force Calculation**
   - Newton's Law of Universal Gravitation: F = G × m₁ × m₂ / r²
   - O(N²) complexity for N-body interactions
   - Decomposition into unique pairwise calculations

3. **Collision Detection**
   - Pairwise distance checks
   - Conservation of momentum for merging

4. **Data Persistence**
   - JSON serialization for save/load functionality

### File Structure
```
SolarSystemSimulator/
├── solar_system_simulator.py   # Main simulation code
├── Images/                     # Planet images folder
│   ├── sun.png
│   ├── earth.png
│   └── ... (other planets)
├── saved_simulation.json       # Saved simulation state
└── README.md                   # This file
```

### Educational Value
This simulation addresses the gap in educational physics tools by providing:
- Interactive experimentation not possible with static diagrams
- Visualisation of abstract concepts (gravity, orbits, momentum)
- Customisable scenarios for exploring physics principles
- Real-time feedback on how changes affect orbital stability
