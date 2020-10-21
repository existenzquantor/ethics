"""
Test the diffrent ways to describe UCAMs in a data file.
"""

from ethics.ucam.semantics import UncertainModel
from ethics.language import Atom, Affects, GEq, Impl, Not, Uo
from ethics.ucam.principles import Threshold, DecisionTheoreticUtilitarianism, Minimax

goals = UncertainModel("./cases/ucam/flowers.yaml", {"giveflowers": 1})
mechanisms = UncertainModel("./cases/ucam/drowning.yaml", {"goLeft": 1})
information = UncertainModel("./cases/ucam/drug.yaml", {"giveDrug": 1})
utilities = UncertainModel("./cases/ucam/drone.yaml", {"shoot": 1})
affects = UncertainModel("./cases/ucam/loudMusic.yaml", {"hearMusic": 1})
action = UncertainModel("./cases/ucam/flowersWithGive.yaml")

# goals
print(repr(goals))

for s in goals.situations:
    print(repr(s))
    print()

assert goals.necessary(Impl(Atom('giveflowers'), Atom('alicehappy'))) is True

assert goals.evaluate(Threshold, reading=2, threshold=0.8) is True
assert goals.evaluate(Threshold, reading=2, threshold=0.1) is True
assert goals.evaluate(Threshold, reading=2, threshold=0.9) is False

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

assert mechanisms.evaluate(DecisionTheoreticUtilitarianism) is False # goLeft
mechanisms = mechanisms.different_action("goRight")
assert mechanisms.evaluate(DecisionTheoreticUtilitarianism) is True # goRight

# information
print(repr(information))

for s in information.situations:
    print(repr(s))
    print()

assert information.necessary(Affects("patientDead", "patient")) is True

assert information.possible(Atom("drugDeadly")) is True

assert information.probability(Atom("patientDead"), "giveDrug") == 0.1

assert information.probability(GEq(Uo("giveDrug"), 1), "giveDrug") == 0.9

assert information.evaluate(DecisionTheoreticUtilitarianism) is True # giveDrug
information = information.different_action("refrain")
assert information.evaluate(DecisionTheoreticUtilitarianism) is False # refrain

# utilities
print(repr(utilities))

for s in utilities.situations:
    print(repr(s))
    print()

assert utilities.necessary(Impl(Atom('shoot'), Atom('targetDead'))) is True

assert utilities.probability(GEq(Uo("shoot"), 100), "shoot") == 0.9

assert utilities.evaluate(DecisionTheoreticUtilitarianism) is True
assert utilities.evaluate(Minimax) is False

# affects
print(repr(affects))

for s in affects.situations:
    print(repr(s))
    print()

assert affects.necessary(Impl(Atom('hearMusic'), Atom('fun'))) is True

assert affects.evaluate(Threshold, reading=2, threshold=0.8) is True
assert affects.evaluate(Threshold, reading=2, threshold=0.1) is True
assert affects.evaluate(Threshold, reading=2, threshold=0.9) is False

# action
print(repr(action))

for s in action.situations:
    print(repr(s))
    print()

assert action.evaluate(Threshold, reading=2, threshold=0.8) is True
