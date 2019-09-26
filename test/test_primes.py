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

    def test_paper_formula(self):

        # First using the normal approach (with QM)
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))),
            use_mhs_only=False)

        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))

        self.assertEqual(result, ([['a', 'c'], ['b', 'c']], [['a', 'b'], ['c']]))

        # Then again using only mhs
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))),
            use_mhs_only=True)

        result = pc.compile()
        result = (sorted(result[0]), sorted(result[1]))

        self.assertEqual(result, ([['a', 'c'], ['b', 'c']], [['a', 'b'], ['c']]))


    def test_long_formula_mhs_gde(self):
        pc = PrimeCompilator(And(And(And(And(GEq(U(Atom('refrain')), 0), Or(And(I(Atom('d1')), Good(Atom('d1'))), And(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(Impl(I(Atom('d1')), Good(Atom('d1'))), Impl(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(And(And(Not(And(Causes(Atom('d1'), Atom('d1')), And(Bad(Atom('d1')), Good(Atom('d1'))))), Not(And(Causes(Atom('d1'), Not(Atom('d2'))), And(Bad(Atom('d1')), Good(Not(Atom('d2'))))))), Not(And(Causes(Not(Atom('d2')), 'd1'), And(Bad(Not(Atom('d2'))), Good(Atom('d1')))))), Not(And(Causes(Not(Atom('d2')), Not(Atom('d2'))), And(Bad(Not(Atom('d2'))), Good(Not(Atom('d2')))))))), Gt(U(And(Atom('d1'), Not(Atom('d2')))), 0)),
            use_mhs_only=True)
        r = pc.compile()

        # Todo: actually check for correct values
        self.assertEqual(len(r[0]), 22, "Number of prime implicants incorrect")
        self.assertEqual(len(r[1]), 28, "Number of prime implicates incorrect")


    def test_long_formula_qm(self):
        pc = PrimeCompilator(And(And(And(And(GEq(U(Atom('refrain')), 0), Or(And(I(Atom('d1')), Good(Atom('d1'))), And(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(Impl(I(Atom('d1')), Good(Atom('d1'))), Impl(I(Not(Atom('d2'))), Good(Not(Atom('d2')))))), And(And(And(Not(And(Causes(Atom('d1'), Atom('d1')), And(Bad(Atom('d1')), Good(Atom('d1'))))), Not(And(Causes(Atom('d1'), Not(Atom('d2'))), And(Bad(Atom('d1')), Good(Not(Atom('d2'))))))), Not(And(Causes(Not(Atom('d2')), 'd1'), And(Bad(Not(Atom('d2'))), Good(Atom('d1')))))), Not(And(Causes(Not(Atom('d2')), Not(Atom('d2'))), And(Bad(Not(Atom('d2'))), Good(Not(Atom('d2')))))))), Gt(U(And(Atom('d1'), Not(Atom('d2')))), 0)),
            use_mhs_only=False)
        r = pc.compile()

        # Todo: actually check for correct values
        self.assertEqual(len(r[0]), 22, "Number of prime implicants incorrect")
        self.assertEqual(len(r[1]), 28, "Number of prime implicates incorrect")

if __name__ == '__main__':
    unittest.main()