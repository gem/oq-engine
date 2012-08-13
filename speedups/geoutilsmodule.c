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
    static char *kwlist[] = {"cxx", "cyy", /* convex coords */
                             "pxx", "pyy", /* points coords */
                             NULL}; /* sentinel */

    PyArrayObject *cxx, *cyy, *pxx, *pyy;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!", kwlist,
                // convex coords
                &PyArray_Type, &cxx, &PyArray_Type, &cyy,
                // points coords
                &PyArray_Type, &pxx, &PyArray_Type, &pyy))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);

    // we use the first iterator ("*_c", for "convex") for iterating over
    // edges of the convex.
    PyArrayObject *op_c[5];
    npy_uint32 op_flags_c[5];
    npy_uint32 flags_c = 0;
    NpyIter_IterNextFunc *iternext_c;
    PyArray_Descr *op_dtypes_c[] = {double_dtype, double_dtype, double_dtype,
                                    double_dtype, double_dtype};
    char **dataptrarray_c;

    op_c[0] = cxx;
    op_c[1] = cyy;
    op_c[2] = NULL; /* length of the edge */
    op_c[3] = NULL; /* cos theta (angle between x-axis and the
                       edge, counterclockwise) */
    op_c[4] = NULL; /* sin theta */

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
    // remember the "end point" of the first segment
    prev_cx = *(double *) dataptrarray_c[0];
    prev_cy = *(double *) dataptrarray_c[1];

    // here we ignore the first iteration, this is intensional: we need
    // to iterate over edges, not points
    while (iternext_c(iter_c))
    {
        // cx and cy are coordinates of the "base point" of the current edge
        // vector, prev_cx and prev_cy are ones of the "end point" of it
        cx = *(double *) dataptrarray_c[0];
        cy = *(double *) dataptrarray_c[1];
        // get the free vector coordinates from the bound one
        double vx = prev_cx - cx;
        double vy = prev_cy - cy;
        // calculate the length of the edge
        length = sqrt(vx * vx + vy * vy);
        // calculate cosine and sine of the angle between x-axis
        // and the free vector, measured counterclockwise
        cos_theta = vx / length;
        sin_theta = vy / length;

        *(double *) dataptrarray_c[2] = length;
        *(double *) dataptrarray_c[3] = cos_theta;
        *(double *) dataptrarray_c[4] = sin_theta;

        // the "base point" of the current vector is in turn the "end point"
        // of the next one
        prev_cx = cx;
        prev_cy = cy;
    };

    // second iterator is over the target points.
    // we will collect distance in it as well.
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
        // loop over points

        // point lies on left hand side from some edges of the polygon
        char has_lefts = 0;
        // same for right hand side
        char has_rights = 0;
        // minimum distance found
        double min_distance = INFINITY;

        double px = *(double *) dataptrarray_p[0];
        double py = *(double *) dataptrarray_p[1];

        NpyIter_Reset(iter_c, NULL);
        while (iternext_c(iter_c))
        {
            // loop over edges: again ignore the first iteration
            cx = *(double *) dataptrarray_c[0];
            cy = *(double *) dataptrarray_c[1];
            length = *(double *) dataptrarray_c[2];
            cos_theta = *(double *) dataptrarray_c[3];
            sin_theta = *(double *) dataptrarray_c[4];

            // now move the point to the coordinate space of the edge (where
            // "base point" of the edge has coordinates (0, 0) and the edge
            // itself goes along x axis) using affine transformations

            // first translate the coordinates
            double px2 = px - cx;
            double py2 = py - cy;
            // then rotate them
            double dist_x = px2 * cos_theta + py2 * sin_theta;
            double dist_y = - px2 * sin_theta + py2 * cos_theta;
            // now dist_y is the perpendicular distance between the point
            // and the line, containing the edge. it is negative in case
            // when point lies on the right hand side of the edge vector.
            // dist_x is the 1d coordinate of the projection of the point
            // on that line. sign is negative if the projection is on the
            // opposite side from the "end point" of the vector with respect
            // to its "base point"

            double dist;

            // if point lies on the left hand side of the vector,
            // set has_lefts to true
            has_lefts |= dist_y > 0;
            // same for right hand side and has_rights
            has_rights |= dist_y < 0;

            if ((0 <= dist_x) && (dist_x <= length)) {
                // if point projection falls inside the vector itself,
                // the actual shortest distance to the vector is dist_y
                dist = fabs(dist_y);
            } else {
                // otherwise we need to consider both dist_x and dist_y,
                // combining them in Pythagorean formula
                if (dist_x > length)
                    // point lies above the "end point" of the vector
                    // along the line, so closest x-distance to the vector
                    // is the distance to the end point
                    dist_x -= length;
                dist = sqrt(dist_x * dist_x + dist_y * dist_y);
            }

            if (dist < min_distance)
                // update the "minimum distance so far" variable if needed
                min_distance = dist;
        }

        if ((has_lefts == 0) || (has_rights == 0))
            // point lies inside the polygon if it is either on the right
            // hand side or on the left hand side of all its edges. note
            // that it is only true for convex polygons.
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


/*
 * Module method reference table
 */
static PyMethodDef GeoutilsSpeedupsMethods[] = {
    {"convex_to_point_distance",
            (PyCFunction)geoutils_convex_to_point_distance,
            METH_VARARGS | METH_KEYWORDS,
            geoutils_convex_to_point_distance__doc__},

    {NULL, NULL, 0, NULL} /* Sentinel */
};


/*
 * Module initialization function
 */
PyMODINIT_FUNC
init_utils_speedups(void)
{
    (void) Py_InitModule("_utils_speedups", GeoutilsSpeedupsMethods);
    import_array();
}
