"""
Test the uncertain ethical principles.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.ucam.principles import Threshold, Category, SmallestRisk

roulette = UncertainModel("./cases/ucam/roulette.yaml")
farmland = UncertainModel("./cases/ucam/farmland.yaml")
farmland_uncertain_food = farmland.different_situations([
    {"probability": 0.5},
    {"probability": 0.2, "information": ["littleFood"]},
    {"probability": 0.3, "information": ["childrenInFarmland"]}])

# Threshold
assert roulette.evaluate(Threshold, "play", reading=2, threshold=0.8) is True
assert roulette.evaluate(Threshold, "play", reading=2, threshold=0.1) is True
assert roulette.evaluate(Threshold, "play", reading=2, threshold=0.9) is False
assert roulette.evaluate(Threshold, "play", reading=1, threshold=0.9) is True

# Category
assert farmland.evaluate(Category, "takeFarmland",
                         reading=2, t_value=(5, 2), t_risk=(0.3, 0.2)) is True
assert farmland.evaluate(Category, "takeFarmland",
                         reading=2, t_value=(10, 5), t_risk=(0.5, 0.3)) is True
assert farmland.evaluate(Category, "takeFarmland",
                         reading=2, t_value=(10, 5), t_risk=(0.2, 0.1)) is False
assert farmland.evaluate(Category, "takeFarmland",
                         reading=2, t_value=(100, 10), t_risk=(0.3, 0.2)) is False

# SmallestRisk
assert farmland_uncertain_food.evaluate(SmallestRisk, "takeFarmland", reading=2) is False
assert farmland_uncertain_food.evaluate(SmallestRisk, "takeRoad", reading=2) is True
