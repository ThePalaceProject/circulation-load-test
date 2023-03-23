import random
import os
from pathlib import Path
from typing import List

class Words:
    """Access to random english words."""
    _words: List[str] = []

    @classmethod
    def _initialize(cls):
        if cls._words == []:
            file = os.path.join(Path(__file__).parent, "words.txt")
            with open(file, "r") as f:
                cls._words = f.readlines()
                random.shuffle(cls._words)

    @classmethod
    def get(cls) -> str:
        cls._initialize()
        return random.choice(cls._words)
