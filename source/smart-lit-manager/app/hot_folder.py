import os
import time
import logging
import threading

log = logging.getLogger(__name__)


class HotFolderMonitor:
    """Monitor a folder for new PDF files and import them automatically."""

    def __init__(self, folder_path=None, callback=None, interval=5.0):
        self.folder_path = folder_path
        self.callback = callback
        self.interval = interval
        self._known_files = set()
        self._running = False
        self._thread = None

    def start(self, folder_path=None):
        if folder_path:
            self.folder_path = folder_path
        if not self.folder_path or not os.path.isdir(self.folder_path):
            log.warning("Hot folder not set or invalid: %s", self.folder_path)
            return False
        self._known_files = set(os.listdir(self.folder_path))
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        log.info("Hot folder monitoring started: %s", self.folder_path)
        return True

    def stop(self):
        self._running = False
        log.info("Hot folder monitoring stopped")

    @property
    def is_running(self):
        return self._running

    def _poll_loop(self):
        while self._running:
            try:
                if self.folder_path and os.path.isdir(self.folder_path):
                    current = set(os.listdir(self.folder_path))
                    new_files = current - self._known_files
                    for fname in sorted(new_files):
                        if fname.lower().endswith(".pdf"):
                            fpath = os.path.join(self.folder_path, fname)
                            if os.path.isfile(fpath):
                                log.info("Hot folder detected: %s", fname)
                                if self.callback:
                                    time.sleep(1.0)
                                    self.callback(fpath)
                    self._known_files = current
            except Exception as e:
                log.error("Hot folder poll error: %s", e)
            time.sleep(self.interval)
