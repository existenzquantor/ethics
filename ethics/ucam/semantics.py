"""
Implements a uncertain ethical situation to be used by principles that deal with uncertainty.

Classes:
    Uncertain Model: A causal agency model with added uncertainty.
    Ethical Situation: A concreate ethical situation with a certain
        probability. To be used by the Uncertain Model.
"""

import copy
import io
import json
import yaml

from ethics.cam.semantics import CausalModel
from ethics.language import Atom, Formula, GEq, U
from ethics.tools import my_eval


class EthicalSituation(CausalModel):
    """
    Implements a Ethical Situation (a CausalModel with added probability)
        to be used in the Uncertain Model (UCAM).
    """

    def __init__(self, **kwargs):
        """
        Initialize a Ethical Situation.

        The arguments are given as key-value pairs:
            Necessary: Actions, Probability.
            Optional: Utilities, patients, description,
                consequences, background, mechanisms, goals, affects.
        """
        # Mandatory entries
        try:
            self.actions = [Atom(a) for a in kwargs["actions"]]
        except KeyError:
            print("Error: No actions set")
        self.action = self.actions[0]
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
        world = {**{v:0 for v in self.actions + self.background}, self.action:1, **information}

        super(CausalModel, self).__init__(
            self.actions + self.background, self.consequences, mechanisms, world)

    def get_utility(self):
        """
        Return the utility that the currently set action produces in the Ethical Situation.
        """
        utility = 0
        consequences = self.get_actual_consequences()
        for consequence in self.utilities:
            if consequence in consequences:
                utility += self.utilities[str(consequence)]
        return utility

    def set_action(self, var):
        """
        Set the action that is performed in the Ethical Situation.
        """
        self.action = var
        self.set_world({**self.world, **{v:0 for v in self.actions}, self.action:1})

    def __str__(self):
        string = "Ethical Situation: " + self.description + "\n" \
        + "Probability: " + str(self.probability) + "\n" \
        + "Action set: " + str(self.action) + "\n" \
        + "World:" + str(self.world)
        try:
            string = string + "\n" + "Model:" + str(self.causal_network_model)
        except KeyError:
            pass
        return string


class UncertainModel:
    """
    Implements a Causal Agency Model with added Uncertainty (UCAM).
    """

    def __init__(self, file):
        """
        Initialize a Uncertain Model.

        Argument:
        file -- the file the Model can be read from, either YAML or JSON.
        """
        self.file = file
        with io.open(file) as data_file:
            if self.file.split(".") == "json":
                self.model = json.load(data_file)
            else:
                self.model = yaml.load(data_file, Loader=yaml.FullLoader)

            try:
                self.description = str(self.model["description"])
            except KeyError:
                self.description = "No Description"

            # Actions are mandatory
            self.actions = [Atom(a) for a in self.model["actions"]]

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
                for situation in self.model["situations"]:
                    situations.append(EthicalSituation(
                        **self.model, **self.model["allSituations"], **situation["situation"]))
                self.situations = situations
            except TypeError:
                print("\nAn error occurred, the input file is probably malformed:\n")
                raise

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
        for situation in situations:
            result.situations.append(EthicalSituation(
                **result.model, **result.model["allSituations"], **situation))
        return result

    def evaluate(self, principle, action, **kwargs):
        """
        Test if the given action is allowed to be performed
            under the given principle in the Uncertain Model.

        Additional arguments for the principle must be given as keyword arguments.
        """
        return principle(self, action, **kwargs).permissible()

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

    def utility_probability(self, bound, action):
        """
        Determine the probability with witch the overall utility
            is higher or equal to the given bound.
        """
        probability = 0
        for situation in self.situations:
            situation.set_action(action)
            utilities = U(Formula.makeConjunction(situation.get_actual_consequences()))
            if situation.models(GEq(utilities, bound)):
                probability += situation.probability
        return probability

    def __str__(self):
        return "Uncertain Model: " + self.description + "\n" \
        + "Actions: " + str(self.actions) + "\n" \
        + "Background: " + str(self.background) + "\n" \
        + "Consequences: " + str(self.consequences) + "\n" \
        + f"{len(self.situations)} Situations" + "\n"
