import unittest
import time
from ethics.primes import PrimeCompilator
from ethics.language import *


class TestPrimes(unittest.TestCase):

    def sortedResult(self, result):
        implicants = result[0]
        implicates = result[1]

        sortedImplicants = []
        sortedImplicates = []

        for implicant in sorted(implicants, key=lambda i: str(i)):
            sortedImplicants.append(sorted(implicant, key=lambda i: str(i)))

        for implicate in sorted(implicates, key=lambda i: str(i)):
            sortedImplicates.append(sorted(implicate, key=lambda i: str(i)))

        return (sortedImplicants, sortedImplicates)

    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        elapsed = time.time() - self.startTime
        print(str(self.id()) + ": " + str(round(elapsed, ndigits=4)) + "s")

    def test_basic(self):
        pc = PrimeCompilator(Atom("a"))

        result = self.sortedResult(pc.compile())
        self.assertEqual(result, ([['a']], [['a']]))

    def test_empty(self):
        pc = PrimeCompilator(And(Atom("a"), Not(Atom('a'))))

        result = self.sortedResult(pc.compile())

        self.assertEqual(result, ([], [])) # not satisfiable

    def test_non_boolean(self):
        pc = PrimeCompilator(Good(Atom("a")))
        result = self.sortedResult(pc.compile())

        self.assertEqual(result, ([[Good('a')]], [[Good('a')]]))

    def test_paper_formula(self):

        # Then again using only mhs
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))))

        result = pc.compile()

        result = self.sortedResult(result)
        self.assertEqual(result, ([['a', 'c'], ['b', 'c']], [['a', 'b'], ['c']]))

    def test_paper_formula_negated(self):

        # Then again using only mhs
        pc = PrimeCompilator(Or(And(Or(And(Atom("a"), Atom("b")), And(Atom("a"), Not(Atom("b")))), Atom("c")), And(Atom("b"), Atom("c"))).getNegation())

        result = self.sortedResult(pc.compile())
        #result = (sorted(result[0], key=lambda i: str(i)), sorted(result[1], key=lambda i: str(i)))

        self.assertEqual(result, ([[Not('a'), Not('b')], [Not('c')]], [[Not('a'), Not('c')], [Not('b'), Not('c')]]))

    def test_biImpl(self):
        formula = BiImpl(Atom("a"), Atom("b"))

        pc = PrimeCompilator(formula)
        result = self.sortedResult(pc.compile())
        #result = (sorted(result[0], key=lambda i: str(i)), sorted(result[1], key=lambda i: str(i)))

        self.assertEqual(result[0], [['a', 'b'], [Not('a'), Not('b')]])
        self.assertEqual(result[1], [[Not('a'), 'b'], [Not('b'), 'a']])


if __name__ == '__main__':
    unittest.main()
