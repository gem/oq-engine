#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""\
See https://earthquake.usgs.gov/scenario/product/shakemap-scenario/sclegacyshakeout2full_se/us/1465655085705/about_formats.html
Here is an example of the format
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<shakemap_grid xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://earthquake.usgs.gov/eqcenter/shakemap" xsi:schemaLocation="http://earthquake.usgs.gov http://earthquake.usgs.gov/eqcenter/shakemap/xml/schemas/shakemap.xsd" event_id="us20002926" shakemap_id="us20002926" shakemap_version="9" code_version="3.5.1440" process_timestamp="2015-07-02T22:50:42Z" shakemap_originator="us" map_status="RELEASED" shakemap_event_type="ACTUAL">
<event event_id="us20002926" magnitude="7.8" depth="8.22" lat="28.230500" lon="84.731400" event_timestamp="2015-04-25T06:11:25UTC" event_network="us" event_description="NEPAL" />
<grid_specification lon_min="81.731400" lat_min="25.587500" lon_max="87.731400" lat_max="30.873500" nominal_lon_spacing="0.016667" nominal_lat_spacing="0.016675" nlon="361" nlat="318" />
<event_specific_uncertainty name="pga" value="0.000000" numsta="" />
<event_specific_uncertainty name="pgv" value="0.000000" numsta="" />
<event_specific_uncertainty name="mi" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa03" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa10" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa30" value="0.000000" numsta="" />
<grid_field index="1" name="LON" units="dd" />
<grid_field index="2" name="LAT" units="dd" />
<grid_field index="3" name="PGA" units="pctg" />
<grid_field index="4" name="PGV" units="cms" />
<grid_field index="5" name="MMI" units="intensity" />
<grid_field index="6" name="PSA03" units="pctg" />
<grid_field index="7" name="PSA10" units="pctg" />
<grid_field index="8" name="PSA30" units="pctg" />
<grid_field index="9" name="STDPGA" units="ln(pctg)" />
<grid_field index="10" name="URAT" units="" />
<grid_field index="11" name="SVEL" units="ms" />
<grid_data>
81.7314 30.8735 0.44 2.21 3.83 1.82 2.8 1.26 0.53 1 400.758
81.7481 30.8735 0.47 2.45 3.88 1.99 3.09 1.41 0.52 1 352.659
81.7647 30.8735 0.47 2.4 3.88 1.97 3.04 1.38 0.52 1 363.687
81.7814 30.8735 0.52 2.78 3.96 2.23 3.51 1.64 0.5 1 301.17
</grid_data>
</shakemap_grid>
"""
from urllib.request import urlopen
import numpy
from openquake.baselib.node import node_from_xml
from openquake.hazardlib import geo


F32 = numpy.float32
SHAKEMAP_URL = 'http://shakemap.rm.ingv.it/shake/{}/download/grid.xml'
SHAKEMAP_FIELDS = set(
    'LON LAT SVEL PGA PSA03 PSA10 PSA30 STDPGA STDPSA03 STDPSHA10 STDPSA30'
    .split())


def get_shakemap_array(grid_file):
    """
    :param grid_file: an shakemap file
    :returns: array with fields lon, lat, val, std
    """
    grid_node = node_from_xml(grid_file)
    fields = grid_node.getnodes('grid_field')
    lines = grid_node.grid_data.text.strip().splitlines()
    rows = [line.split() for line in lines]

    # the indices start from 1, hence the -1 below
    idx = {f['name']: int(f['index']) - 1 for f in fields
           if f['name'] in SHAKEMAP_FIELDS}
    out = {name: [] for name in idx}
    has_sa = False
    for name in idx:
        i = idx[name]
        if name.startswith('PSA'):
            has_sa = True
        out[name].append([float(row[i]) for row in rows])
    if has_sa:  # expect SA for 0.3, 1.0 and 3.0
        dt = numpy.dtype([('PGA', F32), ('SA(0.3)', F32), ('SA(1.0)', F32),
                          ('SA(3.0)', F32)])
    else:  # expect only PGA
        dt = numpy.dtype([('PGA', F32)])
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(rows), dtlist)
    data['lon'] = F32(out['LON'])
    data['lat'] = F32(out['LAT'])
    data['val']['PGA'] = F32(out['PGA'])
    data['std']['PGA'] = F32(out['STDPGA'])
    data['vs30'] = F32(out['SVEL'])
    if has_sa:
        data['val']['SA(0.3)'] = F32(out['PSA03'])
        data['val']['SA(1.0)'] = F32(out['PSA10'])
        data['val']['SA(3.0)'] = F32(out['PSA30'])
        data['std']['SA(0.3)'] = F32(out.get('STDPSA03', 0))
        data['std']['SA(1.0)'] = F32(out.get('STDPSA10', 0))
        data['std']['SA(3.0)'] = F32(out.get('STDPSA30', 0))
    return data


def get_shakemap(shakemap_id_or_fname, sitecol, assoc_dist):
    """
    :param shakemap_id_or_fname: shakemap ID or shakemap file

    :returns: a dictionary site_id -> shakemap record
    """
    if isinstance(shakemap_id_or_fname, int):
        with urlopen(SHAKEMAP_URL.format(shakemap_id_or_fname)) as f1:
            array = get_shakemap_array(f1)
    else:
        array = get_shakemap_array(shakemap_id_or_fname)
    bbox = (array['lon'].min(), array['lat'].min(),
            array['lon'].max(), array['lat'].max())
    sitecol = sitecol.within_bb(bbox)
    data = geo.utils.GeographicObjects(array)
    return data.assoc(sitecol, assoc_dist)


def to_shaking(shakemap, imts):
    """
    >>> imts = ['PGA']
    >>> dt = numpy.dtype([(imt, F32) for imt in imts])
    >>> arr = numpy.zeros(1, [('val', dt), ('std', dt)])
    >>> arr['val']['PGA'] = 0.44
    >>> arr['std']['PGA'] = 0.53
    >>> to_shaking({0: arr}, imts)
    array([[-5.5666008]], dtype=float32)
    """
    sids = numpy.array(list(shakemap))
    data = numpy.array(list(shakemap.values()))
    val = data['val']
    std = data['std']
    arr = numpy.zeros((len(val), len(imts)), F32)
    for imti, imt_ in enumerate(imts):
        arr[:, imti] = numpy.log(val[imt_] / 100) - std[imt_] ** 2 / 2.
    return arr


def calculate_spatial_correlation_matrix(
        dmatrix, imts, correlationType):
    """
    :returns: array of shape (M, N, N)
    """
    n = len(dmatrix)
    out = []
    for imt in imts:
        if correlationType == 'no correlation':
            corr = numpy.zeros((n, n))
        if correlationType == 'full correlation':
            corr = numpy.eye(n)
        elif correlationType == 'spatial':
            b = calculate_spatial_length_scale(imt, 'Vs30clustered')
            corr = numpy.eye(n) + numpy.exp(-3 * dmatrix / b)
        out.append(corr)
    return numpy.array(corr)


def calculate_spatial_covariance_matrices(groundShaking, spatialCorrMatrices):
    # this depends on sPGA, sSa03, sSa10, sSa30
    noIMT = len(spatialCorrMatrices)
    n = len(spatialCorrMatrices[0])
    spatialCovMatrices = []
    for i in range(noIMT):
        tempCovMatrix = numpy.zeros((n, n))
        for j in range(n):
            for k in range(n):
                tempCovMatrix[j, k] = spatialCorrMatrices[i, j, k] * \
                    groundShaking[j, 2 + noIMT + i] * \
                    groundShaking[k, 2 + noIMT + i]
        spatialCovMatrices.append(tempCovMatrix)

    return numpy.array(spatialCovMatrices)


def generate_random_fields_ground_motion(
        IMTs, groundShaking, spatialCovMatrices, crossCorrMatrix,
        siteEffects, noSigmas, noGMFs):
    # groundShaking has shape (N, 11) where
    # 11 = lon lat mPGA mSa03 mSa10 mSa30 sPGA sSa03 sSa10 sSa30 Vs30
    n = spatialCovMatrices.shape[1]
    noIMT = crossCorrMatrix.shape[0]
    L = []
    LLT = []
    Z = []

    for i in range(noIMT):
        L.append(numpy.linalg.cholesky(spatialCovMatrices[i]))

    L = numpy.array(L)

    for i in range(noIMT):
        LLTrow = []
        for j in range(noIMT):
            LLTrow.append(
                numpy.dot(L[i], numpy.transpose(L[j])) * crossCorrMatrix[i, j])
        for irow in range(len(LLTrow[0])):
            singleLLTrow = numpy.zeros((int(len(LLTrow) * len(LLTrow[0]))))
            for iL in range(len(LLTrow)):
                singleLLTrow[
                    iL * len(LLTrow[0]):(iL + 1) * len(LLTrow[0])
                ] = LLTrow[iL][irow]
            LLT.append(singleLLTrow)
    LLT = numpy.array(LLT)

    mu = []
    for i in range(noIMT):
        for j in range(n):
            mu.append(numpy.ones(noGMFs) * groundShaking[j][i + 2])
    mu = numpy.array(mu)
    L = (numpy.linalg.cholesky(LLT))
    Z = truncnorm.rvs(-noSigmas, noSigmas, loc=0, scale=1,
                      size=(n * noIMT, noGMFs))

    gmfs = numpy.exp(numpy.dot(L, Z) + mu)

    if siteEffects:  # use vs30 which is the last field
        gmfs = amplifyGMFs(IMTs, groundShaking[:, -1], gmfs) * 0.8

    return gmfs


def amplifyGMFs(IMTs, Vs30s, gmfs):
    n = len(Vs30s)

    for i in range(4):
        if IMTs[i] == 'PGA':
            T = 0.0
        elif IMTs[0:2] == 'SA':
            IMT = IMTs[i]
            T = float(IMT.replace("SA(", "").replace(")", ""))

        for iloc in range(n):
            gmfs[i * n + iloc] = amplify_ground_shaking(
                T, Vs30s[iloc], gmfs[i * n + iloc])

    return gmfs


def calculate_spatial_length_scale(IMT, Vs30Case):
    if IMT == 'PGA':
        T = 0.0
    elif IMT[0:2] == 'SA':
        T = float(IMT.replace("SA(", "").replace(")", ""))

    if T < 1:
        if Vs30Case != 'Vs30clustered':
            b = 8.5 + 17.2 * T
        elif Vs30Case == 'Vs30clustered':
            b = 40.7 - 15.0 * T
    elif T >= 1:
        b = 22.0 + 3.7 * T

    return b


def calculate_distance_2points(point1, point2):
    lon1 = point1[0]
    lon2 = point2[0]
    lat1 = point1[1]
    lat2 = point2[1]

    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon / 2)**2

    distance = 6367 * 2 * math.asin(math.sqrt(a))
    return distance


def amplify_ground_shaking(T, Vs30, IMLs):
    ampFactorsShort = [(760 / Vs30)**0.35,
                       (760 / Vs30)**0.35,
                       (760 / Vs30)**0.25,
                       (760 / Vs30)**0.10,
                       (760 / Vs30)**-0.05,
                       (760 / Vs30)**-0.05]
    ampFactorsMid = [(760 / Vs30)**0.65,
                     (760 / Vs30)**0.65,
                     (760 / Vs30)**0.60,
                     (760 / Vs30)**0.53,
                     (760 / Vs30)**0.45,
                     (760 / Vs30)**0.45]

    if T <= 0.3:
        interpolator = interpolate.interp1d(
            [-1, 0.1, 0.2, 0.3, 0.4, 100],
            ampFactorsShort, kind='linear')
    if T > 0.3:
        interpolator = interpolate.interp1d(
            [-1, 0.1, 0.2, 0.3, 0.4, 100], ampFactorsMid, kind='linear')

    return interpolator(IMLs) * IMLs

"""
here is an example for Tanzania:
https://earthquake.usgs.gov/archive/product/shakemap/us10006nkx/us/1480920466172/download/grid.xml
"""
