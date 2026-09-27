"""TEST: requests — MissingSchema from URL without http:// scheme."""

import requests

# WRONG (MissingSchema: No scheme supplied. Perhaps you meant https://google.com?)
response = requests.get("google.com")

# CORRECT
# response = requests.get("https://google.com")
