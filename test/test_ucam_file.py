"""
Test the diffrent ways to describe UCAMs in a data file.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.language import Atom, Affects, GEq, Impl, Not, Uo
from ethics.ucam.principles import Threshold, DecisionTheoreticUtilitarianism, Minimax

goals = UncertainModel("./cases/ucam/flowers.yaml")
mechanisms = UncertainModel("./cases/ucam/drowning.yaml")
information = UncertainModel("./cases/ucam/drug.yaml")
utilities = UncertainModel("./cases/ucam/drone.yaml")
affects = UncertainModel("./cases/ucam/loudMusic.yaml")

# goals
print(repr(goals))

for s in goals.situations:
    print(repr(s))
    print()

assert goals.necessary(Impl(Atom('giveflowers'), Atom('alicehappy'))) is True

assert goals.evaluate(Threshold, "giveflowers", reading=2, threshold=0.8) is True
assert goals.evaluate(Threshold, "giveflowers", reading=2, threshold=0.1) is True
assert goals.evaluate(Threshold, "giveflowers", reading=2, threshold=0.9) is False

# mechanisms
print(repr(mechanisms))

for s in mechanisms.situations:
    print(repr(s))
    print()

assert mechanisms.necessary(Impl(Atom('refrain'), Not(Atom('rightGroupSaved')))) is True
assert mechanisms.necessary(Impl(Atom('goRight'), Atom('rightGroupSaved'))) is False

assert mechanisms.possible(Impl(Atom('goRight'), Atom('rightGroupSaved'))) is True

assert mechanisms.probability(Impl(Atom('goLeft'), Atom('leftGroupSaved')), 'goLeft') == 0.98

assert mechanisms.probability(GEq(Uo("goLeft"), 7), "goLeft") == 0.98

assert mechanisms.evaluate(DecisionTheoreticUtilitarianism, "goLeft") is False
assert mechanisms.evaluate(DecisionTheoreticUtilitarianism, "goRight") is True

# information
print(repr(information))

for s in information.situations:
    print(repr(s))
    print()

assert information.necessary(Affects("patientDead", "patient")) is True

assert information.possible(Atom("drugDeadly")) is True

assert information.probability(Atom("patientDead"), "giveDrug") == 0.1

assert information.probability(GEq(Uo("giveDrug"), 1), "giveDrug") == 0.9

assert information.evaluate(DecisionTheoreticUtilitarianism, "giveDrug") is True
assert information.evaluate(DecisionTheoreticUtilitarianism, "refrain") is False

# utilities
print(repr(utilities))

for s in utilities.situations:
    print(repr(s))
    print()

assert utilities.necessary(Impl(Atom('shoot'), Atom('targetDead'))) is True

assert utilities.probability(GEq(Uo("shoot"), 100), "shoot") == 0.9

assert utilities.evaluate(DecisionTheoreticUtilitarianism, "shoot") is True
assert utilities.evaluate(Minimax, "shoot") is False

# affects
print(repr(affects))

for s in affects.situations:
    print(repr(s))
    print()

assert affects.necessary(Impl(Atom('hearMusic'), Atom('fun'))) is True

assert affects.evaluate(Threshold, "hearMusic", reading=2, threshold=0.8) is True
assert affects.evaluate(Threshold, "hearMusic", reading=2, threshold=0.1) is True
assert affects.evaluate(Threshold, "hearMusic", reading=2, threshold=0.9) is False
