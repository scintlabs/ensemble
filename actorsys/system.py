"""ActorSystem implementation."""

from __future__ import annotations

import asyncio
import uuid
from typing import Callable

from .core import Actor, ActorRef, Context, _Envelope, _Ask
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
        return self._system.spawn(behavior, name=name, supervisor=supervisor, dispatcher=dispatcher)

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
        asyncio.create_task(self._run_actor(mailbox, actor, ctx, disp))
        return ref

    async def _run_actor(self, mailbox: FifoMailbox, actor: Actor, ctx: SimpleContext, disp: Dispatcher) -> None:
        while True:
            envelope = await mailbox.get()
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
            except Exception as exc:
                if isinstance(payload, _Ask):
                    payload.future.set_exception(exc)
                # TODO: supervision

    def _enqueue(self, ref: LocalActorRef, msg) -> None:
        envelope = _Envelope(sender=None, msg=msg)
        asyncio.create_task(ref._mailbox.put(envelope))

    def stop(self, ref: ActorRef) -> None:
        # TODO: implement actor stopping
        pass


def spawn(behavior: Callable[[], Actor], *, name: str | None = None) -> ActorRef:
    system = ActorSystem()
    return system.spawn(behavior, name=name)
