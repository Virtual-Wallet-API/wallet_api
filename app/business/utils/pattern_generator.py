import hashlib
import random

from app.models.card_design import DesignPatterns


class PatternGenerator:

    @classmethod
    def generate_color(cls) -> str:
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    @staticmethod
    def generate_pattern(card_id: int) -> dict:
        chash = hashlib.md5(str(card_id).encode("utf-8"))
        seed = int(chash.hexdigest(), 16) % 2 ** 32
        random.seed(seed)

        pattern = random.choice(list(DesignPatterns))

        design = {
            "pattern": pattern,
            "color": PatternGenerator.generate_color()
        }

        params = {}

        if pattern == DesignPatterns.GRID:
            params = {"line_width": random.uniform(1, 5),
                      "spacing": random.randint(10, 30)}

        elif pattern == DesignPatterns.STRIPES:
            params = {"stripe_width": random.uniform(5, 20),
                      "angle": random.choice([0, 45, 90])}

        elif pattern == DesignPatterns.DOTS:
            params = {"dot_size": random.uniform(2, 10),
                      "spacing": random.randint(10, 30)}

        design["params"] = str(params)

        return design
