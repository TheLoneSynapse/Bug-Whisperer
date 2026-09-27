"""TEST: scipy — LinAlgError from inverting a singular matrix."""

import numpy as np
from scipy.linalg import inv

# WRONG (LinAlgError: singular matrix — rows are multiples of each other)
result = inv(np.array([[1, 2], [2, 4]]))

# CORRECT
# result = inv(np.array([[1, 2], [3, 4]]))
