from threading import Lock

from app.services.save_watcher import SaveWatcher

save_watcher: SaveWatcher | None = None
collection_state: dict | None = None
collection_lock: bool = False
_collection_lock = Lock()


def acquire_collection_lock() -> bool:
    global collection_lock
    if collection_lock:
        return False
    _collection_lock.acquire(blocking=False)
    if collection_lock:
        _collection_lock.release()
        return False
    collection_lock = True
    return True


def release_collection_lock() -> None:
    global collection_lock
    collection_lock = False
    _collection_lock.release()
