from pydantic import BaseModel


class AgentCallResult(BaseModel):
    """Return contract every agent node normalizes its LLM call result into,
    so BaseAgent can emit consistent cost/token metadata regardless of provider."""

    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
