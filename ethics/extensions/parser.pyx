from ethics.extensions.c_cudd cimport *
#from primecompilator.cudd cimport Manager, Node
from libc.stdlib cimport malloc, free
from libc.stdio cimport printf
from libc.limits cimport INT_MAX
from ethics.language import *
from libc.stdint cimport uintptr_t, uint64_t

cdef print_c_family(int** family, int length):
    cdef int set_index = 0
    cdef int element_index = 0
    while set_index < length:
        printf("[")
        element_index = 0
        while element_index < INT_MAX:
            if family[set_index][element_index] == INT_MAX:
                break
            printf("%d, ", family[set_index][element_index])
            element_index += 1
        printf("\b\b] ")
        set_index += 1


cdef DdNode* parse_formula(DdManager *bdd, object formula, object var_cache):
    cdef DdNode *top_node = _parse_formula(bdd, formula, var_cache)
    return top_node

cdef DdNode* _parse_formula(DdManager *bdd, object formula, object var_cache):
    cdef DdNode *left_function
    cdef DdNode *right_function
    cdef DdNode *new_function
    
    if isinstance(formula, Atom):
        left_function = Cudd_bddIthVar(bdd, var_cache[formula.f1])
        return left_function

    if isinstance(formula, Not):
        left_function = _parse_formula(bdd, formula.f1, var_cache)
        #Cudd_Ref(left_function)
        # Negate the function
        new_function = Cudd_Not(left_function)

        Cudd_Ref(new_function)

        if not isinstance(formula.f1, Atom):
            Cudd_RecursiveDeref(bdd, left_function)

        return new_function

    if isinstance(formula, TwoPlaced):
        left_function = _parse_formula(bdd, formula.f1, var_cache)
        #Cudd_Ref(left_function)

        right_function = _parse_formula(bdd, formula.f2, var_cache)
        #Cudd_Ref(right_function)

        if isinstance(formula, And):
            new_function = Cudd_bddAnd(bdd, left_function, right_function)
        elif isinstance(formula, Or):
            new_function = Cudd_bddOr(bdd, left_function, right_function)
        elif isinstance(formula, Impl):
            new_function = Cudd_bddIte(bdd, left_function, right_function, Cudd_ReadOne(bdd))
        elif isinstance(formula, BiImpl):
            new_function = Cudd_bddIte(bdd, left_function, right_function, Cudd_Not(right_function))

        Cudd_Ref(new_function)

        if not isinstance(formula.f1, Atom):
            Cudd_RecursiveDeref(bdd, left_function)

        if not isinstance(formula.f2, Atom):
            Cudd_RecursiveDeref(bdd, right_function)

        return new_function
    
    return NULL


cdef DdNode* parse_family(DdManager *zdd, object family):
    cdef int** c_family = _create_c_family(family)
    cdef DdNode *top_node = _parse_family(zdd, c_family, len(family), 0)
    return top_node

cdef int** _create_c_family(object family):
    """Turn a list of integer lists (python objects) into a int**.
    Each list is terminated by INT_MAX.
    
    Returns:
        int** -- The family represented as a c data type.
    """
    cdef int family_size = len(family)
    cdef int set_size = 0
    cdef int **c_family
    cdef int set_index = 0
    cdef int element_index = 0

    # Allocate memory for the number of sets in the family
    c_family = <int **> malloc(family_size * sizeof(int*))

    for set_index in range(family_size):
        set_size = len(family[set_index]) + 1 # +1 because of INT_MAX at the end
        c_family[set_index] = <int *> malloc(set_size * sizeof(int))

        for element_index in range(set_size - 1):
            c_family[set_index][element_index] = family[set_index][element_index]

        c_family[set_index][set_size-1] = INT_MAX

    return c_family

cdef DdNode* _parse_family(DdManager *zdd, int** family, int count, int item):
    cdef DdNode* node
    cdef int smallest_value = family[0][item]
    cdef int separator = 1
    cdef DdNode *high_node
    cdef DdNode *low_node

    if count == 0:
        node = Cudd_ReadZero(zdd)
        Cudd_Ref(node)
        return node

    if smallest_value == INT_MAX:
        node = Cudd_ReadOne(zdd)
        Cudd_Ref(node)
        return node
    
    while separator < count and family[separator][item] == smallest_value:
        separator += 1
    
    high_node = _parse_family(zdd, family, separator, item + 1)
    low_node = _parse_family(zdd, family + separator, count - separator, item)

    node = cuddZddGetNode(zdd, smallest_value, high_node, low_node)
    Cudd_Ref(node)

    Cudd_RecursiveDerefZdd(zdd, high_node)
    Cudd_RecursiveDerefZdd(zdd, low_node)

    return node
