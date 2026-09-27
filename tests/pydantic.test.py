"""TEST: pydantic — ValidationError from string passed as integer field."""

from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# WRONG (ValidationError: age must be an integer, not a string)
user = User(name="Alice", age="not-a-number")

# CORRECT
# user = User(name="Alice", age=25)
