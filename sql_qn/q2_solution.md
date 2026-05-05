# Batch Job Dependency Sequencer (Q2 Solution)

## Problem Summary

Determine the correct execution sequence of stored procedures in a batch job based on dependency rules. Each step (`STEP_SEQ_ID`) may depend on one or more other steps (`STEP_DEP_ID`). Steps that share the same execution level may run in parallel.

## SQL Solution

The core algorithm uses a **recursive common table expression (CTE)** to compute the length of the longest dependency chain from any root step to each target step. This length becomes the `execution_level` — a numeric wave indicating when the step can run.

### Files

- `batch_job.sql` — Standalone SQL file with schema, sample data, and the recursive CTE query.
- `batch_job_sql.py` — Python/SQLite runner that executes the SQL and pretty-prints results.
- `tests/test_batch_job.py` — 10 unit tests covering sample data, edge cases, and multi-unit scenarios.

### How to Run

```bash
# View the raw SQL
sqlite3 < batch_job.sql

# Or run the Python demonstration
python batch_job_sql.py

# Run tests
python -m unittest tests.test_batch_job -v
```

### Key SQL Query

```sql
WITH RECURSIVE execution_paths AS (
    -- Base case: root steps (STEP_DEP_ID = 0)
    SELECT d.UNIT_NBR, d.STEP_SEQ_ID, 1 AS path_level
    FROM dependencies d
    WHERE d.STEP_DEP_ID = 0

    UNION ALL

    -- Recursive: follow dependency edges
    SELECT d.UNIT_NBR, d.STEP_SEQ_ID, ep.path_level + 1
    FROM dependencies d
    INNER JOIN execution_paths ep
        ON d.UNIT_NBR = ep.UNIT_NBR
        AND d.STEP_DEP_ID = ep.STEP_SEQ_ID
),
step_levels AS (
    -- Keep the longest chain (MAX) for each step
    SELECT UNIT_NBR, STEP_SEQ_ID, MAX(path_level) AS execution_level
    FROM execution_paths
    GROUP BY UNIT_NBR, STEP_SEQ_ID
)
SELECT
    s.UNIT_NBR,
    s.STEP_SEQ_ID,
    s.STEP_PROG_NAME,
    COALESCE(sl.execution_level, 1) AS execution_level
FROM steps s
LEFT JOIN step_levels sl
    ON s.UNIT_NBR = sl.UNIT_NBR
    AND s.STEP_SEQ_ID = sl.STEP_SEQ_ID
ORDER BY execution_level, s.STEP_SEQ_ID;
```

### Sample Output

| UNIT_NBR | STEP_SEQ_ID | EXEC_LEVEL | STEP_PROG_NAME |
|----------|-------------|------------|----------------|
| 1 | 1 | 1 | PKGIDS_CMMN_UTILITY.PROCIDS_JOB_START |
| 1 | 2 | 2 | pkgids_ptf_hrchy_processing.Procids_delete_job_set_nbr |
| 1 | 3 | 3 | PKGIDS_PTF_EXTR.ext_static_ptf_table |
| 1 | 4 | 3 | PKGIDS_PTF_EXTR.ext_eff_ptf_table |
| 1 | 5 | 4 | pkgids_ptf_hrchy_processing.procids_get_tree_a |
| 1 | 6 | 4 | pkgids_ptf_hrchy_processing.procids_get_tree_b |
| 1 | 7 | 4 | pkgids_ptf_hrchy_processing.procids_get_tree_c |
| 1 | 8 | 4 | pkgids_ptf_hrchy_processing.procids_get_tree_d |
| 1 | 9 | 4 | pkgids_ptf_hrchy_processing.procids_get_tree_e |
| 1 | 10 | 5 | pkgids_ptf_hrchy_processing.procids_get_active_portf |
| 1 | 11 | 6 | pkgids_ptf_lineage.procids_process_ptf_lineage |
| 1 | 12 | 7 | pkgids_ptf_lineage.procids_summary_to_bookable_rs |
| 1 | 13 | 8 | PKGIDS_CMMN_UTILITY.PROCIDS_JOB_END |

Steps with the same `execution_level` (e.g., 3, 4) are safe to run in parallel.

## Assumptions

1. **No cycles:** The dependency graph is a directed acyclic graph (DAG). Cyclic dependencies would cause the recursive CTE to exhaust SQLite's default recursion limit.
2. **At least one root per unit:** Every `UNIT_NBR` has at least one step with `STEP_DEP_ID = 0`.
3. **All steps are reachable:** Every step in the `steps` table can be reached from a root via dependency chains. If a step has a broken dependency (depends on a non-existent step), it receives a default `execution_level` of `1`.
4. **No duplicate rules:** `(UNIT_NBR, RULE_ID)` is unique in the `dependencies` table.
5. **Single database execution context:** The SQL is written for SQLite (standard SQL- compatible) but uses `COALESCE` and recursive CTEs that are broadly supported.

## Gaps & Areas for Improvement

- **Cycle detection:** Add a `CYCLE` clause (or equivalent path-tracking) to detect and raise an error for circular dependencies rather than silently hitting a recursion limit.
- **Cross-unit dependencies:** The current query isolates each `UNIT_NBR`. If a step in unit A could depend on a step in unit B, the join predicate would need adjustment.
- **Estimated runtime metadata:** Augment the output with historical average duration per `STEP_PROG_NAME` to enable critical-path scheduling.
- **Incremental/retry logic:** In production, failed steps may need to be retried without re-running already-completed downstream steps. A `status` and `last_run_timestamp` column would support this.
- **Parallel-group formatting:** The output could be pivoted or grouped to explicitly list which steps belong to each parallel wave.
