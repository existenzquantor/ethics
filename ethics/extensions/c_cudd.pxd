from libcpp cimport bool
from libc.stdio cimport FILE, fdopen, fopen, fclose, printf
from libc.stdlib cimport malloc, free
from libc cimport stdint

cdef extern from 'cuddInt.h':
    cdef char* CUDD_VERSION
    cdef struct DdSubtable:
        unsigned int slots
        unsigned int keys
    cdef struct DdManager:
        DdSubtable *subtables
        unsigned int keys
        unsigned int dead
        double cachecollisions
        double cacheinserts
        double cachedeletions
    cdef DdNode *cuddUniqueInter(
        DdManager *unique, int index, DdNode *T, DdNode *E)

cdef extern from 'cudd.h':

    ctypedef enum Cudd_ReorderingType:
        pass

    ctypedef unsigned int DdHalfWord
    cdef struct DdNode:
        DdHalfWord index
        DdHalfWord ref
    ctypedef DdNode DdNode

    ctypedef DdManager DdManager
    cdef DdManager* Cudd_Init(
        unsigned int numVars,
        unsigned int numVarsZ,
        unsigned int numSlots,
        unsigned int cacheSize,
        unsigned long maxMemory)
    cdef struct DdGen
    ctypedef enum Cudd_ReorderingType:
        pass

    # General manipulation functions
    cdef DdNode *Cudd_T(DdNode *u)
    cdef DdNode *Cudd_E(DdNode *u)
    cdef unsigned int Cudd_NodeReadIndex(DdNode *u)
    cdef bool Cudd_IsConstant(DdNode *u)
    cdef void Cudd_Ref(DdNode *n)
    cdef void Cudd_RecursiveDeref(DdManager *table, DdNode *n)
    cdef void Cudd_Deref(DdNode *n)
    cdef int Cudd_CheckZeroRef(DdManager *manager)
    cdef DdNode *Cudd_Regular(DdNode *u)
    cdef void Cudd_Quit(DdManager *unique)

    # ZDD manipulation functions
    cdef DdNode * Cudd_ReadZddOne(DdManager *dd, int i)
    cdef DdNode * Cudd_zddIthVar(DdManager *dd, int i)
    cdef int Cudd_zddVarsFromBddVars(DdManager *dd, int multiplicity)
    cdef DdNode * Cudd_zddIte(DdManager *dd, DdNode *f, DdNode *g, DdNode *h)
    cdef DdNode * Cudd_zddUnion(DdManager *dd, DdNode *P, DdNode *Q)
    cdef DdNode * Cudd_zddIntersect(DdManager *dd, DdNode *P, DdNode *Q)
    cdef DdNode * Cudd_zddDiff(DdManager *dd, DdNode *P, DdNode *Q)
    cdef DdNode * Cudd_zddDiffConst(DdManager *zdd, DdNode *P, DdNode *Q)
    cdef DdNode * Cudd_zddSubset1(DdManager *dd, DdNode *P, int var)
    cdef DdNode * Cudd_zddSubset0(DdManager *dd, DdNode *P, int var)
    cdef DdNode * Cudd_zddChange(DdManager *dd, DdNode *P, int var)
    cdef void Cudd_zddSymmProfile(DdManager *table, int lower, int upper)
    cdef int Cudd_zddPrintDebug(DdManager *zdd, DdNode *f, int n, int pr)
    cdef DdGen * Cudd_zddFirstPath(DdManager *zdd, DdNode *f, int **path)
    cdef int Cudd_zddNextPath(DdGen *gen, int **path)
    cdef DdNode * Cudd_zddSupport(DdManager * dd, DdNode * f)
    cdef DdNode * Cudd_zddPortFromBdd(DdManager *dd, DdNode *B)
    cdef DdNode * Cudd_RecursiveDerefZdd(DdManager *table, DdNode *n )
    cdef DdNode * cuddUniqueInterZdd(DdManager *unique, int index, DdNode *T, DdNode *E)
    cdef DdNode * cuddZddGetNode(DdManager * zdd, int id, DdNode *T, DdNode *E)
    cdef int Cudd_zddDumpDot(DdManager *dd, int n, DdNode **f, char **inames, char **onames, FILE *fp)
    cdef DdNode *Cudd_ReadOne(DdManager *dd)
    cdef DdNode *Cudd_ReadZero(DdManager * dd)
    cdef int Cudd_ReadZddSize(DdManager * dd)

    # BDD Manipulation
    cdef DdNode *Cudd_bddIthVar(DdManager * dd, int i)
    cdef DdNode *Cudd_bddAnd(DdManager *dd, DdNode *f, DdNode *g)
    cdef DdNode *Cudd_bddOr(DdManager *dd, DdNode *f, DdNode *g)
    cdef DdNode *Cudd_Not(DdNode *dd)
    cdef void Cudd_Deref(DdNode *node)
    cdef void Cudd_RecursiveDeref(DdManager *table, DdNode *n)
    cdef DdNode * Cudd_bddIte(DdManager *dd, DdNode *f, DdNode *g, DdNode *h)
    cdef DdGen *Cudd_FirstCube(DdManager *dd, DdNode *f, int **cube, double *value)
    cdef int Cudd_NextCube(DdGen *gen, int **cube, double *value)
    cdef int Cudd_GenFree(DdGen *gen)
    cdef int Cudd_ReadSize(DdManager *dd)
    cdef int Cudd_IsGenEmpty(DdGen *gen)
    cdef int Cudd_ReduceHeap(DdManager *table, Cudd_ReorderingType heuristic, int  minsize)