"""Simple timer scheduler using asyncio."""

from __future__ import annotations

import asyncio
from collections.abc import Callable


class TimerScheduler:
    def schedule(self, delay: float, callback: Callable[[], None]) -> None:
        asyncio.get_running_loop().call_later(delay, callback)
