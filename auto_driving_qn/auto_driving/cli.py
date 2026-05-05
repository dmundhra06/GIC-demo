import sys
from typing import Optional

from auto_driving.simulation import Car, Direction, Field, Simulator

class SimulationCLI:
    def __init__(self, input_stream=None, output_stream=None):
        self.input = input_stream or sys.stdin
        self.output = output_stream or sys.stdout
        self.field: Optional[Field] = None
        self.cars: list[Car] = []

    def _print(self, message: str = "") -> None:
        self.output.write(message + "\n")
        self.output.flush()

    def _prompt(self, message: str) -> str:
        self.output.write(message)
        self.output.flush()
        return self.input.readline().strip()

    def _parse_field_dimensions(self, line: str) -> Optional[Field]:
        parts = line.strip().split()
        if len(parts) != 2:
            self._print("Invalid input. Please enter two integers separated by a space.")
            return None
        try:
            width = int(parts[0])
            height = int(parts[1])
            if width <= 0 or height <= 0:
                self._print("Width and height must be positive integers.")
                return None
            return Field(width=width, height=height)
        except ValueError:
            self._print("Invalid input. Please enter valid integers.")
            return None

    def _parse_position(self, line: str, car_name: str) -> Optional[tuple[int, int, Direction]]:
        parts = line.strip().split()
        if len(parts) != 3:
            self._print(
                f"Invalid input. Please enter x, y, and direction for car {car_name}."
            )
            return None
        try:
            x = int(parts[0])
            y = int(parts[1])
            direction_str = parts[2].upper()
            if direction_str not in {"N", "S", "E", "W"}:
                self._print("Invalid direction. Please use N, S, E, or W.")
                return None
            direction = Direction(direction_str)
            return x, y, direction
        except ValueError:
            self._print("Invalid input. Please enter valid integers for position.")
            return None

    def _is_name_unique(self, name: str) -> bool:
        return all(car.name != name for car in self.cars)

    def _is_position_within_bounds(self, x: int, y: int) -> bool:
        if self.field is None:
            return False
        return self.field.is_within_bounds(x, y)

    def _is_position_occupied(self, x: int, y: int) -> bool:
        return any(car.x == x and car.y == y for car in self.cars)

    def _add_car(self) -> None:
        name = self._prompt("Please enter the name of the car:\n")
        if not name:
            self._print("Car name cannot be empty.")
            return
        if not self._is_name_unique(name):
            self._print(f"A car named '{name}' already exists. Please choose a different name.")
            return

        position_input = self._prompt(
            f"Please enter initial position of car {name} in x y Direction format:\n"
        )
        parsed = self._parse_position(position_input, name)
        if parsed is None:
            return
        x, y, direction = parsed

        if not self._is_position_within_bounds(x, y):
            self._print(
                f"Position ({x},{y}) is outside the field boundaries. "
                f"The field is {self.field.width} x {self.field.height}."
            )
            return

        if self._is_position_occupied(x, y):
            self._print(f"Position ({x},{y}) is already occupied by another car.")
            return

        commands = self._prompt(f"Please enter the commands for car {name}:\n")

        car = Car(
            name=name,
            x=x,
            y=y,
            direction=direction,
            commands=commands,
        )
        self.cars.append(car)
        self._print_current_cars()

    def _print_current_cars(self) -> None:
        self._print("Your current list of cars are:")
        for car in self.cars:
            self._print(f"- {car}, {car.commands}")

    def _run_simulation(self) -> None:
        if not self.cars:
            self._print("No cars to simulate. Please add at least one car.")
            return

        self._print_current_cars()
        self._print()

        simulator = Simulator(self.field, self.cars)
        simulator.run()

        self._print("After simulation, the result is:")
        for state in simulator.get_final_state():
            self._print(f"- {state}")

    def _post_simulation_menu(self) -> bool:
        self._print()
        self._print("Please choose from the following options:")
        self._print("[1] Start over")
        self._print("[2] Exit")

        choice = self._prompt("").strip()
        if choice == "1":
            self.cars.clear()
            self.field = None
            return True
        elif choice == "2":
            self._print("Thank you for running the simulation. Goodbye!")
            return False
        else:
            self._print("Invalid option. Please enter 1 or 2.")
            return self._post_simulation_menu()

    def _main_menu(self) -> bool:
        self._print("Please choose from the following options:")
        self._print("[1] Add a car to field")
        self._print("[2] Run simulation")

        choice = self._prompt("").strip()
        if choice == "1":
            self._add_car()
            return True
        elif choice == "2":
            self._run_simulation()
            return self._post_simulation_menu()
        else:
            self._print("Invalid option. Please enter 1 or 2.")
            return True

    def run(self) -> None:
        while True:
            self._print("Welcome to Auto Driving Car Simulation!")
            self._print()

            field_input = self._prompt(
                "Please enter the width and height of the simulation field in x y format:\n"
            )
            self.field = self._parse_field_dimensions(field_input)
            if self.field is None:
                continue

            self._print(f"You have created a field of {self.field.width} x {self.field.height}.")
            self._print()

            while True:
                if not self._main_menu():
                    return
                if self.field is None:
                    break

def main() -> None:
    cli = SimulationCLI()
    cli.run()

if __name__ == "__main__":
    main()
