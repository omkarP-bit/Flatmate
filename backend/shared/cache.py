import logging
from typing import Any

logger = logging.getLogger(__name__)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    logger.debug("cache_set (no-op): key=%s", key)


def cache_get(key: str) -> Any | None:
    return None


def cache_delete(key: str) -> None:
    logger.debug("cache_delete (no-op): key=%s", key)


def cache_delete_pattern(pattern: str) -> None:
    logger.debug("cache_delete_pattern (no-op): pattern=%s", pattern)
