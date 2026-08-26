"""Restricted Python execution for the Code Executor agent.

Security: this module only builds the docker invocation — it never execs
user code in-process. The container has no network (--network none) and is
removed after each run. Prefer a gVisor runtime (--runtime=runsc) in
production if available on the host; falls back to the default runtime
otherwise.
"""

import asyncio
import logging
import shlex
import tempfile
from pathlib import Path

logger = logging.getLogger("deepresearch.tools.code_sandbox")

SANDBOX_IMAGE = "python:3.11-slim"
TIMEOUT_SECONDS = 30


async def run_python(code: str, use_gvisor: bool = False) -> dict:
    """Returns {"stdout": str, "stderr": str, "artifact_paths": list[str]}."""
    with tempfile.TemporaryDirectory() as workdir:
        script_path = Path(workdir) / "script.py"
        script_path.write_text(code, encoding="utf-8")

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1",
            "-v", f"{workdir}:/workspace:rw",
            "-w", "/workspace",
        ]
        if use_gvisor:
            cmd += ["--runtime", "runsc"]
        cmd += [SANDBOX_IMAGE, "python", "script.py"]

        logger.info("code_sandbox_exec", extra={"cmd": shlex.join(cmd)})
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT_SECONDS)
        except TimeoutError:
            proc.kill()
            return {"stdout": "", "stderr": "execution timed out", "artifact_paths": []}

        artifacts = [str(p) for p in Path(workdir).iterdir() if p.name != "script.py"]
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "artifact_paths": artifacts,
        }
