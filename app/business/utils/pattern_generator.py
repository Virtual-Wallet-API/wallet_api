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

        pattern = lambda: random.choice(list(DesignPatterns))

        design = {
            "pattern": pattern,
            "color": PatternGenerator.generate_color()
        }

        params = {}

        while True:
            match pattern():
                case DesignPatterns.GRID:
                    params = {"line_width": random.uniform(1, 5),
                              "spacing": random.randint(10, 30)}

                case DesignPatterns.STRIPES:
                    params = {"stripe_width": random.uniform(5, 20),
                              "angle": random.choice([0, 45, 90])}

                case DesignPatterns.DOTS:
                    params = {"dot_size": random.uniform(2, 10),
                              "spacing": random.randint(10, 30)}

                case DesignPatterns.WAVES:
                    params = {"wave_height": random.randint(5, 50),
                              "wave_frequency": random.randint(1, 10),
                              "wave_width": random.randint(1, 6)}

                case DesignPatterns.TRIANGLES:
                    params = {"triangle_width": random.uniform(10, 100),
                              "border_color": PatternGenerator.generate_color(),
                              "border_width": random.randint(0, 5)}

                case DesignPatterns.HEXAGONS:
                    params = {"hexagon_size": random.uniform(10, 100),
                              "border_color": PatternGenerator.generate_color(),
                              "border_width": random.randint(0, 5)}

                case _:
                    continue


            design["params"] = str(params)

            return design
