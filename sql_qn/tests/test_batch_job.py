import sqlite3
import unittest

from batch_job_sql import (
    CREATE_SCHEMA_SQL,
    EXECUTION_SEQUENCE_SQL,
    SAMPLE_DEPENDENCIES,
    SAMPLE_STEPS,
    setup_database,
    run_query,
)

class TestBatchJobSequencer(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        setup_database(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def _insert_custom_data(
        self,
        steps: list[tuple[int, int, str]],
        dependencies: list[tuple[int, int, int, int]],
    ) -> None:

        self.conn.execute("DELETE FROM steps")
        self.conn.execute("DELETE FROM dependencies")
        self.conn.executemany(
            "INSERT INTO steps (UNIT_NBR, STEP_SEQ_ID, STEP_PROG_NAME) VALUES (?, ?, ?)",
            steps,
        )
        self.conn.executemany(
            "INSERT INTO dependencies (UNIT_NBR, RULE_ID, STEP_SEQ_ID, STEP_DEP_ID) VALUES (?, ?, ?, ?)",
            dependencies,
        )
        self.conn.commit()

    def _levels(self) -> dict[int, int]:
        rows = run_query(self.conn)
        return {row["STEP_SEQ_ID"]: row["execution_level"] for row in rows}

    def test_sample_data_levels(self) -> None:
        levels = self._levels()
        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 2)
        self.assertEqual(levels[3], 3)
        self.assertEqual(levels[4], 3)
        self.assertEqual(levels[5], 4)
        self.assertEqual(levels[6], 4)
        self.assertEqual(levels[7], 4)
        self.assertEqual(levels[8], 4)
        self.assertEqual(levels[9], 4)
        self.assertEqual(levels[10], 5)
        self.assertEqual(levels[11], 6)
        self.assertEqual(levels[12], 7)
        self.assertEqual(levels[13], 8)

    def test_parallel_steps_same_level(self) -> None:
        levels = self._levels()
        self.assertEqual(levels[3], levels[4])
        self.assertEqual(len({levels[i] for i in range(5, 10)}), 1)

    def test_multiple_unit_nbrs(self) -> None:
        steps = [
            (1, 1, "A_START"),
            (1, 2, "A_MID"),
            (2, 1, "B_START"),
            (2, 2, "B_MID"),
        ]
        deps = [
            (1, 1, 1, 0),
            (1, 2, 2, 1),
            (2, 3, 1, 0),
            (2, 4, 2, 1),
        ]
        self._insert_custom_data(steps, deps)
        rows = run_query(self.conn)

        unit1 = [r for r in rows if r["UNIT_NBR"] == 1]
        unit2 = [r for r in rows if r["UNIT_NBR"] == 2]

        self.assertEqual(unit1[0]["execution_level"], 1)
        self.assertEqual(unit1[1]["execution_level"], 2)
        self.assertEqual(unit2[0]["execution_level"], 1)
        self.assertEqual(unit2[1]["execution_level"], 2)

    def test_step_with_no_dependency_entry(self) -> None:
        steps = [
            (1, 1, "ROOT"),
            (1, 99, "ORPHAN"),
        ]
        deps = [
            (1, 1, 1, 0),
        ]
        self._insert_custom_data(steps, deps)
        levels = self._levels()
        self.assertEqual(levels[99], 1)

    def test_single_step_no_dependencies(self) -> None:
        steps = [(1, 1, "ONLY_STEP")]
        deps = [(1, 1, 1, 0)]
        self._insert_custom_data(steps, deps)
        levels = self._levels()
        self.assertEqual(levels[1], 1)

    def test_linear_chain(self) -> None:
        steps = [
            (1, 1, "S1"),
            (1, 2, "S2"),
            (1, 3, "S3"),
        ]
        deps = [
            (1, 1, 1, 0),
            (1, 2, 2, 1),
            (1, 3, 3, 2),
        ]
        self._insert_custom_data(steps, deps)
        levels = self._levels()
        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 2)
        self.assertEqual(levels[3], 3)

    def test_diamond_dependency(self) -> None:
        steps = [
            (1, 1, "S1"),
            (1, 2, "S2"),
            (1, 3, "S3"),
            (1, 4, "S4"),
        ]
        deps = [
            (1, 1, 1, 0),
            (1, 2, 2, 1),
            (1, 3, 3, 1),
            (1, 4, 4, 2),
            (1, 5, 4, 3),
        ]
        self._insert_custom_data(steps, deps)
        levels = self._levels()
        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 2)
        self.assertEqual(levels[3], 2)
        self.assertEqual(levels[4], 3)

    def test_broken_dependency_chain(self) -> None:
        steps = [
            (1, 1, "S1"),
            (1, 2, "S2"),
        ]
        deps = [
            (1, 1, 1, 0),
            (1, 2, 2, 99),
        ]
        self._insert_custom_data(steps, deps)
        levels = self._levels()
        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 1)

    def test_result_row_structure(self) -> None:
        rows = run_query(self.conn)
        self.assertTrue(len(rows) > 0)
        for row in rows:
            self.assertIn("UNIT_NBR", row)
            self.assertIn("STEP_SEQ_ID", row)
            self.assertIn("STEP_PROG_NAME", row)
            self.assertIn("execution_level", row)

    def test_output_order(self) -> None:
        rows = run_query(self.conn)
        levels = [r["execution_level"] for r in rows]
        self.assertEqual(levels, sorted(levels))

if __name__ == "__main__":
    unittest.main()
