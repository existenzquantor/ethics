from ethics.language import Formula, Not
from ethics.solver import satisfiable, smt_all_models
from ethics.tools import my_eval
import mhsModule

def hitting_sets_gde(sets):
    sets = sorted(sets, key=len)
    sets_new = []
    for s in sets:
        new_set = []
        for f in s:
            new_set.append(str(f))
        sets_new.append(new_set)
    mhs = mhsModule.hitting_sets(sets_new)
    result = []
    for m in mhs:
        r = []
        for f in m:
            r.append(my_eval(f))
        result.append(r)
    return result



def remove_trivial_clauses(clauses):
    r = []
    for c in clauses:
        if satisfiable(Not(Formula.makeDisjunction(c))):
            r.append(c)
    return r

def remove_unsatisfiable_terms(terms):
    r = []
    for t in terms:
        if satisfiable(Formula.makeConjunction(t)):
            r.append(t)
    return r

def compute_primes(formula):
    models = smt_all_models(formula)
    prime_implicates = remove_trivial_clauses(hitting_sets_gde(models))
    prime_implicants = remove_unsatisfiable_terms(hitting_sets_gde(prime_implicates))
    return prime_implicants, prime_implicates


def generate_reasons(model, principle, *args):
    perm = principle.permissible()

    # Compute prime implicants and prime implicates
    if perm:
        cants, cates = compute_primes(principle.buildConjunction().nnf())
    else:
        cants, cates = compute_primes(Not(principle.buildConjunction()).nnf())

    # Sufficient reasons from prime implicants
    suff = {Formula.makeConjunction(c) for c in cants if model.models(Formula.makeConjunction(c))}

    # Necessary reasons from prime implicates
    necc = set()
    for cc in cates:
        necc_reason = []
        for c in cc:
            if model.models(c):
                necc_reason.append(c)
        if len(necc_reason) > 0:
            necc.add(Formula.makeDisjunction(necc_reason))

    # Preparing output
    result = []
    for c in suff:
        result.append({"model": model, "perm": perm, "reason": c, "type": "sufficient"})
    for c in necc:
        result.append({"model": model, "perm": perm, "reason": c, "type": "necessary"})

    return result


def generate_inus_reasons(reasons):
    suff = {r["reason"] for r in reasons if r["type"] == "sufficient"}
    nec = {r["reason"] for r in reasons if r["type"] == "necessary"}
    inus = set()
    for rn in nec:
        rn_check = rn.getClause()
        for rs in suff:
            if set(rn_check) <= set(rs.getConj()):
                inus.add(Formula.makeDisjunction(rn_check))
                break
    return inus