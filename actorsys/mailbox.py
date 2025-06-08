"""Mailbox implementations."""

from __future__ import annotations

import asyncio
from typing import Iterable


class PriorityItem:
    __slots__ = ("priority", "envelope")

    def __init__(self, priority: int, envelope: _Envelope):
        self.priority = priority
        self.envelope = envelope

    def __lt__(
        self, other: "PriorityItem"
    ) -> bool:  # pragma: no cover - simple comparator
        return self.priority < other.priority


from .core import _Envelope


class MailboxFull(Exception):
    pass


class AbstractMailbox:
    async def put(self, envelope: _Envelope) -> None:
        raise NotImplementedError

    async def get(self) -> _Envelope:
        raise NotImplementedError


class FifoMailbox(AbstractMailbox):
    def __init__(self, maxsize: int = 1024):
        self._queue = asyncio.Queue(maxsize=maxsize)

    async def put(self, envelope: _Envelope) -> None:
        try:
            await self._queue.put(envelope)
        except asyncio.QueueFull as exc:
            raise MailboxFull from exc

    async def get(self) -> _Envelope:
        return await self._queue.get()


class PriorityMailbox(AbstractMailbox):
    def __init__(self, maxsize: int = 1024):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)

    async def put(self, envelope: _Envelope) -> None:
        item = PriorityItem(envelope.priority, envelope)
        try:
            await self._queue.put(item)
        except asyncio.QueueFull as exc:
            raise MailboxFull from exc

    async def get(self) -> _Envelope:
        item: PriorityItem = await self._queue.get()
        return item.envelope
