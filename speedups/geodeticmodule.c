/*
 The Hazard Library
 Copyright (C) 2012-2016 GEM Foundation

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <Python.h>
#include <numpy/arrayobject.h>

#define EARTH_RADIUS 6371.0


/*
 * Calculate the distance between two points along the geodetic.
 * Parameters are two pairs of spherical coordinates in radians
 * and return value is distance in km.
 *
 * Implements http://williams.best.vwh.net/avform.htm#Dist
 */
static inline double
geodetic__geodetic_distance(double lon1, double lat1, double lon2, double lat2)
{
    return asin(sqrt(
        pow(sin((lat1 - lat2) / 2.0), 2.0)
        + cos(lat1) * cos(lat2) * pow(sin((lon1 - lon2) / 2.0), 2.0)
    )) * 2 * EARTH_RADIUS;
}


static const char geodetic_min_distance__doc__[] = "\n\
    Calculate the minimum distance between two collections of points.\n\
    \n\
    min_distance(mlons, mlats, mdepths, slons, \\\n\
            slats, sdepths, indices) -> min distances or indices of such\n\
    \n\
    Parameters mlons, mlats and mdepths represent coordinates of the first\n\
    collection of points and slons, slats, sdepths are for the second one.\n\
    All the coordinates must be numpy arrays of double. Longitudes and \n\
    latitudes are in radians, depths are in km.\n\
    \n\
    Boolean parameter \"indices\" determines whether actual minimum\n\
    distances should be returned or integer indices of closest points\n\
    from first collection. Thus, result is numpy array of either distances\n\
    (array of double, when indices=False) or indices (array of integers,\n\
    when indices=True).\n\
";
static PyObject *
geodetic_min_distance(
        PyObject *self,
        PyObject *args,
        PyObject *keywds)
{
    static char *kwlist[] = {"mlons", "mlats", "mdepths", /* mesh coords */
                             "slons", "slats", "sdepths", /* site coords */
                             "indices", /* min distance / closest points */
                             NULL}; /* sentinel */

    PyArrayObject *mlons, *mlats, *mdepths, *slons, *slats, *sdepths;
    unsigned char indices = 0;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!O!O!b", kwlist,
                // mesh coords
                &PyArray_Type, &mlons, &PyArray_Type, &mlats,
                &PyArray_Type, &mdepths,
                // site coords
                &PyArray_Type, &slons, &PyArray_Type, &slats,
                &PyArray_Type, &sdepths,
                // min distance / closest points switch
                &indices))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);
    PyArray_Descr *int_dtype = PyArray_DescrFromType(NPY_INT);

    /* we need two iterators: one for mesh points (will run it as inner loop)
     * and one for site points (for outer one).
     */

    PyArrayObject *op_s[4] = {slons, slats, sdepths, NULL /* min distance */};
    PyArrayObject *op_m[3] = {mlons, mlats, mdepths};
    npy_uint32 flags_s = 0, flags_m = 0;
    npy_uint32 op_flags_s[4], op_flags_m[3];
    NpyIter_IterNextFunc *iternext_s, *iternext_m;
    PyArray_Descr *op_dtypes_s[] = {double_dtype, double_dtype, double_dtype,
                                    indices ? int_dtype : double_dtype};

    PyArray_Descr *op_dtypes_m[] = {double_dtype, double_dtype, double_dtype};
    char **dataptrarray_s, **dataptrarray_m;

    op_flags_s[0] = op_flags_s[1] = op_flags_s[2] = NPY_ITER_READONLY;
    op_flags_s[3] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;

    NpyIter *iter_s = NpyIter_MultiNew(
            4, op_s, flags_s, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_s, op_dtypes_s);
    Py_DECREF(int_dtype);
    if (iter_s == NULL) {
        Py_DECREF(double_dtype);
        return NULL;
    }
    iternext_s = NpyIter_GetIterNext(iter_s, NULL);
    dataptrarray_s = NpyIter_GetDataPtrArray(iter_s);

    op_flags_m[0] = op_flags_m[1] = op_flags_m[2] = NPY_ITER_READONLY;

    NpyIter *iter_m = NpyIter_MultiNew(
            3, op_m, flags_m, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_m, op_dtypes_m);
    Py_DECREF(double_dtype);
    if (iter_m == NULL) {
        NpyIter_Deallocate(iter_s);
        return NULL;
    }

    iternext_m = NpyIter_GetIterNext(iter_m, NULL);
    dataptrarray_m = NpyIter_GetDataPtrArray(iter_m);

    do
    {
        // iterate sites in the outer loop
        double slon = *(double *) dataptrarray_s[0];
        double slat = *(double *) dataptrarray_s[1];
        double sdepth = *(double *) dataptrarray_s[2];

        // initialize the minimum distance with inf
        double min_dist = INFINITY;
        int min_dist_idx = -1;

        do
        {
            // iterate points of the mesh in the inner one.
            // this loop is executed for each site
            double mlon = *(double *) dataptrarray_m[0];
            double mlat = *(double *) dataptrarray_m[1];
            double mdepth = *(double *) dataptrarray_m[2];

            double geodetic_dist = geodetic__geodetic_distance(
                mlon, mlat, slon, slat);

            double vertical_dist = sdepth - mdepth;
            double dist;
            if (vertical_dist == 0)
                // total distance is the geodetic one
                dist = geodetic_dist;
            else
                // total distance is hypotenuse of geodetic
                // and vertical distance
                dist = sqrt(geodetic_dist * geodetic_dist
                            + vertical_dist * vertical_dist);

            if (dist < min_dist) {
                // distance that we just found is the smallest so far
                min_dist = dist;
                if (indices)
                    // if we are finding indices of closest points --
                    // remember that index
                    min_dist_idx = NpyIter_GetIterIndex(iter_m);
            }

        } while (iternext_m(iter_m));
        NpyIter_Reset(iter_m, NULL);

        // save the result for the current site: either index
        // of the closest point or actual minimum distance
        if (indices)
            *(int *) dataptrarray_s[3] = min_dist_idx;
        else
            *(double *) dataptrarray_s[3] = min_dist;
    } while (iternext_s(iter_s));

    PyArrayObject *result = NpyIter_GetOperandArray(iter_s)[3];
    Py_INCREF(result);
    if (NpyIter_Deallocate(iter_s) != NPY_SUCCEED
            || NpyIter_Deallocate(iter_m) != NPY_SUCCEED) {
        Py_DECREF(result);
        return NULL;
    }

    return (PyObject *) result;
}

/*
 * Module method reference table
 */
static PyMethodDef GeodeticSpeedupsMethods[] = {
    {"min_distance",
            (PyCFunction)geodetic_min_distance,
            METH_VARARGS | METH_KEYWORDS,
            geodetic_min_distance__doc__},

    {NULL, NULL, 0, NULL} /* Sentinel */
};


/*
 * Module initialization function
 */
#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef geodetic_speedups =
{
    PyModuleDef_HEAD_INIT,
    "_geodetic_speedups",         /* name of module */
    geodetic_min_distance__doc__, /* module documentation */
    -1,                           /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    GeodeticSpeedupsMethods
};

PyMODINIT_FUNC
PyInit__geodetic_speedups(void)
#else
PyMODINIT_FUNC
init_geodetic_speedups(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&geodetic_speedups);
#else
    (void) Py_InitModule("_geodetic_speedups", GeodeticSpeedupsMethods);
#endif
    import_array();

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
