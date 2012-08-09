#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/npy_math.h>
#include <math.h>

#define EARTH_RADIUS 6371.0


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

    PyArrayObject *op[5];
    npy_uint32 flags;
    npy_uint32 op_flags[5];
    NpyIter_IterNextFunc *iternext;
    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);
    PyArray_Descr *op_dtypes[] = {
            double_dtype, double_dtype,
            double_dtype, double_dtype,
            double_dtype};
    char **dataptrarray;

    flags = 0;
    op[0] = lons1;
    op[1] = lats1;
    op[2] = lons2;
    op[3] = lats2;
    op[4] = NULL;
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
        double register lon1 = *(double *) dataptrarray[0];
        double register lat1 = *(double *) dataptrarray[1];
        double register lon2 = *(double *) dataptrarray[2];
        double register lat2 = *(double *) dataptrarray[3];
        double *res = (double *) dataptrarray[4];

        *res = 2 * EARTH_RADIUS * asin(sqrt(
            pow(sin((lat1 - lat2) / 2.0), 2.0)
            + cos(lat1) * cos(lat2) * pow(sin((lon1 - lon2) / 2.0), 2.0)
        ));
    } while (iternext(iter));

    PyArrayObject *result = NpyIter_GetOperandArray(iter)[4];
    Py_INCREF(result);
    if (NpyIter_Deallocate(iter) != NPY_SUCCEED) {
        Py_DECREF(result);
        return NULL;
    }

    return (PyObject *) result;
}


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

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!O!O!|b", kwlist,
                &PyArray_Type, &mlons, &PyArray_Type, &mlats,
                &PyArray_Type, &mdepths,
                &PyArray_Type, &slons, &PyArray_Type, &slats,
                &PyArray_Type, &sdepths,
                &indices))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);
    PyArray_Descr *int_dtype = PyArray_DescrFromType(NPY_INT);

    PyArrayObject *op_s[4], *op_m[3];
    npy_uint32 flags_s, flags_m;
    npy_uint32 op_flags_s[4], op_flags_m[3];
    NpyIter_IterNextFunc *iternext_s, *iternext_m;
    PyArray_Descr *op_dtypes_s[] = {double_dtype, double_dtype, double_dtype,
                                    indices ? int_dtype : double_dtype};

    PyArray_Descr *op_dtypes_m[] = {double_dtype, double_dtype, double_dtype};
    char **dataptrarray_s, **dataptrarray_m;

    flags_s = 0;
    op_s[0] = slons;
    op_s[1] = slats;
    op_s[2] = sdepths;
    op_s[3] = NULL;
    op_flags_s[0] = op_flags_s[1] = op_flags_s[2] = NPY_ITER_READONLY;
    op_flags_s[3] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;
    NpyIter *iter_s = NpyIter_MultiNew(
            4, op_s, flags_s, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_s, op_dtypes_s);
    if (iter_s == NULL) {
        Py_DECREF(double_dtype);
        Py_DECREF(int_dtype);
        return NULL;
    }
    iternext_s = NpyIter_GetIterNext(iter_s, NULL);
    dataptrarray_s = NpyIter_GetDataPtrArray(iter_s);

    flags_m = 0;
    op_m[0] = mlons;
    op_m[1] = mlats;
    op_m[2] = mdepths;
    op_flags_m[0] = op_flags_m[1] = op_flags_m[2] = NPY_ITER_READONLY;
    NpyIter *iter_m = NpyIter_MultiNew(
            3, op_m, flags_m, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_m, op_dtypes_m);
    Py_DECREF(double_dtype);
    Py_DECREF(int_dtype);
    if (iter_m == NULL) {
        NpyIter_Deallocate(iter_s);
        return NULL;
    }
    iternext_m = NpyIter_GetIterNext(iter_m, NULL);
    dataptrarray_m = NpyIter_GetDataPtrArray(iter_m);

    do
    {
        double register slon = *(double *) dataptrarray_s[0];
        double register slat = *(double *) dataptrarray_s[1];
        double register sdepth = *(double *) dataptrarray_s[2];
        double register min_dist = INFINITY;
        int min_dist_idx = -1;

        do
        {
            // TODO: precompute cos(mlat)
            double register mlon = *(double *) dataptrarray_m[0];
            double register mlat = *(double *) dataptrarray_m[1];
            double register mdepth = *(double *) dataptrarray_m[2];

            double register geodetic_dist = asin(sqrt(
                pow(sin((mlat - slat) / 2.0), 2.0)
                + cos(mlat) * cos(slat) * pow(sin((mlon - slon) / 2.0), 2.0)
            )) * 2 * EARTH_RADIUS;

            double register vertical_dist = sdepth - mdepth;
            double register dist;
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
    npy_uint32 flags_c;
    NpyIter_IterNextFunc *iternext_c;
    PyArray_Descr *op_dtypes_c[] = {double_dtype, double_dtype, double_dtype,
                                    double_dtype, double_dtype};
    char **dataptrarray_c;

    flags_c = 0;
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

    double register cx, cy, prev_cx, prev_cy, length, cos_theta, sin_theta;
    prev_cx = *(double *) dataptrarray_c[0];
    prev_cy = *(double *) dataptrarray_c[1];

    while (iternext_c(iter_c))
    {
        cx = *(double *) dataptrarray_c[0];
        cy = *(double *) dataptrarray_c[1];
        double register vx = prev_cx - cx;
        double register vy = prev_cy - cy;
        length = sqrt(vx * vx + vy * vy);
        cos_theta = vx / length;
        sin_theta = vy / length;

        *(double *) dataptrarray_c[2] = length;
        *(double *) dataptrarray_c[3] = cos_theta;
        *(double *) dataptrarray_c[4] = sin_theta;

        prev_cx = cx;
        prev_cy = cy;
    };

    PyArrayObject *op_p[3];
    npy_uint32 op_flags_p[3];
    npy_uint32 flags_p;
    NpyIter_IterNextFunc *iternext_p;
    PyArray_Descr *op_dtypes_p[] = {double_dtype, double_dtype, double_dtype};
    char **dataptrarray_p;

    flags_p = 0;
    op_p[0] = pxx;
    op_p[1] = pyy;
    op_p[2] = NULL; // distance

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
        char register has_lefts = 0;
        char register has_rights = 0;
        double register min_distance = INFINITY;

        double register px = *(double *) dataptrarray_p[0];
        double register py = *(double *) dataptrarray_p[1];

        NpyIter_Reset(iter_c, NULL);
        while (iternext_c(iter_c))
        {
            cx = *(double *) dataptrarray_c[0];
            cy = *(double *) dataptrarray_c[1];
            length = *(double *) dataptrarray_c[2];
            cos_theta = *(double *) dataptrarray_c[3];
            sin_theta = *(double *) dataptrarray_c[4];

            double register px2 = px - cx;
            double register py2 = py - cy;
            double register dist_x = px2 * cos_theta + py2 * sin_theta;
            double register dist_y = - px2 * sin_theta + py2 * cos_theta;
            double register dist;

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
        "TBD"},
    {"min_geodetic_distance",
        (PyCFunction)geodetic_min_geodetic_distance,
        METH_VARARGS | METH_KEYWORDS,
        "TBD"},
    {"min_distance",
        (PyCFunction)geodetic_min_distance,
        METH_VARARGS | METH_KEYWORDS,
        "TBD"},
    {"convex_to_point_distance",
        (PyCFunction)geodetic_convex_to_point_distance,
        METH_VARARGS | METH_KEYWORDS,
        "TBD"},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_geodetic_speedups(void)
{
    (void) Py_InitModule("_geodetic_speedups", GeodeticSpeedupsMethods);
    import_array();
}
