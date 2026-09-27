"""DEMO: numpy mistake — shape mismatch when adding two arrays.

Run with:
    .\run.bat demos\demo_numpy.py
"""

import numpy as np

a = np.array([1, 2, 3])
b = np.array([1, 2])

# WRONG (ValueError: shapes (3,) and (2,) do not match)
print(a + b)

# CORRECT (arrays must have the same shape)
b_fixed = np.array([1, 2, 3])
print(a + b_fixed)
