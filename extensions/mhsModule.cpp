#include <Python.h>
#include <iostream>
#include <vector>
#include <algorithm>
#include <unordered_map>

using namespace std;

unordered_map<string, int> mapping;
unordered_map<int, string> reverseMapping;

// Helper type alias
using setListType = vector<vector<int> >;

/**
* Checks for a non-empty set intersection.
* @param left The left set
* @param right the right set
* @return boolean indicating if the intersection is not empty.
*/
static bool checkHit(vector<int> left, vector<int> right) {
  vector<int> intersection;

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
      PyObject *name = Py_BuildValue("s", reverseMapping[element].c_str());
      PyList_Append(hittingSet, name);
    }

    PyList_Append(hittingSets, hittingSet);
  }

  return hittingSets;
}

/**
* Inserts the given element so that the vector stays sorted.
* Requires the given vector to already be sorted!
*/
vector<int>::iterator sortedInsert(vector<int> &theVector, int element) {
  auto position = lower_bound(theVector.begin(), theVector.end(), element);
  return theVector.emplace(position, element);
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
  vector<int> emptySet;
  hittingSets.push_back(emptySet);

  for (const auto& targetSet : targetSets) {
    // Make a copy of the current hitting sets list
    setListType hittingSetsCopy;
    copy(hittingSets.begin(), hittingSets.end(), inserter(hittingSetsCopy, hittingSetsCopy.begin()));

    setListType::iterator iterator;
    for (iterator = hittingSets.begin(); iterator != hittingSets.end(); ++iterator) {
      vector<int> hittingSet = *iterator;

      if (!checkHit(hittingSet, targetSet)) {

        // No hit
        hittingSetsCopy.erase(remove(hittingSetsCopy.begin(), hittingSetsCopy.end(), hittingSet), hittingSetsCopy.end());

        for (const auto& element : targetSet) {
          vector<int>::iterator insertedPosition = sortedInsert(hittingSet, element);

          bool isValid = true;
          for (const auto& hs : hittingSetsCopy) {
            if (includes(hittingSet.begin(), hittingSet.end(), hs.begin(), hs.end())) {
              isValid = false;
              break;
            }
          }

          if (isValid) {
            // This puts a copy of hittingSet into hittingSetsCopy
            hittingSetsCopy.push_back(hittingSet);
          }

          hittingSet.erase(insertedPosition);
        }
      }
    }

    hittingSets.swap(hittingSetsCopy);
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

  mapping.clear();
  reverseMapping.clear();
  int mappingCounter = 0;

  for (int setIndex=0; setIndex < listsCount; setIndex += 1) {
    PyObject *item = PySequence_Fast_GET_ITEM(lists, setIndex);
    PyObject *list = PySequence_Fast(item, "item must be iterable");

    if (!list)
    return Py_None;

    // Number of elements in the list (set)
    int listCount = PySequence_Fast_GET_SIZE(list);

    // Then add them
    vector<int> set;
    set.reserve(listCount);
    for (int itemIndex=0; itemIndex < listCount; itemIndex += 1) {

      PyObject *item = PyUnicode_AsEncodedString(PySequence_Fast_GET_ITEM(list, itemIndex), "UTF-8", "strict");
      string value = PyBytes_AS_STRING(item);

      if(mapping.find(value) == mapping.end()) {
        // mapping doesn't exist yet. Create new one
        mapping[value] = mappingCounter;
        reverseMapping[mappingCounter] = value;
        mappingCounter += 1;
      }

      sortedInsert(set, mapping[value]);
    }

    sets.push_back(set);
  }

  //sort(sets.begin(), sets.end(), [](const vector<int> &lhs, const vector<int> &rhs) {
  //   return lhs.size() < rhs.size();
  //});

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
