"""DEMO: requests mistake — URL missing http:// scheme.

Run with:
    .\run.bat demos\demo_requests.py
"""

import requests

# WRONG (MissingSchema: No scheme supplied. Perhaps you meant https://google.com?)
response = requests.get("google.com")

# CORRECT (always include https://)
response = requests.get("https://google.com")
print("Status:", response.status_code)
