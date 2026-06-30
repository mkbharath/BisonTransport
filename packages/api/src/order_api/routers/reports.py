"""Dashboard and reporting endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text

from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/dashboard")
async def get_dashboard(current_user: CurrentUser = Depends(get_current_user)):
    """Real-time KPIs for the dashboard."""
    async with async_session_factory() as session:
        # Total orders
        r = await session.execute(text("SELECT COUNT(*) FROM orders WHERE status != 'cancelled'"))
        total_orders = r.scalar() or 0

        # Pending (extracted + validated)
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE status IN ('extracted', 'validated')")
        )
        pending = r.scalar() or 0

        # Awaiting customer response
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE status = 'awaiting_customer'")
        )
        awaiting_customer = r.scalar() or 0

        # Auto-processed (STP)
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE processing_mode = 'auto' AND status = 'order_created'")
        )
        auto_processed = r.scalar() or 0

        # STP rate
        stp_rate = round((auto_processed / total_orders * 100), 1) if total_orders > 0 else 0.0

        # HITL queue depth
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE status = 'pending_review'")
        )
        hitl_queue_depth = r.scalar() or 0

        # Completed
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE status = 'order_created'")
        )
        completed = r.scalar() or 0

        # Failed
        r = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE status = 'failed'")
        )
        failed = r.scalar() or 0

        # Average end-to-end time (from email receipt to order creation) in minutes
        r = await session.execute(
            text("""
                SELECT AVG(EXTRACT(EPOCH FROM (o.updated_at - e.received_at)) / 60)
                FROM orders o
                JOIN emails e ON e.id = o.source_email_id
                WHERE o.status = 'order_created'
                AND o.updated_at IS NOT NULL
                AND e.received_at IS NOT NULL
                AND o.created_at > NOW() - INTERVAL '24 hours'
            """)
        )
        raw_avg = r.scalar()
        avg_e2e_time = round(float(raw_avg), 1) if raw_avg else 0.0

        # Extraction accuracy (average confidence)
        r = await session.execute(
            text("""
                SELECT AVG(overall_confidence_score)
                FROM orders
                WHERE overall_confidence_score IS NOT NULL
            """)
        )
        extraction_accuracy = round(float(r.scalar() or 0), 1)

    return {
        "total_orders": total_orders,
        "pending": pending,
        "awaiting_customer": awaiting_customer,
        "auto_processed": auto_processed,
        "stp_rate": stp_rate,
        "hitl_queue_depth": hitl_queue_depth,
        "completed": completed,
        "failed": failed,
        "avg_e2e_time": avg_e2e_time,
        "extraction_accuracy": extraction_accuracy,
    }


@router.get("/stp-trend")
async def get_stp_trend(
    days: int = 7,
    current_user: CurrentUser = Depends(get_current_user),
):
    """STP rate trend over the last N days."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                SELECT
                    d.day::date as date,
                    COALESCE(total.cnt, 0) as total_orders,
                    COALESCE(stp.cnt, 0) as auto_processed,
                    CASE WHEN COALESCE(total.cnt, 0) > 0
                        THEN ROUND((COALESCE(stp.cnt, 0)::numeric / total.cnt) * 100, 1)
                        ELSE 0
                    END as stp_rate
                FROM generate_series(
                    NOW() - INTERVAL '1 day' * :days,
                    NOW(),
                    '1 day'
                ) d(day)
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) as cnt FROM orders
                    WHERE created_at::date = d.day::date
                    AND status != 'cancelled'
                ) total ON true
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) as cnt FROM orders
                    WHERE created_at::date = d.day::date
                    AND processing_mode = 'auto'
                    AND status = 'order_created'
                ) stp ON true
                ORDER BY d.day ASC
            """),
            {"days": days},
        )
        rows = result.fetchall()

    trend = []
    for row in rows:
        trend.append({
            "date": row[0].isoformat() if row[0] else None,
            "total_orders": int(row[1]),
            "auto_processed": int(row[2]),
            "stp_rate": float(row[3]),
        })

    return {"data": trend, "days": days}
