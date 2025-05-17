import json
from typing import Any, Optional

import redis


class WorkQueueService:
    """Simple Redis-backed work queue service."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_url: str = "redis://localhost:6379/0",
        queue_key: str = "qmtl:gateway:work_queue",
    ) -> None:
        if redis_client is not None:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(redis_url, decode_responses=True)
        self.queue_key = queue_key

    def push(self, item: Any) -> int:
        """Push an item onto the queue."""
        data = json.dumps(item)
        return self.redis.lpush(self.queue_key, data)

    def pop(self) -> Optional[Any]:
        """Pop an item from the queue. Returns ``None`` if empty."""
        raw = self.redis.rpop(self.queue_key)
        if raw is None:
            return None
        return json.loads(raw)

    def size(self) -> int:
        """Return the current queue size."""
        return int(self.redis.llen(self.queue_key))

    def clear(self) -> int:
        """Remove all items from the queue."""
        return int(self.redis.delete(self.queue_key) or 0)
