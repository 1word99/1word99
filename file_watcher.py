# osmanli_ai/core/file_watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"File {event.src_path} has been modified.")


class FileWatcher:
    """
    Monitors the filesystem for real-time change detection.

    - Detects file modifications, creations, and deletions.
    - Triggers analysis and actions based on detected changes.
    - Manages an automatic backup system.
    """

    def __init__(self, path_to_watch):
        self.observer = Observer()
        self.event_handler = FileChangeHandler()
        self.path_to_watch = path_to_watch

    def start(self):
        self.observer.schedule(self.event_handler, self.path_to_watch, recursive=True)
        self.observer.start()
        print(f"Started watching {self.path_to_watch} for changes.")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        print("Stopped file watcher.")
