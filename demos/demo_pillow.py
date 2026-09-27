"""DEMO: Pillow (PIL) mistake — trying to open a file that doesn't exist.

Run with:
    .\run.bat demos\demo_pillow.py
"""

from PIL import Image

# WRONG (FileNotFoundError: No such file or directory: 'ghost.png')
img = Image.open("ghost.png")

# CORRECT (create a new image instead of opening a missing file)
img = Image.new("RGB", (100, 100), color="red")
img.save("demo_output.png")
print("Image saved as demo_output.png")
