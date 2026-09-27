"""TEST: beautifulsoup4 — FeatureNotFound from unknown parser name."""

from bs4 import BeautifulSoup

html = "<html><body><h1>Hello World</h1></body></html>"

# WRONG (FeatureNotFound: 'notaparser' is not a valid parser)
soup = BeautifulSoup(html, "notaparser")

# CORRECT
# soup = BeautifulSoup(html, "html.parser")
