from ethics.plans.semantics import Situation
sit = Situation("./cases/plans/flowers.yaml")

from ethics.plans.principles import KantianHumanity, DoNoHarm, DoNoInstrumentalHarm, Utilitarianism, Deontology, GoalDeontology, DoubleEffectPrinciple, AvoidAnyHarm, AvoidAvoidableHarm

perm = sit.explain(Deontology)
print("Deontology: ", perm)

perm = sit.explain(GoalDeontology)
print("GoalDeontology: ", perm)

perm = sit.explain(KantianHumanity)
print("Kantian: ", perm)

perm = sit.explain(KantianHumanity, 2)
print("Kantian Reading #2: ", perm)

perm = sit.explain(DoNoHarm)
print("DoNoHarm: ", perm)

perm = sit.explain(DoNoInstrumentalHarm)
print("DoNoInstrumentalHarm: ", perm)

perm = sit.explain(Utilitarianism)
print("Utilitarianism: ", perm)

perm = sit.explain(DoubleEffectPrinciple)
print("DoubleEffectPrinciple: ", perm)

perm = sit.explain(AvoidAvoidableHarm)
print("AvoidAvoidableHarm: ", perm)

perm = sit.explain(AvoidAnyHarm)
print("AvoidAnyHarm: ", perm)
