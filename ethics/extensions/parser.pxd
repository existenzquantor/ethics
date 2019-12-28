from ethics.extensions.c_cudd cimport *
#from primecompilator.cudd cimport Manager, Node

cdef DdNode* parse_family(DdManager *zdd, object family)
cdef DdNode* parse_formula(DdManager *bdd, object formula, object var_cache)
#cdef _parse_family(DdManager *zdd, int** family, int count, int item)
