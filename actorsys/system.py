"""ActorSystem implementation."""

from __future__ import annotations

import asyncio
import uuid
from typing import Callable

from .core import Actor, ActorRef, Context, _Envelope, _Ask, _Stop
from .dispatch import AsyncIODisp, Dispatcher
from .scheduler import TimerScheduler
from .mailbox import FifoMailbox


class LocalActorRef:
    def __init__(self, path: str, mailbox: FifoMailbox, system: "ActorSystem"):
        self._path = path
        self._mailbox = mailbox
        self._system = system

    def tell(self, msg):
        self._system._enqueue(self, msg)

    async def ask(self, msg, timeout=None):
        fut = asyncio.get_running_loop().create_future()
        self._system._enqueue(self, _Ask(msg, fut))
        return await asyncio.wait_for(fut, timeout)

    def path(self) -> str:
        return self._path


class SimpleContext(Context):
    def __init__(self, self_ref: ActorRef, system: "ActorSystem"):
        self.self_ref = self_ref
        self.sender: ActorRef | None = None
        self._system = system

    def spawn(
        self,
        behavior: Callable[[], Actor],
        name: str | None = None,
        supervisor=None,
        dispatcher: Dispatcher | None = None,
    ) -> ActorRef:
        return self._system.spawn(
            behavior, name=name, supervisor=supervisor, dispatcher=dispatcher
        )

    def schedule(self, delay: float, msg, target: ActorRef) -> None:
        self._system.scheduler.schedule(delay, lambda: target.tell(msg))

    def stop(self, ref: ActorRef) -> None:
        self._system.stop(ref)


class ActorSystem:
    def __init__(self, *, dispatcher: Dispatcher | None = None):
        self._registry: dict[str, LocalActorRef] = {}
        self._dispatcher = dispatcher or AsyncIODisp()
        self.scheduler = TimerScheduler()

    def spawn(
        self,
        behavior: Callable[[], Actor],
        *,
        name: str | None = None,
        supervisor=None,
        dispatcher: Dispatcher | None = None,
    ) -> ActorRef:
        path = f"actor://local/{name or uuid.uuid4()}"
        mailbox = FifoMailbox()
        ref = LocalActorRef(path, mailbox, self)
        self._registry[path] = ref
        actor = behavior()
        ctx = SimpleContext(ref, self)
        disp = dispatcher or self._dispatcher
        asyncio.create_task(disp.attach(mailbox, actor, ctx))
        return ref

    def _enqueue(
        self,
        ref: LocalActorRef,
        msg,
        *,
        sender: ActorRef | None = None,
        priority: int = 0,
    ) -> None:
        envelope = _Envelope(sender=sender, msg=msg, priority=priority)
        asyncio.create_task(ref._mailbox.put(envelope))

    def stop(self, ref: ActorRef) -> None:
        if isinstance(ref, LocalActorRef):
            self._enqueue(ref, _Stop())
            self._registry.pop(ref.path(), None)


def spawn(behavior: Callable[[], Actor], *, name: str | None = None) -> ActorRef:
    system = ActorSystem()
    return system.spawn(behavior, name=name)
