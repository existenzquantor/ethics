from ethics.extensions.c_cudd cimport *

#cdef Node create_node(DdManager *manager, DdNode *DdNode)

cdef class Manager:
    cdef DdManager *manager

cdef class Node:
    cdef DdNode *DdNode
    cdef DdManager *manager
    cdef create(self, DdManager *manager, DdNode *DdNode)