"""TEST: scikit-learn — ValueError from passing 1D array to fit()."""

import numpy as np
from sklearn.linear_model import LinearRegression

model = LinearRegression()

# WRONG (ValueError: Expected 2D array, got 1D array)
model.fit(np.array([1, 2, 3]), np.array([1, 2, 3]))

# CORRECT
# model.fit(np.array([1, 2, 3]).reshape(-1, 1), np.array([1, 2, 3]))
