import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_alembic_upgrade_downgrade_sqlite(tmp_path):
    dbfile = tmp_path / "migration.db"
    url = f"sqlite+pysqlite:///{dbfile}"
    env = {**os.environ, "DATABASE_URL": url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "fe783411897f"],
        cwd=ROOT,
        check=True,
        env=env,
    )
