from ethics.language import *
from ethics.primes import *


def generateReasons(model, principle, *args):
    perm = principle.permissible()
    #suff = generateSufficientReasons(model, principle, perm)
    #necc = generateNecessaryReasons(model, principle, perm)


    if perm:
        cants, cates = PrimeCompilator(principle.buildConjunction()).compile()
    else:
        cants, cates = PrimeCompilator(Not(principle.buildConjunction()).nnf()).compile()
        
    suff = [Formula.makeConjunction(c) for c in cants if model.models(Formula.makeConjunction(c))]
    necc = set()
    for cc in cates:
        necc_reason = []
        for c in cc:
            if model.models(c):
                necc_reason.append(c)
        if len(necc_reason) > 0:
            necc.add(Formula.makeDisjunction(necc_reason))
    necc = list(necc)
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
