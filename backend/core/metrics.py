from prometheus_client import Counter, Gauge, Histogram

jobs_total = Counter("jobs_total", "Research jobs submitted")
jobs_active = Gauge("jobs_active", "Research jobs currently running")
job_duration_seconds = Histogram("job_duration_seconds", "End-to-end job duration")

agent_calls_total = Counter("agent_calls_total", "Agent node invocations", ["agent"])
llm_tokens_total = Counter("llm_tokens_total", "LLM tokens consumed", ["agent", "direction"])
llm_cost_total = Counter("llm_cost_total", "LLM cost in USD", ["agent"])

worker_queue_depth = Gauge("worker_queue_depth", "Celery queue depth", ["queue"])
