"""Hold an OS lock across backup replacement; never use stale lockfile markers."""
import os

from .paths import private_dir


class InstanceLock:
    def __init__(self, directory):
        self.stream = None
        private_dir(directory)
        fd = os.open(directory / "medilocal.lock", os.O_CREAT | os.O_RDWR, 0o600)
        stream = os.fdopen(fd, "r+b")
        try:
            if os.name == "nt":
                import msvcrt
                if stream.seek(0, 2) == 0:
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.stream = stream
        except OSError:
            stream.close()
            raise

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
