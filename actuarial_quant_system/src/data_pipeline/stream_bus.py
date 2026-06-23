"""
stream_bus.py
=============
Async data-pipeline: ingests live market ticks over a WebSocket and republishes
them on a Redis pub/sub bus, while caching the latest state in Redis keys.

The rest of the system (risk engines, API) reads the live state from Redis
rather than holding direct socket connections, which keeps state consistent
across the daemon and the on-demand API workers.

Fail-soft: if Redis is unavailable the bus degrades to an in-process cache so
local development still works without infrastructure.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger("stream_bus")

try:  # redis is optional for local dev
    import redis.asyncio as aioredis  # type: ignore
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

try:  # websockets is optional until a real feed is wired
    import websockets  # type: ignore
except Exception:  # pragma: no cover
    websockets = None  # type: ignore


# Channels / key prefixes on the bus.
CH_TICKS = "ticks"
KEY_LAST_PRICE = "state:last_price:{symbol}"
KEY_LOSS_RESERVE = "state:loss_reserve:{symbol}"


class StreamBus:
    """Redis-backed pub/sub bus with an in-process fallback."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: Optional["aioredis.Redis"] = None
        self._local_cache: Dict[str, str] = {}
        self._subscribers: list[Callable[[dict], Awaitable[None]]] = []

    async def connect(self) -> None:
        if aioredis is None:
            logger.warning("redis not installed; using in-process cache only.")
            return
        try:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Connected to Redis at %s", self._redis_url)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis unavailable (%s); falling back to local cache.", exc)
            self._redis = None

    async def set_state(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        if self._redis is not None:
            await self._redis.set(key, payload)
        else:
            self._local_cache[key] = payload

    async def get_state(self, key: str) -> Optional[Any]:
        if self._redis is not None:
            raw = await self._redis.get(key)
        else:
            raw = self._local_cache.get(key)
        return json.loads(raw) if raw is not None else None

    async def publish(self, channel: str, message: dict) -> None:
        if self._redis is not None:
            await self._redis.publish(channel, json.dumps(message))
        # Always fan out to in-process subscribers too.
        for cb in self._subscribers:
            with contextlib.suppress(Exception):
                await cb(message)

    def subscribe(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self._subscribers.append(callback)

    async def consume_feed(self, ws_url: str) -> None:
        """
        Connect to a market-data WebSocket and republish ticks.
        This is the long-running coroutine the daemon supervises 24/7.
        """
        if websockets is None:
            logger.warning("websockets not installed; feed consumer disabled.")
            return
        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    logger.info("Market feed connected: %s", ws_url)
                    async for raw in ws:
                        tick = json.loads(raw)
                        symbol = tick.get("symbol")
                        price = tick.get("price")
                        if symbol and price is not None:
                            await self.set_state(
                                KEY_LAST_PRICE.format(symbol=symbol), price
                            )
                            await self.publish(CH_TICKS, tick)
            except asyncio.CancelledError:  # graceful shutdown
                raise
            except Exception as exc:  # pragma: no cover - reconnect loop
                logger.warning("Feed error (%s); reconnecting in 5s.", exc)
                await asyncio.sleep(5)

    async def aclose(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
