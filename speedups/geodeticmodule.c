#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/npy_math.h>
#include <math.h>

#define EARTH_RADIUS 6371.0


/*
 * Calculate the distance between two points along the geodetic.
 * Parameters are two pairs of spherical coordinates in radians.
 */
static inline double
geodetic__geodetic_distance(double lon1, double lat1, double lon2, double lat2)
{
    return asin(sqrt(
        pow(sin((lat1 - lat2) / 2.0), 2.0)
        + cos(lat1) * cos(lat2) * pow(sin((lon1 - lon2) / 2.0), 2.0)
    )) * 2 * EARTH_RADIUS;
}


static const char geodetic_geodetic_distance__doc__[] = "\n\
    Calculate the geodetic distance between two collections of points,\n\
    following the numpy broadcasting rules.\n\
    \n\
    geodetic_distance(lons1, lats1, lons2, lats2) -> dists\n\
    \n\
    Parameters must be numpy arrays of double, representing spherical\n\
    coordinates in radians.\n\
";
static PyObject *
geodetic_geodetic_distance(
        PyObject *self,
        PyObject *args,
        PyObject *keywds)
{
    static char *kwlist[] = {"lons1", "lats1", "lons2", "lats2", NULL};

    PyArrayObject *lons1, *lats1, *lons2, *lats2;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!", kwlist,
                &PyArray_Type, &lons1, &PyArray_Type, &lats1,
                &PyArray_Type, &lons2, &PyArray_Type, &lats2))
        return NULL;

    PyArrayObject *op[5] = {lons1, lats1, lons2, lats2, NULL /* distance */};
    npy_uint32 flags = 0;
    npy_uint32 op_flags[5];
    NpyIter_IterNextFunc *iternext;
    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);
    PyArray_Descr *op_dtypes[] = {double_dtype, double_dtype,
                                  double_dtype, double_dtype,
                                  double_dtype};
    char **dataptrarray;

    op_flags[0] = op_flags[1] = op_flags[2] = op_flags[3] = NPY_ITER_READONLY;
    op_flags[4] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;

    NpyIter *iter = NpyIter_MultiNew(
            5, op, flags, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags, op_dtypes);
    Py_DECREF(double_dtype);
    if (iter == NULL)
        return NULL;

    iternext = NpyIter_GetIterNext(iter, NULL);
    dataptrarray = NpyIter_GetDataPtrArray(iter);
    do
    {
        double lon1 = *(double *) dataptrarray[0];
        double lat1 = *(double *) dataptrarray[1];
        double lon2 = *(double *) dataptrarray[2];
        double lat2 = *(double *) dataptrarray[3];
        *(double *) dataptrarray[4] = geodetic__geodetic_distance(
                lon1, lat1, lon2, lat2);
    } while (iternext(iter));

    PyArrayObject *result = NpyIter_GetOperandArray(iter)[4];
    Py_INCREF(result);
    if (NpyIter_Deallocate(iter) != NPY_SUCCEED) {
        Py_DECREF(result);
        return NULL;
    }

    return (PyObject *) result;
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
    static char *kwlist[] = {"mlons", "mlats", "mdepths",
                             "slons", "slats", "sdepths",
                             "indices", NULL};

    PyArrayObject *mlons, *mlats, *mdepths, *slons, *slats, *sdepths;
    unsigned char indices = 0;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!O!O!b", kwlist,
                &PyArray_Type, &mlons, &PyArray_Type, &mlats,
                &PyArray_Type, &mdepths,
                &PyArray_Type, &slons, &PyArray_Type, &slats,
                &PyArray_Type, &sdepths,
                &indices))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);
    PyArray_Descr *int_dtype = PyArray_DescrFromType(NPY_INT);

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
        double slon = *(double *) dataptrarray_s[0];
        double slat = *(double *) dataptrarray_s[1];
        double sdepth = *(double *) dataptrarray_s[2];
        double min_dist = INFINITY;
        int min_dist_idx = -1;

        do
        {
            double mlon = *(double *) dataptrarray_m[0];
            double mlat = *(double *) dataptrarray_m[1];
            double mdepth = *(double *) dataptrarray_m[2];

            double geodetic_dist = geodetic__geodetic_distance(
                mlon, mlat, slon, slat);

            double vertical_dist = sdepth - mdepth;
            double dist;
            if (vertical_dist == 0)
                dist = geodetic_dist;
            else
                dist = sqrt(geodetic_dist * geodetic_dist
                            + vertical_dist * vertical_dist);

            if (dist < min_dist) {
                min_dist = dist;
                if (indices)
                    min_dist_idx = NpyIter_GetIterIndex(iter_m);
            }

        } while (iternext_m(iter_m));
        NpyIter_Reset(iter_m, NULL);

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


static const char geodetic_convex_to_point_distance__doc__[] = "\n\
    For each point of the collection calculate the distance to the convex\n\
    polygon, treating points lying inside the polygon as having zero\n\
    distance.\n\
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
geodetic_convex_to_point_distance(
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


static PyMethodDef GeodeticSpeedupsMethods[] = {
    {"geodetic_distance",
            (PyCFunction)geodetic_geodetic_distance,
            METH_VARARGS | METH_KEYWORDS,
            geodetic_geodetic_distance__doc__},
    {"min_distance",
            (PyCFunction)geodetic_min_distance,
            METH_VARARGS | METH_KEYWORDS,
            geodetic_min_distance__doc__},
    {"convex_to_point_distance",
            (PyCFunction)geodetic_convex_to_point_distance,
            METH_VARARGS | METH_KEYWORDS,
            geodetic_convex_to_point_distance__doc__},

    {NULL, NULL, 0, NULL} /* Sentinel */
};


PyMODINIT_FUNC
init_geodetic_speedups(void)
{
    (void) Py_InitModule("_geodetic_speedups", GeodeticSpeedupsMethods);
    import_array();
}
