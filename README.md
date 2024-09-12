<div align="center">

# FlashSQL

**FlashSQL** is a high-performance key-value store built on SQLite with support for optional expiration. It offers a simple and efficient interface for storing, retrieving, and managing key-value pairs with additional features like pagination and database optimization.

[![PyPI Version](https://img.shields.io/pypi/v/flashsql?label=PyPI)](https://pypi.org/project/flashsql/)
[![Python Version](https://img.shields.io/pypi/pyversions/flashsql?label=Python)](https://pypi.org/project/flashsql/)
[![License](https://img.shields.io/pypi/l/flashsql?label=License)](https://opensource.org/licenses/MIT)

</div>

## Features

- **SQLite-based**: Utilizes SQLite for persistent storage.
- **In-memory Option**: Supports in-memory databases for transient data.
- **Expiration Support**: Allows setting an expiration time (TTL) for keys.
- **Efficient Storage**: Optimized with PRAGMA settings for performance.
- **Flexible Key Management**: Supports basic CRUD operations (Create, Read, Update, Delete) for keys.
- **Pattern Matching**: Allows retrieval of keys based on patterns using SQL LIKE queries.
- **Pagination**: Supports paginated retrieval of keys.
- **Database Optimization**: Includes methods to clean up expired keys and optimize database file size.
- **Fast Access Times**: Provides quick access to stored values with efficient querying and indexing.

## Installation

You can install FlashSQL using pip:

```bash
pip install FlashSQL
```

## Usage

### Initialization

To initialize a new instance of FlashSQL Client, provide the file path to the SQLite database. Use `":memory:"` for an in-memory database.

```python
from FlashSQL import Client

# For a file-based database
db = Client('database.db')

# For an in-memory database
db = Client(':memory:')
```

### Storing Values

Use the `set` method to store a value under a specific key. You can specify an expiration time (TTL) in seconds or leave it out for no expiration.

**Without Expiration:**

```python
db.set('name', 'hexa')
```

**With Expiration:**

```python
db.set('session', {'user': 'hexa'}, ttl=3600)  # Expires in 1 hour
```

### Storing Multiple Values

Use the `set_many` method to store multiple key-value pairs with optional expiration times in one batch.

```python
items = {
    'session1': ({'user': 'hexa1'}, 3600),  # Expires in 1 hour
    'session2': ({'user': 'hexa2'}, 7200),  # Expires in 2 hours
}
db.set_many(items)
```

### Retrieving Values

Use the `get` method to retrieve the value associated with a key. If the key does not exist or has expired, `None` is returned.

```python
value = db.get('name')
print(value)  # Output: 'hexa'
```

**With Expiration:**

```python
value = db.get('session')
print(value)  # Output: {'user': 'hexa'} if within TTL
```

### Deleting Values

Use the `delete` method to remove a key-value pair from the database.

```python
db.delete('name')
```

### Deleting Multiple Values

Use the `delete_many` method to delete multiple key-value pairs in one batch.

```python
keys_to_delete = ['session1', 'session2']
db.delete_many(keys_to_delete)
```

### Checking Key Existence

Use the `exists` method to check if a key is present and not expired.

```python
exists = db.exists('name')
print(exists)  # Output: False (if the key was deleted)
```

### Renaming Keys

Use the `rename` method to rename an existing key.

```python
db.rename('old_key', 'new_key')
```

### Retrieving Expiration Date

Use the `get_expire` method to get the expiration date of a key.

```python
expire_date = db.get_expire('session')
print(expire_date)  # Output: ISO 8601 formatted expiration date or None
```

### Setting Expiration Date

Use the `set_expire` method to set a new expiration time (TTL) for an existing key.

```python
db.set_expire('session', ttl=7200)  # Expires in 2 hours
```

### Retrieving Keys

Use the `keys` method to retrieve a list of keys matching a specified pattern.

```python
keys = db.keys('%')
print(keys)  # Output: List of all keys
```

### Pagination

Use the `paginate` method to retrieve a paginated list of keys matching a pattern.

```python
paged_keys = db.paginate(pattern='key%', page=1, page_size=2)
print(paged_keys)  # Output: List of keys for the specified page
```

### Counting Keys

Use the `count` method to count the total number of keys in the database.

```python
total_keys = db.count()
print(total_keys)  # Output: Total number of keys
```

### Counting Expired Keys

Use the `count_expired` method to count the number of expired keys.

```python
expired_keys_count = db.count_expired()
print(expired_keys_count)  # Output: Number of expired keys
```

### Cleaning Up Expired Keys

Use the `cleanup` method to remove expired key-value pairs from the database. This is called automatically before any retrieval or key-checking operation.

```python
db.cleanup()
```

### Optimizing Database File

Use the `vacuum` method to optimize the database file and reduce its size.

```python
db.vacuum()
```

### Ensuring Changes Are Written to Disk

Use the `flush` method to ensure all changes are written to disk by performing a full checkpoint of the WAL (Write-Ahead Log).

```python
db.flush()
```

### Executing Raw SQL

Use the `execute` method to execute a raw SQL statement and return the result.

**Example:**

```python
results = db.execute("SELECT key FROM FlashDB WHERE key LIKE ?", ('key%',))
print(results)  # Output: Results of the raw SQL query
```

### Closing the Database

Use the `close` method to close the database connection.

```python
db.close()
```

### Popping Values

Use the `pop` method to retrieve and remove the value associated with a key.

```python
value = db.pop('session')
print(value)  # Output: {'user': 'hexa'} if within TTL and removed from the database
```

### Moving Values

Use the `move` method to move a value from one key to another.

```python
db.move('old_key', 'new_key')
```

### Updating Values

Use the `update` method to update the value of an existing key without changing its expiration.

```python
db.update('name', 'new_value')
```

## Full Example

```python
from FlashSQL import Client

# Initialize the database
db = Client(':memory:')

# Store values
db.set('name', 'hexa', ttl=3600)  # Expires in 1 hour
db.set('age', 30)

# Store multiple values
items = {
    'session1': ({'user': 'hexa1'}, 3600),  # Expires in 1 hour
    'session2': ({'user': 'hexa2'}, 7200),  # Expires in 2 hours
}
db.set_many(items)

# Retrieve values
print(db.get('name'))  # Output: 'hexa' if within TTL
print(db.get('age'))   # Output: 30

# Retrieve multiple values
keys = ['session1', 'session2']
print(db.get_many(keys))  # Output: {'session1': {'user': 'hexa1'}, 'session2': {'user': 'hexa2'}}

# Check existence
print(db.exists('name'))  # Output: True if within TTL
print(db.exists('address'))  # Output: False (if the key does not exist)

# Retrieve keys with a pattern
print(db.keys('se%'))  # Output: ['session1', 'session2']

# Delete a key
db.delete('name')

# Delete multiple keys
keys_to_delete = ['session1', 'session2']
db.delete_many(keys_to_delete)

# Rename a key
db.set('old_key', 'value')
db.rename('old_key', 'new_key')

# Retrieve expiration date
expire_date = db.get_expire('new_key')
print(expire_date)  # Output: ISO 8601 formatted expiration date or None

# Set expiration date
db.set_expire('new_key', ttl=7200)  # Expires in 2 hours

# Pop a value (retrieve and delete)
popped_value = db.pop('age')
print(popped_value)  # Output: 30

# Move a value from one key to another
db.move('new_key', 'moved_key')

# Update a value without changing its expiration
db.update('moved_key', 'updated_value')

# Clean up expired keys
db.cleanup()

# Optimize database file
db.vacuum()

# Ensure changes are written to disk
db.flush()

# Close the database
db.close()
```