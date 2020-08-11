"""
Test ucam module.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.language import Atom, Affects

drug = UncertainModel("./cases/ucam/drug.yaml")

print(drug)

for s in drug.situations:
    print(s)
    print()

assert drug.necessary(Affects("patientDead", "patient")) is True

assert drug.possible(Atom("drugDeadly")) is True

assert drug.probability(Atom("patientDead"), "giveDrug") == 0.1

assert drug.utility_probability(1, "giveDrug") == 0.9

drug.situations[0].set_action("giveDrug")
assert drug.situations[0].get_utility() == 1

drug.situations[1].set_action("giveDrug")
assert drug.situations[1].get_utility() == -2

drug2 = drug.different_situations([{"probability": 0.8},
                                   {"probability": 0.2, "information": ["drugDeadly"]}])

for s in drug2.situations:
    print(s)
    print()

assert drug2.probability(Atom("patientDead"), "giveDrug") == 0.2

assert drug2.utility_probability(1, "giveDrug") == 0.8
