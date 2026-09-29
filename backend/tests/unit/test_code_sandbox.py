"""The worker reaches the *host* Docker daemon via the mounted socket, so the
sandbox must not bind-mount worker-local paths; code goes in on stdin."""

import asyncio

from backend.tools import code_sandbox


class _FakeProc:
    def __init__(self):
        self.input = None

    async def communicate(self, input=None):
        self.input = input
        return b"hello\n", b""


async def test_run_python_pipes_code_on_stdin_without_bind_mount(monkeypatch):
    captured = {}
    proc = _FakeProc()

    async def fake_exec(*cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = kwargs
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    result = await code_sandbox.run_python("print('hello')")

    assert captured["cmd"] == [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1",
        "--pids-limit", "64",
        "python:3.11-slim", "python", "-",
    ]
    assert "-v" not in captured["cmd"] and "--volume" not in captured["cmd"]
    assert captured["kwargs"]["stdin"] is asyncio.subprocess.PIPE
    assert proc.input == b"print('hello')"
    assert result == {"stdout": "hello\n", "stderr": "", "artifact_paths": []}


def test_gvisor_runtime_goes_before_image():
    cmd = code_sandbox.build_command(use_gvisor=True)
    assert cmd[-5:] == ["--runtime", "runsc", "python:3.11-slim", "python", "-"]
