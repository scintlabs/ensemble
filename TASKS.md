# Tasks for implementing the Actor System

This document outlines the steps required to build a fully functional actor framework according to the provided specification.

## 1. Project scaffolding

- [ ] Create an `actorsys` Python package with the module layout described in the spec.
- [ ] Expose `ActorSystem`, `spawn`, `Actor`, and `ActorRef` from `actorsys/__init__.py`.
- [ ] Set up `pyproject.toml` with dependencies (primarily `asyncio`) and basic packaging metadata.

## 2. Core runtime

- [ ] Implement `core.py` with the `Actor`, `ActorRef`, `Context` protocols and internal `_Envelope` type.
- [ ] Create mailbox implementations in `mailbox.py` (`AbstractMailbox`, `FifoMailbox`, `PriorityMailbox`). Ensure mailboxes are bounded and enforce overflow policies.
- [ ] Build dispatcher strategies in `dispatch.py` (`ThreadPoolDisp`, `AsyncIODisp`, `InlineDisp`). Ensure each actor is dispatched by a single strategy.
- [ ] Provide a `TimerScheduler` in `scheduler.py` for delayed and periodic messages.
- [ ] Implement supervision strategies in `supervision.py` (`Strategy`, `Restart`, `Stop`, `Escalate`).

## 3. Actor system

- [ ] Implement `system.py` containing `ActorSystem`, the root guardian actor, `DeadLetters`, and basic metrics hooks.
- [ ] Implement spawn logic, actor registry, and message routing (`tell` and `ask`).
- [ ] Ensure the dispatcher upholds single-threaded execution per actor and FIFO ordering.
- [ ] Provide a simple metrics sink interface and default stdout implementation.

## 4. Supervision & lifecycle hooks

- [ ] Implement restart, stop, and escalation semantics according to the spec.
- [ ] Support `pre_restart` and `post_stop` hooks on actors.
- [ ] Ensure mailboxes are flushed or preserved on restart per configuration.

## 5. Additional features

- [ ] Implement optional persistence module with `PersistentActor`, event replay, and snapshotting.
- [ ] Add an event stream for system-wide pub/sub events.
- [ ] Expose scheduling helpers via `Context.schedule`.

## 6. Testing

- [ ] Write unit tests for mailboxes, dispatchers, supervision decisions, and basic message flow.
- [ ] Include concurrency stress tests ensuring single-threaded execution per actor.
- [ ] Provide example actors (e.g., Echo actor) and integration tests demonstrating `tell` and `ask`.

## 7. Documentation

- [ ] Document public APIs and invariants in the README or a dedicated docs folder.
- [ ] Provide usage examples similar to the reference code snippet.

## 8. Future work

- [ ] Add remote actor references and transport layer.
- [ ] Support clustering features (sharding, routers) after the single-node system is stable.

