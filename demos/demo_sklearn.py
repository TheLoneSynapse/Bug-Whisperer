"""DEMO: scikit-learn mistake — passing a 1D array instead of 2D to fit().

Run with:
    .\run.bat demos\demo_sklearn.py
"""

import numpy as np
from sklearn.linear_model import LinearRegression

model = LinearRegression()

# WRONG (ValueError: Expected 2D array, got 1D array)
model.fit(np.array([1, 2, 3]), np.array([1, 2, 3]))

# CORRECT (reshape to 2D with .reshape(-1, 1))
model.fit(np.array([1, 2, 3]).reshape(-1, 1), np.array([1, 2, 3]))
print("Model trained successfully.")
