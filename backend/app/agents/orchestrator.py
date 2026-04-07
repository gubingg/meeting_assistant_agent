from app.services.agent_service import AgentService


class MeetingOrchestrator:
    def __init__(self) -> None:
        self.agent_service = AgentService()

    def run(self, db, meeting_id: int, message: str):
        return self.agent_service.execute(db, meeting_id, message)

