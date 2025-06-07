"""Core actor interfaces and internal message envelope."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable

Message = Any


@runtime_checkable
class Actor(Protocol):
    async def receive(self, ctx: "Context", msg: Message) -> None:
        ...


@runtime_checkable
class ActorRef(Protocol):
    def tell(self, msg: Message) -> None:
        ...

    async def ask(self, msg: Message, timeout: float | None = None) -> Message:
        ...

    def path(self) -> str:
        ...


@runtime_checkable
class Context(Protocol):
    self_ref: ActorRef
    sender: ActorRef | None

    def spawn(
        self,
        behavior: Callable[[], Actor],
        name: str | None = None,
        supervisor: "Strategy" | None = None,
        dispatcher: "Dispatcher" | None = None,
    ) -> ActorRef:
        ...

    def schedule(self, delay: float, msg: Message, target: ActorRef) -> None:
        ...

    def stop(self, ref: ActorRef) -> None:
        ...


@dataclass(slots=True)
class _Envelope:
    sender: ActorRef | None
    msg: Message


class _Ask:
    __slots__ = ("message", "future")

    def __init__(self, message: Message, future: asyncio.Future):
        self.message = message
        self.future = future
