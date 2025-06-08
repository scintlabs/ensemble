"""Dispatchers pull from mailboxes and execute actor receive methods."""

from __future__ import annotations

import asyncio
from typing import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
import threading

from .core import Actor, Context, _Envelope, _Ask, _Stop
from .mailbox import AbstractMailbox


class Dispatcher:
    """Base dispatcher interface."""

    async def attach(
        self, mailbox: AbstractMailbox, actor: Actor, ctx: Context
    ) -> None:
        """Attach an actor to the dispatcher.

        The dispatcher takes ownership of pulling messages from ``mailbox`` and
        invoking ``actor.receive`` with the provided ``ctx`` until a ``_Stop``
        message is encountered.
        """
        raise NotImplementedError


class AsyncIODisp(Dispatcher):
    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    async def attach(
        self, mailbox: AbstractMailbox, actor: Actor, ctx: Context
    ) -> None:
        async def run() -> None:
            while True:
                envelope = await mailbox.get()
                if isinstance(envelope.msg, _Stop):
                    break
                payload = envelope.msg
                ctx.sender = envelope.sender
                if isinstance(payload, _Ask):
                    real_msg = payload.message
                else:
                    real_msg = payload
                try:
                    result = await actor.receive(ctx, real_msg)
                    if isinstance(payload, _Ask):
                        payload.future.set_result(result)
                except (
                    Exception
                ) as exc:  # pragma: no cover - basic supervision placeholder
                    if isinstance(payload, _Ask):
                        payload.future.set_exception(exc)

        task = asyncio.create_task(run())
        self._tasks.append(task)


class InlineDisp(Dispatcher):
    """Execute actor messages inline in the caller's event loop."""

    async def attach(
        self, mailbox: AbstractMailbox, actor: Actor, ctx: Context
    ) -> None:
        while True:
            envelope = await mailbox.get()
            if isinstance(envelope.msg, _Stop):
                break
            payload = envelope.msg
            ctx.sender = envelope.sender
            if isinstance(payload, _Ask):
                real_msg = payload.message
            else:
                real_msg = payload
            try:
                result = await actor.receive(ctx, real_msg)
                if isinstance(payload, _Ask):
                    payload.future.set_result(result)
            except Exception as exc:  # pragma: no cover - placeholder
                if isinstance(payload, _Ask):
                    payload.future.set_exception(exc)


class ThreadPoolDisp(Dispatcher):
    """Dispatch actor messages on a dedicated event loop in a separate thread."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    async def attach(
        self, mailbox: AbstractMailbox, actor: Actor, ctx: Context
    ) -> None:
        async def run() -> None:
            while True:
                envelope = await mailbox.get()
                if isinstance(envelope.msg, _Stop):
                    break
                payload = envelope.msg
                ctx.sender = envelope.sender
                if isinstance(payload, _Ask):
                    real_msg = payload.message
                else:
                    real_msg = payload
                try:
                    coro = actor.receive(ctx, real_msg)
                    fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
                    result = await asyncio.wrap_future(fut)
                    if isinstance(payload, _Ask):
                        payload.future.set_result(result)
                except Exception as exc:  # pragma: no cover - supervision
                    if isinstance(payload, _Ask):
                        payload.future.set_exception(exc)

        await run()
