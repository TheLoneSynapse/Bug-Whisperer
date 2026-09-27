"""
Test file: mistake-finder catching errors from various Python libraries.
Each test deliberately triggers a known error from a different library.
"""
import pytest

# ── pandas ──────────────────────────────────────────────────────────────────
def test_pandas_keyerror():
    import pandas as pd
    df = pd.DataFrame({"Name": ["Alice"], "Age": [25]})
    _ = df["age"]                          # KeyError: wrong case

# ── numpy ────────────────────────────────────────────────────────────────────
def test_numpy_shape_mismatch():
    import numpy as np
    a = np.array([1, 2, 3])
    b = np.array([1, 2])
    _ = a + b                              # ValueError: shape mismatch

# ── matplotlib ───────────────────────────────────────────────────────────────
def test_matplotlib_bad_color():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2], color="notacolor")   # ValueError: bad color
    plt.close()

# ── scikit-learn ─────────────────────────────────────────────────────────────
def test_sklearn_wrong_shape():
    from sklearn.linear_model import LinearRegression
    import numpy as np
    model = LinearRegression()
    model.fit(np.array([1, 2, 3]), np.array([1, 2, 3]))  # ValueError: 1D input

# ── requests ─────────────────────────────────────────────────────────────────
def test_requests_missing_schema():
    import requests
    requests.get("not-a-url")              # MissingSchema / InvalidSchema

# ── json ─────────────────────────────────────────────────────────────────────
def test_json_decode_error():
    import json
    json.loads("{bad json}")               # JSONDecodeError

# ── math ─────────────────────────────────────────────────────────────────────
def test_math_zero_division():
    import math
    result = math.factorial(-1)            # ValueError: negative factorial

# ── openpyxl ─────────────────────────────────────────────────────────────────
def test_openpyxl_bad_cell():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws["ZZZZ99999"] = "test"              # ValueError / bad cell reference

# ── beautifulsoup4 ───────────────────────────────────────────────────────────
def test_bs4_bad_parser():
    from bs4 import BeautifulSoup
    BeautifulSoup("<html></html>", "notaparser")  # FeatureNotFound error

# ── sqlalchemy ───────────────────────────────────────────────────────────────
def test_sqlalchemy_bad_url():
    from sqlalchemy import create_engine
    engine = create_engine("notavalidurl://")
    engine.connect()                       # ArgumentError / OperationalError

# ── pydantic ─────────────────────────────────────────────────────────────────
def test_pydantic_validation_error():
    from pydantic import BaseModel
    class User(BaseModel):
        name: str
        age: int
    User(name="Alice", age="not-a-number")  # ValidationError

# ── PIL / Pillow ─────────────────────────────────────────────────────────────
def test_pillow_bad_file():
    from PIL import Image
    Image.open("nonexistent_image.png")    # FileNotFoundError

# ── tqdm ─────────────────────────────────────────────────────────────────────
def test_tqdm_bad_total():
    from tqdm import tqdm
    list(tqdm(range(5), total=-999))       # runs but with a warning — passes OK

# ── scipy ────────────────────────────────────────────────────────────────────
def test_scipy_bad_matrix():
    from scipy.linalg import inv
    import numpy as np
    inv(np.array([[1, 2], [2, 4]]))        # LinAlgError: singular matrix

# ── seaborn ──────────────────────────────────────────────────────────────────
def test_seaborn_bad_data():
    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.histplot(data=None, x="col")       # TypeError / ValueError
    plt.close()
