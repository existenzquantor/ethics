import json
import yaml
import io
import copy
import itertools

from ethics.language import Not, Or, And, Finally, Caused, Minus, Add, Sub, U, \
                            Bad, Good, Neutral, Instrumental, Impl, BiImpl, Avoidable, \
                            Goal, Means, Means2, Eq, Gt, GEq, End
from ethics.tools import myEval, minimalSets

class Action:
    """Representation of an endogeneous action"""
    def __init__(self, name, pre, eff, intrinsicvalue):
        """Constructor of an action
        
        Keyword arguments:
        name -- Label of the action
        pre -- Preconditions of the action
        eff -- (Conditional) Effects of the action
        intrinsicvalue -- Intrinsic moral value of the action as required by deontological principles
        """
        self.name = name
        self.pre = pre
        self.eff = eff
        self.intrinsicvalue = intrinsicvalue
        
    def __str__(self):
        """String representation of an action"""
        return self.name
        
class Event:
    """Representation of an event"""
    
    def __init__(self, name, pre, eff, times = None):
        """Constructor of an event
        
        Keyword arguments:
        name -- Label of the event
        pre -- Preconditions of the event
        eff -- (Conditional) Effects of the event
        times -- Time points at which the event will (try to) fire
        """
        self.name = name
        self.pre = pre
        self.eff = eff
        if times == None:
            times = []
        self.times = times
        
class Plan:
    """Representation of an action plan"""
    
    def __init__(self, endoPlan):
        """Constructor of an action plan
        
        Keyword arguments:
        endoPlan -- List of (endogeneous) actions
        """
        self.endoActions = endoPlan
        
    def __str__(self):
        """String representation of an action plan"""
        s = "["
        for a in self.endoActions:
            s += str(a) + ","
        return s+"]"

    def __repr__(self):
        """Representation of an action object"""
        return self.__str__()

class Situation:
    """Representation of a situation"""
    
    def __init__(self, json = None):
        """Constructor of a situation.
        
        Keyword arguments:
        json -- JSON file containing the description of the situation
        """
        if json == None:
            self.actions = None
            self.events = None
            self.init = None
            self.goal = None
            self.affects = None
            self.utilities = None
        else:
            self.__parse_model(json)

        self.alethicAlternatives = []
        self.epistemicAlternatives = []
        self.creativeAlternatives = []

        self.eventcounter = 0

    def clone_situation(self):
        """Build a new situation which equals the current situation."""
        return Situation(self.jsonfile)
 
    def __parse_model(self, jsonfile):
        """Build a situation from a JSON file. Used by the constructor.
        
        Keyword arguments:
        jsonfile -- The JSON file to be loaded.
        """
        self.jsonfile = jsonfile
        with io.open(jsonfile) as data_file:
            if jsonfile.split(".")[-1] == "yaml":
                data = yaml.load(data_file,  Loader=yaml.FullLoader)
            else:
                data = json.load(data_file)
            self.actions = []
            for a in data["actions"]:
                action = Action(a["name"], a["preconditions"], a["effects"], a["intrinsicvalue"])
                self.actions += [action]
            self.events = []
            for a in data["events"]:
                event = Event(a["name"], a["preconditions"], a["effects"], a["timepoints"])
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
        n = 0
        for e in self.events:
            n += len(e.times)
        return n
    
    def getHarmfulConsequences(self):
        """Retrieve all consequences of the action plan, which have negative utility."""
        allCons = self.getAllConsequences()
        harmful = []
        for u in self.utilities:
            if u["utility"] < 0:
                if self.__is_satisfied(u["fact"], allCons):
                    harmful += [u["fact"]]  
        return harmful  

    def getHarmfulFacts(self):
        """Retrieve all harmful facts"""
        harmful = []
        for u in self.utilities:
            if u["utility"] < 0:
                harmful += [u["fact"]]
        return harmful

    def __get_negation(self, fact):
        """Get the Negation of the fact"""
        v = list(fact.values())[0]
        return {list(fact.keys())[0]:not v}

    def getGenerallyAvoidableHarmfulFacts(self):
        """Retrieve all harmful facts for which there is a plan, whose execution does not result in the fact to be true."""
        avoidable = []
        sit = self.clone_situation()
        for h in sit.getHarmfulFacts():
            nh = sit.__get_negation(h)
            sit.goal = nh
            planner = Planner(self)
            plan = planner.generatePlan()
            if plan != False:
                avoidable += [h]
        return avoidable
    
    def getAllConsequences(self):
        """Retrieve all consequences of the action plan, i.e., the final state."""
        return self.simulate()

    def getUtility(self, fact):
        """Retrieve the utility of a particular fact.
        
        Keyword arguments:
        fact -- The fact of interest
        """
        for u in self.utilities:
            if fact == u["fact"]:
                return u["utility"]
        return 0

    def getFinalUtility(self):
        """Retrieve aggregated utility of the final state."""
        utility = 0
        sn = self.simulate()
        for k, v in sn.items():
            utility += self.getUtility({k:v})
        return utility
        
    def __is_instrumental_at(self, effect, positions):
        """Determine if the goal is reached also if some effect is blocked at particular positions of the execution.
        
        Keyword arguments:
        effect -- The effect to block (a fact)
        positions -- An array of bits representing for each endogeneous action in the plan if the introduction of the effect shall be blocked or not.
        """
        sn = self.simulate(blockEffect = effect, blockPositions = positions)
        return not self.satisfies_goal(sn)    
        
    def __is_instrumental(self, effect):
        """Determine if an effect is instrumental, i.e., if blocking this effect somewhere during plan execution will render the goal unachieved."""
        for p in self.__get_sub_plans(len(self.plan.endoActions)):
            if self.__is_instrumental_at(effect, p):
                return True
        return False
        
    def __treats_as_end(self, p):
        """A moral patient p is treated as an end iff it is positively and not negatively affected by some goal.
        
        Keyword arguments:
        p -- The moral patient
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
        
        Keyword arguments:
        p -- The moral patient
        """
        for e in self.affects[p]["pos"] + self.affects[p]["neg"]:
            if reading == 1 and self.__is_instrumental(e):
                return True
            if reading == 2 and self.__caused(e):
                return True
        return False
        
    def __caused(self, effect):
        """Check if some given effect is caused by the agent's actions.
        
        Keyword arguments:
        effect -- The effect
        """
        sn = self.simulate()
        if not self.__is_satisfied(effect, sn):
            return False
        for e in self.__get_sub_events():
            sne = self.simulate(skipEvents = e)
            if self.__is_satisfied(effect, sne):
                for p in self.__get_sub_plans():
                    sn = self.simulate(skipEndo = p, skipEvents = e)
                    if not self.__is_satisfied(effect, sn):
                        return True
        return False
        
    def __is_sufficient(self, skip, effect):
        """Check if some actions are sufficient for the effect to finally occur.
        
        Keyword arguments:
        skip -- actions to skip
        effect -- The effect
        """
        sn = self.simulate(skipEndo=[not b for b in skip])
        if self.__is_satisfied(effect, sn):
            return True
        return False
                    
    
    def getMinSufficient(self, effect):
        """Search for minimal sets of actions sufficient for the effect to finally occur.
        
        Keyword arguments:
        effect -- The effect
        """
        sn = self.simulate()
        if self.__is_satisfied(effect, sn):
            cand = []
            for p in self.__get_sub_plans():
                if self.__is_sufficient(p, effect):
                    cand.append(p)
            return minimalSets(cand)
        return None
        
    def __is_necessary(self, skip, effect):
        """Check if some actions are necessary for the effect to finally occur.
        
        Keyword arguments:
        skip -- actions to skip
        effect -- The effect
        """
        sn = self.simulate()
        if self.__is_satisfied(effect, sn):
            sn = self.simulate(skipEndo=skip)
            if not self.__is_satisfied(effect, sn):
                return True
        return False
   
   
    def getMinNecessary(self, effect):
        """Search for minimal sets of actions sufficient for the effect to finally occur.
        
        Keyword arguments:
        effect -- The effect
        """
        sn = self.simulate()
        if self.__is_satisfied(effect, sn):
            cand = []
            for p in self.__get_sub_plans():
                if self.__is_necessary(p, effect):
                    cand.append(p)
            return minimalSets(cand)
        return None
        
    def evaluate(self, principle, *args):
        """Check if the situation is permissible according to a given ethical principle.
        
        Keyword arguments:
        principle -- The ethical principle
        """
        try:
            p = principle(self, args)
        except:
            p = principle
        return p.permissible()

    def explain(self, principle, *args):
        try:
            p = principle(self, args)
        except:
            p = principle
        return p.explain()
            
    def __is_applicable(self, action, state):
        """Check if an action is applicable in a given state.
        
        Keyword arguments:
        action -- The action
        state -- The state
        """
        return self.__is_satisfied(action.pre, state)
        
    def __apply(self, action, state, blockEffect = None):
        """Apply an action to a state. Possibly block some of the action's effect.
        
        Keyword arguments:
        action -- The action to apply
        state -- The state to apply the action to
        blockEffect -- An effect to be blocked as an effect of the action (Default: None).
        """
        if blockEffect == None:
            blockEffect = {}
        if self.__is_applicable(action, state):
            si = copy.deepcopy(state)
            for condeff in action.eff:
                if self.__is_satisfied(condeff["condition"], si):
                    for v in condeff["effect"].keys():
                        if not v in blockEffect or blockEffect[v] != condeff["effect"][v]:    
                            state[v] = condeff["effect"][v]
        return state

    def __apply_all_events(self, state, events, time, skip):
        """Simulatneously, apply all applicable events to a state.
           
        Keyword arguments:
        state -- The current state to apply all events to
        events -- List of all events
        time -- Point in time
        skip -- Bit string representing which of the events to be skipped.
        """
        eventlist = [e for e in events if (time in e.times and self.__is_applicable(e, state))]
        si = copy.deepcopy(state)
        for e in eventlist:
            for condeff in e.eff:
                if self.__is_satisfied(condeff["condition"], state):
                    for v in condeff["effect"].keys():
                        if skip == None or skip[self.eventcounter] == 0:
                            si[v] = condeff["effect"][v]
            self.eventcounter += 1
        return si
    
    def __is_satisfied(self, partial, state):
        """Check if some partial state is satisfied in some full state.
        
        Keyword arguments:
        partial -- Partial state (e.g., a condition)
        state -- Full state
        """
        for k in partial.keys():
            if k not in state or partial[k] != state[k]:
                return False
        return True
        
    def satisfies_goal(self, state):
        """Check if a state is a goal state.
        
        Keyword arguments:
        state -- state to check for goal state
        """
        return self.__is_satisfied(self.goal, state)
           
    def __last_exo(self):
        """Compute the last event to fire. Used for the simulation to make sure, events after the last action will also be invoked."""
        m = 0
        for e in self.events:
            if max(e.times) > m:
                m = max(e.times)
        return m
        
    def __get_sub_plans(self, n = None):  
        """Computes all bit strings of length n. These are intended to be used as representing for each of the n steps in the plan, whether or not it is included in a subplan.
        
        Keyword arguments:
        n -- Length of the bit string (Default: None). If None, then n is set to the length of the complete plan.
        """     
        if n == None:
            n = len(self.plan.endoActions)
        return itertools.product([1, 0], repeat=n)

    def __get_sub_events(self, n = None):
        """Computes all bit strings of length n. These are intended to be used as representing for each of the n events, whether or not it should be considered.
        
        Keyword arguments:
        n -- Length of the bit string (Default: None). If None, then n is set to the number of events.
        """
        if n == None:
            n = self.__get_number_of_events()
        return itertools.product([0, 1], repeat=n)

    def simulate(self, skipEndo = None, skipEvents = None, blockEffect = None, blockPositions = None):
        """ Simulate a plan in a situation
        
        Keyword arguments:
        init -- The initial State
        skipEndo -- A list of bits representing for each endogeneous action in the plan whether or not to execute it.
        skipEvents -- A list of bits representing for each events whether or not to execute it.
        blockEffect -- An effect to counterfactually not been added to a successor state at actions specified in blockPositions.
        blockPositions -- Positions in the plan where the blockEffect should be blocked (given as a list of bits, one for each endogeneous action in the plan).
        """
        self.eventcounter = 0
        init = copy.deepcopy(self.init)
        if skipEndo == None:
            skipEndo = [0]*len(self.plan.endoActions)
        if blockEffect == None:
            blockEffect = {}
        if blockPositions == None:
            blockPositions = [0] * len(self.plan.endoActions)
        cur = init
        for t in range(len(self.plan.endoActions)):
            if not skipEndo[t]:
                if blockPositions[t] == 1:
                    cur = self.__apply(self.plan.endoActions[t], cur, blockEffect)
                else:
                    cur = self.__apply(self.plan.endoActions[t], cur)
            cur = self.__apply_all_events(cur, self.events, t, skipEvents)
        if self.__last_exo() >= len(self.plan.endoActions):
            for t in range(len(self.plan.endoActions), self.__last_exo()+1):
                cur = self.__apply_all_events(cur, self.events, t, skipEvents)
        return cur
    
    def __is_action(self, a):
        return a in [a.name for a in self.actions]
    
    def __literal_to_dict(self, l):
        l = l.nnf()
        if isinstance(l, Not):
            return {str(l.f1): False}
        return {str(l.f1): True}

    def __dict_to_literal(self, d):
        k = list(d.keys())[0]
        v = list(d.values())[0]
        l = myEval(k)
        if v:
            return l
        return Not(l)

    def __dict_to_literals(self, d):
        lits = []
        for x in d:
            lits.append(self.__dict_to_literal({x:d[x]}))
        return lits

    def get_all_consequences_lits(self):
        return self.__dict_to_literals(self.getAllConsequences())
        

    def __evaluate_term(self, term):
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
        if formula is None:
            return 0
        if isinstance(formula, bool):
            return 0
        if isinstance(formula, And):
            return self.__sum_up(formula.f1) + self.__sum_up(formula.f2)
        return self.getUtility(self.__literal_to_dict(formula))

    def models(self, formula):
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
                return self.getUtility(self.__literal_to_dict(formula.f1)) < 0
        if isinstance(formula, Good):
            if self.__is_action(formula.f1):
                return formula.f1 in [a.name for a in self.actions if a.intrinsicvalue == "good"]
            else:
                return self.getUtility(self.__literal_to_dict(formula.f1)) > 0
        if isinstance(formula, Neutral):
            if self.__is_action(formula.f1):
                return formula.f1 in [a.name for a in self.actions if a.intrinsicvalue == "neutral"]
            else:
                return self.getUtility(self.__literal_to_dict(formula.f1)) == 0
        if isinstance(formula, Caused):
            return self.__caused(self.__literal_to_dict(formula.f1))
        if isinstance(formula, Finally):
            return self.__is_satisfied(self.__literal_to_dict(formula.f1), self.getAllConsequences())
        if isinstance(formula, Means):
            return self.__treats_as_means(formula.f1, 1)
        if isinstance(formula, Means2):
            return self.__treats_as_means(formula.f1, 2)
        if isinstance(formula, End):
            return self.__treats_as_end(formula.f1)
        if isinstance(formula, Instrumental):
            return self.__is_instrumental(self.__literal_to_dict(formula.f1))
        if isinstance(formula, Avoidable):
            return self.__literal_to_dict(formula.f1) in self.getGenerallyAvoidableHarmfulFacts()
        if isinstance(formula, Goal):
            d = self.__literal_to_dict(formula.f1) 
            k = list(d.keys())[0]
            v = list(d.values())[0]
            return k in self.goal and self.goal[k] == v
        if isinstance(formula, Eq):
            return self.__evaluate_term(formula.f1) == self.__evaluate_term(formula.f2)
        if isinstance(formula, Gt):
            return self.__evaluate_term(formula.f1) > self.__evaluate_term(formula.f2)
        if isinstance(formula, GEq):
            return self.__evaluate_term(formula.f1) >= self.__evaluate_term(formula.f2)

class Planner:
    """ A very simplistic planner """

    def __init__(self, situation):
        self.situation = situation

    def generatePlan(self, frontier = None, k = 10, principle = None):
        """A very simple action planner.
        
        Keyword arguments:
        frontier -- The frontier of the current search (Default: None)
        k -- Maximum plan length, for performance reasons (Default: 10)
        principle -- Ethical principle the final plan should satisfy (Default: None)
        """
        if k == 0:
            return False
        if frontier == None:
            frontier = [Plan([])]
            # Maybe the empty plan already does the job
            s = self.__plan_found(frontier[0], principle)
            if s != False:
                return s
        for a in self.situation.actions:
            newplancand = Plan(frontier[0].endoActions+[a])
            s = self.__plan_found(newplancand, principle)
            if s != False:
                return s
            frontier += [newplancand]
        return self.generatePlan(frontier[1:], k - 1, principle)

    def __plan_found(self, newplancand, principle):
        """Check if a new plan has been found. Used by generatePlan.
        
        Keyword arguments:
        newplancand -- New candidate plan to be checked
        principle -- Ethical principle to evaluate the plan
        """
        newsit = Situation(self.situation.jsonfile)
        newsit.plan = newplancand
        fstate = newsit.simulate()
        if self.situation.satisfies_goal(fstate):
            if principle == None or principle(newsit).permissible():
                return newsit
        return False

    def generateCreativeAlternative(self, principle):
        """Generates a permissible alternative to the current situation.
           
           Keyword arguments:
           principle -- Ethical principle the plan of the new situation should satisfy.
        """
        for c in self.situation.creativeAlternatives:
            planner = Planner(c)
            c.plan = (planner.generatePlan(principle = principle)).plan
            if c.plan != False:
                return c
        return False

    def makeMoralSuggestion(self, principle, *args):
        """A procedure to come up with a suggestion as to how
           to respond to a presented solution to a moral dilemma.
           Case 1: The presented solution is permissible according to
                   the ethical principle. Then everything is fine.
           Case 2: Case 1 does not hold. Therefore, a better plan is
                   searched for.
           Case 3: Case 1 does not hold and the search in Case 2 is
                   unsuccessful. A counterfactual alternative situation is 
                   constructed which meets the requirements of the ethical principle.
           
           Keyword arguments:
           principle -- The ethical principle to use to judge the situation
        """
        # Maybe the situation is alright as is
        if principle(self.situation, args).permissible():
            return self.situation
        # Maybe just the plan is bad and we can find a better one
        p = self.generatePlan(principle = principle)
        if p != False:
            sit = self.situation.clone_situation()
            sit.plan = p.plan
            if principle(args).permissible(sit):
                return sit
        # Otherwise, let's be creative
        return self.generateCreativeAlternative(principle)
