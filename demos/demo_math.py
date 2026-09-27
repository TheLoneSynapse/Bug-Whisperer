"""DEMO: math mistake — dividing by zero using math.floor on bad input.

Run with:
    .\run.bat demos\demo_math.py
"""

import math

# WRONG (ValueError: math domain error — sqrt of a negative number)
result = math.sqrt(-9)

# CORRECT (only pass non-negative numbers to sqrt)
result = math.sqrt(9)
print("Square root:", result)
