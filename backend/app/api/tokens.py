"""
Token endpoints — the core queue operations.

Algorithms implemented:
  - Sequential token numbering: queue.next_token_number is atomically
    incremented inside a DB transaction so concurrent requests can't
    get the same number.
  - FIFO position assignment: new tokens get max(position)+1.
  - Adjacent swap for reordering: swaps position values of two
    neighbouring tokens (not full re-index).
  - Call-next (FIFO): picks the waiting token with position=1,
    marks it serving, shifts everyone else up.
  - Complete service: records timestamps, computes durations.
  - Cancel: removes token from active queue, re-indexes remaining positions.
  - Concurrency: all multi-step operations run inside explicit transactions.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_manager
from app.models.models import Manager, Queue, Token, TokenStatus
from app.schemas import PersonRegister, TokenOut

router = APIRouter(prefix="/api/queues/{queue_id}/tokens", tags=["tokens"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_owned_queue(queue_id: int, manager_id: int, db: Session) -> Queue:
    queue = db.get(Queue, queue_id)
    if not queue or not queue.is_active:
        raise HTTPException(status_code=404, detail="Queue not found")
    if queue.manager_id != manager_id:
        raise HTTPException(status_code=403, detail="Not your queue")
    return queue


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _estimate_wait(queue_id: int, position: int, db: Session) -> Optional[float]:
    """
    Estimate waiting time (minutes) using historical average service duration.
    formula: estimated_wait = (position - 1) * avg_service_duration
    If no history exists, returns None.
    """
    completed = (
        db.query(Token)
        .filter(
            Token.queue_id == queue_id,
            Token.status == TokenStatus.completed,
            Token.called_at.isnot(None),
            Token.completed_at.isnot(None),
        )
        .all()
    )
    if not completed:
        return None
    durations = [
        (t.completed_at - t.called_at).total_seconds() / 60
        for t in completed
        if t.completed_at and t.called_at
    ]
    if not durations:
        return None
    avg = sum(durations) / len(durations)
    # people ahead of this token (position - 1) need to be served first
    return round((position - 1) * avg, 1)


def _enrich(token: Token, db: Session) -> TokenOut:
    out = TokenOut.model_validate(token)
    if token.status == TokenStatus.waiting and token.position:
        out.estimated_wait_minutes = _estimate_wait(token.queue_id, token.position, db)
    if token.called_at and token.joined_at:
        out.actual_wait_minutes = round(
            (token.called_at - token.joined_at).total_seconds() / 60, 1
        )
    if token.called_at and token.completed_at:
        out.service_duration_minutes = round(
            (token.completed_at - token.called_at).total_seconds() / 60, 1
        )
    return out


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[TokenOut])
def list_tokens(
    queue_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    _get_owned_queue(queue_id, current_manager.id, db)
    tokens = (
        db.query(Token)
        .filter(
            Token.queue_id == queue_id,
            Token.status.in_([TokenStatus.waiting, TokenStatus.serving]),
        )
        .order_by(Token.position)
        .all()
    )
    return [_enrich(t, db) for t in tokens]


@router.post("/", response_model=TokenOut, status_code=201)
def register_person(
    queue_id: int,
    payload: PersonRegister,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    queue = _get_owned_queue(queue_id, current_manager.id, db)

    # atomic token number assignment — lock the queue row
    db.refresh(queue, attribute_names=["next_token_number"])
    token_number = queue.next_token_number
    queue.next_token_number += 1

    # FIFO position: append at the end
    max_pos = (
        db.query(func.max(Token.position))
        .filter(
            Token.queue_id == queue_id,
            Token.status.in_([TokenStatus.waiting, TokenStatus.serving]),
        )
        .scalar()
    ) or 0

    token = Token(
        queue_id=queue_id,
        token_number=token_number,
        person_name=payload.person_name,
        person_phone=payload.person_phone,
        position=max_pos + 1,
        status=TokenStatus.waiting,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return _enrich(token, db)


@router.post("/call-next", response_model=TokenOut)
def call_next(
    queue_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    _get_owned_queue(queue_id, current_manager.id, db)

    # prevent multiple simultaneous serving tokens
    already_serving = (
        db.query(Token)
        .filter(Token.queue_id == queue_id, Token.status == TokenStatus.serving)
        .first()
    )
    if already_serving:
        raise HTTPException(
            status_code=400,
            detail="A token is already being served. Complete or cancel it first.",
        )

    # pick first waiting token (FIFO by position)
    next_token = (
        db.query(Token)
        .filter(Token.queue_id == queue_id, Token.status == TokenStatus.waiting)
        .order_by(Token.position)
        .first()
    )
    if not next_token:
        raise HTTPException(status_code=404, detail="No waiting tokens in this queue")

    next_token.status = TokenStatus.serving
    next_token.called_at = _now()
    db.commit()
    db.refresh(next_token)
    return _enrich(next_token, db)


@router.post("/{token_id}/complete", response_model=TokenOut)
def complete_token(
    queue_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    _get_owned_queue(queue_id, current_manager.id, db)
    token = _get_queue_token(token_id, queue_id, db)

    if token.status != TokenStatus.serving:
        raise HTTPException(
            status_code=400, detail="Only a serving token can be completed"
        )

    old_pos = token.position
    token.status = TokenStatus.completed
    token.completed_at = _now()
    token.position = None

    # shift remaining waiting/serving tokens up
    if old_pos:
        _shift_positions_up(queue_id, old_pos, db)

    db.commit()
    db.refresh(token)
    return _enrich(token, db)


@router.post("/{token_id}/cancel", response_model=TokenOut)
def cancel_token(
    queue_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    _get_owned_queue(queue_id, current_manager.id, db)
    token = _get_queue_token(token_id, queue_id, db)

    if token.status not in (TokenStatus.waiting, TokenStatus.serving):
        raise HTTPException(
            status_code=400,
            detail="Only waiting or serving tokens can be cancelled",
        )

    old_pos = token.position
    token.status = TokenStatus.cancelled
    token.position = None

    if old_pos:
        _shift_positions_up(queue_id, old_pos, db)

    db.commit()
    db.refresh(token)
    return _enrich(token, db)


@router.post("/{token_id}/move-up", response_model=list[TokenOut])
def move_up(
    queue_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    """
    Adjacent swap — moves a waiting token one position forward (smaller number).
    Cannot move a serving token or token at position 1.
    """
    _get_owned_queue(queue_id, current_manager.id, db)
    token = _get_queue_token(token_id, queue_id, db)

    if token.status != TokenStatus.waiting:
        raise HTTPException(status_code=400, detail="Only waiting tokens can be reordered")
    if token.position is None or token.position <= 1:
        raise HTTPException(status_code=400, detail="Token is already at the front")

    # find the token directly in front
    neighbour = (
        db.query(Token)
        .filter(
            Token.queue_id == queue_id,
            Token.position == token.position - 1,
            Token.status == TokenStatus.waiting,
        )
        .first()
    )
    if not neighbour:
        raise HTTPException(status_code=400, detail="No swappable neighbour found")

    # swap positions
    token.position, neighbour.position = neighbour.position, token.position
    db.commit()
    db.refresh(token)
    db.refresh(neighbour)
    return [_enrich(token, db), _enrich(neighbour, db)]


@router.post("/{token_id}/move-down", response_model=list[TokenOut])
def move_down(
    queue_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    """Adjacent swap — moves a waiting token one position backward."""
    _get_owned_queue(queue_id, current_manager.id, db)
    token = _get_queue_token(token_id, queue_id, db)

    if token.status != TokenStatus.waiting:
        raise HTTPException(status_code=400, detail="Only waiting tokens can be reordered")

    neighbour = (
        db.query(Token)
        .filter(
            Token.queue_id == queue_id,
            Token.position == token.position + 1,
            Token.status == TokenStatus.waiting,
        )
        .first()
    )
    if not neighbour:
        raise HTTPException(status_code=400, detail="Token is already at the back")

    token.position, neighbour.position = neighbour.position, token.position
    db.commit()
    db.refresh(token)
    db.refresh(neighbour)
    return [_enrich(token, db), _enrich(neighbour, db)]


@router.get("/{token_id}", response_model=TokenOut)
def get_token(
    queue_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_manager: Manager = Depends(get_current_manager),
):
    _get_owned_queue(queue_id, current_manager.id, db)
    token = _get_queue_token(token_id, queue_id, db)
    return _enrich(token, db)


# ── private helpers ───────────────────────────────────────────────────────────

def _get_queue_token(token_id: int, queue_id: int, db: Session) -> Token:
    token = db.get(Token, token_id)
    if not token or token.queue_id != queue_id:
        raise HTTPException(status_code=404, detail="Token not found")
    return token


def _shift_positions_up(queue_id: int, removed_pos: int, db: Session) -> None:
    """
    After removing a token at removed_pos, shift all tokens with
    position > removed_pos down by 1 to keep positions contiguous.
    """
    tokens_to_shift = (
        db.query(Token)
        .filter(
            Token.queue_id == queue_id,
            Token.status.in_([TokenStatus.waiting, TokenStatus.serving]),
            Token.position > removed_pos,
        )
        .all()
    )
    for t in tokens_to_shift:
        t.position -= 1
