# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
NRML serialization of risk-related data sets.
- loss ratio curves
- loss curves
"""

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import writer

from openquake.output import nrml
#from openquake.xml import GML_OLD, NSMAP_OLD, NRML_OLD
from openquake.xml import GML, NRML, NSMAP

LOG = logs.RISK_LOG

class RiskXMLWriter(nrml.TreeNRMLWriter):
    """This class serializes a set of loss or loss ratio curves to NRML.
    Since the curves have to be collected under several different asset
    objects, we have to build the whole tree before serializing
    (use base class nrml.TreeNRMLWriter).
    """

    # these tag names have to be redefined in the derived classes
    container_tag = None
    curves_tag = None
    curve_tag = None
    abscissa_tag = None
    
    result_tag = "%sriskResult" % NRML
    asset_tag = "%sasset" % NRML
    site_tag = "%ssite" % NRML
    poe_tag = "%spoE" % NRML
    end_branch_attr_name = 'endBranchLabel'

    CONTAINER_DEFAULT_ID = 'c1'

    def __init__(self, path):
        super(RiskXMLWriter, self).__init__(path)

        self.curve_list_el = None
        self.assets_per_id = {}

    def write(self, point, values):
        """Writes an asset element with loss/loss ratio information.
        
        point must be of type shapes.Site or shapes.GridPoint
        values is a pair of (curve_object, asset_object), with curve_object
        of type shapes.Curve. 
        asset_object is a dictionary that looks like:

        {'assetID': foo, # this is the only required item
         'nrml_id': 'nrml',
         'riskres_id': 'rr',
         'list_id': 'list',
         'endBranchLabel' : '1_1'
        }
        """
        
        if isinstance(point, shapes.GridPoint):
            point = point.site

        (curve_object, asset_object) = values

        # if we are writing the first hazard curve, create wrapping elements
        if self.root_node is None:
            
            # nrml:nrml, needs gml:id
            self._create_root_element()
            if 'nrml_id' in asset_object:
                nrml.set_gml_id(self.root_node, str(asset_object['nrml_id']))
            else:
                nrml.set_gml_id(self.root_node, nrml.NRML_DEFAULT_ID)
            
            # nrml:riskResult, needs gml:id
            result_el = etree.SubElement(self.root_node, self.result_tag)
            if 'riskres_id' in asset_object:
                nrml.set_gml_id(result_el, str(asset_object['riskres_id']))
            else:
                nrml.set_gml_id(result_el, nrml.RISKRESULT_DEFAULT_ID)

            # container element, needs gml:id
            self.curve_list_el = etree.SubElement(result_el, 
                self.container_tag)
            if 'list_id' in asset_object:
                nrml.set_gml_id(self.curve_list_el, str(
                    asset_object['list_id']))
            else:
                nrml.set_gml_id(self.curve_list_el, self.CONTAINER_DEFAULT_ID)

        asset_id = str(asset_object['assetID'])
        try:
            asset_el = self.assets_per_id[asset_id]
        except KeyError:
            
            # nrml:asset, needs gml:id
            asset_el = etree.SubElement(self.curve_list_el, self.asset_tag)
            nrml.set_gml_id(asset_el, asset_id)
            self.assets_per_id[asset_id] = asset_el

        # check if nrml:site is already existing
        site_el = asset_el.find(self.site_tag)
        if site_el is None:
            site_el = etree.SubElement(asset_el, self.site_tag)

            point_el = etree.SubElement(site_el, nrml.GML_POINT_TAG)
            point_el.set(nrml.GML_SRS_ATTR_NAME, nrml.GML_SRS_EPSG_4326)

            pos_el = etree.SubElement(point_el, nrml.GML_POS_TAG)
            pos_el.text = "%s %s" % (point.longitude, point.latitude)

        elif not nrml.element_equal_to_site(site_el, point):
            error_msg = "asset %s cannot have two differing sites: %s, %s " \
                % (asset_id, site_el, point)
            raise ValueError(error_msg)

        # loss/loss ratio curves - sub-element already created?
        curves_el = asset_el.find(self.curves_tag)
        if curves_el is None:
            curves_el = etree.SubElement(asset_el, self.curves_tag)

        curve_el = etree.SubElement(curves_el, self.curve_tag)

        # attribute for endBranchLabel (optional)
        if 'endBranchLabel' in asset_object:
            curve_el.set(self.end_branch_attr_name, 
                str(asset_object[self.end_branch_attr_name]))

        abscissa_el = etree.SubElement(curve_el, self.abscissa_tag)
        abscissa_el.text = _curve_vals_as_gmldoublelist(curve_object)

        poe_el = etree.SubElement(curve_el, self.poe_tag)
        poe_el.text = _curve_poe_as_gmldoublelist(curve_object)


class LossCurveXMLWriter(RiskXMLWriter):
    """NRML serialization of loss curves"""
    container_tag = "%slossCurveList" % NRML
    curves_tag = "%slossCurves" % NRML
    curve_tag = "%slossCurve" % NRML
    abscissa_tag = "%sloss" % NRML
    

class LossRatioCurveXMLWriter(RiskXMLWriter):
    """NRML serialization of loss ratio curves"""
    container_tag = "%slossRatioCurveList" % NRML
    curves_tag = "%slossRatioCurves" % NRML
    curve_tag = "%slossRatioCurve" % NRML
    abscissa_tag = "%slossRatio" % NRML

def _curve_vals_as_gmldoublelist(curve_object):
    """Return the list of loss/loss ratio values from a curve object.
    This is the abscissa of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(abscissa) for abscissa in curve_object.abscissae])

def _curve_poe_as_gmldoublelist(curve_object):
    """Return the list of PoE values from a curve object.
    This is the ordinate of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(ordinate) for ordinate in curve_object.ordinates])

