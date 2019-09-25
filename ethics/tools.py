from ethics.language import *
from itertools import combinations, chain
import pyeda.inter
import time


def makeSetOfAlternatives(*models):
    for m in models:
        m.setAlternatives(*models)


def makeSetOfEpistemicAlternatives(*models):
    for m in models:
        m.setEpistemicAlternatives(*models)
        m.probability = 1/len(models)


def my_eval(content):
    try:
        f = sub_to_atoms(eval(content))
        return f
    except:
        return Atom(content)


def sub_to_atoms(f):
    if isinstance(f, str) and not isinstance(f, Atom) and not isinstance(f, bool) and not isinstance(f, Bool):
        return Atom(f)
    if isinstance(f, bool) and not isinstance(f, Bool):
        return Bool(f)
    if isinstance(f, Bool):
        return f
    if isinstance(f, OnePlaced):
        return type(f)(sub_to_atoms(f.f1))
    if isinstance(f, TwoPlaced):
        f1 = sub_to_atoms(f.f1)
        f2 = sub_to_atoms(f.f2)
        return type(f)(f1,f2)
    if isinstance(f, OnePlacedTerm):
        return type(f)(sub_to_atoms(f.t1))
    if isinstance(f, TwoPlacedTerm):
        f1 = sub_to_atoms(f.t1)
        f2 = sub_to_atoms(f.t2)
        return type(f)(f1,f2)
    return f


def mapBackToFormulae(l, m): # l: model, m: map
    erg = []
    for ll in l:
        found = False
        for mm in m:
            if m[mm] == ll:
                erg.append(my_eval(mm).nnf())
                found = True
                break
        if(found == False):
            for mm in m:
                if m[mm] + ll == 0:
                    erg.append(my_eval(mm).getNegation().nnf())
    return erg


def convert_formula_to_pyeda(formula):
    if isinstance(formula, Not):
        return pyeda.inter.Not(convert_formula_to_pyeda(formula.f1))
    if isinstance(formula, And):
        return pyeda.inter.And(convert_formula_to_pyeda(formula.f1), convert_formula_to_pyeda(formula.f2)) 
    if isinstance(formula, Or):
        return pyeda.inter.Or(convert_formula_to_pyeda(formula.f1), convert_formula_to_pyeda(formula.f2))
    if isinstance(formula, Impl):
        return pyeda.inter.Implies(convert_formula_to_pyeda(formula.f1), convert_formula_to_pyeda(formula.f2))
    if isinstance(formula, BiImpl):
        return pyeda.inter.Equal(convert_formula_to_pyeda(formula.f1), convert_formula_to_pyeda(formula.f2))
    return pyeda.inter.expr("v"+bytearray(str(formula).encode()).hex())


def convert_pyeda_atom_to_hera(atom):
    return my_eval(bytearray.fromhex(str(atom)[1:]).decode())


def convert_pyeda_model_to_hera(model):
    m = set()
    for v in model:
        if model[v] == 1:
            m.add(convert_pyeda_atom_to_hera(v))
        else:
            m.add(Not(convert_pyeda_atom_to_hera(v)))
    return m


def convert_hera_model_to_pyeda(model):
    m = dict()
    for l in model:
        if isinstance(l, Not):
            m[str(l.f1)] = 0
        else:
            m[str(l)] = 1
    return m


def powerset(s):
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def merge_lists(lol):
    return list(chain.from_iterable(lol))


def sub(c, d):
    x = []
    for i in range(len(c)):
        x.append(c[i] - d[i])
    if 1 in x and -1 not in x:
        return True
    return False


def minimalsets(cand):
    mins = []
    for c in cand:
        found = False
        for d in cand:
            if sub(c, d): # detect non-minimal
                found = True
        if not found:
            mins.append(c)
    return mins


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result
    return timed