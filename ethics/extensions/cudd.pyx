from ethics.extensions.c_cudd cimport *

"""
cdef Node create_node(DdManager *manager, DdNode *DdNode):
    cdef Node node = Node()
    node.create(manager, DdNode)
    return node
"""

cdef class Manager:
    cdef DdManager *manager

    def __cinit__(self):
        manager = Cudd_Init(0, 0, 0, 0, 0)
        assert manager != NULL, "Something went wrong"
        self.manager = manager

    def __init__(self):
        print("Okay")

    def something(self):
        Cudd_zddIthVar(self.manager, 1)
        print("Done")

cdef class Node:
    cdef DdNode *DdNode
    cdef DdManager *manager

    cdef create(self, DdManager *manager, DdNode *DdNode):
        self.DdNode = DdNode
        self.manager = manager

    @property
    def index(self):
        cdef int node_index = Cudd_NodeReadIndex(self.DdNode) 
        return node_index

    @property
    def low(self):
        if Cudd_IsConstant(self.DdNode):
            return None
        cdef DdNode *low_node
        low_node = Cudd_E(self.DdNode)
        #return create_node(self.manager, low_node)