

import threading
import time
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
        pass

    @abstractmethod
    def on_access(self, store: OrderedDict, key: str):
        pass

    @abstractmethod
    def on_remove(self, store: OrderedDict, key: str):
        pass

    @abstractmethod
    def evict(self, store: OrderedDict):
        pass


class LRUEviction(EvictionStrategy):
    """Evicts the Least Recently Used item."""

    def on_add(self, store, key):
        pass

    def on_access(self, store, key):
        store.move_to_end(key)

    def on_remove(self, store, key):
        pass

    def evict(self, store):
        key, _ = store.popitem(last=False)
        print(f"[Cache] Evicted '{key}' (LRU, capacity full)")


class FIFOEviction(EvictionStrategy):
    """Evicts in strict First-In-First-Out order. Access never changes eviction order."""

    def on_add(self, store, key):
        pass

    def on_access(self, store, key):
        pass  # FIFO ignores access entirely

    def on_remove(self, store, key):
        pass

    def evict(self, store):
        key, _ = store.popitem(last=False)
        print(f"[Cache] Evicted '{key}' (FIFO, capacity full)")


class InMemoryCache:
    """A thread-safe in-memory cache with TTL expiry, capacity limit,
    pluggable eviction, and an automatic background cleanup thread."""

    MAX_CAPACITY = 5

    def __init__(self, eviction_strategy: EvictionStrategy = None, cleanup_interval: float = 2.0):
        self._store = OrderedDict()
        self._eviction_strategy = eviction_strategy or LRUEviction()

        # --- thread safety ---
        self._lock = threading.RLock()  # RLock: same thread can re-acquire (add -> cleanup_expired)

        # --- background auto-cleanup ---
        self._cleanup_interval = cleanup_interval
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()

    # ---------- Core operations (all lock-protected) ----------

    def add(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Only string values are supported.")

        with self._lock:
            if key in self._store:
                self._store[key] = CacheItem(value)
                self._eviction_strategy.on_access(self._store, key)
                return

            if len(self._store) >= self.MAX_CAPACITY:
                self.cleanup_expired()  # RLock lets us re-enter safely

            if len(self._store) >= self.MAX_CAPACITY:
                self._eviction_strategy.evict(self._store)

            self._store[key] = CacheItem(value)
            self._eviction_strategy.on_add(self._store, key)

    def get(self, key: str):
        with self._lock:
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
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._eviction_strategy.on_remove(self._store, key)
                return True
            return False

    def pop_first(self):
        with self._lock:
            if not self._store:
                return None
            key, item = self._store.popitem(last=False)
            self._eviction_strategy.on_remove(self._store, key)
            return key, item.value

    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if v.is_expired()]
            for k in expired_keys:
                del self._store[k]
                self._eviction_strategy.on_remove(self._store, k)
            return len(expired_keys)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def keys(self):
        with self._lock:
            return list(self._store.keys())

    # ---------- Background cleanup thread ----------

    def _background_cleanup(self):
        """Runs in its own thread. Wakes up periodically and purges expired entries."""
        while not self._stop_event.is_set():
            time.sleep(self._cleanup_interval)
            with self._lock:
                removed = self.cleanup_expired()
                if removed:
                    print(f"[Background] Auto-cleaned {removed} expired item(s)")

    def stop_cleanup(self):
        """Stops the background thread cleanly. Call this before discarding the cache."""
        self._stop_event.set()
        self._cleanup_thread.join()

    # ---------- Dunder methods ----------

    def __len__(self):
        with self._lock:
            return len(self._store)

    def __contains__(self, key):
        with self._lock:
            return key in self._store

    def __str__(self):
        with self._lock:
            items = ", ".join(f"{k}: {v.value!r}" for k, v in self._store.items())
            return f"InMemoryCache({items})"


# ---------- Demo ----------
if __name__ == "__main__":
    cache = InMemoryCache(LRUEviction(), cleanup_interval=1)

    cache.add("a", "1")
    cache.add("b", "2")
    print("Initial state:", cache)

    print("\nNot touching the cache for 5 seconds -- background thread should auto-clean...\n")
    time.sleep(5)

    print("State after waiting (should be empty, cleaned automatically):", cache)

    cache.stop_cleanup()
    print("\nBackground thread stopped.")