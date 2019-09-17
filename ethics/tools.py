from ethics.language import *
from itertools import combinations, chain

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
