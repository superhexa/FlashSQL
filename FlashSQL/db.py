import apsw
from typing import Any, List, Optional
from .encoding import encode_value, decode_value

class Client:
    def __init__(self, path: str):
        """
        Initializes a new instance of FlashSQL.

        This constructor opens a connection to a SQLite database specified by the `path`.
        If the path is ":memory:", an in-memory database is created.

        Args:
            path (str): The file path to the SQLite database. Use ":memory:" for an in-memory database.
        """
        self.conn = apsw.Connection(path)
        self.cursor = self.conn.cursor()
        self._init_database()

    def _init_database(self) -> None:
        """
        Configures the database schema and settings.

        This method ensures that the database schema is set up by creating the necessary table and index.
        It also applies various PRAGMA settings to optimize performance.
        """
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("PRAGMA cache_size=-64000")
        self.conn.execute("PRAGMA mmap_size=30000000000")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS FlashSQL (
                key TEXT PRIMARY KEY,
                value BLOB
            ) WITHOUT ROWID;
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_key ON FlashSQL (key);
        """)

        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.execute("PRAGMA case_sensitive_like=ON")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves the value associated with the given key.

        Args:
            key (str): The key whose value is to be retrieved.

        Returns:
            Optional[Any]: The value associated with the key if it exists, otherwise None.
        """
        self.cursor.execute("SELECT value FROM FlashSQL WHERE key = ? LIMIT 1", (key,))
        result = self.cursor.fetchone()
        if result:
            return decode_value(result[0])
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Stores a value under the specified key.

        If a value already exists for the given key, it is replaced.

        Args:
            key (str): The key under which the value will be stored.
            value (Any): The value to be stored, which should be serializable.
        """
        encoded_value = encode_value(value)
        self.cursor.execute("INSERT OR REPLACE INTO FlashSQL (key, value) VALUES (?, ?)", (key, encoded_value))

    def delete(self, key: str) -> None:
        """
        Removes the entry associated with the specified key.

        Args:
            key (str): The key of the entry to be deleted.
        """
        self.cursor.execute("DELETE FROM FlashSQL WHERE key = ?", (key,))

    def close(self) -> None:
        """
        Closes the database connection and releases all resources.
        """
        self.conn.close()

    def exists(self, key: str) -> bool:
        """
        Checks if a key exists in the database.

        Args:
            key (str): The key to check for existence.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        self.cursor.execute("SELECT 1 FROM FlashSQL WHERE key = ? LIMIT 1", (key,))
        return self.cursor.fetchone() is not None

    def keys(self, pattern: str = "%") -> List[str]:
        """
        Retrieves a list of keys matching the specified pattern.

        Args:
            pattern (str): SQL LIKE pattern to match keys. Defaults to "%" which matches all keys.

        Returns:
            List[str]: A list of keys that match the pattern.
        """
        self.cursor.execute("SELECT key FROM FlashSQL WHERE key LIKE ?", (pattern,))
        return [row[0] for row in self.cursor.fetchall()]
