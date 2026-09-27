"""TEST: pandas — KeyError from wrong column name (case-sensitive)."""

import pandas as pd

df = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})

# WRONG (KeyError: 'age' — column is 'Age' not 'age')
print(df["age"])

# CORRECT
# print(df["Age"])
