from enum import Enum, auto
from ethics.solver import *
from ethics.language import *
from ethics.tools import *
from os.path import expanduser

class AddArgumentState(Enum):
    NAMEAGENT = auto()
    ADDSUPPORT = auto()
    ADDCLAIM = auto()

class ServiceType(Enum):
    SATISFIABILITY = auto()
    ADDARGUMENT = auto()
    DEFINEACTION = auto()
    VALIDITY = auto()
    PROPOSITION = auto()

class Labelvalue(Enum):
    IN = auto()
    OUT = auto()
    UNDEC = auto()
    UNKNOWN = auto()

class Attack:
    def __init__(self, attacker, attacked):
        self.attacker = attacker
        self.attacked = attacked
    
    def __repr__(self):
        return repr(self.attacker) + " -> " +  repr(self.attacked) + "[label=\"" + repr(type(self)).split('\'')[1].split('.')[1] + "\"];\n"


class Undercut(Attack):
    pass
class Rebut(Attack):
    pass

class ArgModel:   
    def __init__(self, adressName, allowSelfContradition = True):
        self.textfile = open(expanduser(adressName), "r")
        self.tempSupport = list()
        self.agentName = ""
        self.mode = ServiceType.SATISFIABILITY
        self.modeState = AddArgumentState.NAMEAGENT
        self.dialog = ArgGraph()
        self.causalModel = None
        self.context = None
        self.principle = None
        self.explain = False

        for line in self.textfile.read().splitlines():
            text = line
            if(text == "EXIT"):
                break
            elif(text == "SAT"):
                self.mode = ServiceType.SATISFIABILITY
            elif(text == "VALID"):
                self.mode = ServiceType.VALIDITY
            elif(text == "NEW DIALOG"):
                self.dialog.empty()
            elif(text == "ADD ARGUMENT"):
                self.mode = ServiceType.ADDARGUMENT
            elif(text == "PROPOSITION"):
                self.mode = ServiceType.PROPOSITION
            elif(text == "DEFINE ACTION"):
                self.mode = ServiceType.DEFINEACTION
            elif(text == "MODE"):
                print(self.mode)
            elif(text == "SHOW DIALOG"):
                print(self.dialog)
            elif(text == "SHOW DOTGRAPH"):
                print(self.dialog.getDotGraph("Argumentation"))
            elif(text == "SEPERATE ACTION DOTGRAPHS"):
                for graph, name in self.dialog.actionArgGraphs():
                    print(graph.getDotGraph(name))
            elif(text == "PREFERRED"):
                print(Labelling.visualizeLabellings(self.dialog.getPreferred()))
            elif(text == "ALWAYS IN"):
                print("Always-IN-labelled arguments:")
                print(self.dialog.getAlwaysIn(self.dialog.getPreferred()))
            elif(text == "UNIVERSALS"):
                print(self.dialog.getAllUniversals("patiens"))
            elif(self.mode == ServiceType.ADDARGUMENT):
                if(self.modeState == AddArgumentState.NAMEAGENT):
                    self.agentName = text.strip()
                    self.modeState = AddArgumentState.ADDSUPPORT
                elif(self.modeState == AddArgumentState.ADDSUPPORT):
                    self.tempSupport.extend(ArgModel.toFormulaSet(text.replace(" ","").split(";")))
                    self.modeState = AddArgumentState.ADDCLAIM
                elif(self.modeState == AddArgumentState.ADDCLAIM):
                    textReplaced = text.replace(" ","")
                    textSplit = textReplaced.split(";")
                    if allowSelfContradition:
                        self.dialog.addArgument(Argument(Agent(self.agentName), self.tempSupport, ArgModel.toFormulaSet(textSplit)))
                    else:
                        if(satisfiable(And(toConjunction(self.tempSupport), toConjunction(ArgModel.toFormulaSet(textSplit))))):
                            self.dialog.addArgument(Argument(Agent(self.agentName), self.tempSupport, ArgModel.toFormulaSet(textSplit)))
                        else:
                            print("The following argument was rejected because of self-contradiction: " + repr(argument))
                    self.tempSupport = list()
                    self.modeState = AddArgumentState.NAMEAGENT
            elif(self.modeState == AddArgumentState.ADDCLAIM):
                    textReplaced = text.replace(" ","")
                    textSplit = textReplaced.split(";")
                    self.dialog.addArgument(Argument(Agent(self.agentName), self.tempSupport, ArgModel.toFormulaSet(textSplit)))
            elif(self.mode == ServiceType.PROPOSITION):
                self.dialog.proposition.append(ArgModel.parseFormula(text))
            elif(self.mode == ServiceType.DEFINEACTION):
                self.dialog.addToActionPeolple(text)
            else:
                formulas = text.replace(" ","").split(";")

    def toFormulaSet(stringList):
        formulaSet = list()
        for item in stringList:
            item.strip()
            item.replace(" ","")
            formulaSet.append(ArgModel.parseFormula(item))
        return formulaSet

    def polish(string):
        s2 = string.strip()
        s2 = s2.replace(" ","").replace("("," ").replace(")"," ").replace(","," ")
        while("  " in s2):
            s2 = s2.replace("  "," ")
        s2 = s2.strip()
        tokens = s2.split(" ")
        tokens.reverse()
        return tokens

    def parseFormula(string):
        pol = ArgModel.polish(string)
        myStack = list()
        for p in pol:
            if p in ["Top", "Bottom"]:
                myStack.append(myEval(p + "()"))
            elif p in ["Good", "Bad", "Neutral", "Not", "Atom"]:
                myStack.append(myEval(p + "(" + repr(myStack.pop()) + ")"))
            elif p in ["And", "Because", "Same", "Or", "Impl", "BiImpl", "Causes", "Intervene"]:
                myStack.append(myEval(p + "(" + repr(myStack.pop()) + ", " + repr(myStack.pop()) + ")"))
            elif p in ["Forall", "Exists"]:
                first = myStack.pop()
                second = myStack.pop()
                myStack.append(myEval(p + "(" + repr(first) + ", " + repr(second) + ")"))
                #omitted: first.variable = True
            elif(p[0:4] == 'Act[' and len(p.split('/')) == 2):
                    myStack.append(Atom(p[0: -1]+"/]"))
            else:
                myStack.append(Atom(p))
        f = myStack[0]
        return f.nnf()

    def permissible(self, principle):
        return principle(self).permissible()

class ArgumentType(Enum):
    STATEMENT = auto()
    PROPOSAL = auto()
    
class Agent:
    def __init__(self, name):
        self.name = name

class Argument:
    def __init__(self, agent, support, claim):
        self.agent = agent
        self.support = support
        self.claim = claim

    def undercuts(self, argument):
        support, claim, argumentSupport = self.support, self.claim, argument.support
        newList = support.copy()
        newList.extend(claim)
        newList.extend(argumentSupport)
        newFormula = ArgSolver.toConjunction(newList)
        return not satisfiable(newFormula)
    
    def rebuts(self, argument):
        support, claim, argumentClaim = self.support, self.claim, argument.claim
        newList = support.copy()
        newList.extend(claim)
        newList.extend(argumentClaim)
        newFormula = ArgSolver.toConjunction(newList)
        return not satisfiable(newFormula)

    def __repr__(self):
        return "\"" + self.agent.name + " says: " + repr(ArgSolver.toConjunction(self.support)) + "; so " + repr(ArgSolver.toConjunction(self.claim)) + "\""

    def __str__(self):
        return "\"" + self.agent.name + " says: " + repr(ArgSolver.toConjunction(self.support)) + "; so " + repr(ArgSolver.toConjunction(self.claim)) + "\""

    def isConsistent(self, setOfArgs):
        return satisfiable(setOfArgs.copy().add(self))

    def __eq__(self, other):
        return self.agent == other.agent and self.support == other.support and self.claim == other.claim if isinstance(other, Argument) else False

class Labelling:
    def __init__(self, arg, lab):
        self.arg = arg
        self.lab = lab
    
    def __str__(self):
        return str(self.arg) + " labelled as " + str(self.lab).split('.')[1]

    def __repr__(self):
        return str(self)

    def consistentLabeller(setOfLabellings, argsRemaining, attacks):
        argIter = iter(argsRemaining)
        if(len(argsRemaining) < 1):
            return setOfLabellings.copy()
        else:
            currentArgument = next(argIter)
            doneSet = list()
            newSet = list()
            for currentSet in setOfLabellings:
                attackersOnCurrentArg = [anyAttack.attacker for anyAttack in attacks if anyAttack.attacked == currentArgument]
                threatToCurrentArg = currentArgument in attackersOnCurrentArg
                for labellingInCurrentSet in currentSet:
                    if threatToCurrentArg:
                        break
                    else:
                        if(labellingInCurrentSet.lab == Labelvalue.IN):
                            for anyAttacker in attackersOnCurrentArg:
                                if anyAttacker == labellingInCurrentSet.arg:
                                    threatToCurrentArg = True
                                    break
                if(threatToCurrentArg):    
                    currentSet.append(Labelling(currentArgument, Labelvalue.OUT))
                    newSet.append(currentSet) 
                else:
                    attackedByCurrent = list()
                    nonAttacking = True
                    for anyAttack in attacks:
                        if anyAttack.attacker == currentArgument:
                            attackedByCurrent.append(anyAttack.attacked)
                    for labellingInCurrentSet in currentSet:
                        if nonAttacking:
                            break
                        else:
                            if labellingInCurrentSet.lab == Labelvalue.IN:
                                for argumentAttackedByCurrent in attackedByCurrent:
                                    if argumentAttackedByCurrent == labellingInCurrentSet.arg:
                                        nonAttacking = False
                                        break
                    if nonAttacking:
                        newSet.append(currentSet.copy())
                        newSet[-1].extend([Labelling(currentArgument,Labelvalue.IN)])
                    newSet.append(currentSet.copy())
                    newSet[-1].extend([Labelling(currentArgument,Labelvalue.OUT)])
                doneSet.append(currentSet)
            lastList = []
            for anyList in setOfLabellings:
                if anyList not in doneSet:
                    lastList.append(anyList.copy())
            for anyList in newSet:
                lastList.append(anyList.copy())
            return Labelling.consistentLabeller(lastList.copy(), [a for a in argsRemaining if a != currentArgument], attacks)

    def visualizeLabellings(inputLabellings):
        sb = "Possible Labellings: (total " +  str(len(inputLabellings)) + ")"
        for metaIter in inputLabellings:
            currentSet = metaIter
            insb = "\n  Labelled IN: "        
            outsb = "\n  Labelled OUT: "
            undecsb = "\n  Labelled UNDEC: "
            for current in currentSet:
                    if(current.lab == Labelvalue.IN):
                        insb += "\n   " + repr(current.arg)
                    elif(current.lab == Labelvalue.OUT):
                        outsb += "\n    " + repr(current.arg)
                    elif(current.lab == Labelvalue.UNDEC):
                        undecsb += "\n    " + repr(current.arg)
            sb += "\n New preferred labelling: " + insb + outsb + undecsb
        return sb

class ArgGraph:
    def __init__(self):
        self.arguments = list()
        self.attacks = list()
        self.actionToAgentes = {}
        self.actionToPatientes = {} 
        self.proposition = []
    
    def empty(self):
        self.arguments = list()
        self.attacks = list()
    
    def addArgument(self, argument):
        self.arguments.append(argument)
        self.addAttacks(argument)

    def addAttacks(self, argument):
        for a in self.arguments:
            if a.undercuts(argument):
                if all(repr(att) != repr(Undercut(a, argument)) for att in self.attacks) or len(self.attacks) == 0:
                    self.attacks.append(Undercut(a, argument))
            if argument.undercuts(a):
                if all(repr(att) != repr(Undercut(argument, a)) for att in self.attacks) or len(self.attacks) == 0:
                    self.attacks.append(Undercut(argument, a))
            if argument.rebuts(a):
                if all(repr(att) != repr(Rebut(argument, a)) for att in self.attacks) or len(self.attacks) == 0:
                    self.attacks.append(Rebut(argument, a))
                    self.attacks.append(Rebut(a, argument))
                
    def getAttackedNodes(self, node):
        att = []
        for n in self.nodes: 
            b = self.satisfiable
            if b == "UNSATISFIABLE":
                att += [n]
        return att 

    def __repr__(self):
        return self.getDotGraph('Argumentation')

    def __str__(self):
        return repr(self)
        
    def addToActionPeolple(self, inputLine):
        nameToPeople = inputLine.split(":")
        if(len(nameToPeople) != 2):
            actionName = "Error"
        else:
            actionName = nameToPeople[0].replace(" ","")
        agentesToPatientes = nameToPeople[1].split("@")
        while(len(agentesToPatientes) < 2):
            agentesToPatientes.append("")
        agentes = []
        for word in agentesToPatientes[0].split(" "):
            while " " in word:
                word = word.replace(" ","")
            if len(word) > 0:
                agentes.append(word)
        if len(agentes) == 0:
            agentes.append("")
        patientes = []
        for word in agentesToPatientes[1].split(" "):
            while " " in word:
                word = word.replace(" ","")
            if len(word) > 0:
                patientes.append(word)
        ArgGraph.insertToDict(self.actionToAgentes, actionName, agentes)
        ArgGraph.insertToDict(self.actionToPatientes, actionName, patientes)

    def insertToDict(dict, key, entry):
        if key in dict.keys():
            for item in entry:
                if item not in dict[key]:
                    dict[key].append(entry)
        else:
            dict[key] = entry

    def getDotGraph(self, name):
        sb = ""
        for arg in self.arguments:
            sb += repr(arg) + "\n"
        for att in self.attacks:
            sb += repr(att)
        return "digraph " + name +  " {" + "\n" + sb + "}"
    
    def getMaximal(inputLabellings):
        currentMaximalLabellings = inputLabellings.copy()
        for labelSet1 in currentMaximalLabellings:
            inLabels1 = [eachLabel.arg for eachLabel in labelSet1 if eachLabel.lab == Labelvalue.IN]
            for labelSet2 in inputLabellings:
                if labelSet1 != labelSet2:
                    inLabels2 = [eachLabel.arg for eachLabel in labelSet2 if eachLabel.lab == Labelvalue.IN]
                    allIncluded = True
                    for in2 in inLabels2:
                        if not in2 in inLabels1:
                            allIncluded = False
                            break
                    if allIncluded and labelSet2 in currentMaximalLabellings:
                        currentMaximalLabellings.remove(labelSet2)
        return currentMaximalLabellings

    def getDefended(self, inputLabellings):
        undefendedLabellings = []
        for labelSet in inputLabellings:
            inLabels = [a for a in labelSet if a.lab == Labelvalue.IN]
            outLabels = [a for a in labelSet if a.lab == Labelvalue.OUT]
            for arg in self.arguments:
                if arg in outLabels:
                    for att1 in self.attacks:
                        if att1.attacked in inLabels:
                            noDefense = True
                            for att2 in self.attacks:
                                if att2.attacked == att1.attacker and att2.attacker in inLabels:
                                    noDefense = False
                                    break
                            if noDefense:
                                undefendedLabellings.append(labelSet)
        return [a for a in inputLabellings if a not in undefendedLabellings]

    def getPreferred(self):
        initLabelling = [Labelling(a, Labelvalue.UNKNOWN) for a in self.arguments]
        initList = [initLabelling]
        admissibleLabellings = Labelling.consistentLabeller(initList, self.arguments, self.attacks)
        return ArgGraph.getMaximal(self.getDefended(admissibleLabellings))

    def getAlwaysIn(self, inputLabellings):
        inSet = []
        if len(inputLabellings) == 0:
            return inSet
        inSet.extend([anyLabelling.arg for anyLabelling in inputLabellings[0] if anyLabelling.lab == Labelvalue.IN])
        for inputLabelling in inputLabellings:
            for anyLabelling in inputLabelling:
                if anyLabelling.arg in inSet:
                    if anyLabelling.lab == Labelvalue.OUT or anyLabelling.lab == Labelvalue.UNDEC:
                        inSet.remove(anyLabelling.arg)
        return inSet

    def satisfiesDiscoursePrinciple(self, f, patientesArgs = True):
        if patientesArgs:
            formulas = []
            for arg in self.getAlwaysIn(self.getPreferred()):
                for claimF in arg.claim:
                    actionToPatientesFromClaimF = self.produceActionPeopleDict(f)[1]
                    for action in actionToPatientesFromClaimF.keys():
                        if len(self.actionToPatientes[action]) < 1:
                            continue #if no patiens exists: per definition true
                        if arg.agent.name in self.actionToPatientes[action]:
                            formulas.append(claimF)
                            break
            formulas.append(f.getNegation())
            return not satisfiable(formulas)
        else:
            formulas = []
            for arg in self.getAlwaysIn(self.getPreferred()):
                for claimF in arg.claim:
                    formulas.append(claimF)
            formulas.append(f.getNegation())
            return not satisfiable(formulas)

    def satisfiesUniversalityPrinciple(self, f, useAgentes = False, usePatientes = True):
        actionMap = self.produceActionPeopleDict(f)
        for action in {a for a in actionMap[1].keys()}.union({a for a in actionMap[0].keys()}):
            actionListBuilder = []
            if(useAgentes):
                if(len(self.actionToAgentes[action])>0):
                    agensScope = self.actionToAgentes[action]
                else:
                    agensScope = [""]
            else:
                agensScope = actionMap[0][action]
            if(usePatientes):
                if(len(self.actionToPatientes[action])>0):
                    patiensScope = self.actionToPatientes[action]
                else:
                    patiensScope = [""]
            else:
                patiensScope = actionMap[1][action]
            for agens in agensScope:
                for patiens in patiensScope:
                    actionListBuilder.append(Atom("Act[" + agens + "/" + action + "/" + patiens + "]"))
            if (self.satisfiesDiscoursePrinciple(Good(ArgSolver.toConjunction(actionListBuilder)), True)):
                return True
        return False

    def getAllUniversals(self, toggle):
        ag = "ag" in toggle
        pat = "pa" in toggle
        sb = ""
        for action in ({a for a in self.actionToAgentes.keys()}.union({a for a in self.actionToPatientes.keys()})):
            print("Status: Checking universalizability of action " + action + " " + (11 - len(action)) * ".", end ="")
            if(len(self.actionToAgentes[action])>0):
                sampleAgens = self.actionToAgentes[action][0]
            else:
                sampleAgens = ""
            if(len(self.actionToPatientes[action])>0):
                samplePatiens = self.actionToPatientes[action][0]
            else:
                samplePatiens = ""
            checkFrom = "Good(Act[" + sampleAgens + "/" + action + "/" + samplePatiens + "])"
            if self.satisfiesUniversalityPrinciple(ArgModel.parseFormula(checkFrom), ag, pat):
                print(" - YES")
                sb += action + " "
            else:
                print(" - NO")
        return "The following actions are " + "agens-"*int(ag) + "patiens-"*int(pat) + "universalizable: " + sb

    def produceActionPeopleDict(self, f):
        if isinstance(f, Argument):
            return self.produceActionPeopleDict(And(f.claim, f.support))
        if isinstance(f, list):
            return self.produceActionPeopleDict(ArgSolver.toConjunction(f))
        locActionToAgentes = {}
        locActionToPatientes = {}
        if isinstance(f, str):
            if f[0:4] == 'Act[':
                words = f[4:-1].replace(" ","").split('/')
                if not words[1] in self.actionToAgentes.keys() or not words[1] in self.actionToPatientes.keys():
                    print("ERROR: Action words[1] not found in action definition.")
                else:
                    if len(words[0]) == 0:
                        agentes = self.actionToAgentes[words[1]]
                    else:
                        agentes = [words[0]]
                    if len(words[2]) == 0:
                        patientes = self.actionToPatientes[words[1]]
                    else:
                        patientes = [words[2]]
                    ArgGraph.insertToDict(locActionToAgentes, words[1], agentes)
                    ArgGraph.insertToDict(locActionToPatientes, words[1], patientes)
            return locActionToAgentes, locActionToPatientes
        elif issubclass(type(f), OnePlaced):
            return self.produceActionPeopleDict(f.f1)
        elif issubclass(type(f), TwoPlaced):
            result1 = self.produceActionPeopleDict(f.f1)
            result2 = self.produceActionPeopleDict(f.f2)
            for action in {a for a in result2[0].keys()}.union({a for a in result2[1].keys()}):
                ArgGraph.insertToDict(result1[0], action, result2[0][action])
                ArgGraph.insertToDict(result1[1], action, result2[1][action])
            return result1
        else:
            print("Type Error in produceActionPeolpeDict function")

    def actionArgGraphs(self):
        arggraphlist = list()
        for action in self.actionToAgentes.keys():
            newGraph = ArgGraph()
            arggraphlist.append((newGraph, action))
            newGraph.actionToAgentes[action] = self.actionToAgentes[action].copy()
            newGraph.actionToPatientes[action] = self.actionToPatientes[action].copy()
            for argument in self.arguments:
                locActionToAgentes, locActionToPatientes = self.produceActionPeopleDict(argument) 
                if action in locActionToPatientes.keys() and len(self.actionToPatientes[action]) > 0 and argument.agent.name in self.actionToPatientes[action]: #or len(self.actionToPatientes[action]) == 0:
                    newGraph.arguments.append(argument)
            completed = False
            while(not completed):
                completed = True
                for att in self.attacks:
                    if (att.attacker in newGraph.arguments or att.attacked in newGraph.arguments) and att not in newGraph.attacks:
                        newGraph.attacks.append(att)
                        completed = False
                    if att.attacked in newGraph.arguments and att.attacker not in newGraph.arguments:
                        newGraph.arguments.append(att.attacker) 
                        completed = False
                    if att.attacker in newGraph.arguments and att.attacked not in newGraph.arguments:
                        newGraph.arguments.append(att.attacked) 
                        completed = False
        return arggraphlist
    
    def tokenGraph(self, token): #currently only patientes 
        tokenActionToAgentes, tokenActionToPatientes = self.produceActionPeopleDict(token)
        newGraph = ArgGraph()
        for argument in self.arguments:
            for argument in self.arguments:
                locActionToAgentes, locActionToPatientes = self.produceActionPeopleDict(argument)
                for action in tokenActionToPatientes.keys():
                    if action in locActionToPatientes.keys() and argument.agent.name in locActionToPatientes[action] and all(a in locActionToPatientes[action] for a in tokenActionToPatientes[action]) and argument not in newGraph.arguments: #or len(self.actionToPatientes[action]) == 0:
                        newGraph.arguments.append(Argument(argument.agent, argument.support, argument.claim))
        completed = False
        while(not completed):
            completed = True
            for att in self.attacks:
                if (att.attacker in newGraph.arguments or att.attacked in newGraph.arguments) and att not in newGraph.attacks:
                    newGraph.attacks.append(att)
                    completed = False
                if att.attacked in newGraph.arguments and att.attacker not in newGraph.arguments:
                    newGraph.arguments.append(att.attacker) 
                    completed = False
                if att.attacker in newGraph.arguments and att.attacked not in newGraph.arguments:
                    newGraph.arguments.append(att.attacked) 
                    completed = False
        return newGraph

class ArgSolver:
    def __init__(self, graph):
        self.graph = graph
    
    def resetLabeling(self):
        self.inLab = []
        self.outLab = []

    def hasInAttacker(self, node):
        for n in node.attackedBy:
            if n in self.inLab:
                return True
        return False

    def allAttackersOut(self, node):
        for n in node.attackedBy:
            if n not in self.outLab:
                return False
        return True

    def groundedLabeling(self):
        self.resetLabeling()        
        for i in range(len(self.graph.nodes)):
            for n in self.graph.nodes:
                if n not in self.inLab and self.allAttackersOut(n):
                    self.inLab += [n]
                elif n not in self.outLab and self.hasInAttacker(n):
                    self.outLab += [n]
        return self.inLab, self.outLab, list(set(self.graph.nodes)-set(self.inLab)-set(self.outLab))

    def toConjunction(formulaList): 
        return Formula.makeConjunction(formulaList)


    def isCausalFormula(formulaList):
        for word in ["Causes", "Same", "Intervene"]:
            if formulaList.toString.contains(word):
                return True
        return False

    def valid(formulaList):
        l = Not(formulaList.toConjunction())
        return not satisfiable(l)

    def equivalent(formulaList1, formulaList2):
        l = []
        l.add(BiImpl(formulaList1.toConjunction(), formulaList2.toConjunction()))
        return valid(l)


if __name__ == '__main__':
    #ArgumentationBuilder(input().split(" ", -1)[0])
    print(DiscoursePrinciple(ArgModel("~/git/moral-reasoning/moral-discussions/test.arg")).permissible())
    print(UniversalityPrinciple(ArgModel("~/git/moral-reasoning/moral-discussions/policemen.arg")).permissible())
    print(DiscoursePrinciple(ArgModel("~/git/moral-reasoning/moral-discussions/punishmentDilemma.arg")).permissible())
    print(UniversalityPrinciple(ArgModel("~/git/moral-reasoning/moral-discussions/punishmentDilemma.arg")).permissible())
