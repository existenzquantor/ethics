from ethics.language import *
from ethics.primes import *

def generateReasons(model, principle, *args):
    perm = principle.permissible()

    # Compute prime implicants and prime implicates
    if perm:
        cants, cates = PrimeCompilator(principle.buildConjunction(), use_mhs_only =True).compile()
    else:
        cants, cates = PrimeCompilator(Not(principle.buildConjunction()).nnf(), use_mhs_only=True).compile()

    # Sufficient reasons from prime implicants
    suff = [Formula.makeConjunction(c) for c in cants if model.models(Formula.makeConjunction(c))]

    # Necessary reasons from prime implicates
    necc = set()
    for cc in cates:
        necc_reason = []
        for c in cc:
            if model.models(c):
                necc_reason.append(c)
        if len(necc_reason) > 0:
            necc.add(Formula.makeDisjunction(necc_reason))
    necc = list(necc)

    # Preparing output
    result = []
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
