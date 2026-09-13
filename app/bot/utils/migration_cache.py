"""Временный in-memory cache для миграции Telegram group -> supergroup."""

from cachetools import TTLCache

cache = TTLCache(maxsize=float("inf"), ttl=10.0)

