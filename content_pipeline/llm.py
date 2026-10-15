from __future__ import annotations

import asyncio
import httpx
from pydantic import BaseModel
from langchain_ollama import ChatOllama


class LocalModel:
    def __init__(self, model: str, base_url: str, concurrency: int, timeout: int, transport_retries: int = 1):
        self.model_name = model
        self.timeout = timeout
        self.transport_retries = transport_retries
        self.semaphore = asyncio.Semaphore(concurrency)
        self.active = 0
        self.peak_active = 0
        self.model = ChatOllama(model=model, base_url=base_url, temperature=0, num_ctx=4096, num_predict=900, reasoning=False)

    async def structured(self, prompt: str, schema: type[BaseModel]) -> tuple[BaseModel, dict]:
        async with self.semaphore:
            self.active += 1
            self.peak_active = max(self.peak_active, self.active)
            try:
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
                self.active -= 1

