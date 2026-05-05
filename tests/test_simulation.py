import unittest

from auto_driving.simulation import Car, Direction, Field, Simulator

class TestDirection(unittest.TestCase):
    def test_turn_left(self) -> None:
        self.assertEqual(Direction.NORTH.turn_left(), Direction.WEST)
        self.assertEqual(Direction.WEST.turn_left(), Direction.SOUTH)
        self.assertEqual(Direction.SOUTH.turn_left(), Direction.EAST)
        self.assertEqual(Direction.EAST.turn_left(), Direction.NORTH)

    def test_turn_right(self) -> None:
        self.assertEqual(Direction.NORTH.turn_right(), Direction.EAST)
        self.assertEqual(Direction.EAST.turn_right(), Direction.SOUTH)
        self.assertEqual(Direction.SOUTH.turn_right(), Direction.WEST)
        self.assertEqual(Direction.WEST.turn_right(), Direction.NORTH)

    def test_move_delta(self) -> None:
        self.assertEqual(Direction.NORTH.move_delta(), (0, 1))
        self.assertEqual(Direction.SOUTH.move_delta(), (0, -1))
        self.assertEqual(Direction.EAST.move_delta(), (1, 0))
        self.assertEqual(Direction.WEST.move_delta(), (-1, 0))

class TestField(unittest.TestCase):
    def test_is_within_bounds(self) -> None:
        field = Field(width=10, height=10)
        self.assertTrue(field.is_within_bounds(0, 0))
        self.assertTrue(field.is_within_bounds(9, 9))
        self.assertTrue(field.is_within_bounds(5, 5))
        self.assertFalse(field.is_within_bounds(-1, 0))
        self.assertFalse(field.is_within_bounds(0, -1))
        self.assertFalse(field.is_within_bounds(10, 0))
        self.assertFalse(field.is_within_bounds(0, 10))

    def test_can_move_to(self) -> None:
        field = Field(width=10, height=10)
        car = Car(name="A", x=0, y=0, direction=Direction.SOUTH, commands="")
        self.assertFalse(field.can_move_to(car))
        car.direction = Direction.NORTH
        self.assertTrue(field.can_move_to(car))
        car.x = 9
        car.direction = Direction.EAST
        self.assertFalse(field.can_move_to(car))

class TestCar(unittest.TestCase):
    def test_move_forward(self) -> None:
        car = Car(name="A", x=1, y=2, direction=Direction.NORTH, commands="FFRFF")
        car.move_forward()
        self.assertEqual(car.current_position(), (1, 3))
        car.turn_right()
        car.move_forward()
        self.assertEqual(car.current_position(), (2, 3))

    def test_has_pending_commands(self) -> None:
        car = Car(name="A", x=0, y=0, direction=Direction.NORTH, commands="LR")
        self.assertTrue(car.has_pending_commands())
        car.advance_command()
        self.assertTrue(car.has_pending_commands())
        car.advance_command()
        self.assertFalse(car.has_pending_commands())

    def test_next_command(self) -> None:
        car = Car(name="A", x=0, y=0, direction=Direction.NORTH, commands="LR")
        self.assertEqual(car.next_command(), "L")
        car.advance_command()
        self.assertEqual(car.next_command(), "R")
        car.advance_command()
        self.assertIsNone(car.next_command())

class TestSimulator(unittest.TestCase):
    def test_single_car_no_collision(self) -> None:
        field = Field(width=10, height=10)
        car = Car(name="A", x=1, y=2, direction=Direction.NORTH, commands="FFRFFFFRRL")
        simulator = Simulator(field, [car])
        simulator.run()
        self.assertEqual(car.current_position(), (5, 4))
        self.assertEqual(car.direction, Direction.SOUTH)
        self.assertIsNone(car.collision_step)

    def test_boundary_ignored(self) -> None:
        field = Field(width=10, height=10)
        car = Car(name="A", x=0, y=0, direction=Direction.SOUTH, commands="F")
        simulator = Simulator(field, [car])
        simulator.run()
        self.assertEqual(car.current_position(), (0, 0))
        self.assertIsNone(car.collision_step)

    def test_multiple_cars_collision(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=1, y=2, direction=Direction.NORTH, commands="FFRFFFFRRL")
        car_b = Car(name="B", x=7, y=8, direction=Direction.WEST, commands="FFLFFFFFFF")
        simulator = Simulator(field, [car_a, car_b])
        simulator.run()

        self.assertFalse(car_a.is_active)
        self.assertFalse(car_b.is_active)
        self.assertEqual(car_a.collision_step, 7)
        self.assertEqual(car_b.collision_step, 7)
        self.assertEqual(car_a.collided_with, "B")
        self.assertEqual(car_b.collided_with, "A")
        self.assertEqual(car_a.current_position(), (5, 4))
        self.assertEqual(car_b.current_position(), (5, 4))

    def test_collision_stops_further_commands(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=1, y=1, direction=Direction.EAST, commands="FFF")
        car_b = Car(name="B", x=3, y=1, direction=Direction.WEST, commands="FF")
        simulator = Simulator(field, [car_a, car_b])
        simulator.run()

        self.assertEqual(car_a.collision_step, 1)
        self.assertEqual(car_b.collision_step, 1)
        self.assertEqual(car_a.current_position(), (2, 1))
        self.assertEqual(car_b.current_position(), (2, 1))

    def test_no_collision_final_positions(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=0, y=0, direction=Direction.NORTH, commands="FF")
        car_b = Car(name="B", x=5, y=5, direction=Direction.EAST, commands="FF")
        simulator = Simulator(field, [car_a, car_b])
        simulator.run()

        self.assertIsNone(car_a.collision_step)
        self.assertIsNone(car_b.collision_step)
        self.assertEqual(car_a.current_position(), (0, 2))
        self.assertEqual(car_b.current_position(), (7, 5))

    def test_cars_with_different_command_lengths(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=0, y=0, direction=Direction.NORTH, commands="F")
        car_b = Car(name="B", x=5, y=0, direction=Direction.NORTH, commands="FFF")
        simulator = Simulator(field, [car_a, car_b])
        simulator.run()

        self.assertEqual(car_a.current_position(), (0, 1))
        self.assertEqual(car_b.current_position(), (5, 3))

    def test_get_final_state_collision(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=1, y=1, direction=Direction.EAST, commands="FF")
        car_b = Car(name="B", x=3, y=1, direction=Direction.WEST, commands="F")
        simulator = Simulator(field, [car_a, car_b])
        simulator.run()

        final_state = simulator.get_final_state()
        self.assertEqual(
            final_state,
            [
                "A, collides with B at (2,1) at step 1",
                "B, collides with A at (2,1) at step 1",
            ],
        )

    def test_get_final_state_no_collision(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=1, y=2, direction=Direction.NORTH, commands="FFRFFFFRRL")
        simulator = Simulator(field, [car_a])
        simulator.run()

        final_state = simulator.get_final_state()
        self.assertEqual(final_state, ["A, (5,4) S"])

    def test_run_step_sequential(self) -> None:
        field = Field(width=10, height=10)
        car_a = Car(name="A", x=0, y=0, direction=Direction.EAST, commands="FF")
        car_b = Car(name="B", x=2, y=0, direction=Direction.WEST, commands="FF")
        simulator = Simulator(field, [car_a, car_b])

        step1_results = simulator.run_step()
        self.assertEqual(len(step1_results), 2)
        self.assertEqual(step1_results[0].car_name, "A")
        self.assertEqual(step1_results[1].car_name, "B")
        self.assertEqual(car_a.current_position(), (1, 0))
        self.assertEqual(car_b.current_position(), (1, 0))
        self.assertEqual(car_a.collision_step, 1)
        self.assertEqual(car_b.collision_step, 1)

if __name__ == "__main__":
    unittest.main()
