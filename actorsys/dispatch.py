"""Dispatchers pull from mailboxes and execute actor receive methods."""

from __future__ import annotations

import asyncio
from typing import Callable, Coroutine

from .core import Actor, _Envelope
from .mailbox import AbstractMailbox


class Dispatcher:
    async def attach(self, mailbox: AbstractMailbox, actor: Actor) -> None:
        raise NotImplementedError


class AsyncIODisp(Dispatcher):
    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    async def attach(self, mailbox: AbstractMailbox, actor: Actor) -> None:
        async def run() -> None:
            while True:
                envelope = await mailbox.get()
                try:
                    await actor.receive(None, envelope.msg)  # Context filled by ActorSystem
                except Exception:
                    pass  # TODO: supervision

        task = asyncio.create_task(run())
        self._tasks.append(task)
