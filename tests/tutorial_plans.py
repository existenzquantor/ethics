from ethics.plans.semantics import Situation
sit = Situation("./cases/plans/flowers.yaml")

from ethics.plans.principles import KantianHumanity, DoNoHarm, DoNoInstrumentalHarm, Utilitarianism, Deontology, GoalDeontology, DoubleEffectPrinciple, AvoidAnyHarm, AvoidAvoidableHarm

perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

perm = sit.evaluate(GoalDeontology)
print("GoalDeontology: ", perm)

perm = sit.evaluate(KantianHumanity)
print("Kantian: ", perm)

perm = sit.evaluate(DoNoHarm)
print("DoNoHarm: ", perm)

perm = sit.evaluate(DoNoInstrumentalHarm)
print("DoNoInstrumentalHarm: ", perm)

perm = sit.evaluate(Utilitarianism)
print("Utilitarianism: ", perm)

perm = sit.evaluate(DoubleEffectPrinciple)
print("DoubleEffectPrinciple: ", perm)

perm = sit.evaluate(AvoidAvoidableHarm)
print("AvoidAvoidableHarm: ", perm)

perm = sit.evaluate(AvoidAnyHarm)
print("AvoidAnyHarm: ", perm)
