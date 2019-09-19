from ethics.cam.semantics import *
from ethics.language import *
from ethics.tools import *
from ethics.explanations import generateReasons, identifyINUSReasons
from ethics.argumentation import ArgModel, ArgGraph, ArgSolver

class Principle(object):
    """
    Common super class
    for all principles.
    """
    def __init__(self, model):
        self.model = model
        self.formulae = []
        self.result = []
        self.symbolformula = dict()
        self.counter = 0
        self.label = ""
        
    def buildConjunction(self):
        return Formula.makeConjunction(self.formulae)

    def _check(self):
        pass

    def permissible(self):
        pass

    def explain(self):
        reasons = generateReasons(self.model, self)
        suff = [r["reason"] for r in reasons if r["type"] == "sufficient"]
        nec = [r["reason"] for r in reasons if r["type"] == "necessary"]
        inus = identifyINUSReasons(reasons)
        if len(reasons) > 0:
            return {"permissible": reasons[0]["perm"], "principle": self.label, "sufficient": suff, "necessary": nec, "inus": inus}
        return []

class DoubleEffectPrinciple(Principle):
    """
    An Implementation of
    the formalization of the
    double effect principle
    according to section 4.
    """
    def __init__(self, model):
        super(DoubleEffectPrinciple, self).__init__(model)
        self.label = "Double Effect Principle"

    # Condition 1 - The Act Itself Must Be Morally Good or Indifferent
    def _condition1(self):
        for a in self.model.get_all_actions():
            return GEq(U(a), 0)

    # Condition 2a - The Positive Consequence Must Be Intended ...
    def _condition2a(self):

        #return Exists('__x__', And(I('__x__'), Gt(U('__x__'), 0)))
        f = None
        for c in self.cons:
            if f == None:
                f = And(I(c), Good(c))
            else: 
                f = Or(f, (And(I(c), Good(c))))
        return f

    # Condition 2b - ... and the Negative Consequence May not Be Intended
    def _condition2b(self):

        #return Forall('__x__', Impl(I('__x__'), GEq(U('__x__'), 0)))
        f = None
        for c in self.cons:
            if f == None:
                f = Impl(I(c), Good(c))
            else: 
                f = And(f, Impl(I(c), Good(c)))
        return f

    # Condition 3 - The Negative Consequence May Not Be a Means to Obtain the Positive Consequence
    def _condition3(self):

        f = None
        for cj in self.cons:
            for ck in self.cons:
                if f == None:
                    f = Not(And(Causes(cj, ck), And(Bad(cj), Good(ck))))
                else: 
                    f = And(f, Not(And(Causes(cj, ck), And(Bad(cj), Good(ck)))))
        return f
        #return Forall('__x__', Forall('__y__', Impl(And(Causes('__x__', '__y__'), Gt(0, U('__x__'))), Gt(0, U('__y__')))))

    # Condition 4 - There Must Be Proportionally Grave Reasons to Prefer the Positive Consequence While Permitting the Negative Consequence
    def _condition4(self):

        f = None
        for c in self.cons:
            if f == None:
                f = c
            else: 
                f = And(f, c)
        return Gt(U(f), 0)

    def _check(self):
        self.cons = self.model.get_actual_consequences()
        self.formulae = [self._condition1(), self._condition2a(), self._condition2b(), self._condition3(), self._condition4()]
        self.result = [self.model.models(f) for f in self.formulae if f is not None]
        return self.result

    def permissible(self):
        self._check()
        return False not in self.result


class UtilitarianPrinciple(Principle):
    """
    This principle compares
    some world to its
    alternatives. According
    to the utilitarian principle,
    a world is permissible
    iff it is among the worlds
    with highest utility.
    """
    def __init__(self, model):
        super(UtilitarianPrinciple, self).__init__(model)
        self.label = "Utilitarianism"

    def _check(self):
        u = U(Formula.makeConjunction(self.model.get_actual_consequences()))
        v = []
        for w in self.model.alternatives:
            v.append(U(Formula.makeConjunction(w.get_actual_consequences())))
        f = None
        for w in v:
            f = GEq(u, w) if f is None else And(f, GEq(u, w))
        if f is None: # no alternatives
            f = True
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        if len(self.model.alternatives) == 0:
            self.model.alternatives.append(self.model)
        self._check()
        f =  self.formulae[0]
        return self.result == [True]


class DoNoHarmPrinciple(Principle):
    """
    This principle permits an action
    iff it has no bad consequence.
    """
    def __init__(self, model):
        super(DoNoHarmPrinciple, self).__init__(model)
        self.label = "Do No Harm"

    def _check(self):
        #actions_combination = [Formula.makeDisjunction(e) for e in list(powerset(self.model.get_performed_actions()))[1:]]
        f = Formula.makeConjunction([Impl(Bad(c), Not(Caused(c))) for c in self.cons])
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self.cons = self.model.get_actual_consequences()
        self._check()
        return self.result == [True]


class DoNoInstrumentalHarmPrinciple(Principle):
    """
    This principle permits an action
    iff it does not make use of bad means.
    """
    def __init__(self, model):
        super(DoNoInstrumentalHarmPrinciple, self).__init__(model)
        self.label = "Do No Instrumental Harm"

    def _check(self):
        f = Formula.makeConjunction([Impl(Instrumental(c), Not(Bad(c))) for c in self.cons])
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self.cons = self.model.get_actual_consequences()
        self._check()
        return self.result == [True]



class DoNoInstrumentalHarmPrincipleWithoutIntentions(Principle):
    """
    This principle permits an action
    iff it does not make use of bad means.
    """
    def __init__(self, model):
        super(DoNoInstrumentalHarmPrincipleWithoutIntentions, self).__init__(model)
        self.label = "Do No Instrumental Harm Without Intentions"

    def _check(self):
        f = None
        for cj in self.cons:
            for ck in self.cons:
                if f == None:
                    f = Not(And(Causes(cj, ck), And(Bad(cj), Good(ck))))
                else: 
                    f = And(f, Not(And(Causes(cj, ck), And(Bad(cj), Good(ck)))))

        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self.cons = self.model.get_actual_consequences()
        self._check()
        return self.result == [True]


class MinimizeHarmPrinciple(Principle):
    """
    This principle permits an action
    iff it has minimal negative direct consequence.
    """
    def __init__(self, model):
        super(MinimizeHarmPrinciple, self).__init__(model)
        self.label = "Minimize Harm"

    def _check(self):
        u = U(Formula.makeConjunction(self.model.getDirectBadConsequences()))
        v = []
        for w in self.model.alternatives:
            if self.model != w:
                v.append(U(Formula.makeConjunction(w.getDirectBadConsequences())))
        f = None
        for w in v:
            f = GEq(u, w) if f is None else And(f, GEq(u, w))
        if f is None: # no alternatives
            f = True
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self._check()
        return self.result == [True]


class MinimaxHarmPrinciple(Principle):
    """
    This principle permits an action
    iff it has minimum maximal negative consequence.
    """
    def __init__(self, model):
        super(MinimaxHarmPrinciple, self).__init__(model)
        self.label = "Minimax Harm"

    def _check(self):
        bc_own = []
        for bc in self.model.getAllBadConsequences():
            bc_own.append(U(bc))
        bc_others = []
        for w in self.model.alternatives:
            if self.model != w:
                bc_other = []
                for bc in w.getAllBadConsequences():
                    bc_other.append(U(bc))
                bc_others.append(bc_other)
                
        fy = None
        for w in bc_others:
            ft = None
            for v in w:
                for u in bc_own:
                    ft = Gt(v, u) if ft is None else And(ft, Gt(v, u))
            fy = ft if fy is None else Or(ft, fy)
        f = Not(fy)
            
        if f is None: # no alternatives
            f = True
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self._check()
        return self.result == [True]


class DeontologicalPrinciple(Principle):
    """
    This principle permits an action
    iff it is intrinsically good or neutral.
    """
    def __init__(self, model):
        super(DeontologicalPrinciple, self).__init__(model)
        self.label = "DeontologicalPrinciple"

    def _check(self):
        f = Formula.makeConjunction([Not(Bad(a)) for a in self.model.get_performed_actions()])
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result

    def permissible(self):
        self._check()
        return self.result == [True]
        
        
class ActionFocusedDeontologicalPrinciple(DeontologicalPrinciple):
    """
    This principle permits an action
    iff it is intrinsically good or neutral.
    """
    def __init__(self, model):
        super(ActionFocusedDeontologicalPrinciple, self).__init__(model)
        self.label = "ActionFocusedDeontologicalPrinciple"
        
        
class IntentionFocusedDeontologicalPrinciple(DeontologicalPrinciple):
    """
    This principle permits an action
    iff all intentions are intrinsically good or neutral.
    """
    def __init__(self, model):
        super(IntentionFocusedDeontologicalPrinciple, self).__init__(model)
        self.label = "IntentionFocusedDeontologicalPrinciple"
    
    def _check(self):
        f = Formula.makeConjunction([Impl(I(c), Not(Bad(c))) for c in self.model.get_actual_consequences()])
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result
    
    def permissible(self):
        self._check()
        return self.result == [True]
 
class GoalFocusedDeontologicalPrinciple(DeontologicalPrinciple):
    """
    This principle permits an action
    iff all intentions are intrinsically good or neutral.
    """
    def __init__(self, model):
        super(GoalFocusedDeontologicalPrinciple, self).__init__(model)
        self.label = "GoalFocusedDeontologicalPrinciple"
    
    def _check(self):
        f = Formula.makeConjunction([Impl(Goal(c), Not(Bad(c))) for c in self.model.get_actual_consequences()])
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result
    
    def permissible(self):
        self._check()
        return self.result == [True]
        
class KantianHumanityPrincipleReading1(Principle):
    """
    This principle permits an action
    iff it passes Kants humanity formulation
    of the categorial imperative.
    """
    def __init__(self, model):
        super(KantianHumanityPrincipleReading1, self).__init__(model)
        self.label = "KantianHumanityPrincipleReading1"

    def _check(self):
        f1 = Impl(Means(self.model.patients[0]), End(self.model.patients[0]))
        for p in self.model.patients[1:]:
            f1 = And(f1, Impl(Means(p), End(p)))
        self.formulae = [f1]
        self.result = [self.model.models(f1)]
        return self.result

    def permissible(self):
        self._check()
        return self.result == [True]
        

class KantianHumanityPrinciple(KantianHumanityPrincipleReading1):
    """
    This principle permits an action
    iff it passes Kants humanity formulation
    of the categorial imperative.
    """
    def __init__(self, model):
        super(KantianHumanityPrinciple, self).__init__(model)


class KantianHumanityPrincipleReading2(Principle):
    """
    This principle permits an action
    iff it passes Kants humanity formulation
    of the categorial imperative.
    """
    def __init__(self, model):
        super(KantianHumanityPrincipleReading2, self).__init__(model)
        self.label = "KantianHumanityPrincipleReading2"

    def _check(self):
        f1 = Impl(Means2(self.model.patients[0]), End(self.model.patients[0]))
        for p in self.model.patients[1:]:
            f1 = And(f1, Impl(Means2(p), End(p)))
        self.formulae = [f1]
        self.result = [self.model.models(f1)]
        return self.result

    def permissible(self):
        self._check()
        return self.result == [True]
    
        
class ParetoPrinciple(Principle):
    """ This principle permits an action
    iff it is not dominated by any other action.
    """
    def __init__(self, model):
        super(ParetoPrinciple, self).__init__(model)
        self.label = "Pareto"

    def _dominates_formula(self, w0, w1):
        cons_good_w1 = []
        cons_bar_good_w1 = []
        cons_bad_w1 = []
        cons = w1.get_all_consequences()
        for c in cons:
            if w1.models(Gt(U(c), 0)):
                cons_good_w1.append(c)
            elif w1.models(Gt(0, U(c))):
                cons_bad_w1.append(c)
            if w1.models(Gt(U(Not(c)), 0)):
                cons_bar_good_w1.append(c)
        
        cons = w0.get_all_consequences()
        cons_bad_w0 = []
        for c in cons:
            if w0.models(Gt(0, U(c))):
                cons_bad_w0.append(c)

        # cond 1
        f1 = None
        for c in cons_good_w1:
            if f1 is None:
                #f1 = self.getSymbol(Impl(Gt(U(c), 0), Intervention(And(Not(w1.action), w0.action), c)))
                f1 = Impl(And(Gt(U(c), 0), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c))
            else:
                #f1 = And(f1, self.getSymbol(Impl(Gt(U(c), 0), Intervention(And(Not(w1.action), w0.action), c))))
                f1 = And(f1, Impl(And(Gt(U(c), 0), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c)))
        
        # cond 2
        f2a = None
        for c in cons_bar_good_w1:
            if f2a is None:
                #f2a = self.getSymbol(Impl(Gt(U(Not(c)), 0), Intervention(And(Not(w1.action), w0.action), c)))
                f2a = Impl(And(Gt(U(Not(c)), 0), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c))
            else:
                #f2a = Or(f2a, self.getSymbol(Impl(Gt(U(Not(c)), 0), Intervention(And(Not(w1.action), w0.action), c))))
                f2a = Or(f2a, Impl(And(Gt(U(Not(c)), 0), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c)))
                
        f2b = None
        for c in cons_bad_w1:
           if f2b is None:
               #f2b = self.getSymbol(Impl(Gt(0, U(c)), Not(Intervention(And(Not(w1.action), w0.action), c))))
               f2b = Impl(And(Gt(0, U(c)), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c))
           else:
               #f2b = Or(f2b, self.getSymbol(Impl(Gt(0, U(c)), Not(Intervention(And(Not(w1.action), w0.action), c)))))
               f2b = Or(f2b, Impl(And(Gt(0, U(c)), Intervention(And(w1.action, Not(w0.action)), c)), Intervention(And(Not(w1.action), w0.action), c)))

        # cond 3
        f3 = None
        for c in cons_bad_w0:
           if f3 is None:
               #f3 = self.getSymbol(Impl(Gt(0, U(c)),c))
               f3 = Impl(And(Gt(0, U(c)), Intervention(And(Not(w1.action), w0.action), c)), Intervention(And(w1.action, Not(w0.action)), c))
           else:
               #f3 = And(f3, self.getSymbol(Impl(Gt(0, U(c)), c)))
               f3 = And(f3, Impl(And(Gt(0, U(c)), Intervention(And(Not(w1.action), w0.action), c)), Intervention(And(w1.action, Not(w0.action)), c)))

        f = None
        if f1 is not None:
            f = f1
        if f3 is not None:
            if f is None:
                f = f3
            else:
                f = And(f, f3)
        if f2a is not None and f2b is not None:
            if f is None:
                f = Or(f2a, f2b)
            else:
                f = And(f, Or(f2a, f2b))
        if f2a is not None and f2b is None:
            if f is None:
                f = f2a
            else:
                f = And(f, f2a)
        if f2a is None and f2b is not None:
            if f is None:
                f = f2b
            else:
                f = And(f, f2b)
                
        return f    

    def _check(self):
        f = None
        for w in self.model.alternatives:
            if w != self.model:
                if f == None:
                    f = Not(self._dominates_formula(w, self.model))
                else:
                    f = And(f, Not(self._dominates_formula(w, self.model)))
        self.formulae = [f.nnf()]
        self.result = [self.model.models(f)]
                

    def permissible(self):
        self._check()
        return self.result == [True]


class DiscoursePrinciple(Principle):

    def __init__(self, model):
        super(DiscoursePrinciple, self).__init__(model)
        self.label = "DiscoursePrinciple"
        
        self.dialog = None
        if isinstance(model, str):
            self.dialog = ArgModel(model).dialog
        elif isinstance(model, ArgGraph):
            self.dialog = model
        elif isinstance(model, ArgModel):
            self.dialog = model.dialog
        else:
            print("Model ERROR, model type was: " + repr(type(model)))

    def permissible(self):
        return self.dialog.satisfiesDiscoursePrinciple(ArgSolver.toConjunction(self.dialog.proposition))

class UniversalityPrinciple(Principle):

    def __init__(self, model):
        super(UniversalityPrinciple, self).__init__(model)
        self.label = "UniversalityPrinciple"
        
        self.dialog = None
        if isinstance(model, str):
            self.dialog = ArgModel(model).dialog
        elif isinstance(model, ArgGraph):
            self.dialog = model
        elif isinstance(model, ArgModel):
            self.dialog = model.dialog
        else:
            print("Model ERROR, model type was: " + repr(type(model)))

    def permissible(self):
        return self.dialog.satisfiesUniversalityPrinciple(ArgSolver.toConjunction(self.dialog.proposition))

