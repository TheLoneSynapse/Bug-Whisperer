"""TEST: math — ValueError from taking sqrt of a negative number."""

import math

# WRONG (ValueError: math domain error — sqrt of negative)
result = math.sqrt(-9)

# CORRECT
# result = math.sqrt(9)
