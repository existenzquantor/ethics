from ethics.plans.semantics import Situation
from ethics.plans.planner import Planner

sit = Situation("cases/plans/crossing.yaml")
print(sit.plan)
n = sit.narrative()
print(n)

planner = Planner(sit)
p = planner.generate_plan()

print(p.plan if p else "No Plan Found")

sit.plan = p.plan
n = sit.narrative()
print(n)