from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import FeishuSyncLog, Meeting


class FeishuService:
    def sync_doc(self, db: Session, meeting: Meeting) -> FeishuSyncLog:
        log = FeishuSyncLog(
            meeting_id=meeting.id,
            target_type='doc',
            target_url=f'https://mock.feishu.cn/docs/{meeting.meeting_uuid}',
            sync_status='success',
            sync_message='Mock 飞书文档同步成功',
            synced_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def sync_bitable(self, db: Session, meeting: Meeting) -> FeishuSyncLog:
        log = FeishuSyncLog(
            meeting_id=meeting.id,
            target_type='bitable',
            target_url=f'https://mock.feishu.cn/base/{meeting.meeting_uuid}',
            sync_status='success',
            sync_message='Mock 飞书多维表格同步成功',
            synced_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

