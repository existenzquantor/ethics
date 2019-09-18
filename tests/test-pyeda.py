from ethics.tools import *
f = And(Caused("d"), "a")
fp = convert_formula_to_pyeda(f)
print(f, fp)

print(convert_pyeda_atom_to_hera("4361757365642827642729"))
