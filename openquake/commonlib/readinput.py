import logging
import collections
import decimal

import numpy

from openquake.hazardlib import geo, site
from openquake.nrmllib.node import read_nodes, LiteralNode
from openquake.commonlib import valid
from openquake.commonlib.oqvalidation import \
    fragility_files, vulnerability_files
from openquake.commonlib.riskmodels import \
    get_fragility_sets, get_imtls_from_vulnerabilities
from openquake.commonlib.converter import Converter
from openquake.commonlib.source import ValidNode, RuptureConverter


def get_mesh(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region or the exposure.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if getattr(oqparam, 'sites', None):
        lons, lats = zip(*oqparam.sites)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))
    elif 'site' in oqparam.inputs:
        csv_data = open(oqparam.inputs['site'], 'U').read()
        coords = valid.coordinates(
            csv_data.strip().replace(',', ' ').replace('\n', ','))
        lons, lats = zip(*coords)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))
    elif getattr(oqparam, 'region', None):
        # close the linear polygon ring by appending the first
        # point to the end
        firstpoint = geo.Point(*oqparam.region[0])
        points = [geo.Point(*xy) for xy in oqparam.region] + [firstpoint]
        return geo.Polygon(points).discretize(oqparam.region_grid_spacing)
    elif 'exposure' in oqparam.inputs:
        exposure = Converter.from_nrml(oqparam.inputs['exposure'])
        coords = sorted(set((s.lon, s.lat)
                            for s in exposure.tableset.tableLocation))
        lons, lats = zip(*coords)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))


class SiteModelNode(LiteralNode):
    validators = valid.parameters(site=valid.site_param)


def get_site_model(oqparam):
    """
    Convert the NRML file into an iterator over 6-tuple of the form
    (z1pt0, z2pt5, measured, vs30, lon, lat)

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for node in read_nodes(oqparam.inputs['site_model'],
                           lambda el: el.tag.endswith('site'),
                           SiteModelNode):
        yield ~node


def get_site_collection(oqparam, mesh=None, site_ids=None,
                        site_model_params=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param mesh:
        a mesh of hazardlib points; if None the mesh is
        determined by invoking get_mesh
    :param site_ids:
        a list of integers to identify the points; if None, a
        range(1, len(points) + 1) is used
    :param site_model_params:
        object with a method ,get_closest returning the closest site
        model parameters and their distance from each point
    """
    mesh = mesh or get_mesh(oqparam)
    site_ids = site_ids or range(1, len(mesh) + 1)
    if oqparam.inputs.get('site_model'):
        sitecol = []
        exact_matches = 0
        for i, pt in zip(site_ids, mesh):
            param, dist = site_model_params.\
                get_closest(pt.longitude, pt.latitude)
            exact_matches += dist is 0
            sitecol.append(
                site.Site(pt, param.vs30, param.vs30_type == 'measured',
                          param.z1pt0, param.z2pt5, i))
        if exact_matches:
            msg = ('Found %d site model parameters exactly at the hazard '
                   'sites, out of %d total sites' %
                   (exact_matches, len(sitecol)))
            logging.info(msg)
        return site.SiteCollection(sitecol)

    # else use the default site params
    return site.SiteCollection.from_points(
        mesh.lons, mesh.lats, site_ids, oqparam)


def get_rupture(oqparam):
    """
    Returns a hazardlib rupture by reading the `rupture_model` file.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    conv = RuptureConverter(oqparam.rupture_mesh_spacing)
    rup_model = oqparam.inputs['rupture_model']
    rup_node, = read_nodes(rup_model, lambda el: 'Rupture' in el.tag,
                           ValidNode)
    return conv.convert_node(rup_node)


def get_source_models(oqparam):
    """
    Read all the source models specified in oqparam.
    Yield pairs (fname, sources).

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for fname in oqparam.inputs['source']:
        srcs = read_nodes(fname, lambda elem: 'Source' in elem.tag, ValidNode)
        yield fname, srcs


def get_imtls(oqparam):
    """
    Return a dictionary {imt_str: intensity_measure_levels}

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if hasattr(oqparam, 'intensity_measure_types'):
        imtls = dict.fromkeys(oqparam.intensity_measure_types)
    elif hasattr(oqparam, 'intensity_measure_types_and_levels'):
        imtls = oqparam.intensity_measure_types_and_levels
    elif vulnerability_files(oqparam.inputs):
        imtls = get_imtls_from_vulnerabilities(oqparam.inputs)
    elif fragility_files(oqparam.inputs):
        fname = oqparam.inputs['fragility']
        imtls = {str(fset.imt): fset.imls
                 for fset in get_fragility_sets(fname)}
    else:
        raise ValueError('Missing intensity_measure_types_and_levels, '
                         'vulnerability file and fragility file')
    return imtls
