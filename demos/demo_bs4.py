"""DEMO: beautifulsoup4 mistake — using a non-existent parser name.

Run with:
    .\run.bat demos\demo_bs4.py
"""

from bs4 import BeautifulSoup

html = "<html><body><h1>Hello World</h1></body></html>"

# WRONG (FeatureNotFound: 'notaparser' is not a valid parser)
soup = BeautifulSoup(html, "notaparser")

# CORRECT (use 'html.parser' which is built into Python)
soup = BeautifulSoup(html, "html.parser")
print("Title tag:", soup.find("h1").text)
