DROP TABLE IF EXISTS steps;
DROP TABLE IF EXISTS dependencies;

CREATE TABLE steps (
    UNIT_NBR       INTEGER NOT NULL,
    STEP_SEQ_ID    INTEGER NOT NULL,
    STEP_PROG_NAME TEXT    NOT NULL,
    PRIMARY KEY (UNIT_NBR, STEP_SEQ_ID)
);

CREATE TABLE dependencies (
    UNIT_NBR    INTEGER NOT NULL,
    RULE_ID     INTEGER NOT NULL,
    STEP_SEQ_ID INTEGER NOT NULL,
    STEP_DEP_ID INTEGER NOT NULL,
    PRIMARY KEY (UNIT_NBR, RULE_ID)
);

INSERT INTO steps (UNIT_NBR, STEP_SEQ_ID, STEP_PROG_NAME) VALUES
(1,  1, 'PKGIDS_CMMN_UTILITY.PROCIDS_JOB_START'),
(1,  2, 'pkgids_ptf_hrchy_processing.Procids_delete_job_set_nbr'),
(1,  3, 'PKGIDS_PTF_EXTR.ext_static_ptf_table'),
(1,  4, 'PKGIDS_PTF_EXTR.ext_eff_ptf_table'),
(1,  5, 'pkgids_ptf_hrchy_processing.procids_get_tree_a'),
(1,  6, 'pkgids_ptf_hrchy_processing.procids_get_tree_b'),
(1,  7, 'pkgids_ptf_hrchy_processing.procids_get_tree_c'),
(1,  8, 'pkgids_ptf_hrchy_processing.procids_get_tree_d'),
(1,  9, 'pkgids_ptf_hrchy_processing.procids_get_tree_e'),
(1, 10, 'pkgids_ptf_hrchy_processing.procids_get_active_portf'),
(1, 11, 'pkgids_ptf_lineage.procids_process_ptf_lineage'),
(1, 12, 'pkgids_ptf_lineage.procids_summary_to_bookable_rs'),
(1, 13, 'PKGIDS_CMMN_UTILITY.PROCIDS_JOB_END');

INSERT INTO dependencies (UNIT_NBR, RULE_ID, STEP_SEQ_ID, STEP_DEP_ID) VALUES
(1,  1,  1, 0),
(1,  2,  2, 1),
(1,  3,  3, 2),
(1,  4,  4, 2),
(1,  5,  5, 3),
(1,  6,  5, 4),
(1,  7,  6, 3),
(1,  8,  6, 4),
(1,  9,  7, 3),
(1, 10,  7, 4),
(1, 11,  8, 3),
(1, 12,  9, 3),
(1, 13,  8, 4),
(1, 14,  9, 4),
(1, 15, 10, 5),
(1, 16, 10, 6),
(1, 17, 10, 7),
(1, 18, 10, 8),
(1, 19, 10, 9),
(1, 20, 11, 10),
(1, 21, 12, 11),
(1, 22, 13, 12);

WITH RECURSIVE execution_paths AS (

    SELECT
        d.UNIT_NBR,
        d.STEP_SEQ_ID,
        1 AS path_level
    FROM dependencies d
    WHERE d.STEP_DEP_ID = 0

    UNION ALL

    SELECT
        d.UNIT_NBR,
        d.STEP_SEQ_ID,
        ep.path_level + 1
    FROM dependencies d
    INNER JOIN execution_paths ep
        ON d.UNIT_NBR = ep.UNIT_NBR
        AND d.STEP_DEP_ID = ep.STEP_SEQ_ID
),
step_levels AS (

    SELECT
        UNIT_NBR,
        STEP_SEQ_ID,
        MAX(path_level) AS execution_level
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
