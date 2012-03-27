# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


from lxml import etree

from openquake import xml


class DmgDistPerAssetXMLWriter(object):

    def __init__(self, path, end_branch_label, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.end_branch_label = end_branch_label

    def serialize(self, assets_data):
        dd_nodes = {}
        
        with open(self.path, "w") as fh:

            root = etree.Element("nrml", nsmap=xml.NSMAP)
            root.set("%sid" % xml.GML, "n1")

            dmg_dist_el = etree.SubElement(root, "dmgDistPerAsset")
            dmg_dist_el.set("endBranchLabel", self.end_branch_label)

            dmg_states = etree.SubElement(dmg_dist_el, "damageStates")
            dmg_states.text = " ".join(self.damage_states)

            for asset_data in assets_data:
                site = asset_data.exposure_data.site

                dd_node_el = nodes.get(site, None)

                if dd_node_el is None:
                    dd_node_el = etree.SubElement(dmg_dist_el, "DDNode")
                    site_el = etree.SubElement(dd_node_el, xml.RISK_SITE_TAG)

                    point_el = etree.SubElement(site_el, xml.GML_POINT_TAG)
                    point_el.set(xml.GML_SRS_ATTR_NAME, xml.GML_SRS_EPSG_4326)

                    pos_el = etree.SubElement(point_el, xml.GML_POS_TAG)
                    pos_el.text = "%s %s" % (site.longitude, site.latitude)

                    nodes[site] = dd_node_el

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))
