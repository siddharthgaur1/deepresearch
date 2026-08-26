import json
import re

from backend.agents.base import BaseAgent
from backend.graph.state import CodeResult, ResearchState
from backend.tools.code_sandbox import run_python

CODE_GEN_PROMPT = """Given these research findings, decide if a chart or numeric \
analysis would help the report (e.g. comparing figures, timelines, trends). \
If not needed, respond with exactly: {{"needed": false}}.

If needed, respond as JSON:
{{"needed": true, "code": "<python code writing a PNG file with matplotlib \
and printing a one-line summary, using only stdlib + matplotlib + pandas>"}}

Findings:
{summaries}
"""


class CodeExecutorAgent(BaseAgent):
    """Runs once per job after summarization. Only executes code the LLM
    judged necessary — most research jobs (pure text topics) skip this
    entirely and code_outputs stays empty."""

    name = "code_executor"

    async def run(self, state: ResearchState) -> dict:
        summaries_text = "\n\n".join(state["summaries"].values()) or "(no findings)"
        result = await self.complete(CODE_GEN_PROMPT.format(summaries=summaries_text))

        tokens_in, tokens_out, cost = result.tokens_in, result.tokens_out, result.cost_usd

        try:
            parsed = json.loads(_strip_code_fence(result.content))
        except Exception:
            parsed = {"needed": False}

        if not parsed.get("needed"):
            return {"_tokens_in": tokens_in, "_tokens_out": tokens_out, "_cost_usd": cost}

        code = str(parsed.get("code", ""))
        exec_result = await run_python(code)

        code_output: CodeResult = {
            "sub_question_id": "global",
            "code": code,
            "stdout": exec_result["stdout"],
            "stderr": exec_result["stderr"],
            "artifact_paths": exec_result["artifact_paths"],
        }

        return {
            "code_outputs": [code_output],
            "_tokens_in": tokens_in,
            "_tokens_out": tokens_out,
            "_cost_usd": cost,
        }


def _strip_code_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1) if match else text
