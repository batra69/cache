
from collections import OrderedDict
from datetime import datetime, timedelta


class CacheItem:
    """Wraps a value along with its expiry time (3 seconds fixed)."""

    def __init__(self, value):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=3)

    def is_expired(self):
        return datetime.now() > self.expires_at


class InMemoryCache:
    """A simple in-memory cache with TTL expiry, capacity limit, and LRU eviction."""

    MAX_CAPACITY = 5

    def __init__(self):
        self._store = OrderedDict()  # internal storage

    def add(self, key: str, value: str) -> None:
        """Add or update a key-value pair. Value must be a string."""
        if not isinstance(value, str):
            raise TypeError("Only string values are supported.")

        if key in self._store:
            # Updating existing key, just refresh it and move to most-recently-used
            self._store[key] = CacheItem(value)
            self._store.move_to_end(key)
            return

        # New key -> make sure there's space
        if len(self._store) >= self.MAX_CAPACITY:
            self.cleanup_expired()

        if len(self._store) >= self.MAX_CAPACITY:
            self._evict_lru()

        self._store[key] = CacheItem(value)

    def get(self, key: str):
        """Retrieve a value by key. Returns None if not found,
        or 'does not exist' if expired."""
        item = self._store.get(key)

        if item is None:
            return None

        if item.is_expired():
            del self._store[key]
            return "does not exist"

        self._store.move_to_end(key)  # mark as recently used
        return item.value

    def remove(self, key: str) -> bool:
        """Remove a key from the cache. Returns True if removed, False if not found."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def pop_first(self):
        """Remove and return the oldest inserted (key, value) pair.
        Returns None if the cache is empty."""
        if not self._store:
            return None
        key, item = self._store.popitem(last=False)
        return key, item.value

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache. Returns count removed."""
        expired_keys = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired_keys:
            del self._store[k]
        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Remove the least recently used item (front of the OrderedDict)."""
        key, _ = self._store.popitem(last=False)
        print(f"[Cache] Evicted '{key}' (LRU, capacity full)")

    def clear(self) -> None:
        """Remove all items from the cache."""
        self._store.clear()

    def keys(self):
        """Return a list of all cached keys."""
        return list(self._store.keys())

    def __len__(self):
        return len(self._store)

    def __contains__(self, key):
        return key in self._store

    def __str__(self):
        items = ", ".join(f"{k}: {v.value!r}" for k, v in self._store.items())
        return f"InMemoryCache({items})"


# ---------- Demo ----------
if __name__ == "__main__":
    import time

    cache = InMemoryCache()

    cache.add("a", "1")
    cache.add("b", "2")
    cache.add("c", "3")
    cache.add("d", "4")
    cache.add("e", "5")
    print("After filling to capacity:", cache)

    cache.get("a")  # access 'a' so it's not the least recently used
    print("\nAccessed 'a', now adding 'f' (cache full, should evict LRU)...")
    cache.add("f", "6")
    print(cache)

    print("\nWaiting 4 seconds for all current items to expire...\n")
    time.sleep(4)

    print("Adding 'g' -> should trigger cleanup_expired() instead of LRU eviction")
    cache.add("g", "7")
    print(cache)