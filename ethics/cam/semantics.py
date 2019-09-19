import json
import yaml
import io
import sys

from ethics.language import *
from ethics.tools import *
from ethics.solver import *

class Model(object):
    """ Models """
    def __init__(self):
        self.alternatives = []
        
    def models(self, formula):
        try:
            return self.checker.models(self, formula)
        except:
            raise "No Model Checker"

    def evaluate(self, principle):
        try:
            p = principle(self)
        except:
            p = principle
        perm = p.permissible()
        return perm

class CausalNetwork(Model):
    """
    Implements a causal network of boolean variables.
    """
    def __init__(self, exo, endo, seq, world):
        super().__init__()
        self.endoVars = endo
        self.exoVars = exo
        self.seq = seq
        
        self.interventions = {}
        self.layers = dict()
        self.causal_network = None
        self.causal_network_model = set()
            
        self.set_world(world)
    
    def do(self, dic_var):
        for v, k in dic_var.items():
            self.interventions[v] = k
        self.__compute()
        
    def release(self, *var):
        for v in var:
            del self.interventions[v]
        self.__compute()
    
    def set_world(self, dic_var):
        self.world = dic_var
        self.__compute()
        
    def compute_layers(self, layer = 0):
        """
        Computes the layers post-hoc, i.e.,
        assumes the model has already been computed.
        """
        if layer == 0:
            self.layers = dict()
            self.layers[layer] = set(self.exoVars) | set(self.interventions.keys())
            self.compute_layers(1)
        else:
            handled_vars = merge_lists(self.layers.values())
            handled_vars_formula = self.__make_representative_formula(handled_vars)
            unhandled_vars = set(self.endoVars) - set(handled_vars)
            if len(unhandled_vars) > 0:
                self.layers[layer] = set()
                for v in unhandled_vars:
                    v_formula = self.__make_representative_formula_of_equations([v])
                    if self.models(v) and entails(And(handled_vars_formula, v_formula), v) or \
                            self.models(Not(v)) and entails(And(handled_vars_formula, v_formula), Not(v)):
                        self.layers[layer].add(v)
                self.compute_layers(layer + 1)
        return self.layers
                
                
    def __make_representative_formula_of_equations(self, variables):
        return Formula.makeConjunction([BiImpl(v, self.seq[v]) for v in variables])
        
    def __make_representative_formula(self, variables):
        """
        params:
        - variables list of variables
        """
        return Formula.makeConjunction([v for v in variables if self.__is_true(v)] + [Not(v) for v in variables if not self.__is_true(v)])
        
    def __is_true(self, var):
        return var in self.causal_network_model
    
    def __get_model(self):
        return And(Formula.makeConjunction([f for f in self.causal_network_model if self.causal_network_model[f]]), \
                Formula.makeConjunction([Not(f) for f in self.causal_network_model if not self.causal_network_model[f]]))
    
    def __compute_model(self, *additional):
        s = []
        s.append(self.causal_network)
        for f in additional:
            s.append(f)
        return set(satisfiable(Formula.makeConjunction(s), model = True))
            
    def __represent_causal_model(self):
        formula = []
        # Exogenous Variables
        for p in self.exoVars:
            if p in self.interventions:
                if self.interventions[p] == True:
                    formula += [Atom(p)]
                else:
                    formula += [Not(Atom(p))]
            else:
                if self.world[p] == True:
                    formula += [Atom(p)]
                else:
                    formula += [Not(Atom(p))]
        # Endogenous Variables
        for p in self.endoVars:
            if p in self.interventions:
                if self.interventions[p] == True:
                    formula += [Atom(p)]
                else:
                    formula += [Not(Atom(p))]
            else:
                formula += [BiImpl(Atom(p), self.seq[p])]
        return Formula.makeConjunction(formula)
        
    def __compute(self):
        self.causal_network = self.__represent_causal_model()
        self.causal_network_model = self.__compute_model()
        
    def models(self, f):
        if isinstance(f, PCauses):
            if self.models(Causes(f.f1, f.f2)):
                return True
            allLit = [e for e in self.endoVars + self.exoVars if self.models(e)] + \
                        [Not(e) for e in self.endoVars + self.exoVars if not self.models(e)]
            l = [e for e in allLit if e not in f.f1.getAllLiteralsEvent()]
            for x in powerset(l):
                if len(x) > 0:
                    fadd = Formula.makeDisjunction(x)
                    if self.models(Causes(Or(f.f1, fadd), f.f2)):
                        return True
            return False
        if isinstance(f, Causes):
            if self.models(f.f1) and self.models(f.f2):
                but_for = self.models(Intervention(f.f1.getNegation().nnf(), f.f2.getNegation()))
                if but_for:
                    cl = list(powerset(f.f1.asClauseList()[0]))[1:-1]
                    if len(cl) > 0:
                        return self.models(Formula.makeConjunction([Not(Causes(Formula.makeDisjunction(c), f.f2)) for c in cl]))
                    return True
                else:
                    return False
            return False
        if isinstance(f, Intervention):
            do_dict = dict()
            cl = f.f1.asConjList()[0]
            for c in cl:
                if isinstance(c, Not):
                    do_dict[c.f1] = False
                else:
                    do_dict[c] = True
            self.do(do_dict)
            r = self.models(f.f2)
            self.release(*list(do_dict.keys()))
            return r
        if isinstance(f, Not):
            return not self.models(f.f1)
        if isinstance(f, Impl):
            return not self.models(f.f1) or self.models(f.f2)
        if isinstance(f, BiImpl):
            return self.models(Impl(f.f1, f.f2)) and self.models(Impl(f.f2, f.f1))
        if isinstance(f, And):
            return self.models(f.f1) and self.models(f.f2)
        if isinstance(f, Or):
            return self.models(f.f1) or self.models(f.f2)
        if isinstance(f, Atom):
            return f in self.causal_network_model
        if isinstance(f, Bool):
            return f.f1

class CausalModel(CausalNetwork):
    """
    Causal Agency Model
    """
    def __init__(self, file, world = None):
        self.file = file
        with io.open(file) as data_file:
            if self.file.split(".")[-1] == "json":
                self.model = json.load(data_file)
            else:
                self.model = yaml.load(data_file, Loader=yaml.FullLoader)
            # Actions are mandatory
            self.actions = [Atom(a) for a in self.model["actions"]]
            # Only for compatibility reasons
            self.action = self.actions[0]
            
            # Optional entries
            try:
                self.utilities = {str(k): v for k, v in self.model["utilities"].items()}
            except:
                self.utilities = dict()
            try:
                self.patients = [str(a) for a in self.model["patients"]] 
            except: 
                self.patients = []
            try:
                self.description = str(self.model["description"])
            except:
                self.description = "No Description"
            try:
                self.consequences = [Atom(c) for c in self.model["consequences"]]
            except:
                self.consequences = []
            try:
                self.background = [Atom(b) for b in self.model["background"]]
            except:
                self.background = []
            try:
                self.events = [Atom(b) for b in self.model["events"]]
            except:
                self.events = []
            try:
                mechanisms = {str(k): myEval(v) for k, v in self.model["mechanisms"].items()}
            except:
                mechanisms = dict()
            try:
                self.intentions = {str(k): list(map(myEval, v)) for k, v in self.model["intentions"].items()}
            except:
                self.intentions = dict()
            try:
                self.goals = {str(k): list(map(myEval, v)) for k, v in self.model["goals"].items()}
            except:
                self.goals = dict()
            try:
                self.affects = {str(k): v for k, v in self.model["affects"].items()}
            except: 
                self.affects = dict()
                
            if world == None:
                world = {v:0 for v in self.actions + self.background + self.events}
                
            super().__init__(self.actions + self.events + self.background, self.consequences, mechanisms, world)

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
        if isinstance(formula, Atom):
            if formula in self.utilities:
                return self.utilities[str(formula)]
            else:
                return 0
        if isinstance(formula, Not):
            if isinstance(formula.f1, Atom):
                if str(formula) in self.utilities:
                    return self.utilities[str(formula)]
                else:
                    return 0
            if isinstance(formula.f1, Not):
                return self.__sum_up(formula.f1.f1)
        if isinstance(formula, And):
            return self.__sum_up(formula.f1) + self.__sum_up(formula.f2)
            
    def __affects(self, affects, formula, posneg):
        if isinstance(formula, And):
            return self.__affects(affects, formula.f1, posneg) and self.__affects(affects, formula.f2, posneg)
        return formula in [i[0] for i in affects if i[1] == posneg]
        
    def get_actual_goals(self):
        goals = []
        for a in self.get_performed_actions():
            goals += self.goals[a]
        return goals
        
    def get_actual_intentions(self):
        intentions = []
        for a in self.get_performed_actions():
            intentions += self.intentions[a]
        return intentions
        
    def get_actual_consequences(self):
        return [e for e in self.consequences if self.models(e)] + [Not(e) for e in self.consequences if not self.models(e)]
        
    def get_all_consequences(self):
        return [e for e in self.consequences] + [Not(e) for e in self.consequences]
    
    def get_direct_consequences(self):
        cons_all = self.get_all_consequences()
        cons_direct = []
        for a in list(powerset(self.get_performed_actions()))[1:]:
            cons_direct += [c for c in cons_all if self.models(Causes(Formula.makeDisjunction(a), c))]
        return cons_direct
        
    def is_direct_consequence(self, c):
        for a in list(powerset(self.get_performed_actions()))[1:]:
            if self.models(Causes(Formula.makeDisjunction(a), c)):
                return True
        return False
        
    def get_all_actions(self):
        return self.actions  
              
    def get_performed_actions(self):
        return [e for e in self.actions if self.models(e)]
        
    def explain(self, principle):
        try:
            p = principle(self)
        except:
            p = principle
        return p.explain()
        
    def models(self, f):
        if isinstance(f, Caused):
            return self.is_direct_consequence(f.f1)
        if isinstance(f, Instrumental):
            for g in self.get_actual_goals():
                if self.models(Causes(f.f1, g)):
                    return True
            return False
        if isinstance(f, Eq):
            return self.__evaluate_term(f.f1) == self.__evaluate_term(f.f2)
        if isinstance(f, Gt):
            return self.__evaluate_term(f.f1) > self.__evaluate_term(f.f2)
        if isinstance(f, GEq):
            return self.__evaluate_term(f.f1) >= self.__evaluate_term(f.f2)
        if isinstance(f, Good):
            return self.__evaluate_term(U(f.f1)) > 0
        if isinstance(f, Bad):
            return self.__evaluate_term(U(f.f1)) < 0
        if isinstance(f, Neutral):
            return self.__evaluate_term(U(f.f1)) == 0
        if isinstance(f, I):
            return f.f1 in self.get_actual_intentions()
        if isinstance(f, Goal):
            return f.f1 in self.get_actual_goals()
        if isinstance(f, Affects):
            if str(f.f1) not in self.affects:
                return False
            return self.__affects(self.affects[str(f.f1)], f.f2, "+") or self.__affects(self.affects[str(f.f1)], f.f2, "-")
        if isinstance(f, AffectsPos):
            if str(f.f1) not in self.affects:
                return False
            return self.__affects(self.affects[str(f.f1)], f.f2, "+")
        if isinstance(f, AffectsNeg):
            if str(f.f1) not in self.affects:
                return False
            return self.__affects(self.affects[str(f.f1)], f.f2, "-")  
        if isinstance(f, End):
            foundPos = False
            for i in self.get_actual_goals():
                if self.models(AffectsNeg(i, f.f1)):
                    return False
                if not foundPos and self.models(AffectsPos(i, f.f1)):
                    foundPos = True
            return foundPos
        if isinstance(f, Means):
            for i in self.get_all_actions()+self.get_direct_consequences():
                for g in self.get_actual_goals():
                    if self.models(And(Causes(i, g), Affects(i, f.f1))):
                        return True
            return False
        if isinstance(f, Means2):
            for i in self.get_all_actions()+self.get_direct_consequences():
                if self.models(Affects(i, f.f1)):
                    return True
            return False
        #Everything else
        return super().models(f)
