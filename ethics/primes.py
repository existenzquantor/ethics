from ethics.language import *
from ethics.tools import *
from enum import Enum
import pyeda.inter
from functools import reduce
import mhsModule


class PrimeCompilator:
    """A simple class compiles prime implicants and prime implicates."""

    def __init__(self, formula, verbose=False):
        """Initialize the compilator class.

        Parameters
        ----------
        formula : Formula
            The formula whose primes should be compiled.
            You can pass a formula containing non-boolean functions as they
            will be replaced with boolean atoms.

            Avoid using atoms with a name like "Cx", where x is a number.
            Those are reserved for non-boolean mappings.
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
        self.found_models = None

        possible_assignments = 2**(len(self.atoms))
        self.found_models = self.__all_models(self.formula)
        num_models = self.__number_of_complete_models(self.found_models)
        if num_models > (possible_assignments / 2):
            self.found_models = None
            if self.verbose:
                print("Using negated formula to speed up the algorithm")

            self.using_negation = True

        if len(self.non_boolean_mapping) > 0 and verbose:
            print("\n\tNon-boolean functions mapping:\n\t----------")
            print("\t" + "\n\t".join(
                [str(value) + ": " + str(key)
                 for key, value in self.non_boolean_mapping.items()]))
            print()

        # Lists to store the found prime implicants and implicates
        self.prime_implicants = []
        self.prime_implicates = []

    def __prepare_formula(self, sub_formula=None):
        """Parse the formula to make it compatible with PrimeCompilator.

        Recursively replaces any occurences of `Impl` and `BiImpl` with their
        corresponding equivalences using only `And`, `Or` and `Not`. This
        method also removes all non-boolean functions with new atoms that act
        as representatives of the respective function. The mapping from atoms
        to non-boolean function is saved in `self.non_boolean_mapping`.

        Parameters
        ----------
        sub_formula : Formula, optional
            The current part of the formula that is being checked.
            Used for recursion, must be be called with None. Default: None

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

        # If the exact same function  have already been replaced
        # simply use the replacement atom again to avoid duplicates.
        if sub_formula_string in self.non_boolean_mapping:
            return Atom(self.non_boolean_mapping[sub_formula_string])

        # Otherwise create a new atom
        name = "C" + str(len(self.non_boolean_mapping.keys()) + 1)
        self.non_boolean_mapping[sub_formula_string] = name
        return Atom(name)

    def compile(self):
        """Compile all prime implicants and prime implicates.

        Returns
        -------
        (prime implicants, prime implicates)

        """
        self.prime_implicants, self.prime_implicates = self.__compile()

        map_back = dict((value, key)
                        for key, value in self.non_boolean_mapping.items())

        cants = []
        for p in self.prime_implicants:
            cant = []
            for s in p:
                if s[0] in map_back:
                    if s[1] == 0:
                        cant.append(Not(my_eval(map_back[s[0]])))
                    else:
                        cant.append(my_eval(map_back[s[0]]))
                else:
                    if s[1] == 0:
                        cant.append(Not(my_eval(s[0])))
                    else:
                        cant.append(my_eval(s[0]))
            cants.append(cant)

        cates = []
        for p in self.prime_implicates:
            cate = []
            for s in p:
                if s[0] in map_back:
                    if s[1] == 0:
                        cate.append(Not(my_eval(map_back[s[0]])))
                    else:
                        cate.append(my_eval(map_back[s[0]]))
                else:
                    if s[1] == 0:
                        cate.append(Not(my_eval(s[0])))
                    else:
                        cate.append(my_eval(s[0]))
            cates.append(cate)

        return cants, cates

    def __find_atoms(self, sub_formula=None):
        """Recursively find all atoms (variables) used in the formula.

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

    def __number_of_complete_models(self, models):
        """Calculate the number of complete models from partial models.

        Parameters
        ----------
        models : dict()
            The partial models.

        Returns
        -------
        int
            The number of complete models.

        """
        atoms = len(self.atoms)
        return reduce(lambda a, b: a+b, [0]
                      + [2**(atoms - len(model)) for model in models])

    def __all_models(self, formula, complete_models=False):
        """Find and returns all models of the given formula.

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

        if self.using_negation:
            negated = Not(formula)
            f = pyeda.inter.expr(convert_formula_to_pyeda(negated))
            f = pyeda.inter.expr2bdd(f)
        else:
            f = pyeda.inter.expr(convert_formula_to_pyeda(formula))
            f = pyeda.inter.expr2bdd(f)

        pyeda_models = list(f.satisfy_all())

        for model in pyeda_models:
            model_dict = dict()

            for atom, bit in model.items():
                atom = convert_pyeda_atom_to_hera(atom)
                model_dict[str(atom)] = bit == 1

            partial_model = list(model_dict.items())
            used_models = (self.__complete_partial_model(partial_model)
                           if complete_models else [partial_model])

            for full_model in used_models:
                models.append(dict(full_model))

        return models

    def __complete_partial_model(self, model):
        """Return the set of complete models the partial models imply.

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
            if atom not in atoms_in_model:
                full_models += self.__complete_partial_model(model
                                                             + [(atom, True)])
                full_models += self.__complete_partial_model(model
                                                             + [(atom, False)])

                return full_models

        return [model]

    def __compile(self):
        prime_implicants = []
        prime_implicates = []

        # Find all models
        if self.found_models is None:
            models = self.__all_models(self.formula, complete_models=False)
        else:
            models = self.found_models

        # Convert models to lists of tuples
        models = [list(model.items()) for model in models]
        sets = self.__model_to_target_sets(models)
        hitting_sets = self.__remove_trivial_clauses(self.__hitting_sets(sets))

        # Generate prime implicates from the hitting sets (just type casting)
        for hitting_set in hitting_sets:
            prime_implicate = self.__hitting_set_to_assignment(hitting_set)
            prime_implicates.append(prime_implicate)

        # Now take the hitting sets and find again all minimal hitting sets
        # Those then are all prime implicants
        hitting_sets = self.__hitting_sets(hitting_sets)
        hitting_sets = self.__remove_trivial_clauses(hitting_sets)

        # Generate prime implicates from the hitting sets (just type casting)
        for hitting_set in hitting_sets:
            prime_implicant = self.__hitting_set_to_assignment(hitting_set)
            prime_implicants.append(prime_implicant)

        # Flip implicants and implicates if necessary
        if self.using_negation:
            actual_prime_implicants = [[(name, not truth)
                                        for name, truth in prime_implicate]
                                       for prime_implicate in prime_implicates]
            actual_prime_implicates = [[(name, not truth)
                                        for name, truth in prime_implicant]
                                       for prime_implicant in prime_implicants]

            prime_implicates = actual_prime_implicates
            prime_implicants = actual_prime_implicants

        return prime_implicants, prime_implicates

    def __remove_trivial_clauses(self, sets):
        """Remove trivial clauses from the sets.

        A clause is trivial if it contains both positive and negative literals
        of any given atom.

        Parameters
        ----------
        sets : [set()]
            A list containing all the sets.

        Returns
        -------
        [set()]
            The filtered sets.

        """
        filtered_sets = []
        for current_set in sets:
            found_atoms = set()
            for literal in current_set:
                if literal[1:] in found_atoms:
                    found_atoms = set()
                    break
                found_atoms.add(literal[1:])

            if len(found_atoms) > 0:
                filtered_sets.append(current_set)

        return filtered_sets

    def __model_to_target_sets(self, models):
        """Create a mhs compatible set of sets using the given model.

        Parameters
        ----------
        prime_implicants : [[(atom_name, truth_value)]]
            The prime implicants.
        use_sets : bool, optional
            Creates the sets using python sets if set to True
            (and lists if set to False). Default: False

        Returns
        -------
        [[str]] or [{str}]

        """
        sets = []
        for prime_implicant in models:
            current_set = []
            for atom, truth_value in prime_implicant:
                variable = "+" + atom if truth_value else "-" + atom
                current_set.append(variable)
            sets.append(current_set)
        return sets

    def __hitting_set_to_assignment(self, hitting_set):
        """Convert a hitting set to an assignment.

        Parameters
        ----------
        hitting_set : [str]
            The hitting set.

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

    def __hitting_sets(self, sets):
        return mhsModule.hitting_sets(sets)
