from __future__ import annotations

import asyncio


class IngestionLock:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def run_once(self, coro):
        if self._lock.locked():
            return None
        async with self._lock:
            return await coro
