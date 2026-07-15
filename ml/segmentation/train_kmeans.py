"""Clusterização dinâmica de clientes (caso de uso 1).

Lê feature.feat_rfm_features (materializada pelo dbt), roda K-Means sobre
RFM padronizado escolhendo k por silhouette score, e grava só o cluster_id
cru em raw.customer_clusters — rotular o cluster (Champions/Loyal/etc.) é
regra de negócio e fica em SQL, dentro de
transform/models/activation/customer_profile.sql.

Rodar depois de `dbt build --select path:models/feature` e antes do
`dbt build` completo (ver README do módulo ml/).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db import connect  # noqa: E402

K_MIN = int(os.environ.get("KMEANS_K_MIN", "3"))
K_MAX = int(os.environ.get("KMEANS_K_MAX", "8"))
RANDOM_STATE = 42


def main() -> int:
    con = connect()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    rows = con.execute("""
        SELECT customer_id, recency_days, total_orders, net_revenue
        FROM feature.feat_rfm_features
        WHERE has_purchase_history
    """).fetchall()

    if not rows:
        print("Nenhum cliente com histórico de compra em feat_rfm_features.", file=sys.stderr)
        return 1

    customer_ids = [r[0] for r in rows]
    X = np.array([[r[1], r[2], r[3]] for r in rows], dtype=float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    max_k = min(K_MAX, len(rows) - 1)
    if max_k < K_MIN:
        print(f"Poucos clientes ({len(rows)}) para testar k entre {K_MIN} e {K_MAX}; "
              f"usando k={max_k}.", file=sys.stderr)
        best_k = max(2, max_k)
    else:
        best_k, best_score = None, -1.0
        for k in range(K_MIN, max_k + 1):
            labels = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            print(f"k={k}: silhouette={score:.4f}", flush=True)
            if score > best_score:
                best_k, best_score = k, score
        print(f"Melhor k: {best_k} (silhouette={best_score:.4f})", flush=True)

    model = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
    cluster_ids = model.fit_predict(X_scaled)

    trained_at = datetime.now(timezone.utc)
    result_rows = [
        (customer_id, int(cluster_id), trained_at)
        for customer_id, cluster_id in zip(customer_ids, cluster_ids)
    ]

    con.execute("""
        CREATE OR REPLACE TABLE raw.customer_clusters (
            customer_id VARCHAR,
            cluster_id INTEGER,
            trained_at TIMESTAMP
        )
    """)
    con.executemany(
        "INSERT INTO raw.customer_clusters VALUES (?, ?, ?)", result_rows
    )

    print(f"Done. raw.customer_clusters: {len(result_rows)} linhas, k={best_k}.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
