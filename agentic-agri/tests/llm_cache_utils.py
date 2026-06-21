import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from universal_agent.utils import get_text_content

CACHE_DIR = Path("F:/data/src/agentic-agri/tests/fixtures/llm_cache")
MAX_NEW_REQUESTS = 10


@dataclass
class CachedResponse:
    content: str


class CachedInvokeClient:
    def __init__(self, model, namespace: str):
        self.model = model
        self.namespace = namespace
        self.new_requests = 0

    def _cache_path(self, prompt: str) -> Path:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{self.namespace}_{digest}.json"

    def invoke(self, prompt: str):
        cache_path = self._cache_path(prompt)
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return CachedResponse(content=payload["content"])

        if self.new_requests >= MAX_NEW_REQUESTS:
            raise RuntimeError(
                f"Đã vượt quá giới hạn {MAX_NEW_REQUESTS} external requests cho namespace {self.namespace}."
            )

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        response = self.model.invoke(prompt)
        content = get_text_content(response)
        cache_path.write_text(
            json.dumps({"content": content}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.new_requests += 1
        return CachedResponse(content=content)


def should_run_live_e2e() -> bool:
    return os.environ.get("RUN_LIVE_SUPERVISOR_E2E", "0") == "1"
