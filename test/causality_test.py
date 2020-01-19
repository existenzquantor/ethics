from ethics.plans.semantics import Situation

sit = Situation("./cases/plans/bottle.yaml")

effect = {"bs": True}

cause = [1, 0]
print(sit.causes(cause, effect))
cause = [0, 1]
print(sit.causes(cause, effect))
cause = [1, 1]
print(sit.causes(cause, effect))