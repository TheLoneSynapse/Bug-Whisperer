"""TEST: numpy — ValueError from shape mismatch when adding two arrays."""

import numpy as np

a = np.array([1, 2, 3])
b = np.array([1, 2])

# WRONG (ValueError: shapes (3,) and (2,) do not match)
print(a + b)

# CORRECT
# b_fixed = np.array([1, 2, 3])
# print(a + b_fixed)
