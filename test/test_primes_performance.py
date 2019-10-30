import unittest
import time
from ethics.primes import PrimeCompilator
from ethics.language import *


class TestPrimesPerformance(unittest.TestCase):

    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        elapsed = time.time() - self.startTime
        print(str(self.id()) + ": " + str(round(elapsed, ndigits=4)) + "s")

    def test_DoubleEffectPrinciple_performance(self):
        endo_actions = ["a" + str(i) for i in range(5)]
        consequences = {"c1": True, "c2": False, "c3": True}
        consequence_literals = [Atom(name) if truth_value else Not(Atom(name)) for name, truth_value in consequences.items()]

        formulae = [Formula.makeConjunction([Not(Bad(Atom(a))) for a in endo_actions])]
        formulae += [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Goal(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Goal(Not(Atom(c))))) for c in consequences])]
        formulae += [Formula.makeDisjunction([And(Good(Atom(c)), Goal(Atom(c))) for c in consequences] + \
                            [And(Good(Not(Atom(c))), Goal(Not(Atom(c)))) for c in consequences])]
        formulae += [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Instrumental(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Instrumental(Not(Atom(c))))) for c in consequences])]
        formulae += [Gt(U(Formula.makeConjunction(consequence_literals)),0)]

        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula)
        compilator.compile()


    def test_DoNoInstrumentalHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False, "c5": False, "c6": False}

        formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Instrumental(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Instrumental(Not(Atom(c))))) for c in consequences])]

        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula)
        compilator.compile()


    def test_DoNolHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False, "c5": False, "c6": False}

        formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Caused(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Caused(Not(Atom(c))))) for c in consequences])]

        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula)
        compilator.compile()


    def test_AvoidAvoidableHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False}

        formulae = [Formula.makeConjunction([Impl(And(Bad(Atom(c)), Finally(Atom(c))), Not(Avoidable(Atom(c)))) for c in consequences] + \
                            [Impl(And(Bad(Not(Atom(c))), Finally(Not(Atom(c)))), Not(Avoidable(Not(Atom(c))))) for c in consequences])]

        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula)
        compilator.compile()



if __name__ == '__main__':
    unittest.main()
