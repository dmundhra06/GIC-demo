import io
import unittest

from auto_driving.cli import SimulationCLI
from auto_driving.simulation import Direction

class TestSimulationCLI(unittest.TestCase):
    def _create_cli(self, inputs: list[str]) -> tuple[SimulationCLI, io.StringIO]:
        input_stream = io.StringIO("\n".join(inputs) + "\n")
        output_stream = io.StringIO()
        cli = SimulationCLI(input_stream=input_stream, output_stream=output_stream)
        return cli, output_stream

    def test_parse_field_dimensions_valid(self) -> None:
        cli, _ = self._create_cli([])
        field = cli._parse_field_dimensions("10 10")
        self.assertIsNotNone(field)
        self.assertEqual(field.width, 10)
        self.assertEqual(field.height, 10)

    def test_parse_field_dimensions_invalid(self) -> None:
        cli, out = self._create_cli([])
        field = cli._parse_field_dimensions("abc")
        self.assertIsNone(field)
        self.assertIn("Invalid input", out.getvalue())

    def test_parse_field_dimensions_zero(self) -> None:
        cli, out = self._create_cli([])
        field = cli._parse_field_dimensions("0 10")
        self.assertIsNone(field)
        self.assertIn("positive integers", out.getvalue())

    def test_parse_position_valid(self) -> None:
        cli, _ = self._create_cli([])
        result = cli._parse_position("1 2 N", "A")
        self.assertIsNotNone(result)
        x, y, direction = result
        self.assertEqual(x, 1)
        self.assertEqual(y, 2)
        self.assertEqual(direction, Direction.NORTH)

    def test_parse_position_invalid_direction(self) -> None:
        cli, out = self._create_cli([])
        result = cli._parse_position("1 2 X", "A")
        self.assertIsNone(result)
        self.assertIn("Invalid direction", out.getvalue())

    def test_is_name_unique(self) -> None:
        cli, _ = self._create_cli([])
        self.assertTrue(cli._is_name_unique("A"))
        cli.cars.append(
            type("Car", (), {"name": "A", "x": 0, "y": 0, "direction": Direction.NORTH, "commands": ""})()
        )
        self.assertFalse(cli._is_name_unique("A"))

    def test_full_flow_single_car(self) -> None:
        inputs = [
            "10 10",
            "1",
            "A",
            "1 2 N",
            "FFRFFFFRRL",
            "2",
            "2",
        ]
        cli, out = self._create_cli(inputs)
        cli.run()
        output = out.getvalue()
        self.assertIn("You have created a field of 10 x 10", output)
        self.assertIn("A, (1,2) N, FFRFFFFRRL", output)
        self.assertIn("After simulation, the result is:", output)
        self.assertIn("A, (5,4) S", output)
        self.assertIn("Thank you for running the simulation", output)

    def test_full_flow_multiple_cars_collision(self) -> None:
        inputs = [
            "10 10",
            "1",
            "A",
            "1 2 N",
            "FFRFFFFRRL",
            "1",
            "B",
            "7 8 W",
            "FFLFFFFFFF",
            "2",
            "2",
        ]
        cli, out = self._create_cli(inputs)
        cli.run()
        output = out.getvalue()
        self.assertIn("A, collides with B at (5,4) at step 7", output)
        self.assertIn("B, collides with A at (5,4) at step 7", output)

    def test_full_flow_start_over(self) -> None:
        inputs = [
            "10 10",
            "1",
            "A",
            "1 2 N",
            "FF",
            "2",
            "1",
            "5 5",
            "2",
            "2",
        ]
        cli, out = self._create_cli(inputs)
        cli.run()
        output = out.getvalue()
        self.assertIn("Welcome to Auto Driving Car Simulation!", output)
        count = output.count("Welcome to Auto Driving Car Simulation!")
        self.assertEqual(count, 2)

    def test_add_car_out_of_bounds(self) -> None:
        inputs = [
            "A",
            "15 15 N",
        ]
        cli, out = self._create_cli(inputs)
        cli.field = cli._parse_field_dimensions("10 10")
        cli._add_car()
        output = out.getvalue()
        self.assertIn("outside the field boundaries", output)

    def test_add_car_occupied_position(self) -> None:
        from auto_driving.simulation import Car

        inputs = [
            "B",
            "1 2 W",
        ]
        cli, out = self._create_cli(inputs)
        cli.field = cli._parse_field_dimensions("10 10")
        cli.cars.append(
            Car(name="A", x=1, y=2, direction=Direction.NORTH, commands="")
        )
        cli._add_car()
        output = out.getvalue()
        self.assertIn("already occupied", output)

    def test_run_simulation_no_cars(self) -> None:
        inputs = [
            "10 10",
            "2",
            "2",
        ]
        cli, out = self._create_cli(inputs)
        cli.run()
        output = out.getvalue()
        self.assertIn("No cars to simulate", output)

if __name__ == "__main__":
    unittest.main()
