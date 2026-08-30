import os
import pytest
from file_manager import LogChunkManager

def test_temporary_chunk_allocation():
    """
    Test Case 06: Resource / File Descriptor Exhaustion
    Taxonomy: resource_exhaustion
    Description: Allocates multiple file descriptors without closing handles,
    causing permission errors / descriptor leaks during repeated runs and cleanup.
    """
    manager = LogChunkManager()
    created_files = []
    for i in range(15):
        filepath = manager.allocate_chunk(f"Log payload entry #{i}".encode("utf-8"))
        created_files.append(filepath)
        assert os.path.exists(filepath)

    manager.cleanup()
    # If handles weren't closed, cleanup failed to unlink files on Windows
    for fp in created_files:
        assert not os.path.exists(fp), f"Resource leak: temp file {fp} was not properly cleaned up"
