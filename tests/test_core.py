from app.core import init_database
from app.database import Base, engine
from app.models import Category, Product


def test_core_models_registered():
    assert Product.__tablename__ in Base.metadata.tables
    assert Category.__tablename__ in Base.metadata.tables


def test_database_initializes():
    init_database()
    assert "products" in Base.metadata.tables
    assert "categories" in Base.metadata.tables
    with engine.connect() as connection:
        assert connection is not None
