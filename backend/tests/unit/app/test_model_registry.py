from sqlalchemy.orm import configure_mappers

from src.infrastructure.db import Base
from src.modules.model_registry import load_all_models


def test_load_all_models_registers_relationship_targets():
    load_all_models()

    configure_mappers()


def test_registered_models_do_not_reference_missing_tables():
    load_all_models()

    missing_targets = []
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            try:
                foreign_key.column
            except Exception as exc:  # pragma: no cover - assertion message path
                missing_targets.append(
                    f"{table.name}.{foreign_key.parent.name} -> "
                    f"{foreign_key.target_fullname}: {exc}"
                )

    assert missing_targets == []
