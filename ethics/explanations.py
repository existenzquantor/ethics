from ethics.language import Formula, Not
from ethics.solver import satisfiable, smt_all_models


def hitting_sets_gde(sets):
    sets = sorted(sets, key=len)
    hitting_sets = [set()]
    for current_set in sets:
        new_hitting_sets = list(hitting_sets)
        for hitting_set in hitting_sets:
            # Check if hitting_set hits current_set
            if hitting_set.intersection(current_set) == set():
                new_hitting_sets.remove(hitting_set)
                # no hit
                for element in current_set:
                    candidate = hitting_set.union({element})

                    is_valid = True
                    for hs in new_hitting_sets:
                        if hs.issubset(candidate):
                            is_valid = False
                            break
                    if is_valid:
                        new_hitting_sets.append(candidate)

        hitting_sets = list(new_hitting_sets)

    return hitting_sets


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