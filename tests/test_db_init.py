"""
Regression test for a real bug: `scripts/init_db.py` printed success but
created zero tables, because SQLModel.metadata only knows about a table
class once it's been imported *somewhere*, and nothing imported
app.resume.models before create_all() ran.

This has to run in a genuinely fresh subprocess, not just call init_db()
from within the existing test session — by the time other test files in
this suite run, they've already imported app.resume.models themselves
(e.g. test_resume_repository.py does `from app.resume.models import
ResumeVersion` for its own fixtures), which would make init_db() "work"
in-process regardless of whether its own import is correct. A subprocess
is the only way to reproduce the exact conditions that caused the bug.
"""
import os
import subprocess
import sqlite3
import sys
import tempfile


def test_init_db_creates_tables_in_a_fresh_process():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}

        result = subprocess.run(
            [sys.executable, "-m", "scripts.init_db"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init_db failed: {result.stderr}"

        conn = sqlite3.connect(db_path)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        conn.close()

        assert "resume_versions" in tables, (
            f"resume_versions table was not created. Tables found: {tables}. "
            f"init_db stdout: {result.stdout}"
        )
        assert "job_postings" in tables, (
            f"job_postings table was not created. Tables found: {tables}. "
            f"init_db stdout: {result.stdout}"
        )