# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import shutil
import operator
from xml.etree.ElementTree import iterparse

from openquake.baselib import sap
from openquake.baselib.general import groupby
from openquake.baselib.node import context, striptag, Node
from openquake.hazardlib.nrml import NRML05
from openquake.hazardlib import InvalidFile, nrml, sourceconverter
from openquake.hazardlib.sourcewriter import obj_to_node
from openquake.risklib import scientific, read_nrml


def get_vulnerability_functions_04(fname):
    """
    Parse the vulnerability model in NRML 0.4 format.

    :param fname:
        path of the vulnerability file
    :returns:
        a dictionary imt, taxonomy -> vulnerability function + vset
    """
    categories = dict(assetCategory=set(), lossCategory=set(),
                      vulnerabilitySetID=set())
    imts = set()
    taxonomies = set()
    vf_dict = {}  # imt, taxonomy -> vulnerability function
    for vset in nrml.read(fname).vulnerabilityModel:
        categories['assetCategory'].add(vset['assetCategory'])
        categories['lossCategory'].add(vset['lossCategory'])
        categories['vulnerabilitySetID'].add(vset['vulnerabilitySetID'])
        IML = vset.IML
        imt_str = IML['IMT']
        imls = ~IML
        imts.add(imt_str)
        for vfun in vset.getnodes('discreteVulnerability'):
            taxonomy = vfun['vulnerabilityFunctionID']
            if taxonomy in taxonomies:
                raise InvalidFile(
                    'Duplicated vulnerabilityFunctionID: %s: %s, line %d' %
                    (taxonomy, fname, vfun.lineno))
            taxonomies.add(taxonomy)
            with context(fname, vfun):
                loss_ratios = ~vfun.lossRatio
                coefficients = ~vfun.coefficientsVariation
            if len(loss_ratios) != len(imls):
                raise InvalidFile(
                    'There are %d loss ratios, but %d imls: %s, line %d' %
                    (len(loss_ratios), len(imls), fname,
                     vfun.lossRatio.lineno))
            if len(coefficients) != len(imls):
                raise InvalidFile(
                    'There are %d coefficients, but %d imls: %s, line %d' %
                    (len(coefficients), len(imls), fname,
                     vfun.coefficientsVariation.lineno))
            with context(fname, vfun):
                vf_dict[imt_str, taxonomy] = scientific.VulnerabilityFunction(
                    taxonomy, imt_str, imls, loss_ratios, coefficients,
                    vfun['probabilisticDistribution'])
    categories['id'] = '_'.join(sorted(categories['vulnerabilitySetID']))
    del categories['vulnerabilitySetID']
    return vf_dict, categories


def upgrade_file(path, multipoint):
    """Upgrade to the latest NRML version"""
    node0 = nrml.read(path, chatty=False)[0]
    shutil.copy(path, path + '.bak')  # make a backup of the original file
    tag = striptag(node0.tag)
    gml = True
    if tag == 'vulnerabilityModel':
        vf_dict, cat_dict = get_vulnerability_functions_04(path)
        # below I am converting into a NRML 0.5 vulnerabilityModel
        node0 = Node(
            'vulnerabilityModel', cat_dict,
            nodes=[obj_to_node(val) for val in vf_dict.values()])
        gml = False
    elif tag == 'fragilityModel':
        node0 = read_nrml.convert_fragility_model_04(
            nrml.read(path)[0], path)
        gml = False
    elif tag == 'sourceModel':
        node0 = nrml.read(path)[0]
        dic = groupby(node0.nodes, operator.itemgetter('tectonicRegion'))
        node0.nodes = [Node('sourceGroup',
                            dict(tectonicRegion=trt, name="group %s" % i),
                            nodes=srcs)
                       for i, (trt, srcs) in enumerate(dic.items(), 1)]
        if multipoint:
            sourceconverter.update_source_model(node0, path + '.bak')
    with open(path, 'wb') as f:
        nrml.write([node0], f, gml=gml)


# NB: this works only for migrations from NRML version 0.4 to 0.5
# we will implement a more general solution when we will need to pass
# to version 0.6
@sap.script
def upgrade_nrml(directory, dry_run, multipoint):
    """
    Upgrade all the NRML files contained in the given directory to the latest
    NRML version. Works by walking all subdirectories.
    WARNING: there is no downgrade!
    """
    for cwd, dirs, files in os.walk(directory):
        for f in files:
            path = os.path.join(cwd, f)
            if f.endswith('.xml'):
                ip = iterparse(path, events=('start',))
                next(ip)  # read node zero
                try:
                    fulltag = next(ip)[1].tag  # tag of the first node
                    xmlns, tag = fulltag.split('}')
                except Exception:  # not a NRML file
                    xmlns, tag = '', ''
                if xmlns[1:] == NRML05:  # already upgraded
                    if 'sourceModel' in tag and multipoint:
                        print('upgrading to multiPointSources', path)
                        node0 = nrml.read(path)[0]
                        sourceconverter.update_source_model(node0, path)
                        with open(path, 'wb') as f:
                            nrml.write([node0], f, gml=True)
                elif 'nrml/0.4' in xmlns and (
                        'vulnerability' in tag or 'fragility' in tag or
                        'sourceModel' in tag):
                    if not dry_run:
                        print('Upgrading', path)
                        try:
                            upgrade_file(path, multipoint)
                        except Exception as exc:
                            raise
                            print(exc)
                    else:
                        print('Not upgrading', path)


upgrade_nrml.arg('directory', 'directory to consider')
upgrade_nrml.flg('dry_run', 'test the upgrade without replacing the files')
upgrade_nrml.flg('multipoint', 'replace PointSources with MultiPointSources')
