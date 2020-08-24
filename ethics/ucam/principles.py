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
from ethics.language import And, End, Impl, Means, Means2, Not


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
        self.is_permissible = None

    def permissible(self):
        """
        Checks if the principle regards an action as permissible.

        The permissibility is only calculated once.
        """
        if self.is_permissible is not None:
            return self.is_permissible
        self.is_permissible = self._check()
        return self.is_permissible

    @abstractmethod
    def _check(self):
        pass


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

    def _check(self):
        formula = get_ci_formula(self.model, self.reading)
        probability_ci = self.model.probability(formula, self.action)
        return probability_ci >= self.threshold


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

    def _check(self):
        formula = Not(get_ci_formula(self.model, self.reading))
        probability_violation = self.model.probability(formula, self.action)
        probability_smaller_gain = self.model.utility_probability(self.t_value[1], self.action)
        # If the probability of violating the CI is very small
        #   a small gain is enough to make the action permissible.
        if probability_violation < self.t_risk[1] and probability_smaller_gain == 1:
            return True
        probability_bigger_gain = self.model.utility_probability(self.t_value[0], self.action)
        # If the probability of violating the CI is only relatively small
        #   a higher gain is needed to make the action permissible.
        if probability_violation < self.t_risk[0] and probability_bigger_gain == 1:
            return True
        # If the probability of violating the CI is too high or no relevant
        #   gain is achieved the action is impermissible.
        return False


class ActionComparing(Principle):
    """
    Implements a common super class for principles,
        that compare a characteristic of the action
        to be performed to the same characteristic
        of all other actions.

    Functions:
    characteristic -- a function that given an action returns a number
                        representing a characteristic of the action.
    comparision -- a function comparing the characterstic for
                     the action with the list of the
                     characteristics for all actions and
                     returning a boolean representing whether
                     the relationship is correct or not.
    """

    def _check(self):
        characteristic_action = self._characteristic(self.action)
        characteristic_all_actions = [self._characteristic(action)
                                      for action in self.model.actions]
        return self._comparision(characteristic_action, characteristic_all_actions)

    @abstractmethod
    def _characteristic(self, action):
        pass

    @abstractmethod
    def _comparision(self, characteristic_action, characteristic_all_actions):
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
        self.reading = reading
        self.formula = get_ci_formula(model, reading)
        super(ActionComparing, self).__init__(model, action)

    def _characteristic(self, action):
        return self.model.probability(self.formula, action)

    def _comparision(self, probability_for_action, probability_all_actions):
        return probability_for_action == max(probability_all_actions)


class DecisionTheoreticUtilitarianism(ActionComparing):
    """
    Implements a extension of classical Utilitarianism using classic decision theory.

    This principle permits an action, if it results in the highest expected utility.
    """

    def _characteristic(self, action):
        """
        Get the expected utility of the action.
        """
        utility = 0
        for situation in self.model.situations:
            situation.set_action(action)
            utility += situation.get_utility() * situation.probability
        return utility

    def _comparision(self, utility_action, utilities_all_actions):
        return utility_action == max(utilities_all_actions)


class Minimax(ActionComparing):
    """
    Implements a utilitarian principle minimizing the possible damage of an action.

    This principle permits an action, if it has the lowest possible damage (negative utility).
    """

    def _characteristic(self, action):
        """
        Get the maximal damage.
        """
        min_utility = 0
        for situation in self.model.situations:
            situation.set_action(action)
            min_utility = min([min_utility,
                               *[situation.utilities[consequence]
                                 for consequence in situation.get_actual_consequences()
                                 if consequence in situation.utilities]])
        return min_utility

    def _comparision(self, damage_action, damage_all_actions):
        return damage_action == max(damage_all_actions)


class NegativeUtilitarianism(ActionComparing):
    """
    Implements a form of decision-theoretic utilitarianism only considering the damage of an action.

    This principle permits an action, if it results in the lowest expected damage.
    """

    def _characteristic(self, action):
        """
        Get expected negative utility.
        """
        expected_utility = 0
        for situation in self.model.situations:
            situation.set_action(action)
            negative_utility = sum(filter(lambda x: x <= 0,
                                          [situation.utilities[str(consequence)]
                                           for consequence in situation.get_actual_consequences()
                                           if str(consequence) in situation.utilities]))
            expected_utility += negative_utility * situation.probability
        return expected_utility

    def _comparision(self, expected_negative_utility_action, expected_negative_utility_all_actions):
        return expected_negative_utility_action == max(expected_negative_utility_all_actions)


class WeakNegativeUtilitarianism(Principle):
    """
    Implements a form of decision-theoretic utilitarianism first considering
        the damage of an action and only second considering the gain.

    This principle permits an action, if it has the lowest expected damage
        and the highest expected gain, of the actions with the same expected damage.
    """

    def _check(self):
        negative_utilitarianism = NegativeUtilitarianism(self.model, self.action)
        # The action needs to be allowed according to the Negative Utilitarianism:
        if not negative_utilitarianism.permissible():
            return False
        # The action needs to have the highest expected positive utility of all
        #   permitted (according to Negative Utilitarianism) actions:
        expected_positive_utility = self._get_expected_positive_utility(self.action)
        for action in self.model.actions:
            negative_utilitarianism.action = action
            if negative_utilitarianism.permissible():
                if self._get_expected_positive_utility(action) > expected_positive_utility:
                    return False
        return True

    def _get_expected_positive_utility(self, action):
        expected_utility = 0
        for situation in self.model.situations:
            situation.set_action(action)
            positive_utility = sum(filter(lambda x: x >= 0,
                                          [situation.utilities[consequence]
                                           for consequence in situation.get_actual_consequences()
                                           if consequence in situation.utilities]))
            expected_utility += positive_utility * situation.probability
        return expected_utility
