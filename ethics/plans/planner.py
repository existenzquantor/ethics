from ethics.plans.concepts import Plan

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
        newsit = self.situation.clone_situation()
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