class Formula(object):
    """
    Classes to programmatically build
    and represent formulae and terms of the language
    specified in Definition 1.
    """
    def __init__(self, f1, f2):
        self.f1 = f1
        self.f2 = f2

    def nnf(self):
        if(isinstance(self, Atom)):
            return self
        if(isinstance(self, Bool)):
            return self
        if(isinstance(self, Not)):
            if(isinstance(self.f1, Bool)):
                return Bool(not self.f1.f1)
            if(isinstance(self.f1, Not)):
                return self.f1.f1.nnf()
            if(isinstance(self.f1, And)):
                return Or(Not(self.f1.f1).nnf(), Not(self.f1.f2).nnf())
            if(isinstance(self.f1, Or)):
                return And(Not(self.f1.f1).nnf(), Not(self.f1.f2).nnf())
            if(isinstance(self.f1, Impl)):
                return Not(Or(Not(self.f1.f1), self.f1.f2)).nnf()
            if(isinstance(self.f1, BiImpl)):
                return Not(Or(And(self.f1.f1, self.f1.f2), And(Not(self.f1.f1), Not(self.f1.f2)))).nnf()
            return self
        if(isinstance(self, And)):
            return And(self.f1.nnf(), self.f2.nnf())
        if(isinstance(self, Or)):
            return Or(self.f1.nnf(), self.f2.nnf())
        if(isinstance(self, Impl)):
            return Or(Not(self.f1), self.f2).nnf()
        if(isinstance(self, BiImpl)):
            return Or(And(self.f1, self.f2), And(Not(self.f1), Not(self.f2))).nnf()
        return self

    def isCALLiteral(self):
        if isinstance(self, And) or isinstance(self, Or): # assumes NNF
            return False
        if isinstance(self, Not) and (isinstance(self.f1, And) or isinstance(self.f1, Or)):
            return False
        if isinstance(self, Bool):
            return False
        return True

    def getAllCALLiterals(self):
        if self.isCALLiteral():
            return [self]
        if isinstance(self, Bool):
            return []
        if isinstance(self, Not):
            return self.f1.getAllCALLiterals()
        return self.f1.getAllCALLiterals() + self.f2.getAllCALLiterals()
        
    @staticmethod
    def make_cnf(f):
        if isinstance(f, Atom):
            return f
        else:
            return f.cnf()
    
    def cnf(self):
        f = self.nnf()
        while(True):
            fcnf = f.cnf_it()
            if(f == fcnf):
                return fcnf
            f = fcnf
        return None
        
    def cnf_it(self):
        if isinstance(self, Atom):
            return self
        # (b v c) & a
        if(isinstance(self, Or) and isinstance(self.f1, And)):
            return And(Or(self.f1.f1, self.f2).cnf_it(), Or(self.f1.f2, self.f2).cnf_it())
        # a & (b v c)
        if(isinstance(self, Or) and isinstance(self.f2, And)):
            return And(Or(self.f1, self.f2.f1).cnf_it(), Or(self.f1, self.f2.f2).cnf_it())
        if(isinstance(self, And)):
            return And(self.f1.cnf_it(), self.f2.cnf_it())
        if(isinstance(self, Or)):
            return Or(self.f1.cnf_it(), self.f2.cnf_it())
        return self

    def writeDimacs(self):
        dlist, dmap = self.dimacs()
        d = "p cnf "+str(len(dmap))+" "+str(len(dlist))
        for c in dlist:
            d += "\n"
            if(type(c) is list):
                for cc in c:
                    d += str(cc) + " "
            else:
                d += str(c) + " " 
            d += "0"
        return d, dlist, dmap                 

    def dimacs(self):
        clauses = self.asClauseList()
        dimacs_map = dict()
        counter = 0
        dimacs_list = []
        for c in clauses:
            if type(c) is list:
                clause = []
                for cc in c:
                    if str(cc) in dimacs_map:
                        clause.append(dimacs_map[str(cc)])
                    elif str(cc.getNegation()) in dimacs_map:
                        clause.append(-1*dimacs_map[str(cc.getNegation())])
                    else:
                        counter = counter + 1
                        if isinstance(cc, Not):
                            dimacs_map[str(cc.f1)] = counter
                            clause.append(-1*dimacs_map[str(cc.f1)])
                        else:
                            dimacs_map[str(cc)] = counter
                            clause.append(dimacs_map[str(cc)])
                dimacs_list.append(clause)
            else:
                clause = []
                if str(c) in dimacs_map:
                    dimacs_list.append([dimacs_map[c]])
                elif str(c.getNegation()) in dimacs_map:
                    dimacs_list.append([-1*dimacs_map[str(c.getNegation())]])
                else:
                        counter = counter + 1
                        if isinstance(c, Not):
                            dimacs_map[str(c.f1)] = counter
                            clause.append(-1*dimacs_map[str(c.f1)])
                        else:
                            dimacs_map[str(c)] = counter
                            clause.append(dimacs_map[str(c)])
                dimacs_list.append(clause)
        return dimacs_list, dimacs_map

    def asClauseList(self):
        #f = self.cnf()
        f = self
        if(isinstance(f, Or)):
            return [f.getClause()]
        elif(isinstance(f, And)):
            return f.f1.asClauseList() + f.f2.asClauseList()
        else:
            return [f.getClause()]
            
    def getClause(self):
        if(isinstance(self, Or)):
            return self.f1.getClause() + self.f2.getClause()
        else:
            return [self]


    def asConjList(self):
        #f = self.dnf()
        f = self
        if(isinstance(f, And)):
            #print("new clause")
            return [f.getConj()]
        elif(isinstance(f, Or)):
            return f.f1.asConjList() + f.f2.asConjList()
        else:
            #print("new clause")
            return [f.getConj()]
            
    def getConj(self):
        if(isinstance(self, And)):
            return self.f1.getConj() + self.f2.getConj()
        else:
            return [self]


    @staticmethod
    def makeConjunction(s):
        """
        >>> Formula.makeConjunction(["a"])
        'a'
        >>> Formula.makeConjunction(["a", "b", "c"])
        And("c", And("b", "a"))
        """
        if not isinstance(s, list):
            if isinstance(s, Atom):
                s = [s]
            if isinstance(s, Bool):
                s = [s]
            if isinstance(s, tuple):
                s = list(s)
        f = None
        for e in s:
            if f == None:
                f = e
            else:
                f = And(f, e)
        if f == None:
            return True
        return f

    @staticmethod
    def makeDisjunction(s):
        """
        >>> Formula.makeDisjunction(["a"])
        'a'
        >>> Formula.makeDisjunction(["a", "b", "c"])
        Or("c", Or("b", "a"))
        """
        if not isinstance(s, list):
            if isinstance(s, Atom):
                s = [s]
            if isinstance(s, Bool):
                s = [s]
            if isinstance(s, tuple):
                s = list(s)
        f = None
        for e in s:
            if f == None:
                f = e
            else:
                f = Or(f, e)
        return f

    def __eq__(self, other):
        return self.f1 == other.f1 and self.f2 == other.f2 if self.__class__ == other.__class__ else False

    def __hash__(self):
        return hash((self.f1, self.f2))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if isinstance(self.f1, str):
            f1 = "'"+self.f1+"'"
        else:
            f1 = str(self.f1)
        if isinstance(self.f2, str):
            f2 = "'"+self.f2+"'"
        else:
            f2 = str(self.f2)

        if isinstance(self, Atom):
            return "Atom("+str(f1)+")"
        if isinstance(self, Bool):
            return "Bool("+str(f1)+")"
        if isinstance(self, Good):
            return "Good("+str(f1)+")"
        if isinstance(self, Bad):
            return "Bad("+str(f1)+")"
        if isinstance(self, Neutral):
            return "Neutral("+str(f1)+")"
        if isinstance(self, Not):
            return "Not("+str(f1)+")"
        if isinstance(self, Or):
            return "Or("+str(f1)+", "+str(f2)+")"
        if isinstance(self, And):
            return "And("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Impl):
            return "Impl("+str(f1)+", "+str(f2)+")"
        if isinstance(self, BiImpl):
            return "BiImpl("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Affects):
            return "Affects("+str(f1)+", "+str(f2)+")"
        if isinstance(self, AffectsPos):
            return "AffectsPos("+str(f1)+", "+str(f2)+")"
        if isinstance(self, AffectsNeg):
            return "AffectsNeg("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Better):
            return "Better("+str(f1)+", "+str(f2)+")"
        if isinstance(self, I):
            return "I("+str(f1)+")"
        if isinstance(self, End):
            return "End("+str(f1)+")"
        if isinstance(self, Means):
            return "Means("+str(f1)+")"
        if isinstance(self, Means2):
            return "Means2("+str(f1)+")"
        if isinstance(self, Causes):
            return "Causes("+str(f1)+", "+str(f2)+")"
        if isinstance(self, PCauses):
            return "PCauses("+str(f1)+", "+str(f2)+")"
        if isinstance(self, SCauses):
            return "SCauses("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Explains):
            return "Explains("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Prevents):
            return "Prevents("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Because):
            return "Because("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Intervention):
            return "Intervention("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Exists):
            return "Exists("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Forall):
            return "Forall("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Gt):
            return "Gt("+str(f1)+", "+str(f2)+")"
        if isinstance(self, GEq):
            return "GEq("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Eq):
            return "Eq("+str(f1)+", "+str(f2)+")"
        if isinstance(self, Must):
            return "Must("+str(f1)+")"
        if isinstance(self, May):
            return "May("+str(f1)+")"
        if isinstance(self, K):
            return "K("+str(f1)+")"
        if isinstance(self, Consequence):
            return "Consequence("+str(f1)+")"
        if isinstance(self, Caused):
            return "Caused("+str(f1)+")"
        if isinstance(self, Instrumental):
            return "Instrumental("+str(f1)+")"
        if isinstance(self, Goal):
            return "Goal("+str(f1)+")"
        if isinstance(self, Choice):
            return "Choice("+str(f1)+")"
        if isinstance(self, Patient):
            return "Patient("+str(f1)+")"
        if isinstance(self, Finally):
            return "Finally("+str(f1)+")"
        if isinstance(self, Avoidable):
            return "Avoidable("+str(f1)+")"

    def getPosLiteralsEvent(self):
        """ 
        For Event Formula Only. 
        Make sure that event formulae are 
        conjunctions of literals!
        """
        r = []
        l = self.getAllLiteralsEvent()
        for e in l:
            if isinstance(e, Not):
                r.append(e.f1)
            else:
                r.append(e)
        return r

    def getAllLiteralsEvent(self):
        """ 
        For Event Formula Only. 
        Make sure that event formulae are 
        conjunctions of literals!
        """
        if isinstance(self, Atom):
            return [self]
        if isinstance(self, Not):
            return [self]
        if isinstance(self, And):
            f1 = []
            f2 = []
            if isinstance(self.f1, str):
                f1 = f1 + [self.f1]
            else:
                f1 = f1 + self.f1.getAllLiteralsEvent()
            if isinstance(self.f2, str):
                f2 = f2 + [self.f2]
            else:
                f2 = f2 + self.f2.getAllLiteralsEvent()
            return f1 + f2

    def stripParentsFromMechanism(self):
        """ Only for preprocessing the mechanisms. """
        if isinstance(self, Atom):
            return [self]
        if isinstance(self, OnePlaced):
            return self.f1.stripParentsFromMechanism()
        if isinstance(self, TwoPlaced):
            return self.f1.stripParentsFromMechanism() + self.f2.stripParentsFromMechanism()
        
        
        #else:
        #    return self.f1.stripParentsFromMechanism() + self.f2.stripParentsFromMechanism()

    def getNegation(self, c = None):
        if c == None:
            c = self
        if isinstance(c, Atom):
            return Not(c)
        if isinstance(c, Bool):
            return Bool(not c.f1)
        if isinstance(c, GEq):
            return Gt(c.f2, c.f1)
        if isinstance(c, Not):
            if isinstance(c.f1, Not):
                return self.getNegation(c.f1.f1)
            else:
                return c.f1
        return Not(c)
        
        
class OnePlaced(Formula):
    def __init__(self, f1):
        super(OnePlaced, self).__init__(f1, None)

class TwoPlaced(Formula):
    def __init__(self, f1, f2):
        super(TwoPlaced, self).__init__(f1, f2)

class Atom(str, OnePlaced):
    def __init__(self, s):
        super(Atom, self).__init__(s)
        
class Bool(str, OnePlaced):
    def __init__(self, s):
        super(Bool, self).__init__(s)
        
class Good(OnePlaced):
    def __init__(self, f1):
        super(Good, self).__init__(f1)
        
class Bad(OnePlaced):
    def __init__(self, f1):
        super(Bad, self).__init__(f1)
        
class Neutral(OnePlaced):
    def __init__(self, f1):
        super(Neutral, self).__init__(f1)
        
class Caused(OnePlaced):
    def __init__(self, f1):
        super(Caused, self).__init__(f1)
        
class Finally(OnePlaced):
    def __init__(self, f1):
        super(Finally, self).__init__(f1)

class Avoidable(OnePlaced):
    def __init__(self, f1):
        super(Avoidable, self).__init__(f1)


class Instrumental(OnePlaced):
    def __init__(self, f1):
        super(Instrumental, self).__init__(f1)
        
class Not(OnePlaced):
    def __init__(self, f1):
        super(Not, self).__init__(f1)


class And(TwoPlaced):
    def __init__(self, f1, f2):
        super(And, self).__init__(f1, f2)

class Same(TwoPlaced):
    def __init__(self, f1, f2):
        super(Same, self).__init__(f1, f2)


class Or(TwoPlaced):
    def __init__(self, f1, f2):
        super(Or, self).__init__(f1, f2)


class Impl(TwoPlaced):
    def __init__(self, f1, f2):
        super(Impl, self).__init__(f1, f2)
        
        
class BiImpl(TwoPlaced):
    def __init__(self, f1, f2):
        super(BiImpl, self).__init__(f1, f2)


class Affects(TwoPlaced):
    def __init__(self, f1, f2):
        super(Affects, self).__init__(f1, f2)
        
class Better(TwoPlaced):
    def __init__(self, f1, f2):
        super(Better, self).__init__(f1, f2)
        
class AffectsPos(TwoPlaced):
    def __init__(self, f1, f2):
        super(AffectsPos, self).__init__(f1, f2)
        
        
class AffectsNeg(TwoPlaced):
    def __init__(self, f1, f2):
        super(AffectsNeg, self).__init__(f1, f2)
        
        
class I(OnePlaced):
    def __init__(self, f1):
        super(I, self).__init__(f1)
        
        
class Goal(OnePlaced):
    def __init__(self, f1):
        super(Goal, self).__init__(f1)
        
        
class Choice(OnePlaced):
    def __init__(self, f1):
        super(Choice, self).__init__(f1)
        
class Patient(OnePlaced):
    def __init__(self, f1):
        super(Patient, self).__init__(f1)
        
        
class End(OnePlaced):
    def __init__(self, f1):
        super(End, self).__init__(f1)

        
class Means(OnePlaced):
    def __init__(self, f1):
        super(Means, self).__init__(f1)
        
class Means2(OnePlaced):
    def __init__(self, f1):
        super(Means2, self).__init__(f1)


class K(OnePlaced):
    def __init__(self, f1):
        super(K, self).__init__(f1)
        
        
class Consequence(OnePlaced):
    def __init__(self, f1):
        super(Consequence, self).__init__(f1)


class May(OnePlaced):
    def __init__(self, f1):
        super(May, self).__init__(f1)


class Must(OnePlaced):
    def __init__(self, f1):
        super(Must, self).__init__(f1)


class Causes(TwoPlaced):
    def __init__(self, f1, f2):
        super(Causes, self).__init__(f1, f2)


class PCauses(TwoPlaced):
    def __init__(self, f1, f2):
        super(PCauses, self).__init__(f1, f2)


class SCauses(TwoPlaced):
    def __init__(self, f1, f2):
        super(SCauses, self).__init__(f1, f2)


class Explains(TwoPlaced):
    def __init__(self, f1, f2):
        super(Explains, self).__init__(f1, f2)


class Prevents(TwoPlaced):
    def __init__(self, f1, f2):
        super(Prevents, self).__init__(f1, f2)


class Intervention(TwoPlaced):
    def __init__(self, f1, f2):
        super(Intervention, self).__init__(f1, f2)
        
        
class Exists(TwoPlaced):
    def __init__(self, f1, f2):
        super(Exists, self).__init__(f1, f2)
        
        
class Forall(TwoPlaced):
    def __init__(self, f1, f2):
        super(Forall, self).__init__(f1, f2)


class Eq(TwoPlaced):
    def __init__(self, f1, f2):
        super(Eq, self).__init__(f1, f2)


class Gt(TwoPlaced):
    def __init__(self, f1, f2):
        super(Gt, self).__init__(f1, f2)


class GEq(TwoPlaced):
    def __init__(self, f1, f2):
        super(GEq, self).__init__(f1, f2)


class Because(TwoPlaced):
    def __init__(self, f1, f2):
        super(Because, self).__init__(f1, f2)

class Term(object):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2

    def __eq__(self, other):
        return self.t1 == other.t1 and self.t2 == other.t2 if self.__class__ == other.__class__ else False

    def __hash__(self):
        return hash((self.t1, self.t2))

    def __repr__(self):
        if isinstance(self.t1, str):
            t1 = "'"+self.t1+"'"
        else:
            t1 = str(self.t1)
        if isinstance(self.t2, str):
            t2 = "'"+self.t2+"'"
        else:
            t2 = str(self.t2)

        if isinstance(self, U):
            return "U("+str(t1)+")"
        if isinstance(self, DR):
            return "DR("+str(t1)+", +"+str(t2)+")"
        if isinstance(self, DB):
            return "DB("+str(t1)+", +"+str(t2)+")"
        if isinstance(self, Minus):
            return "Minus("+str(t1)+")"
        if isinstance(self, Sub):
            return "Sub("+str(t1)+", +"+str(t2)+")"
        if isinstance(self, Add):
            return "Add("+str(t1)+", +"+str(t2)+")"

    def stripParentsFromMechanism(self):
        """ Only for preprocessing the mechanisms. """
        if isinstance(self, Atom):
            return [self]
        if isinstance(self, OnePlacedTerm):
            return self.t1.stripParentsFromMechanism()
        if isinstance(self, TwoPlacedTerm):
            return self.t1.stripParentsFromMechanism() + self.t2.stripParentsFromMechanism()

class OnePlacedTerm(Term):
    def __init__(self, t1):
        super(OnePlacedTerm, self).__init__(t1, None)

class TwoPlacedTerm(Term):
    def __init__(self, t1, t2):
        super(TwoPlacedTerm, self).__init__(t1, t2)
        
class U(OnePlacedTerm):
    def __init__(self, t1):
        super(U, self).__init__(t1)

        
class DR(TwoPlacedTerm):
    def __init__(self, t1, t2):
        super(DR, self).__init__(t1, t2)
        
        
class DB(TwoPlacedTerm):
    def __init__(self, t1, t2):
        super(DB, self).__init__(t1, t2)


class Minus(OnePlacedTerm):
    def __init__(self, t1):
        super(Minus, self).__init__(t1)


class Sub(TwoPlacedTerm):
    def __init__(self, t1, t2):
        super(Sub, self).__init__(t1, t2)


class Add(TwoPlacedTerm):
    def __init__(self, t1, t2):
        super(Add, self).__init__(t1, t2)
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
