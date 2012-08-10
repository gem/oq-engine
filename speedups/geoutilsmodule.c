/*
 nhlib: A New Hazard Library
 Copyright (C) 2012 GEM Foundation

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
#include <numpy/npy_math.h>
#include <math.h>


static const char geoutils_convex_to_point_distance__doc__[] = "\n\
    For each point of the collection calculate the distance to the convex\n\
    polygon, treating points lying inside the polygon as having zero\n\
    distance.\n\
    \n\
    convex_to_point_distance(cxx, cyy, pxx, pyy) -> dists\n\
    \n\
    Parameters cxx and cyy represent coordinates of convex polygon vertices\n\
    in either clockwise or counterclockwise order. The last point must\n\
    repeat the first one.\n\
    \n\
    Parameters pxx, pyy represent coordinates of the point collection.\n\
    Both pairs of coordinates must be numpy arrays of double. They are \n\
    treated as the ones in 2d Cartesian space.\n\
    \n\
    Result is numpy array of doubles -- distance in units of coordinate\n\
    system.\n\
";
static PyObject *
geoutils_convex_to_point_distance(
        PyObject *self,
        PyObject *args,
        PyObject *keywds)
{
    static char *kwlist[] = {"cxx", "cyy", "pxx", "pyy", NULL};

    PyArrayObject *cxx, *cyy, *pxx, *pyy;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!", kwlist,
                &PyArray_Type, &cxx, &PyArray_Type, &cyy,
                &PyArray_Type, &pxx, &PyArray_Type, &pyy))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);

    PyArrayObject *op_c[5];
    npy_uint32 op_flags_c[5];
    npy_uint32 flags_c = 0;
    NpyIter_IterNextFunc *iternext_c;
    PyArray_Descr *op_dtypes_c[] = {double_dtype, double_dtype, double_dtype,
                                    double_dtype, double_dtype};
    char **dataptrarray_c;

    op_c[0] = cxx;
    op_c[1] = cyy;
    op_c[2] = NULL; // length
    op_c[3] = NULL; // cos_theta
    op_c[4] = NULL; // sin_theta

    op_flags_c[0] = op_flags_c[1] = NPY_ITER_READONLY;
    op_flags_c[2] = op_flags_c[3] = op_flags_c[4] \
            = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;
    NpyIter *iter_c = NpyIter_MultiNew(
            5, op_c, flags_c, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_c, op_dtypes_c);
    if (iter_c == NULL) {
        Py_DECREF(double_dtype);
        return NULL;
    }
    iternext_c = NpyIter_GetIterNext(iter_c, NULL);
    dataptrarray_c = NpyIter_GetDataPtrArray(iter_c);

    double cx, cy, prev_cx, prev_cy, length, cos_theta, sin_theta;
    prev_cx = *(double *) dataptrarray_c[0];
    prev_cy = *(double *) dataptrarray_c[1];

    while (iternext_c(iter_c))
    {
        cx = *(double *) dataptrarray_c[0];
        cy = *(double *) dataptrarray_c[1];
        double vx = prev_cx - cx;
        double vy = prev_cy - cy;
        length = sqrt(vx * vx + vy * vy);
        cos_theta = vx / length;
        sin_theta = vy / length;

        *(double *) dataptrarray_c[2] = length;
        *(double *) dataptrarray_c[3] = cos_theta;
        *(double *) dataptrarray_c[4] = sin_theta;

        prev_cx = cx;
        prev_cy = cy;
    };

    PyArrayObject *op_p[3] = {pxx, pyy, NULL /* distance */};
    npy_uint32 op_flags_p[3];
    npy_uint32 flags_p = 0;
    NpyIter_IterNextFunc *iternext_p;
    PyArray_Descr *op_dtypes_p[] = {double_dtype, double_dtype, double_dtype};
    char **dataptrarray_p;

    op_flags_p[0] = op_flags_p[1] = NPY_ITER_READONLY;
    op_flags_p[2] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;

    NpyIter *iter_p = NpyIter_MultiNew(
            3, op_p, flags_p, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_p, op_dtypes_p);

    Py_DECREF(double_dtype);
    if (iter_p == NULL) {
        NpyIter_Deallocate(iter_c);
        return NULL;
    }
    iternext_p = NpyIter_GetIterNext(iter_p, NULL);
    dataptrarray_p = NpyIter_GetDataPtrArray(iter_p);

    do
    {
        char has_lefts = 0;
        char has_rights = 0;
        double min_distance = INFINITY;

        double px = *(double *) dataptrarray_p[0];
        double py = *(double *) dataptrarray_p[1];

        NpyIter_Reset(iter_c, NULL);
        while (iternext_c(iter_c))
        {
            cx = *(double *) dataptrarray_c[0];
            cy = *(double *) dataptrarray_c[1];
            length = *(double *) dataptrarray_c[2];
            cos_theta = *(double *) dataptrarray_c[3];
            sin_theta = *(double *) dataptrarray_c[4];

            double px2 = px - cx;
            double py2 = py - cy;
            double dist_x = px2 * cos_theta + py2 * sin_theta;
            double dist_y = - px2 * sin_theta + py2 * cos_theta;
            double dist;

            has_lefts |= dist_y < 0;
            has_rights |= dist_y > 0;

            if ((0 <= dist_x) && (dist_x <= length)) {
                dist = fabs(dist_y);
            } else {
                if (dist_x > length)
                    dist_x -= length;
                dist = sqrt(dist_x * dist_x + dist_y * dist_y);
            }

            if (dist < min_distance)
                min_distance = dist;
        }

        if ((has_lefts == 0) || (has_rights == 0))
            min_distance = 0;

        *(double *) dataptrarray_p[2] = min_distance;

    } while (iternext_p(iter_p));

    PyArrayObject *result = NpyIter_GetOperandArray(iter_p)[2];
    Py_INCREF(result);
    if (NpyIter_Deallocate(iter_c) != NPY_SUCCEED
            || NpyIter_Deallocate(iter_p) != NPY_SUCCEED) {
        Py_DECREF(result);
        return NULL;
    }

    return (PyObject *) result;
}


static PyMethodDef GeoutilsSpeedupsMethods[] = {
    {"convex_to_point_distance",
            (PyCFunction)geoutils_convex_to_point_distance,
            METH_VARARGS | METH_KEYWORDS,
            geoutils_convex_to_point_distance__doc__},

    {NULL, NULL, 0, NULL} /* Sentinel */
};


PyMODINIT_FUNC
init_utils_speedups(void)
{
    (void) Py_InitModule("_utils_speedups", GeoutilsSpeedupsMethods);
    import_array();
}
