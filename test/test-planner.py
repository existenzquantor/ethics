from ethics.plans.semantics import Situation
from ethics.plans.planner import Planner

sit = Situation("cases/plans/crossing.yaml")
planner = Planner(sit)
p = planner.generate_plan()

print(p.plan if p else "No Plan Found")
