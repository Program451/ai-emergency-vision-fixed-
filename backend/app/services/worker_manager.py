
import threading

from app.config import MAX_CONCURRENT_WORKERS
from app.services.pipeline_runner import run_pipeline_sync


class WorkerManager:
    def __init__(self):
        self._threads: dict[int, threading.Thread] = {}
        self._stop_events: dict[int, threading.Event] = {}
        self._lock = threading.Lock()

    def _prune_dead_threads_locked(self):

        dead = [sid for sid, t in self._threads.items() if not t.is_alive()]
        for sid in dead:
            self._threads.pop(sid, None)
            self._stop_events.pop(sid, None)

    def active_count(self) -> int:
        with self._lock:
            self._prune_dead_threads_locked()
            return len(self._threads)

    def is_active(self, source_id: int) -> bool:
        with self._lock:
            self._prune_dead_threads_locked()
            return source_id in self._threads

    def start_worker(self, source_id: int, stream_url: str, lat: float, lon: float, target_event: str = None):
        with self._lock:
            self._prune_dead_threads_locked()

            if source_id in self._threads:
                return False, "Source уже активен"

            if len(self._threads) >= MAX_CONCURRENT_WORKERS:
                return False, f"Достигнут лимит одновременных источников ({MAX_CONCURRENT_WORKERS})"

            stop_event = threading.Event()
            thread = threading.Thread(
                target=run_pipeline_sync,
                args=(source_id, stream_url, lat, lon, stop_event),
                kwargs={"target_event": target_event},
                daemon=True,
            )
            self._stop_events[source_id] = stop_event
            self._threads[source_id] = thread
            thread.start()
            return True, "started"

    def stop_worker(self, source_id: int):
        with self._lock:
            stop_event = self._stop_events.get(source_id)
            thread = self._threads.get(source_id)

        if not stop_event or not thread:
            return False, "Source не активен"

        stop_event.set()
        thread.join(timeout=5)

        with self._lock:
            self._threads.pop(source_id, None)
            self._stop_events.pop(source_id, None)

        return True, "stopped"

    def list_active(self) -> list:
        with self._lock:
            self._prune_dead_threads_locked()
            return list(self._threads.keys())


# Синглтон на весь процесс — импортируется в api/sources.py и api/simulation.py
manager = WorkerManager()
