from __future__ import annotations

import asyncio
import fcntl
import hashlib
import os
import tempfile
import weakref
import httpx
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage


class LocalModel:
    _loop_limits: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    def __init__(self, model: str, base_url: str, concurrency: int, timeout: int, transport_retries: int = 1):
        self.model_name = model
        self.base_url = base_url
        self.concurrency = concurrency
        self.timeout = timeout
        self.transport_retries = transport_retries
        self.active = 0
        self._shared = None
        self.model = ChatOllama(model=model, base_url=base_url, temperature=0, num_ctx=8192, num_predict=1800, reasoning=False)

    @property
    def peak_active(self) -> int:
        return self._shared["peak"] if self._shared else 0

    def _limit(self):
        loop = asyncio.get_running_loop()
        limits = self._loop_limits.setdefault(loop, {})
        key = (self.base_url, self.model_name)
        if key not in limits:
            limits[key] = {"semaphore": asyncio.Semaphore(self.concurrency), "concurrency": self.concurrency, "active": 0, "peak": 0}
        shared = limits[key]
        if shared["concurrency"] != self.concurrency:
            raise ValueError("Conflicting Ollama concurrency limits for the same endpoint and model")
        self._shared = shared
        return shared

    async def structured(self, prompt: str | list[BaseMessage], schema: type[BaseModel]) -> tuple[BaseModel, dict]:
        shared = self._limit()
        async with shared["semaphore"]:
            fd = None
            acquired = False
            counted = False
            try:
                # Default one-call mode is also serialized across CLI processes.
                # The nonblocking poll is cancellation-safe while waiting.
                if self.concurrency == 1:
                    digest = hashlib.sha256(f"{self.base_url}|{self.model_name}".encode()).hexdigest()[:20]
                    lock_path = os.path.join(tempfile.gettempdir(), f"sanadsquad-ollama-{digest}.lock")
                    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
                    deadline = asyncio.get_running_loop().time() + self.timeout
                    while not acquired:
                        try:
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            acquired = True
                        except BlockingIOError:
                            if asyncio.get_running_loop().time() >= deadline:
                                raise TimeoutError("Timed out waiting for the shared Ollama model lock")
                            await asyncio.sleep(0.05)
                self.active += 1
                shared["active"] += 1
                counted = True
                shared["peak"] = max(shared["peak"], shared["active"])
                runnable = self.model.with_structured_output(schema, method="json_schema", include_raw=True)
                for attempt in range(self.transport_retries + 1):
                    try:
                        result = await asyncio.wait_for(runnable.ainvoke(prompt), timeout=self.timeout)
                        break
                    except (TimeoutError, ConnectionError, httpx.TransportError):
                        if attempt == self.transport_retries:
                            raise
                if result["parsing_error"] or result["parsed"] is None:
                    raise ValueError(f"Structured model output invalid: {result['parsing_error']}")
                usage = result["raw"].usage_metadata or {}
                return result["parsed"], usage
            finally:
                if counted:
                    self.active -= 1
                    shared["active"] -= 1
                if fd is not None:
                    if acquired:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    os.close(fd)

