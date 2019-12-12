from ethics.plans.concepts import Plan
from ethics.plans.semantics import Situation
from ethics.plans.planner import Planner, MoralPlanner
from ethics.plans.principles import KantianHumanity, DoNoHarm, DoNoInstrumentalHarm, Utilitarianism, Deontology, GoalDeontology, DoubleEffectPrinciple, AvoidAnyHarm, AvoidAvoidableHarm


print("*"*50)
print("JSON")
print("*"*50)
sit = Situation("cases/plans/robot_and_frank.yaml")
sit_alt = Situation("cases/plans/robot_and_frank.yaml")
sit_alt.plan = Plan([]) # Compare to empty plan
sit.alethicAlternatives.append(sit_alt)

print("Intial State: "+ str(sit.init))
print("Plan: "+ str(sit.plan))
print("Final State: "+ str(sit.get_all_consequences()))

perm = sit.evaluate(Deontology)
print("Deontology: ", perm)
print("Deontology Explanation:", sit.explain(Deontology))

perm = sit.evaluate(GoalDeontology)
print("GoalDeontology: ", perm)
print("GoalDeontology Explanation:", sit.explain(GoalDeontology))

perm = sit.evaluate(KantianHumanity)
print("Kantian: ", perm)
print("Kantian Explanation:", sit.explain(KantianHumanity))

perm = sit.evaluate(DoNoHarm)
print("DoNoHarm: ", perm)
print("DoNoHarm Explanation:", sit.explain(DoNoHarm))

perm = sit.evaluate(AvoidAnyHarm)
print("AvoidAnyHarm: ", perm)
print("AvoidAnyHarm Explanation:", sit.explain(AvoidAnyHarm))

perm = sit.evaluate(DoNoInstrumentalHarm)
print("DoNoInstrumentalHarm: ", perm)
print("DoNoInstrumentalHarm Explanation:", sit.explain(DoNoInstrumentalHarm))

perm = sit.evaluate(Utilitarianism)
print("Utilitarianism: ", perm)
print("Utilitarianism Explanation:", sit.explain(Utilitarianism))

perm = sit.evaluate(DoubleEffectPrinciple)
print("DoubleEffectPrinciple: ", perm)
print("DoubleEffectPrinciple Explanation:", sit.explain(DoubleEffectPrinciple))

perm = sit.evaluate(AvoidAvoidableHarm)
print("AvoidAvoidableHarm: ", perm)
print("AvoidAvoidableHarm Explanation:", sit.explain(AvoidAvoidableHarm))


planner = Planner(sit)
p = planner.generate_plan()
if p:
    print("Planned: ", p.plan)
else:
    print("No Plan found")