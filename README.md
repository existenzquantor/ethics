# ethics

This is the github repositiory of the HERA machine ethics Python library. For more information on HERA visit http://www.hera-project.com . 


- [Installation](#installation)
- [Moral Planning Domain Definitions](#moral-planning-domain-definitions)
  - [Situations](#plan-situations)
  - [Plan Evaluation](#plan-evaluation)
  - [Explanations](#plan-explanation)
- [Causal Agency Models](#causal-agency-models)
  - [Models](#models)
  - [Evaluation](#evaluation)
  - [Explanations](#explanation)

## Installation

The python implementation of HERA can be installed using pip. First, make sure you have Python3 installed. To install HERA, run:
```console
pip3 install ethics
```
If the module is already installed, you might instead want to update it running: 
```console
pip3 install --upgrade ethics
```

Alternatively, you can checkout this git repository and run:
```console
python3 setup.py install
```

## Moral Planning Domain Definitions

### Plan Situations

Moral Planning Domain Definitions is a format for describing sequences of actions and events in situations that require moral reasoning. The formalism allows to specify which action plan an agent has performed or is about to perform in light of the fact that events out of the agent's control may happen. The general idea is that actions and events alter the current state of the world as described by a set of facts that hold. Thus, actions and events turn world states into new world states. To start with, we consider the Giving Flowers case, which was introduced as an example particularly tailored to the Kantian Humanity principle. 
The situations reads:
> Bob is giving flowers to Celia, however, not to make Celia happy, but to make Alice happy, who is happy if Celia is happy.

The complete description of this example using YAML looks like this (there is also a JSON version available in the cases-plan directory):
```yaml
actions:
    - name: giveFlowers
      intrinsicvalue: good
      preconditions: {}
      effects:
        - condition: {}
          effect: {happy_celia: true}              
events:
    - name: happy_alice
      preconditions: {}
      effects:
        - condition: {happy_celia: true}
          effect: {happy_alice: true}
      timepoints: [0]     
utilities:
    - fact: {happy_celia: true}
      utility: 1
    - fact: {happy_celia: false}
      utility: -1
    - fact: {happy_alice: true}
      utility: 1
    - fact: {happy_alice: false}
      utility: -1
affects:
    celia: 
      pos: [{happy_celia: true}]
      neg: [{happy_celia: false}] 
    alice: 
      pos: [{happy_alice: true}]
      neg: [{happy_alice: false}]
plan: [giveFlowers]
goal: {happy_alice: true}
initialState: {happy_celia: false, happy_alice: false}
```

Let’s break this description into pieces. The first part defines the set of actions (here only one action) the agent, whom we call Bob in the following, can perform under its own control. 
```yaml
actions:
    - name: giveFlowers
      intrinsicvalue: good
      preconditions: {}
      effects:
        - condition: {}
          effect: {happy_celia: true} 
```
That is, Bob can give flowers to Celia. This action has no preconditions. Of course, one could debate that the giving flowers action actually should specify preconditions like Bob having flowers, Celia being near to Bob etc., but these conditions are not relevant in the context of this tutorial example. The effect of the action is that Celia is indeed happy. This effect does not depend on any further conditions (one could, if relevant, for example also include that the effect of Celia’s being happy further depends on her mood). As a moral property, actions have an intrinsic value (good, bad, or neutral), which is evaluated by the Deontological principle.

The second part of the moral domain description defines events, that is, things that happen not under the direct control of Bob.
```yaml
events:
    - name: happy_alice
      preconditions: {}
      effects:
        - condition: {happy_celia: true}
          effect: {happy_alice: true}
      timepoints: [0]   
```

The set of events consists of one event, which brings about Alice’s being happy under the condition that Celia is already happy. If Celia was not already happy, then this event would not have any effect. By the timepoints parameter, the modeler can specify at which time points the event will be executed. In this case, the event will execute only at time point 0. (Time point 0 is the first time point, as we start counting at 0.) This means that after the first action performed by the agent, also this event will be executed. So, only if Bob gives flowers at time point 0, Alice will be happy after time point 0.

The next two parts of the description are moral in nature. Different ethical principles will find different parts of the definition relevant or not. The first part is a definition of the utilities of the facts that may hold in situations or not. This definition just says that happy people yield positive utility, and unhappy people yield negative utility.
```yaml
utilities:
    - fact: {happy_celia: true}
      utility: 1
    - fact: {happy_celia: false}
      utility: -1
    - fact: {happy_alice: true}
      utility: 1
    - fact: {happy_alice: false}
      utility: -1
```

 The next part specifies who is affected by which facts.
```yaml
affects:
    celia: 
      pos: [{happy_celia: true}]
      neg: [{happy_celia: false}] 
    alice: 
      pos: [{happy_alice: true}]
      neg: [{happy_alice: false}]
```

Celia is positively affected by the fact that Celia is happy, and Alice is positively affected by the fact that Alice is happy. If there were two facts f1, f2 in, for example, the list of Celia’s pros, this would be interpreted as: “Celia is positively affected by f1, and Celia is positively affected by f2”, and not “Celia is positively affected if both f1 and f2”. The affect relation thus allows to express that some fact may be positive for one agent and at the same time negative for another agent.

Finally, three components are defined to complete the description of the situation: The plan Bob has planned (or even already performed), the goal Bob has seen to bring about by that plan, and the state Bob was initially facing before the plan was executed.
```yaml
plan: [giveFlowers]
goal: {happy_alice: true}
initialState: {happy_celia: false, happy_alice: false}
```
That is, initially, neither Celia not Alice were happy. Bob then gave the flowers to Celia in order to make Alice happy. Hence, some information that might be relevant is not explicit, for instance, that after Bob’s giving flowers, both Celia and Alice are happy. This must be deduced by the reasoner. Indeed, the reasoner is capable of doing that. 

### Plan Evaluation

To evaluate Bob’s plan using the ethical principles defined in the HERA framework, we first have to load the described situation. We do that by loading a JSON file that contains the description outlined above. HERA provides a Python interface for doing so.
```python
from ethics.plans.semantics import Situation
sit = Situation("./cases/plans/flowers.yaml")
```
Next, we can check permissibility of the situation according to several principles.
```python
from ethics.plans.principles import KantianHumanity, DoNoHarm, DoNoInstrumentalHarm, Utilitarianism, Deontology, GoalDeontology, DoubleEffectPrinciple, AvoidAnyHarm, AvoidAvoidableHarm

perm = sit.evaluate(Deontology)
print("Deontology: ", perm)

perm = sit.evaluate(GoalDeontology)
print("GoalDeontology: ", perm)

perm = sit.evaluate(KantianHumanity)
print("Kantian: ", perm)

perm = sit.evaluate(KantianHumanity, 2)
print("Kantian Reading #2: ", perm)

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
```
Just as expected, all principles but the Kantian will permit Bob's plan. The Kantian principle forbids it, because it uses Celia merely as a means. That is, the console output should look like this:
```console
Deontology:  True
GoalDeontology:  True
Kantian:  False
Kantian Reading #2:  False
DoNoHarm:  True
DoNoInstrumentalHarm:  True
Utilitarianism:  True
DoubleEffectPrinciple:  True
AvoidAvoidableHarm:  True
AvoidAnyHarm:  True
```

### Plan Explanation

The HERA Python software package ethics has recently been updated by a module for explanations. That is, an HERA agent can explain its moral permissibility judgments. This functionality can, for instance, be used to generate natural-language explanations for humans to understand the decisions made by an ethical reasoning agent, e.g., the decisions made by a social robot. The following tutorial will showcase how the new functionality can be used programmatically.

Consider the same situation as above but this time we call ```explain``` rather than ```evaluate```:
```python
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
```

The console output of the above script is quite lengthy. Therefore, let us focus on two explantions given by the Goal-focused Deontology and by the Kantian principle.
```python
{'permissible': True, 
 'principle': 'GoalDeontology',
 'sufficient': [And(And(And(Not(Bad('happy_celia')), Not(Bad('happy_alice'))), Not(Goal(Not('happy_celia')))), Not(Goal(Not('happy_alice')))), 
               And(And(And(Not(Goal('happy_celia')), Not(Bad('happy_alice'))), Not(Goal(Not('happy_celia')))), Not(Goal(Not('happy_alice'))))], 
 'necessary': [Not(Bad('happy_alice')), Not(Goal(Not('happy_alice'))), Not(Goal(Not('happy_celia'))), Or(Not(Bad('happy_celia')), Not(Goal('happy_celia')))],
 'inus': [Not(Bad('happy_alice')), Not(Goal(Not('happy_alice'))), Not(Goal(Not('happy_celia')))]}

{'permissible': False, 
 'principle': 'KantianHumanity',
 'sufficient': [And(Means('celia'), Not(End('celia')))],
 'necessary': [Not(End('celia')), Means('celia')],
 'inus': [Not(End('celia')), Means('celia')]}
```

Goal-focused deontology argues that Bob's plan is permissible. It says that for permissibility it was already sufficient that being happy is not bad and that not being happy was not a goal. Moreover, as celia being happy was not a goal, it also does not matter if she being happy is morally bad. Hence, we have two *sufficient reasons*. The *necessary reasons* state conditions whose negation would result in another judgment: If it were bad that alice is happy, then Bob's plan would be impermissible etc. The *INUS reasons* point to *necessary reasons that are part of sufficient reasons* and often are most concise.

The Kantian principle, on the other hand, renders Bob's plan impermissible. The reason is that Celia is used as a means (to make Alice happy) but not as an End (i.e., her being happy is not among Bob's goals). To fix this, either Bob has to consider Celia as an end, or find another plan that does not use Celia as a means. This is what the INUS reasons say.

## Causal Agency Models

tbd

### Models

tbd

### Evaluation

tbd 

### Explanation

tbd
