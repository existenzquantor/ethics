from libc.stdlib cimport malloc, free, calloc
from ethics.extensions.c_cudd cimport *
from ethics.extensions.parser cimport parse_family
from libc.limits cimport INT_MAX
from libc.time cimport clock,clock_t,CLOCKS_PER_SEC
from libc.stdint cimport uintptr_t, uint64_t

#cdef HASH_TABLE_SIZE = 500000
cdef uint64_t HASH_TABLE_SIZE = 500000 # 2^40
ctypedef unsigned int UInt

cdef struct HashItem:
    uintptr_t key
    DdNode *value
    HashItem *next

cdef struct HashTable:
    uint64_t numBuckets
    HashItem **buckets

cdef int hash(uintptr_t x):
    x = ((x >> 16) ^ x) * 0x45d9f3b
    x = ((x >> 16) ^ x) * 0x45d9f3b
    x = (x >> 16) ^ x
    return <int> (x % HASH_TABLE_SIZE)

cdef void hash_table_delete_item(HashItem *item):
    free(item)

cdef void hash_table_delete(HashTable *table):
    cdef HashItem *item
    cdef uint64_t index = 0
    for index in range(table.numBuckets):
        item = table.buckets[index]
        if item != NULL:
            hash_table_delete_item(item)
    
    free(table.buckets)
    free(table)


cdef HashItem* hash_table_new_item(uintptr_t key, DdNode *value):
    cdef HashItem *item = <HashItem*> malloc(sizeof(HashItem))
    item.key = key
    item.value = value
    item.next = NULL
    return item

cdef HashTable* create_hash_table():
    cdef HashTable *table = <HashTable*> malloc(sizeof(HashTable))
    table.numBuckets = HASH_TABLE_SIZE
    table.buckets = <HashItem**>calloc(<size_t>table.numBuckets, sizeof(HashItem*))
    return table

cdef hash_table_insert(HashTable *table, DdNode *key_node, DdNode *value):
    cdef uintptr_t key = <uintptr_t>key_node
    cdef HashItem *new_item = hash_table_new_item(key, value)
    cdef HashItem *current_item
    cdef int index = hash(key)
    if table.buckets[index] == NULL:
        # Set this bucket to be the new hash item
        table.buckets[index] = new_item
    else:
        current_item = table.buckets[index]
        # Otherwise, this bucket is already occupied. Add the new item
        # to the end of the linked list
        while current_item.next != NULL:
            current_item = current_item.next
        current_item.next = new_item

cdef DdNode* hash_table_search(HashTable *table, DdNode *key_node):
    cdef HashItem *current_item
    cdef uintptr_t key = <uintptr_t>key_node
    cdef int index = hash(key)
    if table.buckets[index] == NULL:
        return NULL
    else:
        current_item = table.buckets[index]
        while current_item.key != key:
            if current_item.next == NULL:
                return NULL
            current_item = current_item.next
        return current_item.value
    
    return NULL


cdef DdNode* _mhs(DdManager *zdd, DdNode *f, HashTable *hash_table):
    cdef DdNode *r
    cdef DdNode *r_low
    cdef DdNode *r_high
    cdef DdNode *unique_node # The node that will be created in this function
    cdef DdNode *cached_node # The unique node if it has been cached; Retreived from the hash table

    if f == Cudd_ReadOne(zdd):
        unique_node = Cudd_ReadZero(zdd)
        Cudd_Ref(unique_node)
        return unique_node
    if f == Cudd_ReadZero(zdd):
        unique_node = Cudd_ReadOne(zdd)
        Cudd_Ref(unique_node)
        return unique_node
    
    cached_node = hash_table_search(hash_table, f)
    if cached_node != NULL:
        return cached_node

    r = Cudd_zddUnion(zdd, Cudd_E(f), Cudd_T(f))
    Cudd_Ref(r)

    r_low = _mhs(zdd, r, hash_table)
    Cudd_Ref(r_low)

    r_tmp = _mhs(zdd, Cudd_E(f), hash_table)
    Cudd_Ref(r_tmp)
    Cudd_RecursiveDerefZdd(zdd, r)
    r = r_tmp

    r_high = _difference(zdd, r, r_low)
    Cudd_Ref(r_high)

    if Cudd_NodeReadIndex(f) != f.index:
        printf("NOT EQUAL\n")


    cdef int f_index = Cudd_NodeReadIndex(f)

    unique_node = cuddZddGetNode(zdd, f_index, r_high, r_low)

    if unique_node.ref == 0:
        Cudd_Ref(unique_node)

    Cudd_Ref(unique_node)

    hash_table_insert(hash_table, f, unique_node)
    
    return unique_node

cdef DdNode* _difference(DdManager *zdd, DdNode *f, DdNode *g):
    if g == Cudd_ReadZero(zdd):
        return f
    if f == Cudd_ReadZero(zdd) or g == Cudd_ReadOne(zdd) or f == g:
        return Cudd_ReadZero(zdd)
    
    cdef int f_index = Cudd_NodeReadIndex(f)
    cdef int g_index = Cudd_NodeReadIndex(g)

    if f_index > g_index:
        return _difference(zdd, f, Cudd_E(g))
    
    cdef DdNode *r_high
    cdef DdNode *r_low
    
    if f_index < g_index:
        r_low = _difference(zdd, Cudd_E(f), g)
        r_high = Cudd_T(f)
    else:
        r_low = _difference(zdd, Cudd_E(f), Cudd_E(g))
        r_high = _difference(zdd, Cudd_T(f), Cudd_T(g))

    return cuddZddGetNode(zdd, f_index, r_high, r_low)

cdef object get_paths(DdManager *zdd, DdNode *top_node):
    paths = []

    cdef int* path
    cdef int path_size = Cudd_ReadZddSize(zdd)
    cdef DdGen* generator = Cudd_zddFirstPath(zdd, top_node, &path)

    cdef int index
    while True:
        new_path = []
        paths.append(new_path)
        for index in range(0, path_size):
            if path[index] == 1:
                new_path.append(index)

        if not Cudd_zddNextPath(generator, &path):
            break
    
    return paths


def mhs(family):
    cdef DdManager *zdd = Cudd_Init(0, 0, 0, 0, 0)

    cdef DdNode *family_rep = parse_family(zdd, family)
    cdef HashTable *hash_table = create_hash_table()
    cdef DdNode *mhs = _mhs(zdd, family_rep, hash_table)
    paths = get_paths(zdd, mhs)

    hash_table_delete(hash_table)
    Cudd_Quit(zdd)

    return paths