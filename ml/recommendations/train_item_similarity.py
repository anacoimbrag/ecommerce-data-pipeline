"""Vitrine inteligente personalizada (caso de uso 3) — similaridade de produto.

Lê feature.feat_customer_product_interactions (matriz implícita cliente x
produto), calcula cosine similarity produto x produto sobre essa matriz
esparsa, e grava só o top-K de vizinhos mais similares por produto em
raw.product_similarity. O ranking por cliente (combinando isso com
product_affinity e o fallback content-based) é feito em SQL, em
transform/models/activation/customer_showcase.sql.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db import connect  # noqa: E402

TOP_K = int(os.environ.get("SIMILARITY_TOP_K", "10"))


def main() -> int:
    con = connect()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    rows = con.execute("""
        SELECT customer_id, product_id, interaction_weight
        FROM feature.feat_customer_product_interactions
    """).fetchall()

    if not rows:
        print("feat_customer_product_interactions está vazia — nada a treinar.", file=sys.stderr)
        return 1

    customer_ids = sorted({r[0] for r in rows})
    product_ids = sorted({r[1] for r in rows})
    customer_idx = {c: i for i, c in enumerate(customer_ids)}
    product_idx = {p: i for i, p in enumerate(product_ids)}

    data = [float(r[2]) for r in rows]
    row_idx = [customer_idx[r[0]] for r in rows]
    col_idx = [product_idx[r[1]] for r in rows]
    matrix = csr_matrix((data, (row_idx, col_idx)), shape=(len(customer_ids), len(product_ids)))

    # produto x produto: transpõe pra linhas = produtos, colunas = clientes
    similarity = cosine_similarity(matrix.T, dense_output=True)
    np.fill_diagonal(similarity, 0.0)  # exclui auto-similaridade

    trained_at = datetime.now(timezone.utc)
    result_rows: list[tuple] = []
    for i, product_id_a in enumerate(product_ids):
        row = similarity[i]
        top_indices = np.argsort(-row)[:TOP_K]
        for j in top_indices:
            score = float(row[j])
            if score <= 0:
                continue
            result_rows.append((product_id_a, product_ids[j], score, trained_at))

    con.execute("""
        CREATE OR REPLACE TABLE raw.product_similarity (
            product_id_a VARCHAR,
            product_id_b VARCHAR,
            similarity_score DOUBLE,
            trained_at TIMESTAMP
        )
    """)
    if result_rows:
        con.executemany(
            "INSERT INTO raw.product_similarity VALUES (?, ?, ?, ?)", result_rows
        )

    print(f"Done. raw.product_similarity: {len(result_rows)} linhas "
          f"({len(product_ids)} produtos, top-{TOP_K} vizinhos cada).", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
