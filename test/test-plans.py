from ethics.plans.semantics import Situation, Planner, MoralPlanner
from ethics.plans.principles import KantianHumanity, DoNoHarm, DoNoInstrumentalHarm, Utilitarianism, Deontology, GoalDeontology, DoubleEffectPrinciple, AvoidAnyHarm, AvoidAvoidableHarm

print("*"*50)
print("JSON")
print("*"*50)
sit = Situation("cases/plans/flowers.yaml")

print("Intial State: "+ str(sit.init))
print("Plan: "+ str(sit.plan))
print("Final State: "+ str(sit.get_all_consequences()))

perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

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

planner = Planner(sit)
p = planner.generate_plan()
if p:
    print("Planned: ", p.plan)
else:
    print("No Plan found")

print("*"*50)

sit = Situation("cases/plans/trolley-50.json")

print("Intial State: "+ str(sit.init))
print("Plan: "+ str(sit.plan))
print("Final State: "+ str(sit.get_all_consequences()))


perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

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

planner = MoralPlanner(sit, DoNoHarm)
p = planner.generate_plan()
if p:
    print("Plannedddd: ", p.plan)
else:
    print("No Plan found")


print("*"*50)

sit = Situation("cases/plans/coal-dilemma.json")

print("Intial State: "+ str(sit.init))
print("Plan: "+ str(sit.plan))
print("Final State: "+ str(sit.get_all_consequences()))


perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

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

planner = Planner(sit)
p = planner.generate_plan()
if p:
    print("Planned: ", p.plan)
else:
    print("No Plan found")


print("*"*50)

sit = Situation("cases/plans/coal-dilemma.json")

print("Intial State: "+ str(sit.init))
print("Plan: "+ str(sit.plan))
print("Final State: "+ str(sit.get_all_consequences()))


perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

perm = sit.evaluate(KantianHumanity, 1)
print("Kantian 1: ", perm)

perm = sit.evaluate(KantianHumanity, 2)
print("Kantian 2: ", perm)

perm = sit.evaluate(DoNoHarm)
print("DoNoHarm: ", perm)

perm = sit.evaluate(DoNoInstrumentalHarm)
print("DoNoInstrumentalHarm: ", perm)

perm = sit.evaluate(Utilitarianism)
print("Utilitarianism: ", perm)

perm = sit.evaluate(DoubleEffectPrinciple)
print("DoubleEffectPrinciple: ", perm)

planner = MoralPlanner(sit, AvoidAnyHarm)
p = planner.generate_plan()
if p:
    print("Planned: ", p.plan)
else:
    print("No Plan found")

sit.creativeAlternatives += [Situation("cases/plans/coal-dilemma-creative1.json")]
a = planner.make_moral_suggestion(AvoidAvoidableHarm)
print(a, a.plan)



print("*"*50)
print("YAML")
print("*"*50)
sit = Situation("cases/plans/flowers.yaml")

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

perm = sit.evaluate(DoubleEffectPrinciple)
print("DoubleEffectPrinciple: ", perm)

perm = sit.evaluate(AvoidAvoidableHarm)
print("AvoidAvoidableHarm: ", perm)
print("AvoidAvoidableHarm Explanation:", sit.explain(AvoidAvoidableHarm))


planner = Planner(sit)
p = planner.generate_plan()
if p:
    print("Planned: ", p.plan)
else:
    print("No Plan found")
