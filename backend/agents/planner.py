import json
import uuid

from backend.agents.base import BaseAgent
from backend.graph.state import ResearchState, SubQuestion

PLANNER_PROMPT = """You are a research planner. Break the user's query into 3-6 \
focused, independently-answerable sub-questions that together cover the topic.

Query: {query}

Respond with a JSON array of strings only, no prose. Example:
["What is X?", "How does X compare to Y?"]
"""


class PlannerAgent(BaseAgent):
    name = "planner"

    async def run(self, state: ResearchState) -> dict:
        result = await self.complete(PLANNER_PROMPT.format(query=state["query"]))

        try:
            raw_questions = json.loads(result.content)
            assert isinstance(raw_questions, list)
        except Exception:
            raw_questions = [state["query"]]  # degrade to a single-branch run

        max_q = self.settings.max_sub_questions
        sub_questions: list[SubQuestion] = [
            SubQuestion(id=str(uuid.uuid4()), text=str(q), status="pending", retry_count=0)
            for q in raw_questions[:max_q]
        ]

        return {
            "sub_questions": sub_questions,
            "status": "researching",
            "_tokens_in": result.tokens_in,
            "_tokens_out": result.tokens_out,
            "_cost_usd": result.cost_usd,
        }
