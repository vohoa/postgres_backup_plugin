"""
Stream wrapper for efficient COPY TO operations
"""


class CopyToStreamWrapper:
    """
    Wrapper to stream COPY TO data directly to file without temp CSV.
    Minimizes RAM usage and disk I/O for large tables.

    This wrapper implements the file-like interface required by psycopg2's
    copy_expert() method, allowing direct streaming from PostgreSQL to file.
    """

    def __init__(self, outfile):
        """
        Initialize stream wrapper

        Args:
            outfile: File-like object to write streamed data
        """
        self.outfile = outfile
        self.bytes_written = 0
        self.chunks_written = 0

    def write(self, data):
        """
        Called by psycopg2 cursor.copy_expert() to write streamed data

        Args:
            data: Data chunk from PostgreSQL COPY TO

        Returns:
            int: Number of bytes written
        """
        self.outfile.write(data)
        bytes_count = len(data)
        self.bytes_written += bytes_count
        self.chunks_written += 1
        return bytes_count

    def flush(self):
        """Flush buffer to ensure data is written to disk"""
        if hasattr(self.outfile, 'flush'):
            self.outfile.flush()

    def close(self):
        """Close the underlying file if needed"""
        if hasattr(self.outfile, 'close'):
            self.outfile.close()

    @property
    def stats(self):
        """Get streaming statistics"""
        return {
            'bytes_written': self.bytes_written,
            'chunks_written': self.chunks_written,
            'avg_chunk_size': self.bytes_written / max(self.chunks_written, 1)
        }

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit"""
        self.flush()
        return False
