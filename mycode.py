"""DEMO: wrong code on purpose -- replace me with your own mistake.

HOW TO USE THIS FILE
--------------------
1.  Paste YOUR wrong code over everything below (keep it one .py file).
2.  In the VS Code terminal (project root, .venv interpreter), run:

        mistake-box python mycode.py      # run it -> box any runtime/syntax error
        mistake-box --file mycode.py      # static syntax check only, no run

    And, if your mistake lives in a test instead:

        pytest

3.  Read the box: WHERE (file:line + your line + caret),
    WHAT WENT WRONG (exception + message), SUGGESTIONS (concrete fixes).
4.  Want the demo back? Restore the code below from git, or just re-paste it.

DEMO BUG (below): df["age"] uses the wrong case — pandas columns are
case-sensitive, so it raises KeyError: 'age' before the correct line runs.
"""


import pandas as pd

df = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})

# WRONG (Causes KeyError because 'age' is lowercase)
print(df["age"])

# CORRECT (Column names are case-sensitive)
print(df["Age"])