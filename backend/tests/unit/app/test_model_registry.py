from sqlalchemy.orm import configure_mappers

from src.modules.model_registry import load_all_models


def test_load_all_models_registers_relationship_targets():
    load_all_models()

    configure_mappers()
