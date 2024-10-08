import apsw
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .encoding import encode_value, decode_value

class Client:
    """
    FlashSQL is a high-performance key-value store built on SQLite with expiration support.
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
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("PRAGMA cache_size=-128000") 
        self.conn.execute("PRAGMA mmap_size=5000000000")  # 5GB memory map
        self.conn.execute("PRAGMA busy_timeout=10000")  
        self.conn.execute("PRAGMA page_size=8192")
        self.conn.execute("PRAGMA locking_mode=EXCLUSIVE")
        self.conn.execute("PRAGMA foreign_keys=OFF")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS FlashDB (
                key TEXT PRIMARY KEY,
                value BLOB,
                expires_at INTEGER
            ) WITHOUT ROWID;
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON FlashDB (expires_at) WHERE expires_at IS NOT NULL;")

        self.conn.execute("PRAGMA optimize")
        self.conn.execute("ANALYZE")
        self.conn.execute("PRAGMA cache_spill=FALSE")  
        self.conn.execute("PRAGMA auto_vacuum=INCREMENTAL") 
        self.conn.execute("PRAGMA wal_autocheckpoint=1000")  

    def _current_time(self) -> int:
        """
        Gets the current UTC time as a Unix timestamp.

        Returns:
            Current UTC time as a Unix timestamp.
        """
        return int(datetime.utcnow().timestamp())

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Sets a key-value pair with an optional expiration (TTL).

        Args:
            key: The key to store.
            value: The value to store, which should be serializable.
            ttl: Time-to-live in seconds. If not provided, the key never expires.
        """
        expires_at = (self._current_time() + ttl) if ttl else None
        self.cursor.execute("""
            INSERT OR REPLACE INTO FlashDB (key, value, expires_at) 
            VALUES (?, ?, ?)
        """, (key, encode_value(value), expires_at))

    def set_many(self, items: Dict[str, Tuple[Any, Optional[int]]]) -> None:
        """
        Sets multiple key-value pairs with optional expiration (TTL) in one batch.

        Args:
            items: Dictionary where keys are the key names and values are tuples containing the value and optional TTL.
        """
        now = self._current_time()
        sql = """
            INSERT OR REPLACE INTO FlashDB (key, value, expires_at) 
            VALUES (?, ?, ?)
        """
        values = [
            (key, encode_value(value), (now + ttl) if ttl else None)
            for key, (value, ttl) in items.items()
        ]
        self.cursor.executemany(sql, values)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves the value associated with the key if it exists and has not expired.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None if the key does not exist or has expired.
        """
        now = self._current_time()
        self.cursor.execute("""
            SELECT value FROM FlashDB 
            WHERE key = ? AND (expires_at IS NULL OR expires_at > ?) 
            LIMIT 1
        """, (key, now))
        result = self.cursor.fetchone()
        return decode_value(result[0]) if result else None

    def get_many(self, keys: List[str]) -> Dict[str, Optional[Any]]:
        """
        Retrieves values for multiple keys efficiently using batching and indexing.

        Args:
            keys: List of keys to look up.

        Returns:
            A dictionary where keys are the key names and values are the associated values or None if not found or expired.
        """
        now = self._current_time()
        batch_size = 1000
        result = {}
        
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            placeholders = ','.join('?' for _ in batch)  
            
            sql = f"""
                SELECT key, value FROM FlashDB 
                WHERE key IN ({placeholders}) AND (expires_at IS NULL OR expires_at > ?)
            """
            
            self.cursor.execute(sql, (*batch, now))
            result.update({key: decode_value(value) for key, value in self.cursor.fetchall()})
        
        return result

    def delete(self, key: str) -> None:
        """
        Deletes a key-value pair from the store.

        Args:
            key: The key to delete.
        """
        self.cursor.execute("DELETE FROM FlashDB WHERE key = ?", (key,))

    def delete_many(self, keys: List[str]) -> None:
        """
        Deletes multiple key-value pairs in batches to avoid SQL variable limit.

        Args:
            keys: List of keys to delete.
        """
        batch_size = 1000
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            placeholders = ','.join('?' for _ in batch)
            sql = f"DELETE FROM FlashDB WHERE key IN ({placeholders})"
            self.cursor.execute(sql, batch)

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
            The expiration date as a Unix timestamp, or None if the key has no expiration.
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
        expires_at = self._current_time() + ttl
        self.cursor.execute("UPDATE FlashDB SET expires_at = ? WHERE key = ?", (expires_at, key))

    def keys(self, pattern: str = "%") -> List[str]:
        """
        Retrieves all keys matching the given pattern.

        Args:
            pattern: SQL LIKE pattern to match keys. The "_" character matches any single character.
                    Defaults to '%' which matches all keys.

        Returns:
            A list of keys matching the pattern.
        """
        self.cursor.execute("SELECT key FROM FlashDB WHERE key LIKE ?", (pattern,))
        return [row[0] for row in self.cursor.fetchall()]

    def paginate(self, pattern: str = "%", page: int = 1, page_size: int = 10) -> List[str]:
        """
        Retrieves a paginated list of keys matching the pattern.

        Args:
            pattern: SQL LIKE pattern to match keys. The "_" character matches any single character.
                    Defaults to '%'.
            page: Page number (1-based).
            page_size: Number of keys per page.

        Returns:
            A list of keys for the specified page.
        """
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
    
    def exists(self, key: str) -> bool:
        """
        Checks if a key exists and is not expired.

        Args:
            key: The key to check.

        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        self.cursor.execute("SELECT EXISTS(SELECT 1 FROM FlashDB WHERE key = ? AND (expires_at IS NULL OR expires_at > ?))", 
                            (key, self._current_time()))
        return self.cursor.fetchone()[0] == 1
    
    def pop(self, key: str) -> Optional[Any]:
        """
        Retrieves and removes the value associated with the key if it exists.

        Args:
            key: The key to pop.

        Returns:
            The value associated with the key, or None if the key does not exist or has expired.
        """
        value = self.get(key)
        if value:
            self.delete(key)
        return value
    
    def update(self, key: str, value: Any) -> bool:
        """
        Updates the value of an existing key without modifying its expiration.

        Args:
            key: The key to update.
            value: The new value to store.

        Returns:
            True if the update was successful (key exists), False otherwise.
        """
        self.cursor.execute("SELECT EXISTS(SELECT 1 FROM FlashDB WHERE key = ?)", (key,))
        if self.cursor.fetchone()[0] == 1:
            self.cursor.execute("UPDATE FlashDB SET value = ? WHERE key = ?", (encode_value(value), key))
            return True
        return False
    
