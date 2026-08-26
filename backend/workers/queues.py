"""One Celery queue per agent type, so `celery -Q planner_q worker` can be
scaled independently from `celery -Q research_q worker`, etc."""

from kombu import Queue

AGENT_QUEUES = [
    "planner_q",
    "research_q",
    "browser_q",
    "summarizer_q",
    "fact_checker_q",
    "critic_q",
    "code_executor_q",
    "writer_q",
    "citation_validator_q",
]

# The graph-runner task (drives the whole LangGraph execution) lives on its
# own queue so it isn't starved behind individual agent tasks.
GRAPH_QUEUE = "graph_q"

CELERY_QUEUES = [Queue(name) for name in [*AGENT_QUEUES, GRAPH_QUEUE]]
