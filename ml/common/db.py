"""Helper de conexão DuckDB para os scripts de treino em ml/.

Mesma convenção dos scripts em scripts/*.py: WAREHOUSE_PATH aponta pro
arquivo montado pelo docker-compose (default /output/warehouse.duckdb).
"""

from __future__ import annotations

import os

import duckdb

WAREHOUSE_PATH = os.environ.get("WAREHOUSE_PATH", "/output/warehouse.duckdb")


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(WAREHOUSE_PATH, read_only=read_only)
