"""Mailbox implementations."""

from __future__ import annotations

import asyncio
from typing import Iterable

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
