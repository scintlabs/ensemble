# Ensemble Actor System

This repository provides a small actor system prototype inspired by Erlang/OTP and Akka. It implements a subset of the specification provided earlier.

## Usage

```
import asyncio
from actorsys import ActorSystem

class Echo:
    async def receive(self, ctx, msg):
        if isinstance(msg, str):
            ctx.sender.tell(f"echo: {msg}")

async def main():
    system = ActorSystem()
    echo = system.spawn(lambda: Echo(), name="echo")
    reply = await echo.ask("hello", timeout=1.0)
    print(reply)

asyncio.run(main())
```

