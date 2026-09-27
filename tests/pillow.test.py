"""TEST: Pillow (PIL) — FileNotFoundError from opening a missing image."""

from PIL import Image

# WRONG (FileNotFoundError: No such file or directory: 'ghost.png')
img = Image.open("ghost.png")

# CORRECT
# img = Image.new("RGB", (100, 100), color="red")
