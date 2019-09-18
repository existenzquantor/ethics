from ethics.language import *
from ethics.explanations import *

"""
Ethical Principles
"""
class Principle:
    def __init__(self, model):
        self.formulae = []
        self.model = model
        self.label = self.__class__.__name__
    
    def buildConjunction(self):
        return Formula.makeConjunction(self.formulae)
        
    def permissible(self):
        pass

    def explain(self, *args):
        reasons = generateReasons(self.model, self, args)
        suff = [r["reason"] for r in reasons if r["type"] == "sufficient"]
        nec = [r["reason"] for r in reasons if r["type"] == "necessary"]
        inus = identifyINUSReasons(reasons)
        if len(reasons) > 0:
            return {"permissible": reasons[0]["perm"], "principle": self.label, "sufficient": suff, "necessary": nec, "inus": inus}
        return []    

class Deontology(Principle):
    def __init__(self, model, *args):
        super().__init__(model)
    
    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Not(Bad(Atom(a.name))) for a in self.model.plan.endoActions])]         

    def permissible(self):
        """The situation is permissible iff no action in the plan is intrinsically bad.
        
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0])
        

class GoalDeontology(Principle):
    def __init__(self, model, *args):
        super().__init__(model)
    
    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Goal(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Goal(Not(Atom(c))))) for c in self.model.getAllConsequences()])]

    def permissible(self):
        """The situation is permissible iff no action in the plan is intrinsically bad.
        
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0])


class AvoidAnyHarm(Principle):
    def __init__(self, model, *args):
        super().__init__(model)
    
    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Finally(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Finally(Not(Atom(c))))) for c in self.model.getAllConsequences()])]
    
    def permissible(self):
        """The situation is permissible iff there are no harmful consequences in the final state.
                
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0])


class AvoidAvoidableHarm(Principle):
    def __init__(self, model, *args):
        super().__init__(model)

    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Impl(And(Bad(Atom(c)), Finally(Atom(c))), Not(Avoidable(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(And(Bad(Not(Atom(c))), Finally(Not(Atom(c)))), Not(Avoidable(Not(Atom(c))))) for c in self.model.getAllConsequences()])]

    def permissible(self):
        """The situation is permissible iff all harmful consequences in the final state could not have been avoided by any plan.

        Keyword arguments:
        situation -- The situation
        """
        """
        hc = self.model.getHarmfulConsequences()
        hf = self.model.getGenerallyAvoidableHarmfulFacts()
        for h in hc:
            if h in hf:
                return False
        return True
        """
        self.__build_formula()
        return self.model.models(self.formulae[0])
            

class DoNoHarm(Principle):
    def __init__(self, model, *args):
        """Empty constructor"""
        super().__init__(model)
        
    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Caused(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Caused(Not(Atom(c))))) for c in self.model.getAllConsequences()])]
        
    def permissible(self):
        """The situation is permissible iff if there is harm in the final state then it's not caused by the agent's actions.
                
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0]) 


class DoNoInstrumentalHarm(Principle):
    def __init__(self, model, *args):
        super().__init__(model)

    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Instrumental(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Instrumental(Not(Atom(c))))) for c in self.model.getAllConsequences()])]
                            
    def permissible(self):
        """The situation is permissible iff if there is harm in the final state then it's not contributing to the agent's goal, i.e., is just a side effect.
                
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0]) 


class KantianHumanity(Principle):
    def __init__(self, model, *args):
        """Constructor for the Humanity principle.
        
        Arguments:
        reading -- indicate whether reading 1 or reading 2 shall be used (Default: 1).
        """
        super().__init__(model)
        if args[0]:
            self.reading = args[0][0]
        else:
            self.reading = 1
    
    def __build_formula(self):
        if self.reading == 1:
            self.formulae = [Formula.makeConjunction([Impl(Means(Atom(p)), End(Atom(p))) for p in self.model.affects.keys()])]
        elif self.reading == 2:
            self.formulae = [Formula.makeConjunction([Impl(Means2(Atom(p)), End(Atom(p))) for p in self.model.affects.keys()])]
    
    def permissible(self):
        """The situation is permissible iff all moral patients used as a means are also used as an end.
                
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(self.formulae[0]) 
        


class Utilitarianism(Principle):
    def __init__(self, model, *args):
        super().__init__(model)

    def __build_formula(self):
        
        u = U(Formula.makeConjunction(self.model.get_all_consequences_lits()))
        v = []
        for w in self.model.alethicAlternatives:
            v.append(U(Formula.makeConjunction(w.get_all_consequences_lits())))
        f = None
        for w in v:
            f = GEq(u, w) if f is None else And(f, GEq(u, w))
        if f is None: # no alternatives
            f = True
        self.formulae = [f]
        self.result = [self.model.models(f)]
        return self.result        

    def permissible(self):
        """The situation is permissible iff there is no alternative which yields more overall utility.
                
        Keyword arguments:
        situation -- The situation
        """
        """
        u = self.model.getFinalUtility()
        for a in self.model.alethicAlternatives:
            if a.getFinalUtility() > u:
                return False
        return True
        """
        if len(self.model.alethicAlternatives) == 0:
            self.model.alethicAlternatives.append(self.model)
        self.__build_formula()
        return self.model.models(self.formulae[0]) 

class DoubleEffectPrinciple(Principle):
    def __init__(self, model, *args):
        super().__init__(model)

    def __build_formula(self):
        self.formulae = [Formula.makeConjunction([Not(Bad(Atom(a.name))) for a in self.model.plan.endoActions])]         
        self.formulae += [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Goal(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Goal(Not(Atom(c))))) for c in self.model.getAllConsequences()])]
        self.formulae += [Formula.makeDisjunction([And(Good(Atom(c)), Goal(Atom(c))) for c in self.model.getAllConsequences()] + \
                            [And(Good(Not(Atom(c))), Goal(Not(Atom(c)))) for c in self.model.getAllConsequences()])]
        self.formulae += [Formula.makeConjunction([Impl(Bad(Atom(c)), Not(Instrumental(Atom(c)))) for c in self.model.getAllConsequences()] + \
                            [Impl(Bad(Not(Atom(c))), Not(Instrumental(Not(Atom(c))))) for c in self.model.getAllConsequences()])]
        self.formulae += [Gt(U(Formula.makeConjunction(self.model.get_all_consequences_lits())),0)]

    def permissible(self):
        """The situation is permissible iff
           1) it is permissible according the deontology
           2) No goal fact is bad and there is at least one good goal fact
           3) it is permissible according to instrumental harm
           4) Overall utility of the final state is positive
                
        Keyword arguments:
        situation -- The situation
        """
        self.__build_formula()
        return self.model.models(Formula.makeConjunction(self.formulae)) 
