import json
import yaml
import io
import copy

from ethics.language import Not, Or, And, Finally, Caused, Minus, Add, Sub, U, \
                            Bad, Good, Neutral, Instrumental, Impl, BiImpl, Avoidable, \
                            Goal, Means, Means2, Eq, Gt, GEq, End, Atom
from ethics.tools import powerset
from ethics.plans.concepts import Plan, Action, EmptyAction, Event
from ethics.plans.planner import Planner

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
                try:
                    action = Action(a["name"], a["preconditions"], a["effects"], a["intrinsicvalue"])
                except:
                    action = Action(a["name"], a["preconditions"], a["effects"], "neutral")
                self.actions += [action]
            self.events = []
            for a in data["events"]:
                for t in a["timepoints"]:
                    event = Event(a["name"], a["preconditions"], a["effects"], t)
                    self.events += [event]
            try:
                self.affects = data["affects"]
            except:
                self.affects = dict()
            try:
                self.goal = data["goal"]
            except:
                self.goal = dict()
            self.init = data["initialState"]
            planactions = []
            try:
                for a in data["plan"]:
                    for b in self.actions:
                        if a == b.name:
                            planactions += [b]
                self.plan = Plan(planactions)
            except:
                self.plan = None
            try:
                self.utilities = data["utilities"]
            except:
                self.utilities = list()

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

    def get_harmful_facts(self):
        """Retrieve all harmful facts
        
        :return: All harmful facts in the domain.
        :rtype: list
        """
        return [u["fact"] for u in self.utilities if u["utility"] < 0]

    def __get_negation(self, partial):
        """Get the Negation of a partial state
        
        :param fact: the partial state
        :type fact: dict
        :return: the negated partial state
        :rtype: dict
        """
        return {k:not v for k,v in partial.items()}
        
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
                if self.__is_satisfied(condeff["condition"], si):
                    for v in condeff["effect"].keys():
                        state[v] = condeff["effect"][v]
        return state
    
    def __is_satisfied(self, partial, state):
        """Check if some partial state is satisfied in some full state.
        
        :param partial: Partial state (e.g., a condition)
        :type partial: dict
        :param state: Full state
        :type state: dict
        :return: True or False
        :rtype: bool
        """
        return all(k in state and partial[k] == state[k] for k in partial)
        
        
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
        m = -1
        for e in self.events:
            if e.time > m:
                m = e.time
        return m

    def simulate(self):
        """Simulated the plan (and the events) in the given situation and returns the final state.
        
        :return: Final state
        :rtype: dict
        """
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
        return {str(l.f1): not isinstance(l, Not)}

    def __dict_to_literal(self, d):
        """Converts a fact to a HERA literal.
        
        :param d: Fact
        :type d: dict
        :return: HERA literal
        :rtype: Formula
        """
        k, v = list(d.items())[0]
        return Atom(k) if v else Not(Atom(k))

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