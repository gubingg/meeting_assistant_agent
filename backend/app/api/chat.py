from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.chat import ChatRequest
from app.services.agent_service import AgentService

router = APIRouter(prefix='/api/chat', tags=['chat'])
service = AgentService()


@router.post('')
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        return service.execute(db, request.meeting_id, request.message)
    except AttributeError as exc:
        raise HTTPException(status_code=404, detail='Meeting not found') from exc


