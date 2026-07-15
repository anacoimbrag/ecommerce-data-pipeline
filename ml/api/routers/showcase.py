from fastapi import APIRouter, Query

from api.db import get_connection
from api.schemas import ShowcaseItem, ShowcaseResponse

router = APIRouter()


@router.get("/customers/{customer_id}/showcase", response_model=ShowcaseResponse)
def get_customer_showcase(
    customer_id: str, limit: int = Query(default=12, ge=1, le=12)
) -> ShowcaseResponse:
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT rank, product_id, sku_id, reason, score
            FROM customer_showcase
            WHERE customer_id = ?
            ORDER BY rank
            LIMIT ?
            """,
            (customer_id, limit),
        ).fetchall()

    return ShowcaseResponse(
        customer_id=customer_id,
        items=[ShowcaseItem(**dict(row)) for row in rows],
    )
