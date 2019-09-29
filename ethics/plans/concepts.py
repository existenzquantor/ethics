import itertools
import copy

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