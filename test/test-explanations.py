from ethics.cam.semantics import CausalModel
from ethics.cam.principles import DeontologicalPrinciple, UtilitarianPrinciple, DoNoHarmPrinciple, KantianHumanityPrinciple, KantianHumanityPrincipleReading2, DeontologicalPrinciple, DoubleEffectPrinciple, DoNoInstrumentalHarmPrinciple, DoNoInstrumentalHarmPrincipleWithoutIntentions,IntentionFocusedDeontologicalPrinciple, ParetoPrinciple, GoalFocusedDeontologicalPrinciple
from ethics.language import *


trolley1 = CausalModel("./cases/cam/trolley-dilemma.json", {"pull":0, "refrain":1})
trolley2 = CausalModel("./cases/cam/trolley-dilemma.json", {"pull":1, "refrain":0})

trolley1.alternatives.append(trolley2)
trolley2.alternatives.append(trolley1)

print("*"*50)
print("REFRAIN")
print("*"*50)
print(trolley1.explain(DeontologicalPrinciple))
print(trolley1.explain(UtilitarianPrinciple))
print(trolley1.explain(DoNoHarmPrinciple))
print(trolley1.explain(KantianHumanityPrinciple))
print(trolley1.explain(KantianHumanityPrincipleReading2))
print(trolley1.explain(IntentionFocusedDeontologicalPrinciple))
print(trolley1.explain(GoalFocusedDeontologicalPrinciple))
print(trolley1.explain(DoNoInstrumentalHarmPrinciple))
print(trolley1.explain(DoubleEffectPrinciple))

print("*"*50)
print("PULL")
print("*"*50)
print(trolley2.explain(DeontologicalPrinciple))
print(trolley2.explain(UtilitarianPrinciple))
print(trolley2.explain(DoNoHarmPrinciple))
print(trolley2.explain(KantianHumanityPrinciple))
print(trolley2.explain(KantianHumanityPrincipleReading2))
print(trolley2.explain(IntentionFocusedDeontologicalPrinciple))
print(trolley1.explain(GoalFocusedDeontologicalPrinciple))
print(trolley2.explain(DoNoInstrumentalHarmPrinciple))
print(trolley2.explain(DoubleEffectPrinciple))
