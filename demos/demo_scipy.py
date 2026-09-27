"""DEMO: scipy mistake — inverting a singular (non-invertible) matrix.

Run with:
    .\run.bat demos\demo_scipy.py
"""

import numpy as np
from scipy.linalg import inv

# WRONG (LinAlgError: singular matrix — rows are multiples of each other)
singular = np.array([[1, 2], [2, 4]])
result = inv(singular)

# CORRECT (use a non-singular matrix)
good = np.array([[1, 2], [3, 4]])
result = inv(good)
print("Inverse:\n", result)
