"""
Test the explantion of uncertain ethical principles.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.ucam.principles import Threshold, Category, SmallestRisk,\
                                   DecisionTheoreticUtilitarianism,\
                                   Minimax, NegativeUtilitarianism,\
                                   WeakNegativeUtilitarianism

roulette = UncertainModel("./cases/ucam/roulette.yaml")
farmland = UncertainModel("./cases/ucam/farmland.yaml")
farmland_uncertain_food = farmland.different_situations([
    {"probability": 0.5},
    {"probability": 0.2, "information": ["littleFood"]},
    {"probability": 0.3, "information": ["childrenInFarmland"]}])
drug = UncertainModel("./cases/ucam/drug.yaml")
coldWar = UncertainModel("./cases/ucam/coldWar.yaml")

# Threshold
print("\nThershold:\n")
print(roulette.explain(Threshold, "play", reading=2, threshold=0.8))

# Category
print("\nCategory:\n")
print(farmland.explain(Category, "takeFarmland",
                       reading=2, t_value=(5, 2), t_risk=(0.3, 0.2)))

# SmallestRisk
print("\nSmallest Risk:\n")
print(farmland_uncertain_food.explain(SmallestRisk, "takeFarmland", reading=2))

# DecisionTheoreticUtilitarianism
print("\nDecision Theoretic Utilitarianism:\n")
print(farmland_uncertain_food.explain(DecisionTheoreticUtilitarianism, "takeFarmland"))

# Minimax
print("\nMinimax:\n")
print(drug.explain(Minimax, "giveDrug"))

# NegativeUtilitarianism
print("\nNegative Utilitarianism:\n")
print(drug.explain(NegativeUtilitarianism, "giveDrug"))

# WeakNegativeUtilitarianism
print("\nWeakNegativeUtilitarianism:\n")
print(coldWar.explain(WeakNegativeUtilitarianism, "USSuperiority"))
coldWar.actions.remove("USNuclearDisarmament")
print("\n")
print(coldWar.explain(WeakNegativeUtilitarianism, "USSuperiority"))
