"""Basic supervision strategies."""

from __future__ import annotations


class Strategy:
    async def handle(self, exc: BaseException) -> None:
        raise NotImplementedError


class Restart(Strategy):
    async def handle(self, exc: BaseException) -> None:
        pass


class Stop(Strategy):
    async def handle(self, exc: BaseException) -> None:
        pass


class Escalate(Strategy):
    async def handle(self, exc: BaseException) -> None:
        pass
