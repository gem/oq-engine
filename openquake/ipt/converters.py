# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import gc
import re
import csv
import logging
import tempfile
import shutil
import numpy
from zipfile import ZipFile
from osgeo import gdal, ogr, osr
from pyproj import Proj, transform

try:
    from multienv_common import VolConst
except ImportError:
    from openquake.ipt.multienv_common import VolConst

from openquake.ipt.common import (
    get_full_path, get_tmp_path, zwrite_or_collect)


def gem_raster2polyg(hea, epsg_in, raster, csv_filepath):
    driver = dst_ds = sourceBand = srs_in = transform = outband = None
    sourceBand = outDatasource = outLayer = newField = multi = None
    geom = wkt = None

    try:
        dst_filename = 'rast_gen_out.vrt'

        driver = gdal.GetDriverByName("MEM")

        dst_ds = driver.Create(dst_filename,
                               xsize=hea['ncols'],
                               ysize=hea['nrows'],
                               bands=1, eType=gdal.GDT_Float32)

        srs_in = osr.SpatialReference()
        srs_in.ImportFromEPSG(int(epsg_in))

        epsg = 4326
        srs = osr.SpatialReference()
        if int(gdal.VersionInfo("VERSION_NUM")[0]) >= 3:
            # GDAL 3 changes axis order:
            #          https://github.com/OSGeo/gdal/issues/1546
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        srs.ImportFromEPSG(epsg)

        transform = None
        if not srs_in.IsSame(srs) or (
                int(gdal.VersionInfo("VERSION_NUM")[0]) >= 3):
            transform = osr.CoordinateTransformation(
                srs_in, srs)

        pixw = hea['cellsize']

        dst_ds.SetGeoTransform((
            hea['xllcorner'],
            pixw, 0,
            hea['yllcorner'] + float(pixw * hea['nrows']),
            0, -pixw))

        dst_ds.SetProjection(srs_in.ExportToWkt())
        outband = dst_ds.GetRasterBand(1)
        outband.WriteArray(raster)
        outband.FlushCache()

        # Once we're done, close properly the dataset

        sourceBand = dst_ds.GetRasterBand(1)
        sourceBand.SetNoDataValue(0.0)
        sourceBand.WriteRaster(
            0, 0, hea['ncols'], hea['nrows'],
            sourceBand.ReadRaster())

        driver = ogr.GetDriverByName("Memory")
        outDatasource = driver.CreateDataSource('poly_ds')
        outLayer = outDatasource.CreateLayer("polygonized", srs=srs)

        newField = ogr.FieldDefn('poly', ogr.OFTReal)
        outLayer.CreateField(newField)

        gdal.Polygonize(sourceBand, sourceBand, outLayer, -1, [],
                        callback=None)

        multi = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in outLayer:
            geom = feature.GetGeometryRef()
            if transform:
                geom.Transform(transform)

            geom.FlattenTo2D()
            wkt = geom.ExportToWkt()
            multi.AddGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))

        with open(csv_filepath, 'w', newline='') as f_out:
            f_out.write('geom\n"')
            f_out.write(str(multi))
            f_out.write('"\n')
    finally:
        driver = dst_ds = sourceBand = srs_in = transform = None
        sourceBand = outDatasource = outLayer = newField = multi = None
        outband = geom = wkt = None
        gc.collect()


class TransToWGS84(object):
    def __init__(self, epsg_in):
        self.proj_in = Proj(init='epsg:%s' % epsg_in)
        self.proj_out = Proj(init='epsg:%s' % VolConst.epsg_out)

    def coord(self, x_in, y_in):
        x_out, y_out = transform(self.proj_in, self.proj_out,
                                 x_in, y_in)
        return (x_out, y_out)


def gem_esritxt2wkt_coreconv(input_filepath, csv_filepath,
                             epsg_in, density, nodata_extra=None):
    if nodata_extra is None:
        nodata_extra = []

    hea = {'ncols': None,
           'nrows': None,
           'xllcorner': None,
           'yllcorner': None,
           'cellsize': None,
           'nodata_value': None}

    is_head = True
    row_ct = 0
    with open(input_filepath, "r") as f:
        for row_s in f:
            row = re.split(r'[\s]\s*', row_s)
            if is_head:
                if row[0].lower() in hea:
                    hea[row[0].lower()] = row[1]
                    continue
                else:
                    raster = numpy.zeros(
                        (
                            int(hea['nrows']),
                            int(hea['ncols'])
                        ),
                        dtype=numpy.float32)

                    hea['xllcorner'] = float(hea['xllcorner'])
                    hea['yllcorner'] = float(hea['yllcorner'])
                    hea['cellsize'] = float(hea['cellsize'])
                    hea['ncols'] = int(hea['ncols'])
                    hea['nrows'] = int(hea['nrows'])
                    hea['nodata_value'] = float(
                        hea['nodata_value'])
                    is_head = False

            if not is_head:
                for i in range(0, len(row)):
                    if row[i].strip() == "":
                        continue
                    row[i] = (1.0 if (
                        float(row[i]) != hea['nodata_value']
                        and row[i] not in nodata_extra) else 0.0)
                raster[row_ct] = row[0:hea['ncols']]
                row_ct += 1
                if row_ct >= hea['nrows']:
                    break

    gem_raster2polyg(hea, epsg_in, raster, csv_filepath)


def gem_esritxt_coreconv(input_filepath, csv_filepath, epsg_in,
                         density):
    raster = gdal.Open(input_filepath)
    rasterArray = raster.ReadAsArray()
    lon, lon_delta, _, lat, _, lat_delta = raster.GetGeoTransform()

    trans = None
    if epsg_in != VolConst.epsg_out:
        trans = TransToWGS84(epsg_in)

    with open(csv_filepath, 'w', newline='') as csv_fout:
        csv_out = csv.writer(csv_fout)
        csv_out.writerow(['lon', 'lat', 'intensity'])

        lat_out = lat + (lat_delta / 2.0)
        for row in rasterArray:
            lon_out = lon + (lon_delta / 2.0)
            for el in row:
                if float(el) <= 0.0:
                    continue
                if trans:
                    # original coordinates
                    # transformed to EPGS:4326 using pyproj
                    lon_out, lat_out = trans.coord(lon_out, lat_out)

                if density is not None:
                    el = ((float(density) * VolConst.g *
                           (float(el) / 1000.)) / 1000.)

                row_out = ["%.5f" % lon_out, "%.5f" % lat_out,
                           "%.5f" % el]
                csv_out.writerow(row_out)

                lon_out += lon_delta
            lat_out += lat_delta


def gem_titan2_coreconv(input_filepath, csv_filepath, epsg_in):
    trans = None
    if epsg_in != VolConst.epsg_out:
        trans = TransToWGS84(epsg_in)

    with open(input_filepath, 'r', newline='') as file_in, open(
            csv_filepath, 'w', newline='') as csv_fout:
        csv_out = csv.writer(csv_fout)
        csv_out.writerow(['lon', 'lat', 'intensity'])

        line1 = file_in.readline()
        ret = re.search(
            '^Nx=([0-9]+): X={[ 	]*([0-9]+),[ 	]*([0-9]+)',
            line1)

        ret1_grp = ret.groups()
        if len(ret1_grp) != 3:
            raise ValueError(
                'Malformed Titan2 first line header [%s]' % line1)
        cols_n = int(ret1_grp[0])
        x_min = float(ret1_grp[1])
        x_max = float(ret1_grp[2])

        line2 = file_in.readline()
        ret = re.search(
            '^Ny=([0-9]+): Y={[ 	]*([0-9]+),[ 	]*([0-9]+)',
            line2)

        ret2_grp = ret.groups()
        if len(ret2_grp) != 3:
            raise ValueError(
                'Malformed Titan2 second line header [%s]' % line2)
        rows_n = int(ret1_grp[0])
        y_min = float(ret1_grp[1])
        y_max = float(ret1_grp[2])

        x_step = float((x_max - x_min) / float(cols_n))
        y_step = float((y_max - y_min) / float(rows_n))

        line3 = file_in.readline()
        ret = re.search(r'^(Pileheight=)\s*', line3)

        ret3_grp = ret.groups()
        if len(ret3_grp) != 1:
            raise ValueError(
                'Malformed Titan2 third line header [%s]' % line3)

        x_cur = 0
        y_cur = 0
        for row in file_in:
            for el in re.split(r'\s+', row.strip()):
                if float(el) <= 0.0:
                    x_cur += 1
                    if x_cur == cols_n:
                        x_cur = 0
                        y_cur += 1
                    continue
                x = x_min + (x_step / 2.0) + x_cur * x_step
                y = y_min + (y_step / 2.0) + y_cur * y_step
                if trans:
                    lon, lat = trans.coord(x, y)
                else:
                    lon, lat = x, y
                # This is necessary ONLY for converted geo coordinates
                if lon > 180.0:
                    lon = lon - 360.0
                # Writing .csv file with EPGS:4326 coordinates

                csv_out.writerow(["%.5f" % lon, "%.5f" % lat,
                                  "%.5f" % float(el)])

                x_cur += 1
                if x_cur == cols_n:
                    x_cur = 0
                    y_cur += 1


def gem_titan2wkt_coreconv(input_filepath, csv_filepath, epsg_in):
    trans = None
    if epsg_in != VolConst.epsg_out:
        trans = TransToWGS84(epsg_in)

    with open(input_filepath, 'r', newline='') as file_in, open(
            csv_filepath, 'w', newline='') as csv_fout:
        csv_out = csv.writer(csv_fout)
        csv_out.writerow(['lon', 'lat', 'intensity'])

        line1 = file_in.readline()
        ret = re.search(
            '^Nx=([0-9]+): X={[ 	]*([0-9]+),[ 	]*([0-9]+)',
            line1)

        ret1_grp = ret.groups()
        if len(ret1_grp) != 3:
            raise ValueError(
                'Malformed Titan2 first line header [%s]' % line1)
        cols_n = int(ret1_grp[0])
        x_min = float(ret1_grp[1])
        x_max = float(ret1_grp[2])

        line2 = file_in.readline()
        ret = re.search(
            '^Ny=([0-9]+): Y={[ 	]*([0-9]+),[ 	]*([0-9]+)',
            line2)

        ret2_grp = ret.groups()
        if len(ret2_grp) != 3:
            raise ValueError(
                'Malformed Titan2 second line header [%s]' % line2)
        rows_n = int(ret1_grp[0])
        y_min = float(ret1_grp[1])
        y_max = float(ret1_grp[2])

        x_step = float((x_max - x_min) / float(cols_n))
        y_step = float((y_max - y_min) / float(rows_n))

        line3 = file_in.readline()
        ret = re.search(r'^(Pileheight=)\s*', line3)

        ret3_grp = ret.groups()
        if len(ret3_grp) != 1:
            raise ValueError(
                'Malformed Titan2 third line header [%s]' % line3)

        if x_step != y_step:
            raise ValueError(
                'Malformed Titan2 x and y distance'
                ' are different [%f, %f]' % (x_step, y_step))

        x_cur = 0
        y_cur = 0
        for row in file_in:
            for el in re.split(r'\s+', row.strip()):
                if float(el) <= 0.0:
                    x_cur += 1
                    if x_cur == cols_n:
                        x_cur = 0
                        y_cur += 1
                    continue
                x = x_min + (x_step / 2.0) + x_cur * x_step
                y = y_min + (y_step / 2.0) + y_cur * y_step
                if trans:
                    lon, lat = trans.coord(x, y)
                else:
                    lon, lat = x, y
                # This is necessary ONLY for converted geo coordinates
                if lon > 180.0:
                    lon = lon - 360.0
                # Writing .csv file with EPGS:4326 coordinates

                csv_out.writerow(["%.5f" % lon, "%.5f" % lat,
                                  "%.5f" % float(el)])

                x_cur += 1
                if x_cur == cols_n:
                    x_cur = 0
                    y_cur += 1


def gem_shape_coreconv(input_filepath, csv_filepath,
                       attrib, p_size, density):
    try:
        tmp_path = os.path.dirname(input_filepath)
        shp_filename = os.path.basename(input_filepath)
        tif_filename = shp_filename[:-4] + ".tif"
        csv_filename = shp_filename[:-4] + "__shp.csv"
        ogr_drv = ogr.GetDriverByName('ESRI Shapefile')
        s_ds = ogr_drv.Open(input_filepath)
        s_layer = s_ds.GetLayer()
        l_name = s_layer.GetName()
        x_min, x_max, y_min, y_max = s_layer.GetExtent()

        InDS = gdal.OpenEx(input_filepath,
                           nOpenFlags=(gdal.OF_VECTOR |
                                       gdal.OF_VERBOSE_ERROR))

        rast_opts_s = (
            "-l {0} -a {1} -tr {2} {2} -te {3} {4} {5} {6}"
            " -of GTiff -ot Float32 -a_srs EPSG:4326".format(
                l_name,
                attrib, p_size,
                x_min, y_min, x_max, y_max))
        rast_opts = gdal.RasterizeOptions(options=rast_opts_s)

        RetDS = gdal.Rasterize(os.path.join(tmp_path, tif_filename),
                               InDS, options=rast_opts)

        band = RetDS.GetRasterBand(1)

        cols = RetDS.RasterXSize
        rows = RetDS.RasterYSize
        gt = RetDS.GetGeoTransform()

        data = band.ReadAsArray()
        csv_filepath = os.path.join(tmp_path, csv_filename)
        with open(csv_filepath, 'w', newline='') as f_csv:
            f_csv.write("lon,lat,intensity\r\n")
            for row in range(rows):
                for col in range(cols):
                    x = gt[0] + (col * gt[1]) + (row * gt[2])
                    y = gt[3] + (col * gt[4]) + (row * gt[5])
                    z = data[row, col]
                    load_kpa = ((float(density) * VolConst.g *
                                 (float(z) / 1000.)) / 1000.)
                    intens = "%.5f" % load_kpa

                    if not numpy.isnan(z):  # only write if not NaN
                        f_csv.write(f"{x:.5f},{y:.5f},{intens:s}\r\n")
    except Exception as exc:
        logging.error(exc)
    finally:
        del RetDS
        del s_ds
        del InDS
        del ogr_drv
        gc.collect()


def gem_shape2wkt_coreconv(input_filepath, wkt_filepath):
    try:
        ogr_drv = ogr.GetDriverByName('ESRI Shapefile')
        shp_ds = ogr_drv.Open(input_filepath, 0)
        shp_layer = shp_ds.GetLayerByIndex(0)

        if shp_layer.GetFeatureCount() != 1:
            raise ValueError('1 feature only layers are supported')

        target_prj = osr.SpatialReference()
        if int(gdal.VersionInfo("VERSION_NUM")[0]) >= 3:
            # GDAL 3 changes axis order:
            #          https://github.com/OSGeo/gdal/issues/1546
            target_prj.SetAxisMappingStrategy(
                osr.OAMS_TRADITIONAL_GIS_ORDER)

        target_prj.ImportFromEPSG(4326)
        source_prj = shp_layer.GetSpatialRef()

        transform = None
        if not source_prj.IsSame(target_prj) or (
                int(gdal.VersionInfo("VERSION_NUM")[0]) >= 3):
            transform = osr.CoordinateTransformation(
                source_prj, target_prj)

        for shp_fea in shp_layer:
            geom = shp_fea.GetGeometryRef()

            if transform:
                geom.Transform(transform)
            # Excluding Z dimension
            geom.FlattenTo2D()
            geom_wkt = geom.ExportToWkt()
            break

        with open(wkt_filepath, 'w', newline='') as f_out:
            f_out.write('geom\n"')
            f_out.write(geom_wkt)
            f_out.write('"\n')
    finally:
        del shp_ds
        del ogr_drv
        gc.collect()


def gem_shapefile_get_fields_exec(input_filepath, tmp_path):
    with ZipFile(input_filepath, 'r') as zip:
        zip.extractall(path=tmp_path)

    shp_files = [f for f in os.listdir(tmp_path) if (
        f.endswith('.shp') or f.endswith('.SHP'))]

    if len(shp_files) != 1:
        raise ValueError(
            'Not uniq .shp file not found in [%s] file.' %
            input_filepath)

    shp_filename = shp_files[0]
    shp_filepath = os.path.join(tmp_path, shp_filename)

    ogr_drv = ogr.GetDriverByName('ESRI Shapefile')
    s_ds = ogr_drv.Open(shp_filepath)
    s_layer = s_ds.GetLayer()
    # here the layer name l_name = s_layer.GetName()
    ldefn = s_layer.GetLayerDefn()
    schema = []
    for n in range(ldefn.GetFieldCount()):
        fdefn = ldefn.GetFieldDefn(n)
        schema.append(fdefn.name)
    return schema


def gem_shapefile_get_fields(userid, namespace, filename):
    input_filepath = get_full_path(userid, namespace, filename)
    tmp_basepath = get_tmp_path(userid)
    tmp_path = tempfile.mkdtemp(prefix='shpin_', dir=tmp_basepath)

    try:
        ret = gem_shapefile_get_fields_exec(input_filepath, tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

    return ret


def gem_esritxt_converter(z, userid, namespace, filename, file_collect,
                          epsg_in, density):
    csv_filepath = None
    csv_filename = ""
    try:
        input_filepath = get_full_path(userid, namespace, filename)
        output_file = os.path.basename(filename)
        extension = os.path.splitext(output_file)[1][1:]
        if not extension:
            raise ValueError('extension of input file not found')

        csv_filename = output_file[:-4] + "__" + extension + ".csv"

        tmp_path = get_tmp_path(userid)
        csv_filepath = os.path.join(tmp_path, csv_filename)
        gem_esritxt_coreconv(input_filepath, csv_filepath, epsg_in, density)
        zwrite_or_collect(z, userid, 'tmp', csv_filename, file_collect)
    finally:
        if os.path.exists(csv_filepath):
            os.remove(csv_filepath)

    return csv_filename


def gem_esritext2wkt_converter(z, userid, namespace, filename, file_collect,
                               epsg_in, density, nodata_extra):
    csv_filepath = None
    csv_filename = ""
    try:
        input_filepath = get_full_path(userid, namespace, filename)
        output_file = os.path.basename(filename)
        extension = os.path.splitext(output_file)[1][1:]
        if not extension:
            raise ValueError('extension of input file not found')

        csv_filename = output_file[:-4] + "__" + extension + ".csv"

        tmp_path = get_tmp_path(userid)
        csv_filepath = os.path.join(tmp_path, csv_filename)
        gem_esritxt2wkt_coreconv(input_filepath, csv_filepath, epsg_in,
                                 density, nodata_extra)
        zwrite_or_collect(z, userid, 'tmp', csv_filename, file_collect)
    finally:
        if os.path.exists(csv_filepath):
            os.remove(csv_filepath)

    return csv_filename


# convert 'sim_run.txt' => 'sim_run__txt.csv'
def gem_titan2_converter(z, userid, namespace, filename, file_collect,
                         epsg_in):
    """
    Note: Only Pileheight!
    Nx=1024: X={              641941,              645559}
    Ny=1024: Y={             2154941,             2158559}
    Pileheight=
    """
    input_filepath = get_full_path(userid, namespace, filename)
    output_file = os.path.basename(filename)
    extension = os.path.splitext(output_file)[1][1:]  # strip dot
    if not extension:
        raise ValueError('extension of input file not found')

    # 'sim_run.txt' => 'sim_run__txt.csv'
    csv_filename = output_file[:-4] + "__" + extension + ".csv"
    csv_filepath = os.path.join(get_tmp_path(userid), csv_filename)
    gem_titan2_coreconv(input_filepath, csv_filepath, epsg_in)
    zwrite_or_collect(z, userid, 'tmp', csv_filepath, file_collect)
    return csv_filepath


def gem_shape_converter(z, userid, namespace, filename, file_collect,
                        p_size, attrib, density):
    if z is None:
        raise ValueError("Shapefile input format not yet supported for"
                         " hybridge QGIS integration")

    input_filepath = get_full_path(userid, namespace, filename)
    tmp_basepath = get_tmp_path(userid)
    tmp_path = tempfile.mkdtemp(prefix='shpin_', dir=tmp_basepath)
    try:
        with ZipFile(input_filepath, 'r') as zip:
            zip.extractall(path=tmp_path)

        shp_files = [f for f in os.listdir(tmp_path) if (
            f.endswith('.shp') or f.endswith('.SHP'))]

        if len(shp_files) != 1:
            raise ValueError('Not uniq .shp file not found in [%s] file.' %
                             filename)

        shp_filename = shp_files[0]
        csv_filename = shp_filename[:-4] + "__shp.csv"
        shp_filepath = os.path.join(tmp_path, shp_filename)
        csv_filepath = os.path.join(tmp_path, csv_filename)

        gem_shape_coreconv(shp_filepath, csv_filepath,
                           attrib, p_size, density)

        zwrite_or_collect(z, userid, 'tmp',
                          csv_filepath, file_collect)
        csv_name = os.path.basename(csv_filename)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

    return csv_name


def gem_shape2wkt_converter(z, userid, namespace, filename, file_collect):
    if z is None:
        raise ValueError("Shapefile input format not yet supported for"
                         " hybridge QGIS integration")

    input_filepath = get_full_path(userid, namespace, filename)
    tmp_basepath = get_tmp_path(userid)
    tmp_path = tempfile.mkdtemp(prefix='shpin_', dir=tmp_basepath)
    try:
        with ZipFile(input_filepath, 'r') as zip:
            zip.extractall(path=tmp_path)

        shp_files = [f for f in os.listdir(tmp_path) if (
            f.endswith('.shp') or f.endswith('.SHP'))]

        if len(shp_files) != 1:
            raise ValueError('Not uniq .shp file not found in [%s] file.' %
                             filename)

        shp_filename = shp_files[0]
        wkt_filename = shp_filename[:-4] + "__shp.csv"
        shp_filepath = os.path.join(tmp_path, shp_filename)
        wkt_filepath = os.path.join(tmp_path, wkt_filename)

        gem_shape2wkt_coreconv(shp_filepath, wkt_filepath)

        zwrite_or_collect(z, userid, 'tmp',
                          wkt_filepath, file_collect)
        wkt_name = os.path.basename(wkt_filename)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

    return wkt_name


def gem_input_converter(z, key, input_type, userid, namespace, filename,
                        file_collect, *args):
    """
    a part of mandatory fields, optional are managed as follow:
    input_type == VolConst.ty_shape:
        p_size = args[0]
        attrib = args[1]
        density = args[2] (value or None)

    input_type == VolConst.ty_text && key != pyro:
        epsg_in = arg[0]
        density = args[2] (value or None)
    input_type == VolConst.ty_text && key == pyro:
        epsg_in = arg[0]
    """
    if input_type == VolConst.ty_shap:
        p_size = args[0]
        attrib = args[1]
        density = args[2]
        return gem_shape_converter(z, userid, namespace, filename,
                                   file_collect, p_size, attrib, density)
    elif input_type == VolConst.ty_swkt:
        return gem_shape2wkt_converter(z, userid, namespace, filename,
                                       file_collect)
    elif input_type == VolConst.ty_text:
        epsg_in = args[0]
        density = args[1]

        if key in [VolConst.ph_ashf]:
            return gem_esritxt_converter(
                z, userid, namespace, filename, file_collect,
                epsg_in, density)
    elif input_type == VolConst.ty_twkt:
        epsg_in = args[0]
        density = args[1]
        nodata_extra = args[2]

        if key == VolConst.ph_lava:
            return gem_esritext2wkt_converter(
                z, userid, namespace, filename, file_collect,
                epsg_in, density, nodata_extra)
        elif key == VolConst.ph_laha:
            return gem_esritext2wkt_converter(
                z, userid, namespace, filename, file_collect,
                epsg_in, density, nodata_extra)
        else:  # pyro case
            return gem_titan2_converter(
                z, userid, namespace, filename, file_collect,
                epsg_in)
