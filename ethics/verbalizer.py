from ethics.language import *

def reasonToNL(reason):
    if isinstance(reason, str):
        return reason
    if isinstance(reason, Not):
        return "it is not the case that "+reasonToNL(reason.f1)
    if isinstance(reason, Causes):
        return reasonToNL(reason.f1)+" directly causes "+ reasonToNL(reason.f2)
    if isinstance(reason, And):
        return reasonToNL(reason.f1)+" and "+reasonToNL(reason.f2)
    if isinstance(reason, Or):
        return reasonToNL(reason.f1)+" or "+reasonToNL(reason.f2)
    if isinstance(reason, Gt):
        if reason.f1 == 0:
            return reasonToNL(reason.f2.t1)+" is bad "
        if reason.f2 == 0:
            return reasonToNL(reason.f1.t1)+" is good "

def verbalize(reason):
    nlp_reason = ""
    for r in reason:
        if len(nlp_reason) > 0:
            nlp_reason = nlp_reason.strip()+". Moreover, "
        nlp_reason += reasonToNL(r).capitalize()           
    return nlp_reason.strip()+"."


# Test
if __name__ == '__main__':
    # Reason 1
    # Pull directly causes tram_hits_man and tram_hits_man is bad.
    reason1 = [And(Causes("pull", "tram_hits_man"), Gt(0, U("tram_hits_man")))]
    print(verbalize(reason1))
    # Reason 2
    # It is not the case that refrain directly causes it is not the case that five_survive.
    reason2 = [Not(Causes("refrain", Not("five_survive")))]
    print(verbalize(reason2))
    # Reason 3
    # It is not the case that refrain directly causes it is not the case that person1_survives. Moreover, It is not the case that refrain directly causes it is not the case that person2_survives.
    reason3 = [Not(Causes("refrain", Not("person1_survives"))), Not(Causes("refrain", Not("person2_survives")))]
    print(verbalize(reason3))
    # Reason 4
    # C1. Moreover, C2. Moreover, It is not the case that c3.
    reason4 = ["c1", "c2", Not("c3")]
    print(verbalize(reason4))
    # Reason 5
    # C1 and c2 and it is not the case that c3.
    reason5 = [And("c1", And("c2", Not("c3")))]
    print(verbalize(reason5))
