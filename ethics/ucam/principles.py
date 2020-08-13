"""
Implements a collection of ethical principles that deal with uncertainty.

Classes:
    Threshold: Implements a deontological principle using a threshold.
    Category: Implements a deontological principle using diffrent categories.
    SmallestRisk: Implements a deontological principle comparing options.
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


class SmallestRisk(Principle):
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
        super().__init__(model, action)

    def _check(self):
        formula = get_ci_formula(self.model, self.reading)
        probability_for_action = self.model.probability(formula, self.action)
        probability_all_actions = [self.model.probability(formula, action)
                                   for action in self.model.actions]
        return probability_for_action == max(probability_all_actions)
