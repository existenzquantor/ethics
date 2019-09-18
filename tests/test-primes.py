from ethics.primes import *
from ethics.language import *

pc = PrimeCompilator(And(Not(Caused(Atom("d"))), Or(Causes(Atom("a"), Atom("b")), Atom("c"))))
r = pc.compile()
print(r)
