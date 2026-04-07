from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.action_item import ActionItemUpdateRequest, ActionItemUpdateResponse
from app.services.meeting_service import MeetingService

router = APIRouter(prefix='/api/action-items', tags=['action-items'])
service = MeetingService()


@router.patch('/{item_id}', response_model=ActionItemUpdateResponse)
def update_action_item(item_id: int, payload: ActionItemUpdateRequest, db: Session = Depends(get_db)):
    try:
        item = service.update_action_item(db, item_id, payload.model_dump())
        return ActionItemUpdateResponse.model_validate(item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

