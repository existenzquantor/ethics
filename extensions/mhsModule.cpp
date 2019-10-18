#include <Python.h>
#include <iostream>
#include <set>
#include <list>
#include <algorithm>

using namespace std;

// Helper type alias
using setListType = list<set<string> >;

/**
 * Checks for a non-empty set intersection.
 * @param left The left set
 * @param right the right set
 * @return boolean indicating if the intersection is not empty.
 */
static bool checkHit(set<string> left, set<string> right) {
    set<string> intersection;
    set_intersection(left.begin(), left.end(), right.begin(), right.end(), inserter(intersection, intersection.begin()));
    return intersection.size() != 0;
}

/**
 * Prepares the given list of sets for return to python.
 * @param sets The hitting sets in C++.
 * @return A PyObject* representing the hitting sets.
 */
static PyObject* buildReturnValue(setListType sets) {
    PyObject *hittingSets = PyList_New(0);

    for (const auto& set : sets) {
        PyObject *hittingSet = PyList_New(0);

        for (const auto& element : set) {
            // Py_BuildValue only works with C types, so element has to be cast as c string
            PyObject *name = Py_BuildValue("s", element.c_str());
            PyList_Append(hittingSet, name);
        }

        PyList_Append(hittingSets, hittingSet);
    }

    return hittingSets;
}


/**
 * The algorithm that finds all minimal hitting sets in the given targetSets.
 * @param targetSets
 * @return The minimal hitting sets.
 */
static setListType findHittingSets(setListType targetSets) {

    // Create the hitting sets list
    setListType hittingSets;

    // Add empty set as initial hitting set
    set<string> emptySet;
    hittingSets.push_back(emptySet);

    for (const auto& targetSet : targetSets) {
        // Make a copy of the current hitting sets list
        setListType hittingSetsCopy;
        copy(hittingSets.begin(), hittingSets.end(), inserter(hittingSetsCopy, hittingSetsCopy.begin()));
	
        for (const auto& hittingSet : hittingSets) { 
            if (!checkHit(hittingSet, targetSet)) {
                // No hit
		        hittingSetsCopy.remove(hittingSet);

                for (const auto& element : targetSet) {
                    set<string> candidate;
                    copy(hittingSet.begin(), hittingSet.end(), inserter(candidate, candidate.begin()));
                    candidate.insert(element);

                    bool isValid = true;
                    for (const auto& hs : hittingSetsCopy) {
                        if (includes(candidate.begin(), candidate.end(), hs.begin(), hs.end())) {
                            isValid = false;
                            break;
                        }
                    }

                    if (isValid) {
                        hittingSetsCopy.push_back(candidate);
                    }
                }
            }
        }

        hittingSets = hittingSetsCopy;
    }

    return hittingSets;
}

/**
 * Function callable from within Python that parses the python arguments and runs the minimal hitting set algorithm.
 * @param self
 * @param args
 * @return The minimal hitting sets cast as python object
 */
static PyObject* hitting_sets(PyObject* self, PyObject* args) {
    Py_INCREF(Py_None);
    PyObject* lists; // The sets as python object

    // Try to parse the tuple as python object
    if(!PyArg_ParseTuple(args, "O", &lists))
        return Py_None;

    // Cast the python object as sequence python PyObject
    lists = PySequence_Fast(lists, "argument must be iterable");

    if (!lists)
        return Py_None;

    int listsCount = PySequence_Fast_GET_SIZE(lists);

    setListType sets;

    for (int setIndex=0; setIndex < listsCount; setIndex += 1) {
        PyObject *item = PySequence_Fast_GET_ITEM(lists, setIndex);
        PyObject *list = PySequence_Fast(item, "item must be iterable");

        if (!list)
            return Py_None;

        // Number of elements in the list (set)
        int listCount = PySequence_Fast_GET_SIZE(list);

        // Then add them
        set<string> set;
        for (int itemIndex=0; itemIndex < listCount; itemIndex += 1) {
            PyObject *item = PyUnicode_AsEncodedString(PySequence_Fast_GET_ITEM(list, itemIndex), "UTF-8", "strict");
            string value = PyBytes_AS_STRING(item);

            set.insert(value);
        }

        sets.push_back(set);
    }

    setListType hittingSets = findHittingSets(sets);
    return buildReturnValue(hittingSets);
}


static PyMethodDef myMethods[] = {
    { "hitting_sets", hitting_sets, 1, "Computes Minimal Hitting Sets of given sets." },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef mhsModule = {
    PyModuleDef_HEAD_INIT,
    "mhsModule",
    "Minimal Hitting Set Algorithm",
    -1,
    myMethods
};

PyMODINIT_FUNC PyInit_mhsModule(void) {
    Py_Initialize();
    return PyModule_Create(&mhsModule);
};
