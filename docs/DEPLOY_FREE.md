# Deploying DeepResearch for free (public demo)

The full local stack (Ollama, RabbitMQ, Postgres+pgvector, Redis, Grafana,
Flower — see `infra/docker-compose.yml`) needs more RAM/GPU than any current
free-tier host gives a single instance. Ollama alone needs several GB with
no GPU on the free plans, so this isn't a "free tier of a paid API" problem —
it just doesn't fit.

This config swaps only what free tiers *can't* run — the local model runtime
and the three self-hosted infra services — for managed free equivalents. It
does not change any application code: `backend/core/config.py` already reads
every one of these as a `.env`-swappable URL/key, exactly as the README's
"Why I built it this way" section describes.

| Local (docker-compose) | Free-tier swap | Why |
|---|---|---|
| Ollama (`llama3.1`) | [Groq](https://console.groq.com) free API | Fast, generous free-tier LLM inference; no local model to load |
| Ollama (`nomic-embed-text`) | OpenAI `text-embedding-3-small` | Groq has no embeddings endpoint; OpenAI's free trial credit covers a demo's embedding volume |
| Postgres + pgvector | [Neon](https://neon.tech) free tier | Managed Postgres with pgvector, free forever (not a 90-day trial) |
| Redis | [Upstash](https://upstash.com) free tier | Serverless Redis, free forever, supports pub/sub (needed for the SSE feed) |
| RabbitMQ | [CloudAMQP](https://www.cloudamqp.com) "Little Lemur" free plan | 1M msgs/month, enough for a demo's job volume |
| Celery worker (own container) | Same container as the API (`backend/Dockerfile`'s `combo` target) | Render's free plan only offers Web Services, not a separate background-worker dyno |

**Known limitations of this deploy** (not fixed here — see rationale in each):
- **Code Executor agent will fail on every job.** It needs `/var/run/docker.sock`
  to launch sandboxed containers (see README's security section); no free
  PaaS grants that. `backend/agents/base.py` already catches this per-agent
  and the report ships with a visible warning instead of crashing the job —
  same behavior as any other agent failure.
- **Browser agent (headless Chromium) may be slow or OOM** on Render free's
  512MB RAM. It's included in the `combo` image; if jobs stall, that's the
  likely cause — increasing sub-question count makes it worse.
- **Free-tier cold starts.** Render free web services spin down after 15
  minutes idle; the first request after that takes ~30-50s to wake up.

## Setup (about 15 minutes, all free, no credit card required for the ones below)

1. **Neon** (Postgres): sign up at neon.tech → New Project → copy the
   pooled connection string. You need it twice:
   - `DATABASE_URL` — replace `postgresql://` with `postgresql+asyncpg://`
   - `DATABASE_URL_SYNC` — replace `postgresql://` with `postgresql+psycopg://`
   - Run `CREATE EXTENSION IF NOT EXISTS vector;` once in Neon's SQL editor.

2. **Upstash** (Redis): sign up at upstash.com → Create Database (Regional,
   free) → copy the `redis://` connection string (not the REST URL) → use it
   for both `REDIS_URL` and `CELERY_RESULT_BACKEND` (Upstash supports
   separate logical DBs via `/0`, `/1` suffixes if you want them split).

3. **CloudAMQP** (RabbitMQ): sign up at cloudamqp.com → Create instance →
   plan "Little Lemur" (free) → copy the AMQP URL → use it as
   `CELERY_BROKER_URL`.

4. **Groq** (LLM): sign up at console.groq.com → API Keys → create one →
   `GROQ_API_KEY`. Already wired to `LLM_MODEL=groq/llama-3.1-8b-instant` in
   `render.yaml`.

5. **OpenAI** (embeddings only): platform.openai.com → API Keys → create one
   → `OPENAI_API_KEY`. New accounts get free trial credit that comfortably
   covers a demo's embedding volume.

6. **Render**: sign up at render.com (GitHub login is fastest) → New →
   Blueprint → connect the `deepresearch` repo → Render reads `render.yaml`
   at the repo root and proposes two free Web Services
   (`deepresearch-api`, `deepresearch-frontend`) → paste in the 6 values
   from steps 1-5 when prompted (they're the `sync: false` env vars) →
   Apply.

7. Wait for both builds (the API image installs Chromium, so first build is
   ~5-8 min). Once live, open the frontend service's `.onrender.com` URL —
   that's the public demo link.

If the Render blueprint UI rejects any field in `render.yaml` (Render's
Blueprint schema changes over time), the fix is almost always renaming or
dropping that one field in the UI's review step — the two Docker services
and env var list are the parts that matter, not the exact YAML keys.

## Migrations

`backend/start-combo.sh` runs `alembic -c backend/alembic.ini upgrade head` before
starting the worker or the API. Render's `preDeployCommand` — the dedicated hook
for this — is gated behind a paid plan, so the start script is the only place a
free-tier deploy can run migrations. Without it the service comes up against an
empty database and every request fails on a missing table.

