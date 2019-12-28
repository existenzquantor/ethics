from libc.stdlib cimport malloc, free, calloc
from ethics.extensions.c_cudd cimport *
from ethics.extensions.parser cimport parse_formula
from libc.limits cimport INT_MAX
from libc.time cimport clock,clock_t,CLOCKS_PER_SEC
from libc.stdint cimport uintptr_t, uint64_t
from ethics.language import *

cdef CUDD_REORDER_GROUP_SIFT = 14

cdef object get_cubes(DdManager *bdd, DdNode *top_node, object atom_for_index):
    cubes = []

    cdef int *cube
    cdef double value
    cdef int cube_size = Cudd_ReadSize(bdd)
    cdef DdGen *generator = Cudd_FirstCube(bdd, top_node, &cube, &value)

    cdef int index
    while Cudd_IsGenEmpty(generator) == 0:
        new_cube = dict()
        cubes.append(new_cube)
        for index in range(0, cube_size):
            if cube[index] != 2:
                new_cube[atom_for_index[index]] = True if cube[index] == 1 else False

        Cudd_NextCube(generator, &cube, &value)
    
    Cudd_GenFree(generator)
    return cubes

def sat(formula, atoms):

    index_for_atom = {value: index for index, value in enumerate(atoms)}
    atom_for_index = {value: key for key, value in index_for_atom.items()}

    cdef DdManager *bdd = Cudd_Init(0, 0, 0, 0, 0)
    cdef DdNode *top_node = parse_formula(bdd, formula, index_for_atom)

    # Not sure what happens to top_node after this but the unit tests still work
    # and the number of models if ridiculuously reduced
    Cudd_ReduceHeap(bdd, CUDD_REORDER_GROUP_SIFT, 1)

    cubes = get_cubes(bdd, top_node, atom_for_index)
    return cubes

