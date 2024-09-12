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
