# LightDB

**LightDB** is a lightweight key-value store built on top of SQLite. It is designed for simplicity and efficiency, providing a straightforward interface for storing, retrieving, and managing key-value pairs in an SQLite database.

## Features

- **SQLite-based**: Utilizes SQLite for persistent storage.
- **In-memory Option**: Supports in-memory databases for transient data.
- **Efficient Storage**: Optimized with PRAGMA settings for performance.
- **Flexible Key Management**: Supports basic CRUD operations (Create, Read, Update, Delete) for keys.
- **Pattern Matching**: Allows retrieval of keys based on patterns using SQL LIKE queries.
- **High Performance**: Designed for high performance with optimized SQLite settings.
- **Fast Access Times**: Provides quick access to stored values with efficient querying and indexing.

## Installation

You can install LightSQL using pip:

```bash
pip install lightsql
```

## Usage

### Initialization

To initialize a new instance of LightDB, provide the file path to the SQLite database. Use `":memory:"` for an in-memory database.

```python
from lightdb import LightDB

# For a file-based database
db = LightDB('database.db')

# For an in-memory database
db = LightDB(':memory:')
```

### Storing Values

Use the `set` method to store a value under a specific key. If the key already exists, the value will be updated.

```python
db.set('key', 'value')
```

### Retrieving Values

Use the `get` method to retrieve the value associated with a key. If the key does not exist, `None` is returned.

```python
value = db.get('key')
print(value)  # Output: 'value'
```

### Deleting Values

Use the `delete` method to remove a key-value pair from the database.

```python
db.delete('key')
```

### Checking Key Existence

Use the `exists` method to check if a key is present in the database.

```python
exists = db.exists('key')
print(exists)  # Output: False (if the key has been deleted)
```

### Retrieving Keys

Use the `keys` method to retrieve a list of keys matching a specified pattern. 

```python
keys = db.keys('%')
print(keys) # Output: key
```

### Closing the Database

Use the `close` method to close the database connection.

```python
db.close()
```

## Full Example

```python
from lightdb import LightDB

# Initialize the database
db = LightDB(':memory:')

# Store values
db.set('name', 'hexa')
db.set('age', 5)

# Retrieve values
print(db.get('name'))  # Output: 'hexa'
print(db.get('age'))   # Output: 5

# Check existence
print(db.exists('name'))  # Output: True
print(db.exists('address'))  # Output: False

# Retrieve keys with a pattern
print(db.keys('na%'))  # Output: ['name']

# Delete a key
db.delete('name')

# Close the database
db.close()
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues to improve the functionality and performance of LightDB.
