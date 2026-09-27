"""TEST: matplotlib — ValueError from invalid color name."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

# WRONG (ValueError: 'notacolor' is not a valid color)
ax.plot([1, 2, 3], [4, 5, 6], color="notacolor")

# CORRECT
# ax.plot([1, 2, 3], [4, 5, 6], color="blue")
