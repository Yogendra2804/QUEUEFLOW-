"""
Analytics endpoints — real SQL aggregation, no mock data.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_manager
from app.models.models import Manager, Queue, Token, TokenStatus
from app.schemas import OverallAnalytics, QueueAnalytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _queue_analytics(queue: Queue, db: Session) -> QueueAnalytics:
    base = db.query(Token).filter(Token.queue_id == queue.id)

    total = base.count()
    completed = base.filter(Token.status == TokenStatus.completed).count()
    cancelled = base.filter(Token.status == TokenStatus.cancelled).count()
    waiting = base.filter(Token.status == TokenStatus.waiting).count()
    serving = base.filter(Token.status == TokenStatus.serving).count()

    # avg wait — only for completed tokens that actually had both timestamps
    wait_data = (
        db.query(Token)
        .filter(
            Token.queue_id == queue.id,
            Token.status == TokenStatus.completed,
            Token.called_at.isnot(None),
            Token.joined_at.isnot(None),
        )
        .all()
    )
    waits = [
        (t.called_at - t.joined_at).total_seconds() / 60
        for t in wait_data
        if t.called_at and t.joined_at
    ]
    avg_wait = round(sum(waits) / len(waits), 1) if waits else None

    # avg service duration
    service_data = (
        db.query(Token)
        .filter(
            Token.queue_id == queue.id,
            Token.status == TokenStatus.completed,
            Token.called_at.isnot(None),
            Token.completed_at.isnot(None),
        )
        .all()
    )
    services = [
        (t.completed_at - t.called_at).total_seconds() / 60
        for t in service_data
        if t.completed_at and t.called_at
    ]
    avg_service = round(sum(services) / len(services), 1) if services else None

    # daily breakdown — last 7 days
    daily_stats = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        day_tokens = (
            db.query(Token)
            .filter(
                Token.queue_id == queue.id,
                Token.joined_at >= day_start,
                Token.joined_at < day_end,
            )
            .all()
        )
        daily_stats.append(
            {
                "date": day.isoformat(),
                "total": len(day_tokens),
                "completed": sum(
                    1 for t in day_tokens if t.status == TokenStatus.completed
                ),
                "cancelled": sum(
                    1 for t in day_tokens if t.status == TokenStatus.cancelled
                ),
            }
        )

    return QueueAnalytics(
        queue_id=queue.id,
        queue_name=queue.name,
        total_tokens=total,
        completed_tokens=completed,
        cancelled_tokens=cancelled,
        waiting_tokens=waiting,
        serving_tokens=serving,
        avg_wait_minutes=avg_wait,
        avg_service_minutes=avg_service,
        daily_stats=daily_stats,
    )


@router.get("/", response_model=OverallAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queues = (
        db.query(Queue)
        .filter(Queue.manager_id == current_manager.id, Queue.is_active == True)
        .all()
    )

    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    queue_ids = [q.id for q in queues]
    today_tokens = (
        db.query(Token)
        .filter(
            Token.queue_id.in_(queue_ids),
            Token.joined_at >= today_start,
            Token.joined_at < today_end,
        )
        .all()
    ) if queue_ids else []

    total_today = len(today_tokens)
    completed_today = sum(1 for t in today_tokens if t.status == TokenStatus.completed)
    cancelled_today = sum(1 for t in today_tokens if t.status == TokenStatus.cancelled)

    # overall averages across all queues
    all_completed = (
        db.query(Token)
        .filter(
            Token.queue_id.in_(queue_ids),
            Token.status == TokenStatus.completed,
        )
        .all()
    ) if queue_ids else []

    waits = [
        (t.called_at - t.joined_at).total_seconds() / 60
        for t in all_completed
        if t.called_at and t.joined_at
    ]
    services = [
        (t.completed_at - t.called_at).total_seconds() / 60
        for t in all_completed
        if t.called_at and t.completed_at
    ]

    queue_analytics = [_queue_analytics(q, db) for q in queues]

    return OverallAnalytics(
        total_queues=len(queues),
        total_tokens_today=total_today,
        total_completed_today=completed_today,
        total_cancelled_today=cancelled_today,
        avg_wait_minutes=round(sum(waits) / len(waits), 1) if waits else None,
        avg_service_minutes=round(sum(services) / len(services), 1) if services else None,
        queue_analytics=queue_analytics,
    )
