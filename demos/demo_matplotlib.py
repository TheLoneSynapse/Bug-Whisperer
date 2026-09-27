"""DEMO: matplotlib mistake — invalid color name passed to plot.

Run with:
    .\run.bat demos\demo_matplotlib.py
"""

import matplotlib.pyplot as plt

fig, ax = plt.subplots()

# WRONG (ValueError: 'notacolor' is not a valid color)
ax.plot([1, 2, 3], [4, 5, 6], color="notacolor")

# CORRECT (use a valid color name)
ax.plot([1, 2, 3], [4, 5, 6], color="blue")

plt.savefig("output.png")
