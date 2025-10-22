#!/usr/bin/env python3
"""
Ad-hoc test to verify project_workflow_steps state is saved per-project.

This script creates an isolated SQLite DB, seeds a Standard template with two
steps, creates two projects, seeds workflow steps into each project, toggles a
flag for the first project's first step, and verifies the second project's
steps remain unchanged.

Run: python test_workflow_persistence.py
"""

import os
import sqlite3
from datetime import datetime
from database_setup import DatabaseManager

TEST_DB = "test_workflow.db"


def debug_dump_project(conn, job_number):
    print(f"\n=== DUMP Project {job_number} ===")
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects WHERE job_number = ?", (job_number,))
    row = cur.fetchone()
    if not row:
        print("Project not found")
        return
    pid = row[0]
    cur.execute(
        """
        SELECT pws.id, pws.template_step_id, pws.order_index,
               pws.department, pws.title,
               pws.start_flag, pws.start_ts, pws.completed_flag, pws.completed_ts
        FROM project_workflow_steps pws
        WHERE pws.project_id = ?
        ORDER BY pws.order_index
        """,
        (pid,),
    )
    rows = cur.fetchall()
    if not rows:
        print("No steps")
        return
    for r in rows:
        print(
            f"id={r[0]} tmpl={r[1]} ord={r[2]} dept={r[3]} title={r[4]} start={r[5]} completed={r[7]}"
        )


def ensure_template(conn):
    cur = conn.cursor()
    # Create/activate Standard template version
    cur.execute(
        "SELECT id, version FROM workflow_templates WHERE name = 'Standard' ORDER BY version DESC LIMIT 1"
    )
    row = cur.fetchone()
    if row:
        tid = row[0]
    else:
        cur.execute(
            "INSERT INTO workflow_templates (name, version, is_active, created_date) VALUES (?, ?, 1, ?)",
            ("Standard", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        tid = cur.lastrowid
    # Activate this template
    cur.execute("UPDATE workflow_templates SET is_active = CASE WHEN id = ? THEN 1 ELSE 0 END", (tid,))
    # If no steps, add a couple
    cur.execute("SELECT COUNT(*) FROM workflow_template_steps WHERE template_id = ?", (tid,))
    if cur.fetchone()[0] == 0:
        cur.execute(
            """
            INSERT INTO workflow_template_steps (template_id, order_index, department, group_name, title, planned_duration_days)
            VALUES (?, 1, 'Drafting', 'Project Scheduling', 'Assignment', 1),
                   (?, 2, 'Drafting', 'Status', 'Check Project Status', 1)
            """,
            (tid, tid),
        )
    conn.commit()
    return tid


def seed_project_from_template(conn, job_number, template_id):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (job_number) VALUES (?)
        ON CONFLICT(job_number) DO NOTHING
        """,
        (job_number,),
    )
    cur.execute("SELECT id FROM projects WHERE job_number = ?", (job_number,))
    pid = cur.fetchone()[0]
    # Clear any existing steps
    cur.execute("DELETE FROM project_workflow_steps WHERE project_id = ?", (pid,))
    # Insert steps from template
    cur.execute(
        """
        SELECT id, order_index, department, group_name, title
        FROM workflow_template_steps WHERE template_id = ? ORDER BY order_index
        """,
        (template_id,),
    )
    for sid, order_i, dept, group, title in cur.fetchall():
        cur.execute(
            """
            INSERT INTO project_workflow_steps
            (project_id, template_id, template_step_id, order_index, department, group_name, title)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (pid, template_id, sid, order_i, dept, group, title),
        )
    conn.commit()
    return pid


def toggle_first_step_start(conn, job_number, value=True):
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects WHERE job_number = ?", (job_number,))
    pid = cur.fetchone()[0]
    cur.execute(
        "SELECT id FROM project_workflow_steps WHERE project_id = ? ORDER BY order_index LIMIT 1",
        (pid,),
    )
    sid = cur.fetchone()[0]
    cur.execute(
        "UPDATE project_workflow_steps SET start_flag = ?, start_ts = COALESCE(start_ts, ?) WHERE id = ?",
        (1 if value else 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sid),
    )
    conn.commit()
    return sid


def main():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Initialize test DB
    DatabaseManager(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    print(f"Using DB: {TEST_DB}")
    tid = ensure_template(conn)
    print(f"Active template id: {tid}")

    # Seed two projects
    pid_a = seed_project_from_template(conn, "11111", tid)
    pid_b = seed_project_from_template(conn, "22222", tid)
    print(f"Seeded projects: A={pid_a}, B={pid_b}")

    print("Initial state:")
    debug_dump_project(conn, "11111")
    debug_dump_project(conn, "22222")

    # Toggle first step for project A only
    sid = toggle_first_step_start(conn, "11111", True)
    print(f"Toggled start for project A step id={sid}")

    print("After toggle:")
    debug_dump_project(conn, "11111")
    debug_dump_project(conn, "22222")

    # Validate isolation
    cur = conn.cursor()
    cur.execute(
        """
        SELECT start_flag FROM project_workflow_steps
        WHERE project_id = (SELECT id FROM projects WHERE job_number = '22222')
        AND order_index = 1
        """
    )
    b_flag = cur.fetchone()[0]
    if b_flag != 0:
        raise SystemExit("ERROR: Project B was modified when toggling Project A!")
    print("OK: Project states are isolated.")


if __name__ == "__main__":
    main()

