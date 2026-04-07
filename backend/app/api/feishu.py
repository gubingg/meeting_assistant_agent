from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Meeting
from app.services.feishu_service import FeishuService

router = APIRouter(prefix='/api/meetings/{meeting_id}/sync', tags=['feishu'])
service = FeishuService()


@router.post('/feishu-doc')
def sync_feishu_doc(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail='Meeting not found')
    return service.sync_doc(db, meeting)


@router.post('/feishu-bitable')
def sync_feishu_bitable(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail='Meeting not found')
    return service.sync_bitable(db, meeting)

