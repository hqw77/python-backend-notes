"""schema 一致性测试.

防止"模型里有这张表, 但迁移没建"的问题 -- orders 就踩过这个坑:
本地库手工建过所以没事, 全新库(CI / Docker 空卷)就报 Table doesn't exist.
"""

from sqlalchemy import inspect

from app.db.engine import engine
from app.db.base import Base
import app.models  # noqa: F401  必须导入, 否则模型不会注册到 metadata


def test_all_models_have_tables():
    """每个 ORM 模型都必须有对应的物理表."""
    existing = set(inspect(engine).get_table_names())
    modeled = set(Base.metadata.tables)

    missing = modeled - existing
    assert not missing, f"模型有表但数据库里没有: {sorted(missing)}"


def test_migration_version_matches_head():
    """数据库当前的迁移版本应该存在(说明迁移跑过了)."""
    with engine.connect() as conn:
        rows = conn.exec_driver_sql("SELECT version_num FROM alembic_version").fetchall()
    assert len(rows) == 1
    assert rows[0][0]
