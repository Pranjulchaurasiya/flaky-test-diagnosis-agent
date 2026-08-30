import tempfile
import os

class LogChunkManager:
    """
    Log chunk manager creating temporary scratch descriptors.
    Flake Cause: Unclosed file handles leak descriptors across repeated test runs.
    """
    def __init__(self):
        self._open_handles = []

    def allocate_chunk(self, content: bytes) -> str:
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(content)
        # Intentional bug: handle kept in list without f.close(), keeping file locked
        self._open_handles.append(f)
        return f.name

    def cleanup(self):
        # Flawed cleanup that fails to close handles before attempting os.unlink
        for h in list(self._open_handles):
            try:
                # On Windows, deleting an open file raises PermissionError
                os.unlink(h.name)
                h.close()
                self._open_handles.remove(h)
            except PermissionError:
                pass  # Leaks open descriptors!
