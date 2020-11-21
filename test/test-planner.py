from ethics.plans.semantics import Situation
from ethics.plans.planner import Planner
from ethics.tools import situation_to_prolog

sit = Situation("cases/plans/service-robots.yaml")

print(situation_to_prolog(sit))
"""
print(sit.plan)
n = sit.narrative()
print(n)
"""

planner = Planner(sit)
p = planner.generate_plan()

print(p.plan if p else "No Plan Found")

sit.plan = p.plan
n = sit.narrative()
"""print(n)"""
