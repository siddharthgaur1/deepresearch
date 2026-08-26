"""The StateGraph definition: wires all nine agents into one orchestrated run.

research_branch is a nested subgraph (researcher -> browser -> summarizer)
compiled once and added as a single node, so each of the N parallel
Send()-dispatched sub-question branches runs that three-step pipeline
independently, then rejoins the main graph at fact_checker.
"""

from langgraph.graph import END, START, StateGraph

from backend.agents.browser import BrowserAgent
from backend.agents.citation_validator import CitationValidatorAgent
from backend.agents.code_executor import CodeExecutorAgent
from backend.agents.critic import CriticAgent
from backend.agents.fact_checker import FactCheckerAgent
from backend.agents.planner import PlannerAgent
from backend.agents.researcher import ResearcherAgent
from backend.agents.summarizer import SummarizerAgent
from backend.agents.writer import WriterAgent
from backend.graph.state import ResearchState
from backend.graph.supervisor import fan_out_research, route_after_critic


def _build_research_branch():
    sub = StateGraph(ResearchState)
    sub.add_node("researcher", ResearcherAgent())
    sub.add_node("browser", BrowserAgent())
    sub.add_node("summarizer", SummarizerAgent())
    sub.add_edge(START, "researcher")
    sub.add_edge("researcher", "browser")
    sub.add_edge("browser", "summarizer")
    sub.add_edge("summarizer", END)
    return sub.compile()


def build_graph(checkpointer=None):
    graph = StateGraph(ResearchState)

    graph.add_node("planner", PlannerAgent())
    graph.add_node("research_branch", _build_research_branch())
    graph.add_node("fact_checker", FactCheckerAgent())
    graph.add_node("critic", CriticAgent())
    graph.add_node("code_executor", CodeExecutorAgent())
    graph.add_node("writer", WriterAgent())
    graph.add_node("citation_validator", CitationValidatorAgent())

    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", fan_out_research, ["research_branch", END])
    graph.add_edge("research_branch", "fact_checker")
    graph.add_edge("fact_checker", "critic")
    graph.add_conditional_edges("critic", route_after_critic, ["research_branch", "code_executor"])
    graph.add_edge("code_executor", "writer")
    graph.add_edge("writer", "citation_validator")
    graph.add_edge("citation_validator", END)

    return graph.compile(checkpointer=checkpointer)
