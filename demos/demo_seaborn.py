"""DEMO: seaborn mistake — passing None as data with a column name.

Run with:
    .\run.bat demos\demo_seaborn.py
"""

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# WRONG (TypeError/ValueError: data is None but x='col' was specified)
sns.histplot(data=None, x="col")

# CORRECT (pass actual DataFrame data)
df = pd.DataFrame({"col": [1, 2, 3, 4, 5, 3, 2, 1]})
sns.histplot(data=df, x="col")
plt.savefig("seaborn_output.png")
print("Plot saved as seaborn_output.png")
