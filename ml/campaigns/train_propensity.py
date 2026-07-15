"""Próxima campanha sugerida (caso de uso 2) — modelo de propensão.

Lê feature.feat_campaign_training_data (1 linha por customer_id x
promotion_id exposto), treina uma Regressão Logística por campanha
(features numéricas de engajamento/RFM -> P(converteu)) e grava só o score
cru em raw.campaign_propensity. A escolha final da "melhor" campanha por
cliente (propensity_score x avg_order_value, com fallback para
segment_campaign_affinity) é feita em SQL, em
transform/models/activation/customer_profile.sql.

Campanhas com poucas amostras ou só uma classe (ninguém converteu, ou todo
mundo converteu) são puladas — o fallback de customer_profile.sql cobre
esses clientes.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db import connect  # noqa: E402

MIN_SAMPLES_PER_CAMPAIGN = int(os.environ.get("PROPENSITY_MIN_SAMPLES", "20"))
FEATURE_COLUMNS = [
    "view_count", "select_count", "days_since_last_exposure",
    "recency_days", "total_orders", "net_revenue", "avg_order_value",
]


def main() -> int:
    con = connect()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    rows = con.execute(f"""
        SELECT customer_id, promotion_id, {", ".join(FEATURE_COLUMNS)}, converted
        FROM feature.feat_campaign_training_data
    """).fetchall()

    if not rows:
        print("feat_campaign_training_data está vazia — nada a treinar.", file=sys.stderr)
        return 1

    by_promotion: dict[str, list[tuple]] = defaultdict(list)
    for row in rows:
        by_promotion[row[1]].append(row)

    trained_at = datetime.now(timezone.utc)
    result_rows: list[tuple] = []
    skipped = []

    for promotion_id, group in by_promotion.items():
        labels = [r[-1] for r in group]
        if len(group) < MIN_SAMPLES_PER_CAMPAIGN or len(set(labels)) < 2:
            skipped.append(promotion_id)
            continue

        X = np.array([
            [float(v) if v is not None else 0.0 for v in r[2:-1]]
            for r in group
        ])
        y = np.array(labels, dtype=int)

        model = LogisticRegression(class_weight="balanced", max_iter=1000)
        model.fit(X, y)
        scores = model.predict_proba(X)[:, 1]

        for (customer_id, _promotion_id, *_rest), score in zip(group, scores):
            result_rows.append((customer_id, promotion_id, float(score), trained_at))

        print(f"{promotion_id}: {len(group)} amostras, {sum(labels)} conversões, treinado.",
              flush=True)

    if skipped:
        print(f"Puladas (poucas amostras ou só uma classe): {skipped}", flush=True)

    con.execute("""
        CREATE OR REPLACE TABLE raw.campaign_propensity (
            customer_id VARCHAR,
            promotion_id VARCHAR,
            propensity_score DOUBLE,
            trained_at TIMESTAMP
        )
    """)
    if result_rows:
        con.executemany(
            "INSERT INTO raw.campaign_propensity VALUES (?, ?, ?, ?)", result_rows
        )

    print(f"Done. raw.campaign_propensity: {len(result_rows)} linhas "
          f"({len(by_promotion) - len(skipped)} campanhas treinadas).", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
