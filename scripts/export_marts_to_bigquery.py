"""Publica as tabelas do schema marts (já construídas pelo dbt) no BigQuery.

Não reprocessa SQL: lê cada tabela de marts.* do warehouse.duckdb, grava um
parquet temporário e faz load (WRITE_TRUNCATE) na tabela correspondente no
BigQuery. Rode depois de `docker compose run --rm dbt` (dbt build), que é
quem materializa as tabelas de marts no DuckDB.
"""

from __future__ import annotations

import os
import sys
import tempfile

import duckdb
from google.cloud import bigquery

WAREHOUSE_PATH = os.environ.get("WAREHOUSE_PATH", "/output/warehouse.duckdb")
GCP_PROJECT = os.environ.get("GCP_PROJECT")
BQ_DATASET = os.environ.get("BQ_DATASET", "agentic_cdp")


def main() -> int:
    if not GCP_PROJECT:
        print("GCP_PROJECT não definido.", file=sys.stderr)
        return 1

    con = duckdb.connect(WAREHOUSE_PATH, read_only=True)
    tables = [
        row[0]
        for row in con.execute(
            "select table_name from information_schema.tables where table_schema = 'marts' order by 1"
        ).fetchall()
    ]
    if not tables:
        print("Nenhuma tabela em marts.* — rode o dbt build antes.", file=sys.stderr)
        return 1

    bq = bigquery.Client(project=GCP_PROJECT)
    dataset_ref = bigquery.DatasetReference(GCP_PROJECT, BQ_DATASET)
    bq.create_dataset(bigquery.Dataset(dataset_ref), exists_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for table in tables:
            parquet_path = os.path.join(tmp_dir, f"{table}.parquet")
            con.execute(f"copy marts.{table} to '{parquet_path}' (format parquet)")

            table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{table}"
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
            with open(parquet_path, "rb") as f:
                job = bq.load_table_from_file(f, table_id, job_config=job_config)
            job.result()

            row_count = con.execute(f"select count(*) from marts.{table}").fetchone()[0]
            print(f"{table}: {row_count} linhas -> {table_id}", flush=True)

    print("Export concluído.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
