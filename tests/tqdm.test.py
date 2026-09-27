"""TEST: tqdm — TypeError from iterating over None."""

from tqdm import tqdm

# WRONG (TypeError: 'NoneType' object is not iterable)
for item in tqdm(None):
    print(item)

# CORRECT
# for item in tqdm(range(5), desc="Processing"):
#     pass
