

from collections import OrderedDict
from datetime import datetime, timedelta


class CacheItem:
   

    def __init__(self, value):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=3)

    def is_expired(self):
        return datetime.now() > self.expires_at


class InMemoryCache:
    

    def __init__(self):
        self._store = OrderedDict()  # internal storage

    def add(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Only string values are supported.")
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

    cache.add("name", "Alice")
    cache.add("city", "Paris")
    cache.add("lang", "Python")

    print(cache)
    print("Get 'name':", cache.get("name"))

    print("\nWaiting 4 seconds for items to expire...\n")
    time.sleep(4)

    print("Get 'name' (should be expired):", cache.get("name"))
    print("Get 'unknown':", cache.get("unknown"))

    print("\nPop first item:", cache.pop_first())
    print(cache)
