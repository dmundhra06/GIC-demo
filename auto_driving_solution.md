# Auto Driving Car Simulation

A command-line simulation program for autonomous driving cars on a rectangular field.

## Requirements

- Python 3.9 or higher

No external dependencies are required; the project uses only the Python standard library.

## How to Run

### Run the Simulation (Interactive Mode)

```bash
python main.py
```

Follow the on-screen prompts to:
1. Set the field dimensions (width height)
2. Add one or more cars with name, initial position, direction, and commands
3. Run the simulation

### Run the Tests

```bash
python -m unittest discover -v tests/
```

Or run a specific test file:

```bash
python -m unittest tests.test_simulation -v
python -m unittest tests.test_cli -v
```

## Commands

Each car accepts a sequence of commands:
- **L** – Rotate 90 degrees to the left
- **R** – Rotate 90 degrees to the right
- **F** – Move forward by 1 grid point

If a forward command would move a car outside the field boundaries, that command is ignored.

## Multi-Car Simulation & Collisions

When multiple cars are present, commands are processed **sequentially** per step:
- At step 1, car A processes its next command, then car B processes its next command, and so on.
- If two or more cars occupy the same grid point after any sub-step within a simulation step, they are marked as collided.
- Collided cars immediately stop processing further commands.

## Assumptions

1. The field lower-left coordinate is `(0, 0)` and the upper-right coordinate is `(width-1, height-1)`. For example, a `10 x 10` field spans `(0, 0)` to `(9, 9)`.
2. Valid directions are **N** (North), **S** (South), **E** (East), and **W** (West).
3. Car names must be unique within a single simulation run.
4. Cars cannot be placed on an already occupied position.
5. Only one command is processed per car per simulation step, in the order the cars were added.
6. Invalid commands (anything other than `L`, `R`, or `F`) are silently skipped.

## Areas for Improvement

- **File-based input/output:** Support reading simulation configurations from a file and writing results to a file.
- **Visualization:** Add ASCII or graphical rendering of the field and car positions over time.
- **More robust collision detection:** Support cars "crossing paths" (swapping positions in the same step) as a collision scenario.
- **Obstacles:** Add static or dynamic obstacles on the field.
- **Speed commands:** Support variable step sizes or speed modifiers.
