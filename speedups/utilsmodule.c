#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/npy_math.h>
#include <math.h>


static PyObject *
utils_vector_length(PyObject *self, PyObject *args, PyObject *keywds)
{
    static char *kwlist[] = {"vector", "keepdims", NULL};
    PyArrayObject *vector;

    char keepdims = 1;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!|b", kwlist,
                &PyArray_Type, &vector, &keepdims))
        return NULL;

    if (NULL == vector) return NULL;

    if (vector->descr->type_num != NPY_DOUBLE || vector->nd == 0) {
        PyErr_SetString(PyExc_ValueError, "vector_length: expected array of double");
        return NULL;
    }


    npy_intp *dims = malloc(sizeof(npy_intp) * vector->nd);
    memcpy(dims, vector->dimensions, sizeof(npy_intp) * vector->nd);
    dims[vector->nd - 1] = 1;
    PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(vector->nd, dims, NPY_DOUBLE);
    free(dims);

    PyArrayObject *op[2];
    op[0] = vector;
    op[1] = result;
    npy_uint32 op_flags[2];
    op_flags[0] = NPY_ITER_READONLY;
    op_flags[1] = NPY_ITER_READWRITE;


    NpyIter* iter;
    NpyIter_IterNextFunc *iternext;
    npy_intp itemsize, *innersizeptr, innerstride;
    char **dataptrarray;

    /*
     * The iternext function gets stored in a local variable
     * so it can be called repeatedly in an efficient manner.
     */
    /* Construct the iterator */
    npy_uint32 flags = NPY_ITER_EXTERNAL_LOOP \
                       | NPY_ITER_REDUCE_OK \
                       | NPY_ITER_DONT_NEGATE_STRIDES \
                       | NPY_ITER_ZEROSIZE_OK;
    iter = NpyIter_MultiNew(2, op, flags, NPY_KEEPORDER, NPY_NO_CASTING,
                            op_flags, NULL);
    if (iter == NULL) {
        return NULL;
    }


    /*
     * Make a copy of the iternext function pointer and
     * a few other variables the inner loop needs.
     */
    iternext = NpyIter_GetIterNext(iter, NULL);
    innerstride = NpyIter_GetInnerStrideArray(iter)[0];
    itemsize = NpyIter_GetDescrArray(iter)[0]->elsize;
    /*
     * The inner loop size and data pointers may change during the
     * loop, so just cache the addresses.
     */
    innersizeptr = NpyIter_GetInnerLoopSizePtr(iter);
    dataptrarray = NpyIter_GetDataPtrArray(iter);

    double v1, v2;
    npy_intp i;
    /*
     * Note that because the iterator allocated the output,
     * it matches the iteration order and is packed tightly,
     * so we don't need to check it like the input.
     */
    do {
        npy_intp size = *innersizeptr;
        char *src = dataptrarray[0], *dst = dataptrarray[1];
        v2 = 0;
        for(i = 0; i < size; i++, src += innerstride) {
            v1 = *(double *)src;
            v2 += v1 * v1;
        }
        *(double *)dst = sqrt(v2);
    } while (iternext(iter));

    if (keepdims)
        return (PyObject*)result;

    if (vector->nd == 1)
        return PyArray_GETITEM(result, PyArray_GETPTR1(result, 0));

    PyArray_Dims newshape;
    newshape.ptr = result->dimensions;
    newshape.len = result->nd - 1;

    return PyArray_Newshape(result, &newshape, NPY_KEEPORDER);
}


static PyObject *
utils_normalized(PyObject *self, PyObject *args, PyObject *keywds)
{
    static char *kwlist[] = {"vector", NULL};
    PyArrayObject *vector;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!", kwlist,
                &PyArray_Type, &vector))
        return NULL;

    if (NULL == vector) return NULL;

    if (vector->descr->type_num != NPY_DOUBLE || vector->nd == 0) {
        PyErr_SetString(PyExc_ValueError, "normalized: expected array of double");
        return NULL;
    }


    NpyIter *iter;
    NpyIter_IterNextFunc *iternext;
    PyArrayObject *op[2], *ret;
    npy_uint32 flags;
    npy_uint32 op_flags[2];
    npy_intp itemsize, *innersizeptr, innerstride;
    char **dataptrarray;

    /*
     * No inner iteration - inner loop is handled by CopyArray code
     */
    flags = NPY_ITER_EXTERNAL_LOOP;
    /*
     * Tell the constructor to automatically allocate the output.
     * The data type of the output will match that of the input.
     */
    op[0] = vector;
    op[1] = NULL;
    op_flags[0] = NPY_ITER_READONLY;
    op_flags[1] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;

    /* Construct the iterator */
    iter = NpyIter_MultiNew(2, op, flags, NPY_KEEPORDER, NPY_NO_CASTING,
                            op_flags, NULL);
    if (iter == NULL) {
        return NULL;
    }

    /*
     * Make a copy of the iternext function pointer and
     * a few other variables the inner loop needs.
     */
    iternext = NpyIter_GetIterNext(iter, NULL);
    innerstride = NpyIter_GetInnerStrideArray(iter)[0];
    itemsize = NpyIter_GetDescrArray(iter)[0]->elsize;
    /*
     * The inner loop size and data pointers may change during the
     * loop, so just cache the addresses.
     */
    innersizeptr = NpyIter_GetInnerLoopSizePtr(iter);
    dataptrarray = NpyIter_GetDataPtrArray(iter);

    /*
     * Note that because the iterator allocated the output,
     * it matches the iteration order and is packed tightly,
     * so we don't need to check it like the input.
     */
    npy_intp i, i2;
    double v1, v2;

    do {
        npy_intp size = *innersizeptr;
        char *src = dataptrarray[0], *dst = dataptrarray[1];

        i = 0;
        while (i < size) {
            v2 = 0;
            for (i2 = 0; i2 < vector->dimensions[vector->nd - 1]; i2 ++, src += innerstride, dst += itemsize) {
                v1 = *(double *)src;
                v2 += v1 * v1;
                //printf("l1 %e, %e\n", v1, v2);
            }
            i += i2;
            v2 = sqrt(v2);
            src -= i2 * innerstride;
            dst -= i2 * itemsize;
            for (i2 -= 1; i2 >= 0; i2 --, src += innerstride, dst += itemsize) {
                //printf("l2 %e, %e\n", v1, v2);
                if (v2 == 0) {
                    *(double *)dst = 0;
                } else {
                    v1 = *(double *)src;
                    *(double *)dst = v1 / v2;
                }
            }
        }
    } while (iternext(iter));

    /* Get the result from the iterator object array */
    ret = NpyIter_GetOperandArray(iter)[1];
    Py_INCREF(ret);

    if (NpyIter_Deallocate(iter) != NPY_SUCCEED) {
        Py_DECREF(ret);
        return NULL;
    }

    return (PyObject*)ret;
}



static PyObject *
utils_spherical_to_cartesian(PyObject *self, PyObject *args, PyObject *keywds)
{
    static char *kwlist[] = {"lons", "lats", "depths", NULL};
    PyArrayObject *lons, *lats, *depths;
    PyObject *plons, *plats, *pdepths;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOO", kwlist,
                //&PyArray_Type, &lons, &PyArray_Type, &lats, &PyArray_Type, &depths))
                &plons, &plats, &pdepths))
        return NULL;

    if (NULL == plons || NULL == plats || NULL == pdepths) {
        PyErr_SetString(PyExc_ValueError, "spherical_to_cartesian: failed parsing arguments");
        return NULL;
    }


    PyArray_Descr dtype = *PyArray_DescrFromType(NPY_DOUBLE);

    lons = (PyArrayObject*)PyArray_FromAny(plons, &dtype, 0, 0, NPY_CARRAY, NULL);
    lats = (PyArrayObject*)PyArray_FromAny(plats, &dtype, 0, 0, NPY_CARRAY, NULL);

    if (pdepths == Py_None) {
        depths = (PyArrayObject*)PyArray_Zeros(lons->nd, lons->dimensions, &dtype, 0);
    } else {
        depths = (PyArrayObject*)PyArray_FromAny(pdepths, &dtype, 0, 0, NPY_CARRAY, NULL);
    }



    if (lons->nd != lats->nd) {
        PyErr_SetString(PyExc_ValueError, "spherical_to_cartesian: lons and lats arrays should have the same number of dimensions");
        return NULL;
    }
    int i;
    for (i = 0; i < lons->nd; i++) {
        if (lons->dimensions[i] != lats->dimensions[i]) {
            PyErr_SetString(PyExc_ValueError, "spherical_to_cartesian: lons and lats arrays should have the same shape");
            return NULL;
        }
    }

    npy_intp *dims = malloc(sizeof(npy_intp) * (lons->nd + 1));
    memcpy(dims, lons->dimensions, sizeof(npy_intp) * lons->nd);
    dims[lons->nd] = 3;
    PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(lons->nd + 1, dims, NPY_DOUBLE);

    dims[lons->nd] = 1;


    PyArray_Dims newshape;
    newshape.ptr = dims;
    newshape.len = lons->nd + 1;

    lons = (PyArrayObject*)PyArray_Newshape(lons, &newshape, NPY_KEEPORDER);
    lats = (PyArrayObject*)PyArray_Newshape(lats, &newshape, NPY_KEEPORDER);
    depths = (PyArrayObject*)PyArray_Newshape(depths, &newshape, NPY_KEEPORDER);
    free(dims);



    PyArrayObject *op[4];
    op[0] = lons;
    op[1] = lats;
    op[2] = depths;
    op[3] = result;
    npy_uint32 op_flags[4];
    op_flags[0] = NPY_ITER_READONLY;
    op_flags[1] = NPY_ITER_READONLY;
    op_flags[2] = NPY_ITER_READONLY;
    op_flags[3] = NPY_ITER_WRITEONLY;


    NpyIter* iter;
    NpyIter_IterNextFunc *iternext;
    npy_intp itemsize, *innersizeptr, innerstride;
    char **dataptrarray;

    /*
     * The iternext function gets stored in a local variable
     * so it can be called repeatedly in an efficient manner.
     */
    /* Construct the iterator */
    npy_uint32 flags = NPY_ITER_EXTERNAL_LOOP \
                       | NPY_ITER_REDUCE_OK \
                       | NPY_ITER_DONT_NEGATE_STRIDES \
                       | NPY_ITER_ZEROSIZE_OK;
    iter = NpyIter_MultiNew(4, op, flags, NPY_KEEPORDER, NPY_NO_CASTING,
                            op_flags, NULL);
    if (iter == NULL) {
        return NULL;
    }


    /*
     * Make a copy of the iternext function pointer and
     * a few other variables the inner loop needs.
     */
    iternext = NpyIter_GetIterNext(iter, NULL);
    innerstride = NpyIter_GetInnerStrideArray(iter)[0];
    itemsize = NpyIter_GetDescrArray(iter)[0]->elsize;
    /*
     * The inner loop size and data pointers may change during the
     * loop, so just cache the addresses.
     */
    innersizeptr = NpyIter_GetInnerLoopSizePtr(iter);
    dataptrarray = NpyIter_GetDataPtrArray(iter);

    double lon, lat, depth, phi, theta, rr, cos_theta_r;
    double EARTH_RADIUS = 6371.0;
    double to_radians = NPY_PI / 180;
    /*
     * Note that because the iterator allocated the output,
     * it matches the iteration order and is packed tightly,
     * so we don't need to check it like the input.
     */
    do {
        npy_intp size = *innersizeptr;
        char *lonp = dataptrarray[0], *latp = dataptrarray[1];
        char *depthp = dataptrarray[2], *dst = dataptrarray[3];

        lon = *(double *)dataptrarray[0];
        lat = *(double *)dataptrarray[1];
        depth = *(double *)dataptrarray[2];

        phi = lon * to_radians;
        theta = lat * to_radians;
        rr = EARTH_RADIUS - depth;
        cos_theta_r = cos(theta) * rr;

        // X coordinate
        *(double *)dst = cos_theta_r * cos(phi);
        dst += itemsize;

        // Y coordinate
        *(double *)dst = cos_theta_r * sin(phi);
        dst += itemsize;

        // Z coordinate
        *(double *)dst = rr * sin(theta);
    } while (iternext(iter));

    return (PyObject*)result;
}




static PyObject *
utils_point_at(PyObject *self, PyObject *args, PyObject *keywds)
{
    static char *kwlist[] = {"lon", "lat", "azimuth", "distance", NULL};
    PyArrayObject *lons, *lats, *azimuths, *distances;
    PyObject *plons, *plats, *pazimuths, *pdistances;

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOOO", kwlist,
                &plons, &plats, &pazimuths, &pdistances))
        return NULL;

    if (NULL == plons || NULL == plats || NULL == pazimuths || NULL == pdistances) {
        PyErr_SetString(PyExc_ValueError, "point_at: failed parsing arguments");
        return NULL;
    }


    //PyArray_Descr dtype = *PyArray_DescrFromType(NPY_DOUBLE);

    lons = (PyArrayObject*)PyArray_FROMANY(plons, NPY_DOUBLE, 0, 0, 0);
    if (lons == NULL)
        return NULL;
    lats = (PyArrayObject*)PyArray_FROMANY(plats, NPY_DOUBLE, 0, 0, 0);
    if (lats == NULL) {
        Py_DECREF(lons);
        return NULL;
    }
    azimuths = (PyArrayObject*)PyArray_FROMANY(pazimuths, NPY_DOUBLE, 0, 0, 0);
    if (azimuths == NULL) {
        Py_DECREF(lons);
        Py_DECREF(lats);
        return NULL;
    }
    distances = (PyArrayObject*)PyArray_FROMANY(pdistances, NPY_DOUBLE, 0, 0, 0);
    if (distances == NULL) {
        Py_DECREF(lons);
        Py_DECREF(lats);
        Py_DECREF(azimuths);
        return NULL;
    }


    PyArrayObject *op[6];
    op[0] = lons;
    op[1] = lats;
    op[2] = azimuths;
    op[3] = distances;
    op[4] = NULL;
    op[5] = NULL;

    npy_uint32 op_flags[6];
    op_flags[0] = NPY_ITER_READONLY;
    op_flags[1] = NPY_ITER_READONLY;
    op_flags[2] = NPY_ITER_READONLY;
    op_flags[3] = NPY_ITER_READONLY;
    op_flags[4] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;
    op_flags[5] = NPY_ITER_WRITEONLY | NPY_ITER_ALLOCATE;

    NpyIter* iter;
    NpyIter_IterNextFunc *iternext;
    npy_intp *innersizeptr, *innerstride;
    PyArray_Descr **datadescr;
    char **dataptrarray;

    /*
     * The iternext function gets stored in a local variable
     * so it can be called repeatedly in an efficient manner.
     */
    /* Construct the iterator */
    npy_uint32 flags = NPY_ITER_EXTERNAL_LOOP \
                       | NPY_ITER_REDUCE_OK \
                       | NPY_ITER_DONT_NEGATE_STRIDES \
                       | NPY_ITER_ZEROSIZE_OK;
    iter = NpyIter_MultiNew(6, op, flags, NPY_KEEPORDER, NPY_NO_CASTING,
                            op_flags, NULL);
    if (iter == NULL) {
        Py_DECREF(lons);
        Py_DECREF(lats);
        Py_DECREF(azimuths);
        Py_DECREF(distances);
        return NULL;
    }


    /*
     * Make a copy of the iternext function pointer and
     * a few other variables the inner loop needs.
     */
    iternext = NpyIter_GetIterNext(iter, NULL);
    innerstride = NpyIter_GetInnerStrideArray(iter);
    datadescr = NpyIter_GetDescrArray(iter);
    /*
     * The inner loop size and data pointers may change during the
     * loop, so just cache the addresses.
     */
    innersizeptr = NpyIter_GetInnerLoopSizePtr(iter);
    dataptrarray = NpyIter_GetDataPtrArray(iter);

    double lon, lat, azimuth, tc, distance, rlon, rlat;
    double sin_dist, cos_dist, sin_lat, cos_lat, sin_lats, dlon;
    double EARTH_RADIUS = 6371.0;
    double to_radians = NPY_PI / 180;
    int i;
    /*
     * Note that because the iterator allocated the output,
     * it matches the iteration order and is packed tightly,
     * so we don't need to check it like the input.
     */
    do {
        npy_intp size = *innersizeptr;

        char *lonptr = dataptrarray[0], *latptr = dataptrarray[1];
        char *azimuthptr = dataptrarray[2], *distptr = dataptrarray[3];
        char *rlonptr = dataptrarray[4], *rlatptr = dataptrarray[5];

        for(i = 0; i < size; i++,
                lonptr += innerstride[0],
                latptr += innerstride[1],
                azimuthptr += innerstride[2],
                distptr += innerstride[3],
                rlonptr += datadescr[4]->elsize,
                rlatptr += datadescr[5]->elsize) {

            lon = *(double *)lonptr;
            lon *= to_radians;
            lat = *(double *)latptr;
            lat *= to_radians;
            azimuth = *(double *)azimuthptr;
            tc = (360 - azimuth) * to_radians;

            distance = *(double *)distptr;
            sin_dist = sin(distance / EARTH_RADIUS);
            cos_dist = cos(distance / EARTH_RADIUS);
            sin_lat = sin(lat);
            cos_lat = cos(lat);

            sin_lats = sin_lat * cos_dist + cos_lat * sin_dist * cos(tc);
            if (sin_lats < -1)
                sin_lats = -1;
            else if (sin_lats > 1)
                sin_lats = 1;
            rlat = asin(sin_lats) / to_radians;

            dlon = atan2(sin(tc) * sin_dist * cos_lat, cos_dist - sin_lat * sin_lats);
            rlon = fmod(lon - dlon + NPY_PI, 2 * NPY_PI) - NPY_PI;
            rlon /= to_radians;

            *(double *) rlonptr = rlon;
            *(double *) rlatptr = rlat;
        }
    } while (iternext(iter));

    PyArrayObject* rlons = NpyIter_GetOperandArray(iter)[4];
    Py_INCREF(rlons);
    PyArrayObject* rlats = NpyIter_GetOperandArray(iter)[5];
    Py_INCREF(rlats);

    if (NpyIter_Deallocate(iter) != NPY_SUCCEED) {
        Py_DECREF(rlons);
        Py_DECREF(rlats);
        return NULL;
    }

    Py_DECREF(lons);
    Py_DECREF(lats);
    Py_DECREF(azimuths);
    Py_DECREF(distances);

    PyObject* ret = Py_BuildValue("(OO)", rlons, rlats);
    if (ret == NULL) {
        Py_DECREF(rlons);
        Py_DECREF(rlats);
        return NULL;
    }
    return ret;
}



static PyMethodDef UtilsSpeedupsMethods[] = {
    {"vector_length",  (PyCFunction)utils_vector_length, METH_VARARGS | METH_KEYWORDS,
     "return length of the vector (vectors)."},

    {"normalized",  (PyCFunction)utils_normalized, METH_VARARGS | METH_KEYWORDS,
     "Normalize vector (vectors)."},

    {"spherical_to_cartesian", (PyCFunction)utils_spherical_to_cartesian, METH_VARARGS | METH_KEYWORDS,
     "Convert spherical coordinates to cartesian ones."},

    {"point_at", (PyCFunction)utils_point_at, METH_VARARGS | METH_KEYWORDS,
     "Point at a given distance and azimuth"},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_utils_speedups(void)
{
    (void) Py_InitModule("_utils_speedups", UtilsSpeedupsMethods);
    import_array();
}
