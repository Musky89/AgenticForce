from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.models import ReviewItem, ReviewStatus, Deliverable, GeneratedImage

router = APIRouter(prefix="/review", tags=["review"])


class ReviewItemOut(BaseModel):
    id: str
    project_id: str
    task_id: str | None
    deliverable_id: str | None
    image_id: str | None
    title: str
    item_type: str
    status: str
    quality_score: float | None
    feedback: str | None
    priority: int
    created_at: str
    reviewed_at: str | None

    model_config = {"from_attributes": True}


class ReviewQueueStats(BaseModel):
    pending: int
    approved: int
    revision_requested: int
    total: int


class ReviewAction(BaseModel):
    status: str  # "approved" or "revision_requested"
    feedback: str | None = None


@router.get("/queue", response_model=list[ReviewItemOut])
async def get_review_queue(
    status: str | None = None,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """The founder's daily queue — all items awaiting review."""
    query = select(ReviewItem).order_by(ReviewItem.priority.desc(), ReviewItem.created_at)
    if status:
        query = query.where(ReviewItem.status == status)
    else:
        query = query.where(ReviewItem.status == ReviewStatus.PENDING)
    if project_id:
        query = query.where(ReviewItem.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=ReviewQueueStats)
async def get_queue_stats(db: AsyncSession = Depends(get_db)):
    pending = (await db.execute(select(func.count(ReviewItem.id)).where(ReviewItem.status == ReviewStatus.PENDING))).scalar() or 0
    approved = (await db.execute(select(func.count(ReviewItem.id)).where(ReviewItem.status == ReviewStatus.APPROVED))).scalar() or 0
    revision = (await db.execute(select(func.count(ReviewItem.id)).where(ReviewItem.status == ReviewStatus.REVISION_REQUESTED))).scalar() or 0
    total = (await db.execute(select(func.count(ReviewItem.id)))).scalar() or 0
    return ReviewQueueStats(pending=pending, approved=approved, revision_requested=revision, total=total)


@router.post("/{item_id}/action", response_model=ReviewItemOut)
async def review_action(item_id: str, action: ReviewAction, db: AsyncSession = Depends(get_db)):
    """Approve or request revision on a review item."""
    item = await db.get(ReviewItem, item_id)
    if not item:
        raise HTTPException(404, "Review item not found")

    if action.status == "approved":
        item.status = ReviewStatus.APPROVED
    elif action.status == "revision_requested":
        item.status = ReviewStatus.REVISION_REQUESTED
    else:
        raise HTTPException(400, "Status must be 'approved' or 'revision_requested'")

    item.feedback = action.feedback
    item.reviewed_at = datetime.utcnow()

    # Mark underlying deliverable/image as approved if applicable
    if action.status == "approved":
        if item.deliverable_id:
            d = await db.get(Deliverable, item.deliverable_id)
            if d:
                d.is_approved = True
        if item.image_id:
            img = await db.get(GeneratedImage, item.image_id)
            if img:
                img.is_approved = True

    await db.flush()
    await db.refresh(item)
    return item
