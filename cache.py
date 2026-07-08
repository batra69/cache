

from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta


class CacheItem:
    """Wraps a value along with its expiry time (3 seconds fixed)."""

    def __init__(self, value):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=3)

    def is_expired(self):
        return datetime.now() > self.expires_at


class EvictionStrategy(ABC):
    """Blueprint for any eviction strategy. Every strategy must implement all 4 hooks."""

    @abstractmethod
    def on_add(self, store: OrderedDict, key: str):
        """Called right after a new key is inserted."""
        pass

    @abstractmethod
    def on_access(self, store: OrderedDict, key: str):
        """Called right after a key is successfully read via get()."""
        pass

    @abstractmethod
    def on_remove(self, store: OrderedDict, key: str):
        """Called right after a key is removed (manually or due to expiry)."""
        pass

    @abstractmethod
    def evict(self, store: OrderedDict):
        """Called when the cache is full and one item must be removed."""
        pass


class LRUEviction(EvictionStrategy):
    """Evicts the Least Recently Used item. Relies on OrderedDict ordering."""

    def on_add(self, store, key):
        pass  # OrderedDict already places new keys at the end automatically

    def on_access(self, store, key):
        store.move_to_end(key)  # mark this key as most recently used

    def on_remove(self, store, key):
        pass  # nothing extra to clean up for LRU

    def evict(self, store):
        key, _ = store.popitem(last=False)  # remove from the front (oldest/least used)
        print(f"[Cache] Evicted '{key}' (LRU, capacity full)")


class FIFOEviction(EvictionStrategy):
    """Evicts in strict First-In-First-Out order. Access never changes eviction order."""

    def on_add(self, store, key):
        pass  # OrderedDict already places new keys at the end automatically

    def on_access(self, store, key):
        pass  # FIFO ignores access entirely -- order is insertion order, period

    def on_remove(self, store, key):
        pass  # nothing extra to clean up for FIFO

    def evict(self, store):
        key, _ = store.popitem(last=False)  # remove the oldest-inserted item
        print(f"[Cache] Evicted '{key}' (FIFO, capacity full)")


class InMemoryCache:
    """A simple in-memory cache with TTL expiry, capacity limit, and pluggable eviction.
    This class has NO idea what eviction policy is active -- it only calls the 4 hooks."""

    MAX_CAPACITY = 5

    def __init__(self, eviction_strategy: EvictionStrategy = None):
        self._store = OrderedDict()  # internal storage
        self._eviction_strategy = eviction_strategy or LRUEviction()

    def add(self, key: str, value: str) -> None:
        """Add or update a key-value pair. Value must be a string."""
        if not isinstance(value, str):
            raise TypeError("Only string values are supported.")

        if key in self._store:
            self._store[key] = CacheItem(value)
            self._eviction_strategy.on_access(self._store, key)  # treat update as an access
            return

        if len(self._store) >= self.MAX_CAPACITY:
            self.cleanup_expired()

        if len(self._store) >= self.MAX_CAPACITY:
            self._eviction_strategy.evict(self._store)

        self._store[key] = CacheItem(value)
        self._eviction_strategy.on_add(self._store, key)

    def get(self, key: str):
        """Retrieve a value by key. Returns None if not found,
        or 'does not exist' if expired."""
        item = self._store.get(key)

        if item is None:
            return None

        if item.is_expired():
            del self._store[key]
            self._eviction_strategy.on_remove(self._store, key)
            return "does not exist"

        self._eviction_strategy.on_access(self._store, key)
        return item.value

    def remove(self, key: str) -> bool:
        """Remove a key from the cache. Returns True if removed, False if not found."""
        if key in self._store:
            del self._store[key]
            self._eviction_strategy.on_remove(self._store, key)
            return True
        return False

    def pop_first(self):
        """Remove and return the oldest inserted (key, value) pair.
        Returns None if the cache is empty."""
        if not self._store:
            return None
        key, item = self._store.popitem(last=False)
        self._eviction_strategy.on_remove(self._store, key)
        return key, item.value

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache. Returns count removed."""
        expired_keys = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired_keys:
            del self._store[k]
            self._eviction_strategy.on_remove(self._store, k)
        return len(expired_keys)

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


# ---------- Demo: same scenario, two different policies ----------
def run_scenario(strategy, label):
    print(f"\n===== Using {label} =====")
    cache = InMemoryCache(strategy)

    cache.add("a", "1")
    cache.add("b", "2")
    cache.add("c", "3")
    cache.add("d", "4")
    cache.add("e", "5")
    print("After filling to capacity:", cache)

    cache.get("a")  # access 'a' -- matters for LRU, ignored by FIFO
    print("Accessed 'a', now adding 'f' (cache full)...")
    cache.add("f", "6")
    print(cache)


if __name__ == "__main__":
    run_scenario(LRUEviction(), "LRU")    # 'a' was accessed -> survives -> 'b' evicted
    run_scenario(FIFOEviction(), "FIFO")  # access ignored -> 'a' still evicted (it's oldest)
# tan1
