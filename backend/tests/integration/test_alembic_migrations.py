from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_DIR = Path(__file__).resolve().parents[2]
INITIAL_REVISION = "0f1e2d3c4b5a"
FIRST_INCREMENTAL_REVISION = "48a22a87c5de"


def _script_directory() -> ScriptDirectory:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(config)


def test_alembic_history_has_single_base_and_head():
    script = _script_directory()

    assert script.get_bases() == [INITIAL_REVISION]
    assert script.get_heads() == ["e2f3a4b5c6d7"]


def test_empty_database_history_starts_with_schema_creating_revision():
    script = _script_directory()
    initial_revision = script.get_revision(INITIAL_REVISION)
    first_incremental_revision = script.get_revision(FIRST_INCREMENTAL_REVISION)

    assert initial_revision.down_revision is None
    assert first_incremental_revision.down_revision == INITIAL_REVISION

    initial_migration = Path(initial_revision.path).read_text(encoding="utf-8")
    assert 'op.create_table(\n        "users"' in initial_migration
    assert 'op.create_table(\n        "plaid_items"' in initial_migration
