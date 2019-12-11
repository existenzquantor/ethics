from ethics.extensions.c_cudd cimport *
#from primecompilator.cudd cimport Manager, Node

cdef DdNode* parse_family(DdManager *zdd, object family)
#cdef _parse_family(DdManager *zdd, int** family, int count, int item)
