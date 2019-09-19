from ethics.language import *
from ethics.tools import *
from enum import Enum
from BinPy.Algorithms import QM
import ethics.minihit as minihit
import pyeda.inter

class Structure(Enum):
    """Helper structure that distinguishes between implicant and implicate."""
    implicant = "Implicant"
    implicate = "Implicate"


class PrimeStructure:
    """Represents a prime implicant or prime implicate.
    """

    def __init__(self, structure_type, structure):
        """Main initializer.
        
        Parameters
        ----------
        structure_type : Structure
            The type of the structure (Structure.implicant or Structure.implicate).
        structure : [(atom_name, truth_value)]
            A list containing the structure's literals represented by a tuple (atom_name, truth_value).
            An example structure would be [("a", True), ("b", False)].
        """

        self.structure_type = structure_type
        self.structure = structure
        
        # Sort to make it easier to compare when printed
        self.structure.sort(key=lambda tuple: tuple[0])
                    
    def __str__(self):
        return "[" + self.structure_type.name + ", ".join([str(Atom(atom)) if truth else str(Not(Atom(atom))) for (atom, truth) in self.structure]) + "]"


    def __repr__(self):
        return self.__str__()


    def __eq__(self, other):

        if not isinstance(other, PrimeStructure):
            return False

        if other.structure_type != self.structure_type: return False
        if len(self.structure) != len(other.structure): return False

        # Iterate the literals and check for equality
        for i in range(0, len(self.structure)):
            if self.structure[i][0] != other.structure[i][0] or self.structure[i][1] != other.structure[i][1]:
                return False
        
        return True


    def __hash__(self):
        return hash("".join([str(atom) + str(truth) for atom, truth in self.structure]))


class PrimeCompilator:
    """Class that extracts all prime implicants and prime implicates from a given formula.
    """

    def __init__(self, formula, verbose=False):
        """Main initializer.
        Use instances of this class to determine all prime implicants and implicates of 
        the given formula.
        
        Parameters
        ----------
        formula : Formula
            The formula whose primes should be compiled.
            You can pass a formula containing non-boolean functions as they will automatically 
            be replaced with boolean atoms (see `self.__prepare_formula(sub_formula)`).

            Avoid using atoms with a name like "Cx", where x is a number. Those are reserved for non-boolean mappings.
        verbose : bool, optional
            Extended debug output, by default False
        """

        if not isinstance(formula, Formula):
            print("Please provide a working formula")
            exit(0)

        self.verbose = verbose
        self.formula = formula
        
        self.non_boolean_mapping = dict()

        # Turn the formula into one only consisting of AND, OR, NOT, ATOM
        # and replace non-boolean functions with atoms
        self.__prepare_formula()

        # Find the atoms of the formula (sorted for use in BinPy library later)
        self.atoms = sorted(self.__find_atoms(), reverse=True)

        # If the negation of the formula has fewer models, 
        # use the negation instead and negate the resulting prime implicants 
        # and implicates
        self.using_negation = False
        possible_assignments = 2**(len(self.atoms))
        if len(self.__find_all_models(formula)) > (possible_assignments / 2):
            
            if self.verbose:
                print("Using negated formula to speed up the algorithm")
            
            self.using_negation = True
            self.formula = self.formula.getNegation()


        if len(self.non_boolean_mapping) > 0 and verbose:
            print("\n\tNon-boolean functions mapping:\n\t----------")
            print("\t" + "\n\t".join([str(value) + ": " + str(key) for key, value in self.non_boolean_mapping.items()]))
            print()

        # Quine McCluskey algorithm implementation of BinPy
        self.qm = QM(self.atoms)

        # Lists to store the found prime implicants and implicates
        self.prime_implicants = []
        self.prime_implicates = []


    def __prepare_formula(self, sub_formula=None):
        """Recursively replaces any occurences of `Impl` and `BiImpl` with their corresponding equivalences using only `And`, `Or` and `Not`.
        This method also removes all non-boolean functions with new atoms that act as representatives of the respective function. 
        The mapping from atoms to non-boolean function is saved in `self.non_boolean_mapping`.
        
        Parameters
        ----------
        sub_formula : Formula, optional
            The current part of the formula that is being checked. Used for recursion, must be be called with None. Default: None
        """

        if sub_formula is None:
            self.formula = self.__prepare_formula(self.formula)
            return

        if isinstance(sub_formula, Atom):
            return sub_formula

        if isinstance(sub_formula, Not):
            sub_formula.f1 = self.__prepare_formula(sub_formula.f1)
            return sub_formula

        # Replace Impl
        if isinstance(sub_formula, Impl):
            sub_formula = Or(Not(sub_formula.f1), sub_formula.f2)

        # Replace BiImpl
        if isinstance(sub_formula, BiImpl):
            sub_formula = And(
                Or(Not(sub_formula.f1), sub_formula.f2),
                Or(Not(sub_formula.f2), sub_formula.f1)
            )

        if (isinstance(sub_formula, And) or isinstance(sub_formula, Or)):
            sub_formula.f1 = self.__prepare_formula(sub_formula.f1)
            sub_formula.f2 = self.__prepare_formula(sub_formula.f2)
            return sub_formula

        # Otherwise it's non-boolean.

        sub_formula_string = str(sub_formula)

        # If the exact same function (along with all parameters) have already been replaced
        # simply use the replacement atom again to avoid duplicates.
        if sub_formula_string in self.non_boolean_mapping:
            return Atom(self.non_boolean_mapping[sub_formula_string])

        # Otherwise create a new atom
        name = "C" + str(len(self.non_boolean_mapping.keys()) + 1)
        self.non_boolean_mapping[sub_formula_string] = name
        return Atom(name)


    def __find_atoms(self, sub_formula=None):
        """Recursively finds all atoms (variables) used in the formula.

        Parameters
        ----------
        sub_formula : Formula, optional
            Call it without this argument to use self.formula as root.

        Returns
        -------
        [str]
            List of all atom names
        """

        if sub_formula is None:
            # Root case
            return list(self.__find_atoms(self.formula))

        if isinstance(sub_formula, str):
            # It's an atom
            return {sub_formula}

        if isinstance(sub_formula, OnePlaced):
            return self.__find_atoms(sub_formula.f1)

        return (self.__find_atoms(sub_formula.f1)
                | (self.__find_atoms(sub_formula.f2)))


    def __find_all_models(self, formula):
        """Finds and returns all models of the given formula using pyeda's binary decision diagrams.
        
        Parameters
        ----------
        formula : Formula
            The formula whose models you want to find.
        
        Returns
        -------
        [dict(atom_name: truth_value)]
            A list containing all models of the given formula.
        """
        models = []

        f = pyeda.inter.expr(convert_formula_to_pyeda(formula))
        f = pyeda.inter.expr2bdd(f)
        pyeda_models = list(f.satisfy_all())

        for model in pyeda_models:
            model_dict = dict()

            for atom, bit in model.items():
                atom = convert_pyeda_atom_to_hera(atom)
                model_dict[str(atom)] = bit == 1

            for full_model in self.__calculate_full_models_from_partial_model(list(model_dict.items())):
                models.append(dict(full_model))

        return models        


    def __calculate_full_models_from_partial_model(self, model):
        """Takes a partial model and returns every possible complete model that the partial model implies.
        
        Parameters
        ----------
        model : [(atom_name, truth_value)]
            The partial model.
        
        Returns
        -------
        [[(atom_name, truth_value)]]
            The complete models.
        """

        atoms_in_model = [atom for atom, truth in model]

        full_models = []
        for atom in self.atoms:
            if not atom in atoms_in_model:
                full_models += self.__calculate_full_models_from_partial_model(model + [(atom, True)])
                full_models += self.__calculate_full_models_from_partial_model(model + [(atom, False)])

                return full_models

        return [model]


    def compile(self):
        """Main method that compiles the given formula and returns all prime implicants and implicates.

        Returns
        -------
        (prime implicants, prime implicates)
        """
        
        # Calculate the prime implicants and implicates
        prime_implicants, prime_implicates = self.__compile()

        # Convert into Prime Structure
        self.prime_implicants = [PrimeStructure(Structure.implicant, implicant) for implicant in prime_implicants]
        self.prime_implicates = [PrimeStructure(Structure.implicate, implicate) for implicate in prime_implicates]
 
        # Remove duplicates
        self.prime_implicants = list(dict.fromkeys(self.prime_implicants))
        self.prime_implicates = list(dict.fromkeys(self.prime_implicates))


        map_back = dict((value, key) for key, value in self.non_boolean_mapping.items())
            
        cants = []
        for p in self.prime_implicants:
            cant = []
            for s in p.structure:
                if s[0] in map_back:
                    if s[1] == 0:
                        cant.append(Not(myEval(map_back[s[0]])))
                    else:
                        cant.append(myEval(map_back[s[0]]))
                else:
                    if s[1] == 0:
                        cant.append(Not(myEval(s[0])))
                    else:
                        cant.append(myEval(s[0]))
            cants.append(cant)
            
        cates = []
        for p in self.prime_implicates:
            cate = []
            for s in p.structure:
                if s[0] in map_back:
                    if s[1] == 0:
                        cate.append(Not(myEval(map_back[s[0]])))
                    else:
                        cate.append(myEval(map_back[s[0]]))
                else:
                    if s[1] == 0:
                        cate.append(Not(myEval(s[0])))
                    else:
                        cate.append(myEval(s[0]))
            cates.append(cate)

        return cants, cates

    
    def __compile(self):
        """Internal compilation method that determines all prime implicants and implicates.
        
        Returns
        -------
        [PrimeStructure], [PrimeStructure]
            Returns two lists of `PrimeStructure`. 
            The first one contains all prime implicants and the second one all prime implicates.
        """

        prime_implicants = []
        prime_implicates = []

        models = self.__find_all_models(self.formula)

        true_lines_in_truth_table = []
        for model in models:
            true_lines_in_truth_table.append(self.__compute_truth_table_line_number(model))

        # Get the minimized boolean expression
        formula = self.qm.get_function(self.qm.compute_primes(true_lines_in_truth_table))

        # Add the prime implicants
        for prime_implicant in self.__structure_from_binPy_formula(formula):
            prime_implicants.append(prime_implicant)

        # Find all minimal hitting sets of the prime implicants to get all the prime implicates
        hitting_sets = self.__create_sets_for_hitting_sets_using_prime_implicants(prime_implicants, use_sets=True)

        tree = minihit.RcTree(hitting_sets)
        tree.solve(prune=True, sort=False)
        hitting_sets = list(tree.generate_minimal_hitting_sets())

        for hitting_set in hitting_sets:
            prime_implicate = self.__convert_hitting_set_into_assignment(list(hitting_set))
            prime_implicates.append(prime_implicate)

        if self.using_negation:
            actual_prime_implicants = [[(name, not truth) for name, truth in prime_implicate] for prime_implicate in prime_implicates]
            actual_prime_implicates = [[(name, not truth) for name, truth in prime_implicant] for prime_implicant in prime_implicants]
            prime_implicants, prime_implicates = actual_prime_implicants, actual_prime_implicates

        return prime_implicants, prime_implicates


    def __compute_truth_table_line_number(self, model):
        return sum([model.get(atom, False) * (2**(index)) for index, atom in enumerate(self.atoms)])


    def __structure_from_binPy_formula(self, formula):
        """Converts the result of bynPy to a list of assignments.
        
        Parameters
        ----------
        formula : binPy formula
        
        Returns
        -------
        [[(atom_name, truth_value)]]
        """
        # Pre-process the string to put all pirme implicants into a list
        formula = formula.replace("(","").replace(")","")
        formula = formula.split(" OR ")
        minterms = [minterm.split(" AND ") for minterm in formula]

        prime_implicants = []

        # extract prime implicants
        for minterm in minterms:
            prime_implicant = []

            for assignment in minterm:
                if assignment[:4] == "NOT ":
                    prime_implicant.append((assignment[4:], False))
                else:
                    prime_implicant.append((assignment, True))
            prime_implicants.append(prime_implicant)
        
        return prime_implicants
        

    def __create_sets_for_hitting_sets_using_prime_implicants(self, prime_implicants, use_sets=False):
        """Takes the given prime_implicants and turns them into sets readable by minihit.
        
        Parameters
        ----------
        prime_implicants : [[(atom_name, truth_value)]]
            The prime implicants.
        use_sets : bool, optional
            Creates the sets using python sets if set to True (and lists if set to False). Default: False
        
        Returns
        -------
        [[str]] or [{str}]
        """
        sets = []
        for prime_implicant in prime_implicants:
            current_set = set() if use_sets else []
            for atom, truth_value in prime_implicant:
                variable = "+" + atom if truth_value else "-" + atom
                if use_sets:
                    current_set.add(variable)
                else :
                    current_set.append(variable)
            sets.append(current_set)
        return sets


    def __convert_hitting_set_into_assignment(self, hitting_set):
        """Converts a hitting set returned by minihit to an assignment.
        
        Parameters
        ----------
        hitting_set : [str]
            The hitting set returned by minihit.
        
        Returns
        -------
        [(atom_name, truth_value)]
            The corresponding assignment.
        """
        
        assignment = []
        for variable in hitting_set:
            prefix = str(variable)[0]
            name = str(variable)[1:]

            truth_value = True if prefix == "+" else False
            assignment.append((name, truth_value))

        return assignment