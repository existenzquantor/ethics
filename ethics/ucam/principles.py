"""
Implements a collection of ethical principles that deal with uncertainty.

Classes:
    Threshold: Implements a deontological principle using a threshold.
    Category: Implements a deontological principle using diffrent categories.
    SmallestRisk: Implements a deontological principle comparing options.
    DecisionTheoreticUtilitarianism: Implements a utilitarian principle
                                        using classic decision theory.
    Minimax: Implements a utilitarian principle with sole emphasis
                                        on the possible damage.
    NegativeUtilitarianism: Implements a utilitarian principle only
                                considering the expected damage.
    WeakNegativeUtilitarianism: Implements a utilitarian principle
                                    focusing first on expected damgage
                                    and only second on expected gain.
"""

from abc import ABC, abstractmethod
from ethics.explanations import generate_reasons, generate_inus_reasons
from ethics.language import And, End, Eq, Formula, GEq, Gt, Impl, \
                            Means, Means2, Mul, Not, Or, P, Ps, S, Um, Uo, Up


class Principle(ABC):
    """
    Common super class for all uncertain principles.
    """

    def __init__(self, model, action):
        """
        Initialize a abstract principle.

        Arguments:
        model -- the uncertain model to be evaluated by the principle.
        action -- the action, in the model, that is to be considered by the principle.
        """
        self.action = action
        self.model = model
        self.label = ""
        self.is_permissible = None

    def buildConjunction(self):
        """
        Return the formula of the principle.
        """
        return Formula.makeConjunction(self.formulae)

    def explain(self):
        """
        Explain the decision of the principle.
        """
        reasons = generate_reasons(self.model, self)
        suff = {r["reason"] for r in reasons if r["type"] == "sufficient"}
        nec = {r["reason"] for r in reasons if r["type"] == "necessary"}
        inus = generate_inus_reasons(reasons)
        if len(reasons) > 0:
            return {"permissible": reasons[0]["perm"], "principle": self.label,
                    "sufficient": suff, "necessary": nec, "inus": inus}
        return {"permissible": self.permissible(), "principle": self.label,
                "sufficient": set(), "necessary": set(), "inus": set()}

    @property
    @abstractmethod
    def formulae(self):
        """
        Return the formulae describing the principle.
        """

    def permissible(self):
        """
        Check if the principle regards an action as permissible.

        The permissibility is only calculated once.
        """
        if self.is_permissible is not None:
            return self.is_permissible
        self.is_permissible = self.model.models(Formula.makeConjunction(self.formulae))
        return self.is_permissible


def get_ci_formula(model, reading):
    """
    Calculate the formula, that needs to hold, so that the CI is fullfilled.

    Arguments:
    model -- the Uncertain Model to consider.
    reading -- the variant/reading of "to be treated as a means" to be used.
    """
    # select correct means variant according to reading
    means = lambda x: Means(x) if reading == 1 else Means2(x)

    formula = Impl(means(model.patients[0]), End(model.patients[0]))
    for patient in model.patients[1:]:
        formula = And(formula, Impl(means(patient), End(patient)))
    return formula


class Threshold(Principle):
    """
    Implements a deontological principle based on a threshold.

    This principle permits an action, if the probability of acting
        in accordance with the Categorical Imperative is above a given threshold.
    """

    def __init__(self, model, action, reading, threshold):
        """
        Initialize the Threshold Principle.

        Arguments:
        reading -- the reading of beeing treated as a means to be used.
        threshold -- the threshold, the probability of acting in accordance
                        with the CI must at least reach (P(CI) >= threshold).
        """
        super().__init__(model, action)
        self.reading = reading
        self.threshold = threshold
        self.label = "Threshold Principle"

    @property
    def formulae(self):
        formula = get_ci_formula(self.model, self.reading)
        return [GEq(P(formula, self.action), self.threshold)]


class Category(Principle):
    """
    Implements a deontological principle based on diffrent categories.

    This principle permits an action, if the probability of following the CI
        and a certain gain from the action, are in one
        of two permitted relationships to each other:
    1. P(not(CI)) < r_1 and P(u >= v_1) = 1.
    2. P(not(CI)) < r_2 and P(u >= v_2) = 1.
    """

    def __init__(self, model, action, reading, t_risk, t_value):
        """
        Initialize the Category Principle.

        Arguments:
        reading -- the reading of beeing treated as a means to be used.
        t_risk -- the tuple defining (r_1, r_2).
        t_value -- the tuple defining (v_1, v_2).
        """
        super().__init__(model, action)
        self.reading = reading
        self.t_risk = t_risk
        self.t_value = t_value
        self.label = "Category Principle"

    def _get_option(self, not_ci_formula, probability_ci_violation, necessary_gain):
        # The probability of violating the CI must be low eonugh:
        ci_violation_small_enough = Gt(probability_ci_violation, P(not_ci_formula, self.action))
        # The probability of achieving enough gain must be 1:
        probability_enough_gain = P(GEq(Uo(self.action), necessary_gain), self.action)
        return And(ci_violation_small_enough, Eq(probability_enough_gain, 1))

    @property
    def formulae(self):
        not_ci = Not(get_ci_formula(self.model, self.reading))
        # If the probability of violating the CI is very small
        #   a small gain is enough to make the action permissible:
        option_2 = self._get_option(not_ci, self.t_risk[1], self.t_value[1])
        # If the probability of violating the CI is only relatively small
        #   a higher gain is needed to make the action permissible:
        option_1 = self._get_option(not_ci, self.t_risk[0], self.t_value[0])
        return [Or(option_1, option_2)]


class ActionComparing(Principle):
    """
    Implements a common super class for principles,
        that compare a characteristic of the action
        to be performed to the same characteristic
        of all other actions.

    The the action is allowed if its characteristic is the
        maximum characteristic of all possible actions.

    Functions:
    characteristic -- a function that given an action returns a formula
                        representing a characteristic of the action.
    """

    @property
    def formulae(self):
        characteristic_action = self._characteristic(self.action)
        characteristic_all_actions = [self._characteristic(action)
                                      for action in self.model.actions]
        return [Eq(characteristic_action, Formula.makeMax(characteristic_all_actions))]

    @abstractmethod
    def _characteristic(self, action):
        pass


class SmallestRisk(ActionComparing):
    """
    Implements a deontological principle based on comparing the
        probabilities of CI accordance of diffrent options.

    This principle permits an action, if the probability of
        fullfilling the CI by choosing this action,
        is higher than that of every other action.
    """

    def __init__(self, model, action, reading):
        """
        Initialize the Smallest Risk Principle.

        Arguments:
        reading -- the reading of beeing treated as a means to be used.
        """
        super(ActionComparing, self).__init__(model, action)
        self.reading = reading
        self.ci_formula = get_ci_formula(model, reading)
        self.label = "Smallest Risk Principle"

    def _characteristic(self, action):
        return P(self.ci_formula, action)


class DecisionTheoreticUtilitarianism(ActionComparing):
    """
    Implements a extension of classical Utilitarianism using classic decision theory.

    This principle permits an action, if it results in the highest expected utility.
    """

    def __init__(self, model, action):
        super(ActionComparing, self).__init__(model, action)
        self.label = "Decision Theoretic Utilitarianism"

    def _characteristic(self, action):
        """
        Get the formula for the expected utility of the action.
        """
        expected_utility = []
        for situation in self.model.situations:
            situation.set_action(action)
            expected_utility.append(Mul(situation.get_utility(), Ps(situation.designation)))
        return Formula.makeSum(expected_utility)


class Minimax(ActionComparing):
    """
    Implements a utilitarian principle minimizing the possible damage of an action.

    This principle permits an action,
        if it has the lowest possible damage (highest negative utility).
    """

    def __init__(self, model, action):
        super(ActionComparing, self).__init__(model, action)
        self.label = "Minimax Principle"

    def _characteristic(self, action):
        """
        Get the formula for the maximal damage.
        """
        min_utility = []
        for situation in self.model.situations:
            situation.set_action(action)
            min_utility.extend([S(situation.designation, Um(consequence))
                                for consequence in situation.get_actual_consequences()
                                if str(consequence) in situation.utilities])
        return Formula.makeMin(min_utility)


class NegativeUtilitarianism(ActionComparing):
    """
    Implements a form of decision-theoretic utilitarianism only considering the damage of an action.

    This principle permits an action, if it results in the lowest expected damage.
    """

    def __init__(self, model, action):
        super(ActionComparing, self).__init__(model, action)
        self.label = "(Strong) Negative Utilitarianism"

    def _characteristic(self, action):
        """
        Get the formula for the expected negative utility.
        """
        expected_utility = []
        for situation in self.model.situations:
            situation.set_action(action)
            negative_utility = Formula.makeSum([S(situation.designation, Um(consequence))
                                                for consequence
                                                in situation.get_actual_consequences()
                                                if str(consequence) in situation.utilities])
            expected_utility.append(Mul(negative_utility, Ps(situation.designation)))
        return Formula.makeSum(expected_utility)


class WeakNegativeUtilitarianism(Principle):
    """
    Implements a form of decision-theoretic utilitarianism first considering
        the damage of an action and only second considering the gain.

    This principle permits an action, if it has the lowest expected damage
        and the highest expected gain, of the actions with the same expected damage.
    """

    def __init__(self, model, action):
        super().__init__(model, action)
        self.label = "Weak Negative Utilitarianism"

    @property
    def formulae(self):
        negative_utilitarianism = NegativeUtilitarianism(self.model, self.action)
        # The action needs to be allowed according to the Negative Utilitarianism:
        negative_utilitarianism_own_action = Formula.makeConjunction(
            negative_utilitarianism.formulae)
        # The action needs to have the highest expected positive utility of all
        #   permitted (according to Negative Utilitarianism) actions:
        expected_positive_utility = self._get_expected_positive_utility(self.action)
        requirement_actions = []
        for action in self.model.actions:
            negative_utilitarianism.action = action
            negative_utilitarianism_action = Formula.makeConjunction(
                negative_utilitarianism.formulae)
            requirement_actions.append(Impl(negative_utilitarianism_action,
                                            GEq(expected_positive_utility,
                                                self._get_expected_positive_utility(action))))
        return [negative_utilitarianism_own_action, *requirement_actions]

    def _get_expected_positive_utility(self, action):
        expected_utility = []
        for situation in self.model.situations:
            situation.set_action(action)
            positive_utility = Formula.makeSum(
                [S(situation.designation, Up(consequence))
                 for consequence in situation.get_actual_consequences()
                 if str(consequence) in situation.utilities])
            expected_utility.append(Mul(positive_utility, Ps(situation.designation)))
        return Formula.makeSum(expected_utility)
