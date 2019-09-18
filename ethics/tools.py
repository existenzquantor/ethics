from ethics.language import *
from itertools import combinations, chain
import pyeda.inter

def makeSetOfAlternatives(*models):
    for m in models:
        m.setAlternatives(*models)
        
def makeSetOfEpistemicAlternatives(*models):
    for m in models:
        m.setEpistemicAlternatives(*models)
        m.probability = 1/len(models)
        
def myEval(content):
    try:
        f = subToAtoms(eval(content))
        return f
    except:
        return Atom(content)
    
def subToAtoms(f):
    if isinstance(f, str) and not isinstance(f, Atom) and not isinstance(f, bool) and not isinstance(f, Bool):
        return Atom(f)
    if isinstance(f, bool) and not isinstance(f, Bool):
        return Bool(f)
    if isinstance(f, Bool):
        return f
    if isinstance(f, OnePlaced):
        return type(f)(subToAtoms(f.f1))
    if isinstance(f, TwoPlaced):
        f1 = subToAtoms(f.f1)
        f2 = subToAtoms(f.f2)
        return type(f)(f1,f2)
    if isinstance(f, OnePlacedTerm):
        return type(f)(subToAtoms(f.t1))
    if isinstance(f, TwoPlacedTerm):
        f1 = subToAtoms(f.t1)
        f2 = subToAtoms(f.t2)
        return type(f)(f1,f2)
    return f
        
def mapBackToFormulae(l, m): # l: model, m: map
    erg = []
    for ll in l:
        found = False
        for mm in m:
            if m[mm] == ll:
                erg.append(myEval(mm).nnf())
                found = True
                break
        if(found == False):
            for mm in m:
                if m[mm] + ll == 0:
                    erg.append(myEval(mm).getNegation().nnf())
    return erg


def convert_formula_to_pyeda(formula):
    if isinstance(formula, Atom):
        return pyeda.inter.expr("v"+bytearray(str(formula).encode()).hex())
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
    return myEval(bytearray.fromhex(str(atom)[1:]).decode())

def convert_pyeda_model_to_hera(model):
    m = []
    for v in model:
        if model[v] == 1:
            m.append(convert_pyeda_atom_to_hera(v))
        else:
            m.append(Not(convert_pyeda_atom_to_hera(v)))
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
    
def minimalSets(cand):
    mins = []
    for c in cand:
        found = False
        for d in cand:
            if sub(c, d): # detect non-minimal
                found = True
        if not found:
            mins.append(c)
    return mins
