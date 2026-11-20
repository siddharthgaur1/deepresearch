"""Restricted Python execution for the Code Executor agent.

Security: this module only builds the docker invocation — it never execs
user code in-process. The container has no network (--network none) and is
removed after each run. Prefer a gVisor runtime (--runtime=runsc) in
production if available on the host; falls back to the default runtime
otherwise.

The code goes in on stdin (`python -`), not via a bind mount: the worker
talks to the *host* daemon through the mounted /var/run/docker.sock, so a
`-v <path>:...` would resolve <path> on the host filesystem, where a temp
dir created inside the worker container doesn't exist.
"""

import asyncio
import logging
import shlex

logger = logging.getLogger("deepresearch.tools.code_sandbox")

SANDBOX_IMAGE = "python:3.11-slim"
TIMEOUT_SECONDS = 30


def build_command(use_gvisor: bool = False) -> list[str]:
    cmd = [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1",
        "--pids-limit", "64",
    ]
    if use_gvisor:
        cmd += ["--runtime", "runsc"]
    return cmd + [SANDBOX_IMAGE, "python", "-"]


async def run_python(code: str, use_gvisor: bool = False) -> dict:
    """Returns {"stdout": str, "stderr": str, "artifact_paths": list[str]}.

    artifact_paths is always empty: files the script writes live only in the
    --rm'd container. (Before this, the paths pointed into a temp dir deleted
    on return, so nothing downstream could read them either.)
    """
    cmd = build_command(use_gvisor)
    logger.info("code_sandbox_exec", extra={"cmd": shlex.join(cmd)})
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=code.encode("utf-8")), timeout=TIMEOUT_SECONDS
        )
    except TimeoutError:
        # ponytail: kills the docker CLI client only; the container itself runs
        # on until its script exits. Name it + `docker kill` if that matters.
        proc.kill()
        return {"stdout": "", "stderr": "execution timed out", "artifact_paths": []}

    return {
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
        "artifact_paths": [],
    }
