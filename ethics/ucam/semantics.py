"""
Implements a uncertain ethical situation to be used by principles that deal with uncertainty.

Classes:
    Uncertain Model: A causal agency model with added uncertainty.
    Ethical Situation: A concreate ethical situation with a certain
        probability. To be used by the Uncertain Model.
"""

import copy
import io
import yaml

from ethics.cam.semantics import CausalModel
from ethics.language import Add, And, Atom, BiImpl, Bool, Eq, Formula, GEq, \
                            Gt, Impl, Max, Min, Minus, Mul, Not, Or, P, Ps, S, Sub, U, Um, Uo, Up
from ethics.tools import my_eval


class EthicalSituation(CausalModel):
    """
    Implements a Ethical Situation (a CausalModel with added probability)
        to be used in the Uncertain Model (UCAM).
    """

    def __init__(self, number, action, world, **kwargs):
        """
        Initialize a Ethical Situation.

        The arguments are given as key-value pairs:
            Necessary: Actions, Probability.
            Optional: Utilities, patients, description,
                consequences, background, mechanisms, goals, affects.
        """
        # Mandatory entries
        self.number = number
        try:
            self.actions = [Atom(a) for a in kwargs["actions"]]
        except KeyError:
            print("Error: No actions set")
        self.action = action
        try:
            self.probability = kwargs["probability"]
        except KeyError:
            print("Error: No probability set for situation")
        # Optional entries
        try:
            self.utilities = {str(k): v for k, v in kwargs["utilities"].items()}
        except KeyError:
            self.utilities = dict()
        try:
            self.patients = [str(a) for a in kwargs["patients"]]
        except KeyError:
            self.patients = []
        try:
            self.description = str(kwargs["description"])
        except KeyError:
            self.description = "No Description"
        try:
            self.designation = str(kwargs["designation"])
        except KeyError:
            self.designation = self.description + "#" + str(self.number)
        try:
            self.consequences = [Atom(c) for c in kwargs["consequences"]]
        except KeyError:
            self.consequences = []
        try:
            self.background = [Atom(b) for b in kwargs["background"]]
        except KeyError:
            self.background = []
        try:
            # use a dummy action for non existing mechanisms
            mechanisms = {**{str(k): Atom('dummy') for k in kwargs["consequences"]},
                          **{str(k): my_eval(v) for k, v in kwargs["mechanisms"].items()}}
        except KeyError:
            mechanisms = {str(k): Atom('dummy') for k in kwargs["consequences"]}
        try:
            self.goals = {str(k): list(map(my_eval, v)) for k, v in kwargs["goals"].items()}
        except KeyError:
            self.goals = dict()
        try:
            self.affects = {str(k): v for k, v in kwargs["affects"].items()}
        except KeyError:
            self.affects = dict()
        # Only for compatibility reasons
        self.events = []
        self.intentions = dict()

        # set world
        try:
            information = {v:1 for v in kwargs["information"]}
        except KeyError:
            information = dict()
        world = {**{v:0 for v in self.actions + self.background},
                 self.action:1, **information, **world}

        super(CausalModel, self).__init__(
            self.actions + self.background, self.consequences, mechanisms, world)

    def get_utility(self):
        """
        Return the formula for the utility that the currently set action
            produces in the Ethical Situation.
        """
        utility = []
        consequences = self.get_actual_consequences()
        for consequence in self.utilities:
            consequence = Atom(consequence)
            if consequence in consequences:
                utility.append(S(self.designation, U(consequence)))
        return Formula.makeSum(utility)

    def set_action(self, var):
        """
        Set the action that is performed in the Ethical Situation.
        """
        self.action = var
        self.set_world({**self.world, **{v:0 for v in self.actions}, self.action:1})

    def _evaluate_term(self, term):
        if isinstance(term, Uo):
            self.set_action(term.t1)
            return super()._evaluate_term(
                U(Formula.makeConjunction(self.get_actual_consequences())))
        if isinstance(term, Um):
            return min(super()._evaluate_term(U(term.t1)), 0)
        if isinstance(term, Up):
            return max(super()._evaluate_term(U(term.t1)), 0)
        # Everything else
        return super()._evaluate_term(term)
    evaluate_term = _evaluate_term # for compatibility

    def __repr__(self):
        string = "Ethical Situation: " + self.designation + "\n" \
        + "In UCAM: " + self.description + "\n" \
        + "Probability: " + str(self.probability) + "\n" \
        + "Action set: " + str(self.action) + "\n" \
        + "World:" + str(self.world)
        try:
            string = string + "\n" + "Model:" + str(self.causal_network_model)
        except KeyError:
            pass
        return string

    def __str__(self):
        return self.designation


class UncertainModel:
    """
    Implements a Causal Agency Model with added Uncertainty (UCAM).
    """

    def __init__(self, file, world=None):
        """
        Initialize a Uncertain Model.

        Argument:
        file -- the file the Model can be read from, either YAML or JSON.
        """
        if isinstance(file, str):
            file = io.open(file)
        with file as data_file:
            self.model = yaml.load(data_file, Loader=yaml.FullLoader)

            try:
                self.description = str(self.model["description"])
            except KeyError:
                self.description = "No Description"

            if world is None:
                self.world = {}
            else:
                self.world = world

            # Actions are mandatory
            self.actions = [Atom(a) for a in self.model["actions"]]

            try:
                self.testing_action = Atom(self.model["testing"])
            except KeyError:
                if not self.world:
                    self.testing_action = self.actions[0]
                else:
                    self.testing_action = self._get_action_from_world(self.world)

            # Optional variables
            try:
                self.consequences = [Atom(c) for c in self.model["consequences"]]
            except KeyError:
                self.consequences = []
            try:
                self.background = [Atom(b) for b in self.model["background"]]
            except KeyError:
                self.background = []
            try:
                self.patients = [str(a) for a in self.model["patients"]]
            except KeyError:
                self.patients = []

            try:
                # create situations
                situations = []
                number = 0
                for situation in self.model["situations"]:
                    situations.append(EthicalSituation(
                        number,
                        self.testing_action,
                        self.world,
                        **self.model,
                        **self.model["allSituations"],
                        **situation["situation"]))
                    number += 1
                self.situations = situations
            except TypeError:
                print("\nAn error occurred, the input file is probably malformed:\n")
                raise

    def different_action(self, action):
        """
        Create the same Uncertain Model with a different action.
        """
        result = copy.deepcopy(self)
        result.testing_action = Atom(action)
        for situation in result.situations:
            situation.set_action(action)
        return result

    def different_situations(self, situations):
        """
        Create the same Uncertain Model with different situations.

        A new Uncertain Model is created, with the existing situations removed and
            new ones are created according to the information given in situations.

        Arguments:
        situations -- a list of dicts (one for each situation),
            containing information for each situation (at least the probability).
        """
        result = copy.deepcopy(self)
        result.situations = []
        number = 0
        for situation in situations:
            result.situations.append(EthicalSituation(
                number,
                self.testing_action,
                self.world,
                **result.model,
                **result.model["allSituations"],
                **situation))
            number += 1
        return result

    def different_world(self, world):
        """
        Create the same Uncertain Model with a different world.
        """
        result = copy.deepcopy(self)
        result.testing_action = self._get_action_from_world(world)
        result.world = world
        result.situations = []
        number = 0
        for situation in self.situations:
            result.situations.append(EthicalSituation(
                number,
                result.testing_action,
                result.world,
                **result.model,
                **result.model["allSituations"],
                **situation))
            number += 1
        return result

    def evaluate(self, principle, **kwargs):
        """
        Test if the given action is allowed to be performed
            under the given principle in the Uncertain Model.

        Additional arguments for the principle must be given as keyword arguments.
        """
        return principle(self, self.testing_action, **kwargs).permissible()

    def explain(self, principle, **kwargs):
        """
        Explain the decision of the given principle in the Uncertain Model.

        Additional arguments for the principle must be given as keyword arguments.
        """
        return principle(self, self.testing_action, **kwargs).explain()

    def models(self, formula):
        """
        Return whether the given formula holds in the Uncertain Model.
        """
        if isinstance(formula, Eq):
            return self.evaluate_term(formula.f1) == self.evaluate_term(formula.f2)
        if isinstance(formula, Gt):
            return self.evaluate_term(formula.f1) > self.evaluate_term(formula.f2)
        if isinstance(formula, GEq):
            return self.evaluate_term(formula.f1) >= self.evaluate_term(formula.f2)
        if isinstance(formula, Or):
            return self.models(formula.f1) or self.models(formula.f2)
        if isinstance(formula, And):
            return self.models(formula.f1) and self.models(formula.f2)
        if isinstance(formula, Not):
            return not self.models(formula.f1)
        if isinstance(formula, Impl):
            return not self.models(formula.f1) or self.models(formula.f2)
        if isinstance(formula, BiImpl):
            return self.models(Impl(formula.f1, formula.f2)) and \
                   self.models(Impl(formula.f2, formula.f1))
        if isinstance(formula, Bool):
            return formula.f1
        raise TypeError(f'The type {type(formula)} of the given formula is not supported.')

    def necessary(self, formula):
        """
        Test if a given formula necessarily holds,
            i. e. it is modeled by all situations for all actions.
        """
        for action in self.actions:
            for situation in self.situations:
                situation.set_action(action)
                if not situation.models(formula):
                    return False
        return True

    def possible(self, formula):
        """
        Test if a given formula can hold,
            i. e. holds in one of the situations for a certain action.
        """
        for action in self.actions:
            for situation in self.situations:
                situation.set_action(action)
                if situation.models(formula):
                    return True
        return False

    def probability(self, formula, action):
        """
        Determine the probability with witch a given formula holds in the Uncertain Model.
        """
        probability = 0
        for situation in self.situations:
            situation.set_action(action)
            if situation.models(formula):
                probability += situation.probability
        return probability

    def evaluate_term(self, term):
        """
        Determine the value, that the given term has in the Uncertain Model.
        """
        if isinstance(term, (int, float)):
            return term
        if isinstance(term, Minus):
            return -1*self.evaluate_term(term.f1)
        if isinstance(term, Add):
            return self.evaluate_term(term.t1) + self.evaluate_term(term.t2)
        if isinstance(term, Sub):
            return self.evaluate_term(term.t1) - self.evaluate_term(term.t2)
        if isinstance(term, Mul):
            return self.evaluate_term(term.t1) * self.evaluate_term(term.t2)
        if isinstance(term, Max):
            return max(self.evaluate_term(term.t1), self.evaluate_term(term.t2))
        if isinstance(term, Min):
            return min(self.evaluate_term(term.t1), self.evaluate_term(term.t2))
        if isinstance(term, P):
            return self.probability(term.t1, term.t2)
        if isinstance(term, Ps):
            return self._get_situation_from_designation(term.t1).probability
        if isinstance(term, S):
            return self._get_situation_from_designation(term.t1).evaluate_term(term.t2)
        raise TypeError(f'The type {type(term)} of the given term is not supported.')

    def _get_action_from_world(self, world):
        for variable, truth in world.items():
            if truth == 1 and Atom(variable) in self.actions:
                return Atom(variable)
        raise ValueError(f"The given world ({world}) does not set an action.")

    def _get_situation_from_designation(self, designation):
        for situation in self.situations:
            if situation.designation == designation:
                return situation
        raise KeyError()

    def __repr__(self):
        return "Uncertain Model: " + self.description + "\n" \
        + "Actions: " + str(self.actions) + "\n" \
        + "Testing Action: " + str(self.testing_action) + "\n" \
        + "Background: " + str(self.background) + "\n" \
        + "Consequences: " + str(self.consequences) + "\n" \
        + f"{len(self.situations)} Situations" + "\n"

    def __str__(self):
        return self.description
