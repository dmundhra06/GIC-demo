from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"

    def turn_left(self) -> "Direction":
        mapping = {
            Direction.NORTH: Direction.WEST,
            Direction.WEST: Direction.SOUTH,
            Direction.SOUTH: Direction.EAST,
            Direction.EAST: Direction.NORTH,
        }
        return mapping[self]

    def turn_right(self) -> "Direction":
        mapping = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH,
        }
        return mapping[self]

    def move_delta(self) -> tuple[int, int]:
        mapping = {
            Direction.NORTH: (0, 1),
            Direction.SOUTH: (0, -1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0),
        }
        return mapping[self]

@dataclass
class Car:
    name: str
    x: int
    y: int
    direction: Direction
    commands: str
    command_index: int = 0
    is_active: bool = True
    collision_step: Optional[int] = None
    collided_with: Optional[str] = None

    def current_position(self) -> tuple[int, int]:
        return self.x, self.y

    def has_pending_commands(self) -> bool:
        return self.command_index < len(self.commands)

    def next_command(self) -> Optional[str]:
        if self.command_index < len(self.commands):
            return self.commands[self.command_index]
        return None

    def advance_command(self) -> None:
        self.command_index += 1

    def turn_left(self) -> None:
        self.direction = self.direction.turn_left()

    def turn_right(self) -> None:
        self.direction = self.direction.turn_right()

    def move_forward(self) -> None:
        dx, dy = self.direction.move_delta()
        self.x += dx
        self.y += dy

    def __str__(self) -> str:
        return f"{self.name}, ({self.x},{self.y}) {self.direction.value}"

@dataclass
class SimulationResult:
    step: int
    car_name: str
    action: str
    old_position: tuple[int, int]
    new_position: tuple[int, int]
    collided_with: Optional[str] = None

@dataclass
class Field:
    width: int
    height: int

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def can_move_to(self, car: Car) -> bool:
        dx, dy = car.direction.move_delta()
        new_x = car.x + dx
        new_y = car.y + dy
        return self.is_within_bounds(new_x, new_y)

class Simulator:
    def __init__(self, field: Field, cars: list[Car]):
        self.field = field
        self.cars = cars
        self.step = 0
        self.results: list[SimulationResult] = []

    def _get_active_cars(self) -> list[Car]:
        return [car for car in self.cars if car.is_active]

    def _positions_dict(self) -> dict[tuple[int, int], list[Car]]:
        positions: dict[tuple[int, int], list[Car]] = {}
        for car in self.cars:
            pos = car.current_position()
            positions.setdefault(pos, []).append(car)
        return positions

    def _check_collisions(self) -> list[tuple[Car, Car]]:
        collisions: list[tuple[Car, Car]] = []
        positions = self._positions_dict()
        for pos, cars_at_pos in positions.items():
            if len(cars_at_pos) > 1:
                for i in range(len(cars_at_pos)):
                    for j in range(i + 1, len(cars_at_pos)):
                        collisions.append((cars_at_pos[i], cars_at_pos[j]))
        return collisions

    def _resolve_collisions(self) -> None:
        collisions = self._check_collisions()
        for car_a, car_b in collisions:
            if car_a.is_active:
                car_a.is_active = False
                car_a.collision_step = self.step
                car_a.collided_with = car_b.name
            if car_b.is_active:
                car_b.is_active = False
                car_b.collision_step = self.step
                car_b.collided_with = car_a.name

    def _process_single_command(self, car: Car) -> SimulationResult:
        old_pos = car.current_position()
        cmd = car.next_command()

        if cmd is None:
            return SimulationResult(
                step=self.step,
                car_name=car.name,
                action="idle",
                old_position=old_pos,
                new_position=old_pos,
            )

        car.advance_command()

        if cmd == "L":
            car.turn_left()
        elif cmd == "R":
            car.turn_right()
        elif cmd == "F":
            if self.field.can_move_to(car):
                car.move_forward()
            else:
                return SimulationResult(
                    step=self.step,
                    car_name=car.name,
                    action="F-ignored",
                    old_position=old_pos,
                    new_position=old_pos,
                )
        else:
            return SimulationResult(
                step=self.step,
                car_name=car.name,
                action=f"invalid-{cmd}",
                old_position=old_pos,
                new_position=old_pos,
            )

        return SimulationResult(
            step=self.step,
            car_name=car.name,
            action=cmd,
            old_position=old_pos,
            new_position=car.current_position(),
        )

    def run_step(self) -> list[SimulationResult]:
        self.step += 1
        step_results: list[SimulationResult] = []
        active_cars = self._get_active_cars()

        for car in active_cars:
            if not car.has_pending_commands():
                continue
            result = self._process_single_command(car)
            step_results.append(result)

        self._resolve_collisions()
        self.results.extend(step_results)
        return step_results

    def run(self) -> list[SimulationResult]:
        max_steps = max((len(car.commands) for car in self.cars), default=0)
        for _ in range(max_steps):
            active_cars_with_commands = [
                car for car in self._get_active_cars() if car.has_pending_commands()
            ]
            if not active_cars_with_commands:
                break
            self.run_step()
        return self.results

    def get_final_state(self) -> list[str]:
        output: list[str] = []
        for car in self.cars:
            if car.collision_step is not None:
                output.append(
                    f"{car.name}, collides with {car.collided_with} at "
                    f"({car.x},{car.y}) at step {car.collision_step}"
                )
            else:
                output.append(f"{car.name}, ({car.x},{car.y}) {car.direction.value}")
        return output
