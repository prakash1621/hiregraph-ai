from pydantic import BaseModel
from typing import Literal

class SeniorityClassification(BaseModel):
    level: Literal[
        "junior",
        "mid",
        "senior",
        "executive"
    ]