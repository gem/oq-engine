#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/npy_math.h>
#include <math.h>

#define RAD(x) ((x) * M_PI / 180)
#define EARTH_RADIUS 6371


static PyObject *
geodetic_min_geodetic_distance(
        PyObject *self,
        PyObject *args,
        PyObject *keywds)
{
    static char *kwlist[] = {"mlons", "mlats", "slons", "slats", NULL};

    PyArrayObject *mlons, *mlats, *slons, *slats;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!O!O!O!", kwlist,
                &PyArray_Type, &mlons, &PyArray_Type, &mlats,
                &PyArray_Type, &slons, &PyArray_Type, &slats))
        return NULL;

    PyArray_Descr *double_dtype = PyArray_DescrFromType(NPY_DOUBLE);

    PyArrayObject *op_s[3], *op_m[2];
    npy_uint32 flags_s, flags_m;
    npy_uint32 op_flags_s[3], op_flags_m[2];
    NpyIter_IterNextFunc *iternext_s, *iternext_m;
    PyArray_Descr *op_dtypes_s[] = {double_dtype, double_dtype, double_dtype};
    PyArray_Descr *op_dtypes_m[] = {double_dtype, double_dtype};
    char **dataptrarray_s, **dataptrarray_m;


    flags_s = 0;
    op_s[0] = slons;
    op_s[1] = slats;
    op_s[2] = NULL;
    op_flags_s[0] = op_flags_s[1] = NPY_ITER_READONLY;
    op_flags_s[2] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;
    NpyIter *iter_s = NpyIter_MultiNew(
            3, op_s, flags_s, NPY_KEEPORDER, NPY_NO_CASTING,
            op_flags_s, op_dtypes_s);
    if (iter_s == NULL) {
        Py_DECREF(double_dtype);
        return NULL;
    }
    iternext_s = NpyIter_GetIterNext(iter_s, NULL);
    dataptrarray_s = NpyIter_GetDataPtrArray(iter_s);

    flags_m = 0;
    op_m[0] = mlons;
    op_m[1] = mlats;
    op_flags_m[0] = op_flags_m[1] = NPY_ITER_READONLY;
    NpyIter *iter_m = NpyIter_MultiNew(
            2, op_m, flags_m, NPY_KEEPORDER, NPY_NO_CASTING,
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
        double register slon = RAD(*(double *) dataptrarray_s[0]);
        double register slat = RAD(*(double *) dataptrarray_s[1]);
        double *res = (double *) dataptrarray_s[2];
        double register min_dist = INFINITY;

        do
        {
            // TODO: precompute mlons/mlats in radians, precompute cos(mlat)
            double register mlon = RAD(*(double *) dataptrarray_m[0]);
            double register mlat = RAD(*(double *) dataptrarray_m[1]);

            double register dist = asin(sqrt(
                pow(sin((mlat - slat) / 2.0), 2.0)
                + cos(mlat) * cos(slat) * pow(sin((mlon - slon) / 2.0), 2.0)
            ));
            if (dist < min_dist)
                min_dist = dist;

        } while (iternext_m(iter_m));
        NpyIter_Reset(iter_m, NULL);

        *res = min_dist * 2 * EARTH_RADIUS;
    } while (iternext_s(iter_s));

    PyArrayObject *result = NpyIter_GetOperandArray(iter_s)[2];
    Py_INCREF(result);
    if (NpyIter_Deallocate(iter_s) != NPY_SUCCEED
            || NpyIter_Deallocate(iter_m) != NPY_SUCCEED) {
        Py_DECREF(result);
        return NULL;
    }

    return (PyObject *) result;
}


static PyMethodDef GeodeticSpeedupsMethods[] = {
    {"min_geodetic_distance",
        (PyCFunction)geodetic_min_geodetic_distance,
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
