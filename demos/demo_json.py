"""DEMO: json mistake — malformed JSON string (single quotes instead of double).

Run with:
    .\run.bat demos\demo_json.py
"""

import json

# WRONG (JSONDecodeError: JSON keys must use double quotes, not single quotes)
data = json.loads("{'name': 'Alice', 'age': 25}")

# CORRECT (use double quotes)
data = json.loads('{"name": "Alice", "age": 25}')
print("Parsed:", data)
