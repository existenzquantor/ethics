from ethics.language import *
from ethics.tools import *
from ethics.solver import *
from itertools import combinations

def noDuplicate(r, s):
    for e in r:
        if set(e) == set(s):
            return False
    return True


def minimalSets(setofsets):
    r = []
    for s1 in setofsets:
        no = False
        for s2 in setofsets:
            if set(s1) > set(s2):
                no = True
                break
        if not no and noDuplicate(r, s1):
            r += [s1]
    return r


def generateReasons(model, principle, *args):
    perm = principle.permissible()
    suff = generateSufficientReasons(model, principle, perm)
    necc = generateNecessaryReasons(model, principle, perm)

    result = []
    if args:
        perm = model.evaluate(principle, args)
    else:
        perm = model.evaluate(principle)

    for c in suff:
        result.append({"model": model, "perm": perm, "reason": c, "type": "sufficient"})
    for c in necc:
        result.append({"model": model, "perm": perm, "reason": c, "type": "necessary"})

    return result


def identifyINUSReasons(reasons):
    suff = [r["reason"] for r in reasons if r["type"] == "sufficient"]
    nec = [r["reason"] for r in reasons if r["type"] == "necessary"]
    inus = []

    for rn in nec:
        rn_check = None
        rn_check = rn.getClause()
        for rs in suff:
            rs_check = None
            rs_check = rs.getConj()
            if set(rn_check) <= set(rs_check):
                inus.append(Formula.makeDisjunction(rn_check))
                break
    return inus


def isAlreadyCovered(cand, results):
    for r in results:
        if set(r) <= set(cand):
            return True
    return False


def getCombinations(cand, k): # , mode, cm, m
    return combinations(cand, k)

def must_be_in(l, lm, cand, f):
    m = [e for e in cand if e not in lm and e != l]
    #print("m", m, l, lm, cand, f)
    if len(m) == 0:
        return satisfiable(Not(f))
    return satisfiable(And(Formula.makeConjunction(m), Not(f)))

def suffReasons(fo, mode = None, cm = None):
    """
    fo -- the principle formula
    mode -- suff or necc
    cm -- the causal agency model
    """

    models = smtAllModels(fo)

    if mode == "suff":
        # Actually, for sufficient reasons we are only interested in the model which corresponds
        # to the given situation. In future, room for optimization.
        models = [mod for mod in models if cm.models(Formula.makeConjunction(mod))]
    
    realsuffs = []
    
    for cand in models:
        for k in range(1, len(cand) + 1):
            for c in getCombinations(cand, k):
                if not isAlreadyCovered(c, realsuffs):
                    if not satisfiable(And(Formula.makeConjunction(c), Not(fo))):
                        realsuffs.append(c)
    """
    for cand in models:
        local_model = []
        for l in cand:
            if must_be_in(l, local_model, cand, fo):
                local_model.append(l)
        if not isAlreadyCovered(local_model, realsuffs):
            realsuffs.append(local_model)
    """
    #print("realsuffs", realsuffs)
    return realsuffs


def generateSufficientReasons(model, principle, perm = None):
    if perm == None:
        perm = principle.permissible()
    if perm:
        f = principle.buildConjunction()
    else:
        f = Not(principle.buildConjunction())
    suff = suffReasons(f, "suff", model)
    suff = [Formula.makeConjunction(e) for e in suff]
    return suff


def generateNecessaryReasons(model, principle, perm = None):
    if perm == None:
        perm = principle.permissible()
    if perm:
        f = Not(principle.buildConjunction())
    else:
        f = principle.buildConjunction()
    suff = suffReasons(f, "necc", model)
    
    result = []
    for rs in suff:
        cl = []
        for s in rs:
            if not model.models(s):
                cl.append(s)
        if len(cl) > 0:
            cl_neg = []
            for c in cl:
                cl_neg.append(Not(c).nnf())
            result.append(Formula.makeDisjunction(cl_neg))

    # minimize
    s = []
    for r in result:
        s.append(r.getClause())
    minimal = minimalSets(s)
    result = []
    for m in minimal:
        result.append(Formula.makeDisjunction(m))
    return result


