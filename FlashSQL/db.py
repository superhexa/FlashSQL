import apsw
from typing import Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .encoding import encode_value, decode_value

class Client:
    """
    FlashSQL is a high-performance key-value store built on SQLite with expiration support.

    Provides efficient operations to store, retrieve, and manage key-value pairs with optional expiration times.
    Supports pagination, cleaning up expired keys, and optimizing the database file size.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initializes the FlashSQL instance.

        Args:
            db_path: File path to the SQLite database. Use ":memory:" for an in-memory database.
        """
        self.conn = apsw.Connection(db_path)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self) -> None:
        """
        Sets up the database schema and PRAGMA settings for optimal performance.
        """
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("PRAGMA cache_size=-64000")
        self.conn.execute("PRAGMA mmap_size=30000000000")
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS FlashDB (
                key TEXT PRIMARY KEY,
                value BLOB,
                expires_at DATETIME
            ) WITHOUT ROWID;
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON FlashDB (key);")
        self.conn.execute("PRAGMA busy_timeout=5000")

    def _current_time(self) -> str:
        """
        Gets the current UTC time as a string in ISO 8601 format.

        Returns:
            Current UTC time in ISO format.
        """
        return datetime.utcnow().isoformat()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Sets a key-value pair with an optional expiration (TTL).

        Args:
            key: The key to store.
            value: The value to store, which should be serializable.
            ttl: Time-to-live in seconds. If not provided, the key never expires.
        """
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat() if ttl else None
        self.cursor.execute("""
            INSERT OR REPLACE INTO FlashDB (key, value, expires_at) 
            VALUES (?, ?, ?)
        """, (key, encode_value(value), expires_at))

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves the value associated with the key if it exists and has not expired.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None if the key does not exist or has expired.
        """
        self.cleanup()
        self.cursor.execute("SELECT value FROM FlashDB WHERE key = ? AND (expires_at IS NULL OR expires_at > ?) LIMIT 1", 
                            (key, self._current_time()))
        result = self.cursor.fetchone()
        return decode_value(result[0]) if result else None

    def exists(self, key: str) -> bool:
        """
        Checks if a key exists and is not expired.

        Args:
            key: The key to check.

        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        self.cleanup()
        self.cursor.execute("SELECT 1 FROM FlashDB WHERE key = ? AND (expires_at IS NULL OR expires_at > ?) LIMIT 1", 
                            (key, self._current_time()))
        return self.cursor.fetchone() is not None

    def delete(self, key: str) -> None:
        """
        Deletes a key-value pair from the store.

        Args:
            key: The key to delete.
        """
        self.cursor.execute("DELETE FROM FlashDB WHERE key = ?", (key,))

    def rename(self, old_key: str, new_key: str) -> None:
        """
        Renames a key to a new key.

        Args:
            old_key: The current key name.
            new_key: The new key name.
        """
        self.cursor.execute("UPDATE FlashDB SET key = ? WHERE key = ?", (new_key, old_key))

    def get_expire(self, key: str) -> Optional[str]:
        """
        Gets the expiration date of a key if it exists.

        Args:
            key: The key to check.

        Returns:
            The expiration date as an ISO formatted string, or None if the key has no expiration.
        """
        self.cursor.execute("SELECT expires_at FROM FlashDB WHERE key = ? LIMIT 1", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_expire(self, key: str, ttl: int) -> None:
        """
        Sets a new expiration time for a key.

        Args:
            key: The key to set expiration for.
            ttl: Time-to-live in seconds from now.
        """
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        self.cursor.execute("UPDATE FlashDB SET expires_at = ? WHERE key = ?", (expires_at, key))

    def keys(self, pattern: str = "%") -> List[str]:
        """
        Retrieves all keys matching the given pattern.

        Args:
            pattern: SQL LIKE pattern to match keys. Defaults to '%' which matches all keys.

        Returns:
            A list of keys matching the pattern.
        """
        self.cleanup()
        self.cursor.execute("SELECT key FROM FlashDB WHERE key LIKE ?", (pattern,))
        return [row[0] for row in self.cursor.fetchall()]

    def paginate(self, pattern: str = "%", page: int = 1, page_size: int = 10) -> List[str]:
        """
        Retrieves a paginated list of keys matching the pattern.

        Args:
            pattern: SQL LIKE pattern to match keys. Defaults to '%'.
            page: Page number (1-based).
            page_size: Number of keys per page.

        Returns:
            A list of keys for the specified page.
        """
        self.cleanup()
        offset = (page - 1) * page_size
        self.cursor.execute("""
            SELECT key FROM FlashDB WHERE key LIKE ? LIMIT ? OFFSET ?
        """, (pattern, page_size, offset))
        return [row[0] for row in self.cursor.fetchall()]

    def count(self) -> int:
        """
        Counts the total number of keys in the database.

        Returns:
            The total number of keys.
        """
        self.cursor.execute("SELECT COUNT(*) FROM FlashDB")
        return self.cursor.fetchone()[0]

    def count_expired(self) -> int:
        """
        Counts the number of expired keys in the database.

        Returns:
            The number of expired keys.
        """
        now = self._current_time()
        self.cursor.execute("SELECT COUNT(*) FROM FlashDB WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
        return self.cursor.fetchone()[0]

    def cleanup(self) -> None:
        """
        Removes expired key-value pairs from the database.

        This method is called automatically before any retrieval or key-checking operation to keep the database clean.
        """
        now = self._current_time()
        self.cursor.execute("DELETE FROM FlashDB WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))

    def vacuum(self) -> None:
        """
        Optimizes the database file by reducing its size using the VACUUM command.
        """
        self.conn.execute("VACUUM")

    def flush(self) -> None:
        """
        Ensures all changes are written to disk by performing a full checkpoint of the WAL (Write-Ahead Log).
        """
        self.conn.execute("PRAGMA wal_checkpoint(FULL)")

    def execute(self, query: str, params: Tuple = ()) -> Any:
        """
        Executes a raw SQL statement and returns the result.

        Args:
            query: The SQL query to execute.
            params: Parameters for the SQL query.

        Returns:
            The result of the query.
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.conn.close()
        
