import unittest
import time
from ethics.primes import *
from ethics.language import *

class TestPrimes(unittest.TestCase):

    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        elapsed = time.time() - self.startTime
        print(str(self.id()) + ": " + str(round(elapsed, ndigits=4)) + "s")
    
    def test_basic(self):
        pc = PrimeCompilator(Atom("a"))

        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))
        self.assertEqual(result, ([['a']], [['a']]))

        pc = PrimeCompilator(Not(Atom("a")), use_mhs_only=True)
        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))
        
        self.assertEqual(result, ([[Not('a')]], [[Not('a')]]))


    def test_empty(self):
        pc = PrimeCompilator(And(Atom("a"), Not(Atom('a'))), use_mhs_only=True)

        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))

        self.assertEqual(result, ([], [])) # not satisfiable

    
    def test_non_boolean(self):
        pc = PrimeCompilator(Good(Atom("a")), use_mhs_only=True)
        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))

        self.assertEqual(result, ([[Good('a')]], [[Good('a')]]))


    def test_paper_formula(self):

        # Then again using only mhs
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))),
            use_mhs_only=True)

        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))

        self.assertEqual(result, ([['a', 'c'], ['b', 'c']], [['a', 'b'], ['c']]))
    

    def test_paper_formula_negated(self):

        # Then again using only mhs
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))).getNegation(),
            use_mhs_only=True)

        result = pc.compile()
        result = (sorted(result[0], key=lambda i: str(i)), sorted(result[1], key=lambda i: str(i)))

        self.assertEqual(result, ([[Not('a'), Not('b')], [Not('c')]], [[Not('a'), Not('c')], [Not('b'), Not('c')]]))


    def test_long_formula_mhs_gde(self):
        pc = PrimeCompilator(And(And(And(And(GEq(U(Atom('refrain')), 0), Or(And(I(Atom('d1')), Good(Atom('d1'))), And(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(Impl(I(Atom('d1')), Good(Atom('d1'))), Impl(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(And(And(Not(And(Causes(Atom('d1'), Atom('d1')), And(Bad(Atom('d1')), Good(Atom('d1'))))), Not(And(Causes(Atom('d1'), Not(Atom('d2'))), And(Bad(Atom('d1')), Good(Not(Atom('d2'))))))), Not(And(Causes(Not(Atom('d2')), 'd1'), And(Bad(Not(Atom('d2'))), Good(Atom('d1')))))), Not(And(Causes(Not(Atom('d2')), Not(Atom('d2'))), And(Bad(Not(Atom('d2'))), Good(Not(Atom('d2')))))))), Gt(U(And(Atom('d1'), Not(Atom('d2')))), 0)),
            use_mhs_only=True)
        r = pc.compile()
        r = (sorted(r[0], key=lambda i: str(i)), sorted(r[1], key=lambda i: str(i)))

        self.assertEqual(len(r[0]), 22, "Number of prime implicants incorrect")
        self.assertEqual(len(r[1]), 28, "Number of prime implicates incorrect")

        self.assertEqual(r[0], [[GEq(U('refrain'), 0), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Good(Not('d2'))), Not(Bad('d1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Good(Not('d2'))), Not(Causes('d1', 'd1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Good('d1'), I(Not('d2')), Good(Not('d2')), Not(Bad('d1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Good('d1'), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2')))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Good(Not('d2')), Not(Bad('d1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2')))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Bad('d1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2')))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Good(Not('d2'))), Not(Causes('d1', 'd1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), I(Not('d2')), Good(Not('d2')), Not(Bad('d1'))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2')))], [GEq(U('refrain'), 0), Not(Bad(Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), Not(Good('d1')), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', Not('d2')))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Good('d1'), I(Not('d2')), Good(Not('d2')), Not(Bad('d1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Good('d1'), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Good(Not('d2')), Not(Bad('d1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Bad('d1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), I('d1'), Good('d1'), Not(I(Not('d2'))), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), I(Not('d2')), Good(Not('d2')), Not(Bad('d1')), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Causes('d1', Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), Not(Good('d1')), I(Not('d2')), Good(Not('d2')), Not(Bad('d1'))], [GEq(U('refrain'), 0), Not(Causes(Not('d2'), Not('d2'))), Gt(U(And('d1', Not('d2'))), 0), Not(I('d1')), Not(Good('d1')), I(Not('d2')), Good(Not('d2')), Not(Causes('d1', Not('d2')))]])
        self.assertEqual(r[1], [[GEq(U('refrain'), 0)], [Good('d1'), Good(Not('d2'))], [Good('d1'), I(Not('d2'))], [Good('d1'), Not(Bad('d1')), Not(Causes('d1', Not('d2')))], [Good(Not('d2')), Not(Causes('d1', 'd1')), Not(Bad('d1'))], [Gt(U(And('d1', Not('d2'))), 0)], [I('d1'), Good(Not('d2'))], [I('d1'), I(Not('d2'))], [I('d1'), Not(Bad('d1')), Not(Causes('d1', Not('d2')))], [I(Not('d2')), Not(Causes('d1', 'd1')), Not(Bad('d1'))], [Not(Bad(Not('d2'))), Good(Not('d2')), Not(Causes(Not('d2'), 'd1'))], [Not(Bad(Not('d2'))), I(Not('d2')), Not(Causes(Not('d2'), 'd1'))], [Not(Bad(Not('d2'))), Not(Bad('d1')), Not(Causes('d1', Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), Good('d1')], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), I('d1')], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), Not(Causes('d1', 'd1')), Not(Bad('d1'))], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), Not(Causes(Not('d2'), 'd1'))], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), Not(Good(Not('d2')))], [Not(Bad(Not('d2'))), Not(Causes(Not('d2'), Not('d2'))), Not(I(Not('d2')))], [Not(Bad(Not('d2'))), Not(Good('d1')), Not(Causes(Not('d2'), 'd1'))], [Not(Bad(Not('d2'))), Not(I('d1')), Not(Causes(Not('d2'), 'd1'))], [Not(Causes('d1', 'd1')), Not(Bad('d1')), Not(Causes('d1', Not('d2')))], [Not(Good('d1')), Not(Causes('d1', 'd1')), Not(Bad('d1'))], [Not(Good(Not('d2'))), Not(Bad('d1')), Not(Causes('d1', Not('d2')))], [Not(I('d1')), Good('d1')], [Not(I('d1')), Not(Causes('d1', 'd1')), Not(Bad('d1'))], [Not(I(Not('d2'))), Good(Not('d2'))], [Not(I(Not('d2'))), Not(Bad('d1')), Not(Causes('d1', Not('d2')))]])


    def test_biImpl(self):
        formula = BiImpl(Atom("a"), Atom("b"))

        pc = PrimeCompilator(formula)
        result = pc.compile()
        result = (sorted(result[0], key=lambda i: str(i)), sorted(result[1], key=lambda i: str(i)))
        
        self.assertEqual(result[0], [['a', 'b'], [Not('a'), Not('b')]])
        self.assertEqual(result[1], [['a', Not('b')], [Not('a'), 'b']])
        

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

        compilator = PrimeCompilator(formula, use_mhs_only=True)
        compilator.compile()


    def test_DoNoInstrumentalHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False, "c5": False, "c6": False}

        formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Instrumental(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Instrumental(Not(Atom(c))))) for c in consequences])]
    
        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula, use_mhs_only=True)
        compilator.compile()


    def test_DoNolHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False, "c5": False, "c6": False}

        formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Caused(Atom(c)))) for c in consequences] + \
                            [Impl(Bad(Not(Atom(c))), Not(Caused(Not(Atom(c))))) for c in consequences])]
    
        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula, use_mhs_only=True)
        compilator.compile()


    def test_AvoidAvoidableHarm_performance(self):
        consequences = {"c1": True, "c2": False, "c3": True, "c4": False}

        formulae = [Formula.makeConjunction([Impl(And(Bad(Atom(c)), Finally(Atom(c))), Not(Avoidable(Atom(c)))) for c in consequences] + \
                            [Impl(And(Bad(Not(Atom(c))), Finally(Not(Atom(c)))), Not(Avoidable(Not(Atom(c))))) for c in consequences])]

        formula = Formula.makeConjunction(formulae)

        compilator = PrimeCompilator(formula, use_mhs_only=True)
        compilator.compile()
    


if __name__ == '__main__':
    unittest.main()