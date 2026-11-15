"""
Queue CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_manager
from app.models.models import Manager, Queue, Token, TokenStatus
from app.schemas import QueueCreate, QueueOut, QueueUpdate

router = APIRouter(prefix="/api/queues", tags=["queues"])


def _queue_out(queue: Queue, db: Session) -> QueueOut:
    """Build a QueueOut with live waiting/serving counts."""
    waiting = (
        db.query(Token)
        .filter(Token.queue_id == queue.id, Token.status == TokenStatus.waiting)
        .count()
    )
    serving = (
        db.query(Token)
        .filter(Token.queue_id == queue.id, Token.status == TokenStatus.serving)
        .count()
    )
    out = QueueOut.model_validate(queue)
    out.waiting_count = waiting
    out.serving_count = serving
    return out


@router.get("/", response_model=list[QueueOut])
def list_queues(
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queues = (
        db.query(Queue)
        .filter(Queue.manager_id == current_manager.id, Queue.is_active == True)
        .order_by(Queue.created_at)
        .all()
    )
    return [_queue_out(q, db) for q in queues]


@router.post("/", response_model=QueueOut, status_code=201)
def create_queue(
    payload: QueueCreate,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queue = Queue(
        name=payload.name,
        description=payload.description,
        manager_id=current_manager.id,
    )
    db.add(queue)
    db.commit()
    db.refresh(queue)
    return _queue_out(queue, db)


@router.get("/{queue_id}", response_model=QueueOut)
def get_queue(
    queue_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queue = _get_owned_queue(queue_id, current_manager.id, db)
    return _queue_out(queue, db)


@router.put("/{queue_id}", response_model=QueueOut)
def update_queue(
    queue_id: int,
    payload: QueueUpdate,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queue = _get_owned_queue(queue_id, current_manager.id, db)
    if payload.name is not None:
        queue.name = payload.name.strip()
    if payload.description is not None:
        queue.description = payload.description
    db.commit()
    db.refresh(queue)
    return _queue_out(queue, db)


@router.delete("/{queue_id}", status_code=204)
def delete_queue(
    queue_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queue = _get_owned_queue(queue_id, current_manager.id, db)
    queue.is_active = False
    db.commit()


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_owned_queue(queue_id: int, manager_id: int, db: Session) -> Queue:
    queue = db.get(Queue, queue_id)
    if not queue or not queue.is_active:
        raise HTTPException(status_code=404, detail="Queue not found")
    if queue.manager_id != manager_id:
        raise HTTPException(status_code=403, detail="Not your queue")
    return queue
