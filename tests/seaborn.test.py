"""TEST: seaborn — ValueError from passing None as data."""

import matplotlib
matplotlib.use("Agg")
import seaborn as sns
import matplotlib.pyplot as plt

# WRONG (ValueError: data is None but x='col' was specified)
sns.histplot(data=None, x="col")

# CORRECT
# import pandas as pd
# df = pd.DataFrame({"col": [1, 2, 3, 4, 5]})
# sns.histplot(data=df, x="col")
