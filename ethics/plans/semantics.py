import json
import yaml
import io
import copy
import itertools

from ethics.language import Not, Or, And, Finally, Caused, Minus, Add, Sub, U, \
                            Bad, Good, Neutral, Instrumental, Impl, BiImpl, Avoidable, \
                            Goal, Means, Means2, Eq, Gt, GEq, End
from ethics.tools import my_eval, minimal_plans, timeit, powerset

class Plan:
    """Representation of an action plan"""
    
    def __init__(self, endoPlan):
        """Constructor of an action plan
        
        :param endoPlan: List of (endogeneous) actions
        :type endoPlan: list
        """
        self.endoActions = endoPlan
    
    def __substitute_empty_actions(self, positions):
        """Substitute actions in the plan by the empty action at the given positions.
        
        :param positions: The positions as bit arry, 1-bit = substitute, 0-bit = original action
        :type positions: tuple
        :return: New plan with substitutions
        :rtype: Plan
        """
        p = copy.deepcopy(self)
        for i in range(len(positions)):
            if positions[i]:
                p.endoActions[i] = EmptyAction()
        return p

    def compute_all_epsilon_alternatives(self):
        """Retrieves all alternatives to the plan where each alternative is another way to substitute some actions
            by the empty action epsilon.

            :return: Iterator over epsilon alternative
            :rtype: Iterator
        """
        for b in sorted(itertools.product([1, 0], repeat=len(self.endoActions)), key=sum, reverse=True):
            if sum(b) > 0:
                yield self.__substitute_empty_actions(b)

    def __delete_effect_from_actions(self, effect, positions):
        """Deletes the given effect from all actions where the corresponding bit in list positions is 1.
        
        :param effect: The effect to be deleted
        :type effect: dict
        :param positions: Positions at which to delete the effect
        :type positions: tiple
        :return: New plan where the effects are deleted from the specified actions
        :rtype: Plan
        """
        p = copy.deepcopy(self)
        for i in range(len(positions)):
            if positions[i] and p.endoActions[i].has_effect_somewhere(effect):
                p.endoActions[i] = p.endoActions[i].delete_effect(effect)
        return p

    def __all_manipulated_actions_have_effect_somewhere(self, effect, positions):
        """Checks if all actions considered for effect deletion indeed have the effect
        
        :param effect: The effect
        :type effect: dict
        :param positions: Bit tuple indicating the actions to consider
        :type positions: tuple
        :return: True or False
        :rtype: bool
        """
        for i in range(len(positions)):
            if positions[i] and not self.endoActions[i].has_effect_somewhere(effect):
                return False
        return True

    def compute_all_effect_alternatives(self, effect):
        """Computes all plans where the effect is deleted from some actions
        
        :param effect: The effect to be deleted
        :type effect: dict
        :return: Iterator over alternatives
        :rtype: Iterator
        """
        for b in sorted(itertools.product([1, 0], repeat=len(self.endoActions)), key=sum, reverse=True):
            if sum(b) > 0 and self.__all_manipulated_actions_have_effect_somewhere(effect, b):
                yield self.__delete_effect_from_actions(effect, b)

    def __str__(self):
        """String representation of an action plan
        
        :return: String representation
        :rtype: str
        """
        s = "["
        for a in self.endoActions:
            s += str(a) + ","
        return s+"]"

    def __repr__(self):
        """Representation of an action object
        
        :return: String representation
        :rtype: str
        """
        return self.__str__()

class Action:
    """Representation of an endogeneous action"""

    def __init__(self, name, pre, eff, intrinsicvalue):
        """Constructor of an action.
        
        :param name: Label of the action
        :type name: str
        :param pre: Preconditions of the action
        :type pre: dict
        :param eff: (Conditional) Effects of the action
        :type eff: list
        :param intrinsicvalue: Intrinsic moral value of the action as required by deontological principles (good, bad, neutral)
        :type intrinsicvalue: str
        """
        self.name = name
        self.pre = pre
        self.eff = eff
        self.intrinsicvalue = intrinsicvalue
        
    def __str__(self):
        """String representation of an action
        
        :return: String representation
        :rtype: str
        """
        return self.name

    def has_effect_somewhere(self, effect):
        """Checks if a given effect is potentially an effect of the action.
        
        :param effect: The effect.
        :type effect: dict
        :return: True or False
        :rtype: bool
        """
        for e in self.eff:
            if set(effect.keys()) <= set(e["effect"].keys()):
                count = 0
                for ek in effect.keys():
                    if e["effect"][ek] == effect[ek]:
                        count = count + 1
                if count == len(effect.keys()):
                    return True
        return False

    def delete_effect(self, effect):
        """Delete an effect from all effects.
        
        :param effect: The effect to be deleted.
        :type effect: dict
        :return: New action with deleted effect
        :rtype: Action
        """
        k, v = list(effect.items())[0]
        a = self.clone_action()
        for e in a.eff:
            if k in e["effect"] and v == e["effect"][k]:
                del e["effect"][k]
        return a

    def clone_action(self):
        return copy.deepcopy(self)

class EmptyAction(Action):
    """Empty Action"""

    def __init__(self):
        super().__init__("epsilon", dict(), dict(), "neutral")
    
    def has_effect_somewhere(self, effect):
        return False

class Event:
    """Representation of an event"""
    
    def __init__(self, name, pre, eff, time):
        """Constructor of an event
        
        :param name: Label of the event
        :type name: str
        :param pre: Preconditions of the event
        :type pre: dict
        :param eff: (Conditional) Effects of the event
        :type eff: dict
        :param times: Time point at which the event will (try to) fire
        :type times: int
        """
        self.name = name
        self.pre = pre
        self.eff = eff
        self.time = time

class Situation:
    """Representation of a situation"""
    
    def __init__(self, inputfile = None):
        """Constructor of a situation
        
        :param inputfile: Path to the JSON/YAML description of the situation, defaults to None
        :type inputfile: str, optional
        """
        if inputfile == None:
            self.actions = None
            self.events = None
            self.init = None
            self.goal = None
            self.affects = None
            self.utilities = None
        else:
            self.__parse_model(inputfile)

        self.alethicAlternatives = []
        self.epistemicAlternatives = []
        self.creativeAlternatives = []

        self.eventcounter = 0

    def clone_situation(self):
        """Build a new situation which equals the current situation.
        
        :return: New situation object (cloned)
        :rtype: Situation
        """
        return copy.deepcopy(self)
 
    def __parse_model(self, inputfile):
        """Build a situation from a JSON/YAML file. Used by the constructor.
        
        :param inputfile: Path to the JSON/YAML file to be loaded.
        :type inputfile: str
        """
        self.inputfile = inputfile
        with io.open(inputfile) as data_file:
            if inputfile.split(".")[-1] == "yaml":
                data = yaml.load(data_file,  Loader=yaml.FullLoader)
            else:
                data = json.load(data_file)
            self.actions = []
            for a in data["actions"]:
                action = Action(a["name"], a["preconditions"], a["effects"], a["intrinsicvalue"])
                self.actions += [action]
            self.events = []
            for a in data["events"]:
                for t in a["timepoints"]:
                    event = Event(a["name"], a["preconditions"], a["effects"], t)
                    self.events += [event]
            self.affects = data["affects"]
            self.goal = data["goal"]
            self.init = data["initialState"]
            planactions = []
            for a in data["plan"]:
                for b in self.actions:
                    if a == b.name:
                        planactions += [b]
            self.plan = Plan(planactions)
            self.utilities = data["utilities"]

    def __get_number_of_events(self):
        """Return number of event tokens in the situation.
        
        :return: Number of event tokens
        :rtype: int
        """
        return len(self.events)

    def __compute_event_subsets(self):
        """Compute all proper subsets of events.

        :return: Iterator over all event subsets
        :rtype: Iterator
        """
        for ep in sorted(powerset(self.events), key=len, reverse=True):
            yield ep
    
    def get_harmful_consequences(self):
        """Retrieve all consequences of the action plan, which have negative utility.
        
        :return: List of harmful consequences true in the final state
        :rtype: list
        """
        allCons = self.get_all_consequences()
        harmful = []
        for u in self.utilities:
            if u["utility"] < 0:
                if self.__is_satisfied(u["fact"], allCons):
                    harmful += [u["fact"]]  
        return harmful  

    def get_harmful_facts(self):
        """Retrieve all harmful facts
        
        :return: All harmful facts in the domain.
        :rtype: list
        """
        return [u["fact"] for u in self.utilities if u["utility"] < 0]

    def __get_negation(self, fact):
        """Get the Negation of the fact
        
        :param fact: the fact
        :type fact: dict
        :return: the negated fact
        :rtype: dict
        """
        k, v = list(fact.items())[0]
        return {k: not v}
    
    def get_avoidable_harmful_facts(self):
        """Retrieve all harmful facts for which there is a plan, whose execution does not result in the fact to be finally true.
        
        :return: Avoidable facts
        :rtype: list
        """
        avoidable = []
        sit = self.clone_situation()
        for h in sit.get_harmful_facts():
            if not self.models(Finally(self.__dict_to_literal(h))):
                avoidable.append(h)
            else:
                nh = sit.__get_negation(h)
                sit.goal = nh
                planner = Planner(self)
                plan = planner.generate_plan()
                if plan != False:
                    avoidable.append(h)
        return avoidable
    
    def get_all_consequences(self):
        """Retrieve all consequences of the action plan, i.e., the final state.
        
        :return: List of all true facts in the final state.
        :rtype: list
        """
        return self.simulate()

    def get_utility(self, fact):
        """Retrieve the utility of a particular fact.
        
        :param fact: The fact
        :type fact: dict
        :return: The fact's utility
        :rtype: int
        """
        for u in self.utilities:
            if fact == u["fact"]:
                return u["utility"]
        return 0

    def get_final_utility(self):
        """Retrieve aggregated utility of the final state.
        
        :return: Utility of the final state
        :rtype: int
        """
        utility = 0
        sn = self.simulate()
        for k, v in sn.items():
            utility += self.get_utility({k:v})
        return utility
    
    def __is_instrumental(self, effect):
        """Determine if an effect is instrumental, i.e., if blocking this effect somewhere during plan execution will render the goal unachieved.
        
        :param effect: The effect to be checked for instrumentality
        :type effect: dict
        :return: True or False
        :rtype: bool
        """
        if not self.satisfies_goal(self.simulate()):
            return False
        for p in self.plan.compute_all_effect_alternatives(effect):
            sit = self.clone_situation()
            sit.plan = p
            if not sit.satisfies_goal(sit.simulate()):
                return True
        return False
        
    def __treats_as_end(self, p):
        """A moral patient p is treated as an end iff it is positively and not negatively affected by some goal.
        
        :param p: The patient to be checked for being treated as an end
        :type p: str
        :return: True or False
        :rtype: bool
        """
        for e in self.affects[p]["neg"]:
            if self.__is_satisfied(e, self.goal):
                return False
        for e in self.affects[p]["pos"]:
            if self.__is_satisfied(e, self.goal):
                return True
        return False
        
    def __treats_as_means(self, p, reading = 1):
        """A moral patient p is treated as a means iff p is affected by some instrumental effect.
        
        :param p: The patient to be checked for being treated as a means
        :type p: str
        :param reading: Reading of the categorical imperative (1 or 2), defaults to 1
        :type reading: int, optional
        :return: True or False
        :rtype: bool
        """
        for e in self.affects[p]["pos"] + self.affects[p]["neg"]:
            if reading == 1 and self.__is_instrumental(e):
                return True
            if reading == 2 and self.__caused(e):
                return True
        return False
    
    def __caused(self, effect):
        """Check if some given effect is caused by the agent's actions.
        
        :param effect: The effect to be checked for being caused
        :type effect: dict
        :return: True or False
        :rtype: bool
        """
        if not self.__is_satisfied(effect, self.simulate()):
            return False
        sit = self.clone_situation()
        for e in self.__compute_event_subsets():
            sit.events = e
            if self.__is_satisfied(effect, sit.simulate()):
                for p in self.plan.compute_all_epsilon_alternatives():
                    sit.plan = p
                    if not self.__is_satisfied(effect, sit.simulate()):
                        return True
        return False
        
    def evaluate(self, principle, *args):
        """Check if the situation is permissible according to a given ethical principle.
        
        :param principle: The ethical principle
        :type principle: Principle
        :return: True if principle permits the situation, otherwise False
        :rtype: bool
        """
        try:
            p = principle(self, args)
        except:
            p = principle
        return p.permissible()

    def explain(self, principle, *args):
        """Explain why the ethical principle permits the situation.
        
        :param principle: Ethical principle
        :type principle: Principle
        :return: An explanation consisting of sufficient, necessary, and inus reasons
        :rtype: dict
        """
        try:
            p = principle(self, args)
        except:
            p = principle
        return p.explain()
            
    def __is_applicable(self, action, state):
        """Check if an action is applicable in a given state.
        
        :param action: The action to apply
        :type action: Action
        :param state: The state to apply the action in
        :type state: dict
        :return: True if applicable, otherwise False
        :rtype: bool
        """
        return self.__is_satisfied(action.pre, state)
        
    def __apply(self, action, state): 
        """Apply an action to a state. 
        
        :param action: The action to apply
        :type action: Action
        :param state: The state to apply the action to
        :type state: List
        :return: New state
        :rtype: dict
        """   
        if self.__is_applicable(action, state):
            si = copy.deepcopy(state)
            for condeff in action.eff:
                if self.__is_satisfied(condeff["condition"], si):
                    for v in condeff["effect"].keys():
                        state[v] = condeff["effect"][v]
        return state

    def __apply_all_events(self, state, time):
        """Simulatneously, apply all applicable events to a state.
        
        :param state: The current state to apply all events to
        :type state: dict
        :param time: Point in time
        :type time: int
        :return: New state
        :rtype: dict
        """
        eventlist = [e for e in self.events if (time == e.time and self.__is_applicable(e, state))]
        si = copy.deepcopy(state)
        for e in eventlist:
            for condeff in e.eff:
                if self.__is_satisfied(condeff["condition"], state):
                    for v in condeff["effect"].keys():
                        si[v] = condeff["effect"][v]
        return si
    
    def __is_satisfied(self, partial, state):
        """Check if some partial state is satisfied in some full state.
        
        :param partial: Partial state (e.g., a condition)
        :type partial: dict
        :param state: Full state
        :type state: dict
        :return: True or False
        :rtype: bool
        """
        for k in partial.keys():
            if k not in state or partial[k] != state[k]:
                return False
        return True
        
    def satisfies_goal(self, state):
        """Check if a state is a goal state.
        
        :param state: state to check for goal state
        :type state: dict
        :return: True or False
        :rtype: bool
        """
        return self.__is_satisfied(self.goal, state)
           
    def __last_exo(self):
        """Compute the last event to fire. Used for the simulation to make sure, events after the last action will also be invoked."""
        m = 0
        for e in self.events:
            if e.time > m:
                m = e.time
        return m

    def simulate(self):
        state = copy.deepcopy(self.init)
        for t in range(len(self.plan.endoActions)):
            state = self.__apply(self.plan.endoActions[t], state)
            state = self.__apply_all_events(state, t)
        if self.__last_exo() >= len(self.plan.endoActions):
            for t in range(len(self.plan.endoActions), self.__last_exo()+1):
                state = self.__apply_all_events(state, t)
        return state
    
    def __is_action(self, a):
        """Checks if parameter is an action variable.
        
        :param a: Some input
        :type a: Any
        :return: True or False
        :rtype: bool
        """
        return a in [a.name for a in self.actions]
    
    def __literal_to_dict(self, l):
        """Converts a HERA literal to a fact
        
        :param l: HERA literal
        :type l: Formula
        :return: Fact
        :rtype: dict
        """
        l = l.nnf()
        if isinstance(l, Not):
            return {str(l.f1): False}
        return {str(l.f1): True}

    def __dict_to_literal(self, d):
        """Converts a fact to a HERA literal.
        
        :param d: Fact
        :type d: dict
        :return: HERA literal
        :rtype: Formula
        """
        k, v = list(d.items())[0]
        l = my_eval(k)
        if v:
            return l
        return Not(l)

    def __dict_to_literals(self, d):
        """Converts a partial state to a list of HERA literals.
        
        :param d: partial state
        :type d: dict
        :return: List of HERA literals
        :rtype: list
        """
        return [self.__dict_to_literal({x:d[x]}) for x in d]

    def get_all_consequences_lits(self):
        """Retrieve all consequences that hold in the final state.
        
        :return: The list of HERA literals that finally hold.
        :rtype: list
        """
        return self.__dict_to_literals(self.get_all_consequences())
        
    def __evaluate_term(self, term):
        """Evaluate an arithmetic term.
        
        :param term: The term to be evaluated
        :type term: Term
        :return: Result of the computation
        :rtype: int
        """
        if isinstance(term, int):
            return term
        if isinstance(term, Minus):
            return -1*self.__evaluate_term(term.f1)
        if isinstance(term, Add):
            return self.__evaluate_term(term.t1) + self.__evaluate_term(term.t2)
        if isinstance(term, Sub):
            return self.__evaluate_term(term.t1) - self.__evaluate_term(term.t2)
        if isinstance(term, U):
            return self.__sum_up(term.t1)
            
    def __sum_up(self, formula):
        """Sums up the utilities of a conjunction of literals.
        
        :param formula: Conjunction of literals.
        :type formula: Formula
        :return: Overall utility
        :rtype: int
        """
        if formula is None:
            return 0
        if isinstance(formula, bool):
            return 0
        if isinstance(formula, And):
            return self.__sum_up(formula.f1) + self.__sum_up(formula.f2)
        return self.get_utility(self.__literal_to_dict(formula))

    def models(self, formula):
        """Checks if a given formula is satisfied in the situation.
        
        :param formula: The formula to be checked.
        :type formula: Formula
        :return: True or False
        :rtype: bool
        """
        if isinstance(formula, Not):
            return not self.models(formula.f1)
        if isinstance(formula, Or):
            return self.models(formula.f1) or self.models(formula.f2)
        if isinstance(formula, Impl):
            return not self.models(formula.f1) or self.models(formula.f2)
        if isinstance(formula, BiImpl):
            return self.models(Impl(formula.f1, formula.f2)) and self.models(Impl(formula.f2, formula.f1))
        if isinstance(formula, And):
            return self.models(formula.f1) and self.models(formula.f2)
        if isinstance(formula, Bad):
            if self.__is_action(formula.f1):
                return formula.f1 in [a.name for a in self.actions if a.intrinsicvalue == "bad"]
            else:
                return self.get_utility(self.__literal_to_dict(formula.f1)) < 0
        if isinstance(formula, Good):
            if self.__is_action(formula.f1):
                return formula.f1 in [a.name for a in self.actions if a.intrinsicvalue == "good"]
            else:
                return self.get_utility(self.__literal_to_dict(formula.f1)) > 0
        if isinstance(formula, Neutral):
            if self.__is_action(formula.f1):
                return formula.f1 in [a.name for a in self.actions if a.intrinsicvalue == "neutral"]
            else:
                return self.get_utility(self.__literal_to_dict(formula.f1)) == 0
        if isinstance(formula, Caused):
            return self.__caused(self.__literal_to_dict(formula.f1))
        if isinstance(formula, Finally):
            return self.__is_satisfied(self.__literal_to_dict(formula.f1), self.get_all_consequences())
        if isinstance(formula, Means):
            return self.__treats_as_means(formula.f1, 1)
        if isinstance(formula, Means2):
            return self.__treats_as_means(formula.f1, 2)
        if isinstance(formula, End):
            return self.__treats_as_end(formula.f1)
        if isinstance(formula, Instrumental):
            return self.__is_instrumental(self.__literal_to_dict(formula.f1))
        if isinstance(formula, Avoidable):
            return self.__literal_to_dict(formula.f1) in self.get_avoidable_harmful_facts()
        if isinstance(formula, Goal):
            d = self.__literal_to_dict(formula.f1) 
            return set(d.items()) <= set(self.goal.items())
        if isinstance(formula, Eq):
            return self.__evaluate_term(formula.f1) == self.__evaluate_term(formula.f2)
        if isinstance(formula, Gt):
            return self.__evaluate_term(formula.f1) > self.__evaluate_term(formula.f2)
        if isinstance(formula, GEq):
            return self.__evaluate_term(formula.f1) >= self.__evaluate_term(formula.f2)

class Planner:
    """ A very simplistic planner """

    def __init__(self, situation):
        """Constructor
        
        :param situation: Description of the situation
        :type situation: Situation
        """
        self.situation = situation

    def generate_plan(self, frontier = None, k = 10, goal_checker = None):
        """A very simple action planner.
        
        :param frontier: The frontier of the current search (default is None)
        :type frontier: list
        :param k: Maximum plan length, for performance reasons (default is 10)
        :type k: int
        :param goal_checker: Function to map situation to true iff situation is a goal (default is None)
        :type goal_checker: function
        :returns: A plan that reaches the goal
        :rtype: Plan
        """
        if goal_checker == None:
            goal_checker = self.plan_found
        if k <= 0:
            return False
        if frontier == None:
            frontier = [Plan([])]
            # Maybe the empty plan already does the job
            s = goal_checker(frontier[0])
            if s != False:
                return s
        for a in self.situation.actions:
            newplancand = Plan(frontier[0].endoActions+[a.clone_action()])
            s = goal_checker(newplancand)
            if s != False:
                return s
            frontier += [newplancand]
        return self.generate_plan(frontier[1:], k - 1, goal_checker)

    def plan_found(self, newplancand):
        """Check if a new plan has been found. Used by generatePlan.
        
        :param newplancand: New candidate plan to be checked
        :type newplancand: Plan
        :return: Situation if plan has been found, otherwise False
        :rtype: Situation or bool
        """
        newsit = Situation(self.situation.inputfile)
        newsit.plan = newplancand
        fstate = newsit.simulate()
        if self.situation.satisfies_goal(fstate):
            return newsit
        return False

class MoralPlanner(Planner):

    def __init__(self, situation, principle):
        """Constructor
        
        :param situation: Description of the situation
        :type situation: Situation
        :param principle: Ethical principle
        :type principle: Principle
        """
        super().__init__(situation)
        self.principle = principle

    def generate_plan(self, frontier=None, k=10, goal_checker = None):
        """Generates a new plan.
        
        :param frontier: Current frontiert, defaults to None
        :type frontier: list of Plan, optional
        :param k: Search depth, defaults to 10
        :type k: int, optional
        :param goal_checker: Checks if plan satisfies goal, defaults to None
        :type goal_checker: Function, optional
        :return: Plan or False if no plan can be found
        :rtype: Plan or bool
        """
        if goal_checker == None:
            goal_checker = self.plan_found
        return super().generate_plan(frontier=frontier, k=k, goal_checker=goal_checker)

    def plan_found(self, newplancand):
        """Checks if Situation satisfies the goal
        
        :param newplancand: New plan candidate
        :type newplancand: Plan
        :return: Situation if plan achieves goal, otherwise False
        :rtype: Situation or bool
        """
        newsit = super().plan_found(newplancand)
        if newsit == False or not newsit.evaluate(self.principle):
            return False
        return newsit

    def generate_creative_alternative(self, principle):
        """Generates a permissible alternative to the current situation.
        
        :param principle: Ethical principle the plan of the new situation should satisfy.
        :type principle: Principle
        :return: Situation which the principle permits
        :rtype: Situation
        """
        for c in self.situation.creativeAlternatives:
            planner = MoralPlanner(c, principle)
            p = planner.generate_plan()
            if p != False:
                c.plan = p.plan
                return c
        return False

    def make_moral_suggestion(self, principle, *args):
        """A procedure to come up with a suggestion as to how
           to respond to a presented solution to a moral dilemma.
           * Case 1: The presented solution is permissible according to
                   the ethical principle. Then everything is fine.
           * Case 2: Case 1 does not hold. Therefore, a better plan is
                   searched for.
           * Case 3: Case 1 does not hold and the search in Case 2 is
                   unsuccessful. A counterfactual alternative situation is 
                   constructed which meets the requirements of the ethical principle.
        
        :param principle: The ethical principle to use to judge the situation
        :type principle: Principle
        :return: The solution
        :rtype: Situation
        """
        # Maybe the situation is alright as is
        if principle(self.situation, args).permissible():
            return self.situation
        # Maybe just the plan is bad and we can find a better one
        p = self.generate_plan()
        if p != False:
            sit = self.situation.clone_situation()
            sit.plan = p.plan
            if principle(args).permissible(sit):
                return sit
        # Otherwise, let's be creative
        return self.generate_creative_alternative(principle)