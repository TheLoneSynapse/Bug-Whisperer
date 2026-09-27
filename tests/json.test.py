"""TEST: json — JSONDecodeError from single quotes instead of double quotes."""

import json

# WRONG (JSONDecodeError: Expecting property name enclosed in double quotes)
data = json.loads("{'name': 'Alice', 'age': 25}")

# CORRECT
# data = json.loads('{"name": "Alice", "age": 25}')
