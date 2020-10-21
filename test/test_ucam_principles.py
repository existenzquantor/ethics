"""
Test the uncertain ethical principles.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.ucam.principles import Threshold, Category, SmallestRisk,\
                                   DecisionTheoreticUtilitarianism,\
                                   Minimax, NegativeUtilitarianism,\
                                   WeakNegativeUtilitarianism

roulette = UncertainModel("./cases/ucam/roulette.yaml", {"play": 1})
farmland = UncertainModel("./cases/ucam/farmland.yaml", {"takeFarmland": 1})
farmland_uncertain_food_Farmland = farmland.different_situations([
    {"probability": 0.5},
    {"probability": 0.2, "information": ["littleFood"]},
    {"probability": 0.3, "information": ["childrenInFarmland"]}])
farmland_uncertain_food_Road = farmland_uncertain_food_Farmland.different_action("takeRoad")
drug_give = UncertainModel("./cases/ucam/drug.yaml", {"giveDrug": 1})
drug_refrain = drug_give.different_action("refrain")
coldWar_superiority = UncertainModel("./cases/ucam/coldWar.yaml", {"USSuperiority": 1})
coldWar_equivalence = coldWar_superiority.different_action("USEquivalence")

# Threshold
assert roulette.evaluate(Threshold, reading=2, threshold=0.8) is True
assert roulette.evaluate(Threshold, reading=2, threshold=0.1) is True
assert roulette.evaluate(Threshold, reading=2, threshold=0.9) is False
assert roulette.evaluate(Threshold, reading=1, threshold=0.9) is True

# Category
assert farmland.evaluate(Category,
                         reading=2, t_value=(5, 2), t_risk=(0.3, 0.2)) is True
assert farmland.evaluate(Category,
                         reading=2, t_value=(10, 5), t_risk=(0.5, 0.3)) is True
assert farmland.evaluate(Category,
                         reading=2, t_value=(10, 5), t_risk=(0.2, 0.1)) is False
assert farmland.evaluate(Category,
                         reading=2, t_value=(100, 10), t_risk=(0.3, 0.2)) is False

# SmallestRisk
assert farmland_uncertain_food_Farmland.evaluate(SmallestRisk, reading=2) is False
assert farmland_uncertain_food_Road.evaluate(SmallestRisk, reading=2) is True

# DecisionTheoreticUtilitarianism
assert farmland_uncertain_food_Farmland.evaluate(DecisionTheoreticUtilitarianism) is True
assert farmland_uncertain_food_Road.evaluate(DecisionTheoreticUtilitarianism) is False

# Minimax
assert drug_give.evaluate(Minimax) is False
assert drug_refrain.evaluate(Minimax) is True

# NegativeUtilitarianism
assert drug_give.evaluate(NegativeUtilitarianism) is True
assert drug_refrain.evaluate(NegativeUtilitarianism) is False

# WeakNegativeUtilitarianism
assert coldWar_superiority.evaluate(WeakNegativeUtilitarianism) is False
assert coldWar_equivalence.evaluate(WeakNegativeUtilitarianism) is False
coldWar_equivalence.actions.remove("USNuclearDisarmament")
coldWar_superiority.actions.remove("USNuclearDisarmament")
assert coldWar_superiority.evaluate(WeakNegativeUtilitarianism) is True
assert coldWar_equivalence.evaluate(WeakNegativeUtilitarianism) is True
