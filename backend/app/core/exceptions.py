class BusinessException(ValueError):
    """Domain-level business exception."""


class AgentSchemaValidationError(BusinessException):
    def __init__(self, agent_name: str, message: str = 'Agent schema validation failed') -> None:
        super().__init__(f'{agent_name}: {message}')
        self.agent_name = agent_name
