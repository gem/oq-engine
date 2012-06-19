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

"""
Module for writing SDAC (Scenario Damage Assessment Calculator)
risk NRML artifacts.
"""

from lxml import etree

from openquake import xml


class DmgDistPerAssetXMLWriter(object):
    """
    Write the damage distribution per asset artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param end_branch_label: logic tree branch which was used for the
        realization associated with this distribution.
    :type end_branch_label: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, end_branch_label, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.end_branch_label = end_branch_label

        # <nrml /> element
        self.root = None

        # <dmgDistPerAsset /> element
        self.dmg_dist_el = None

    def serialize(self, assets_data):
        """
        Serialize the entire distribution.

        :param assets_data: the distribution to be written.
        :type assets_data: list of
            :py:class:`openquake.db.models.DmgDistPerAssetData` instances.
            There are no restrictions about the ordering of the elements,
            the component is able to correctly re-order the elements by
            site and asset.

        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if assets_data is None or not len(assets_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        # contains the set of <DDNode /> elements indexed per site
        dd_nodes = {}

        # contains the set of <asset /> elements indexed per asset ref
        asset_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.dmg_dist_el = _create_root_elems(
                self.end_branch_label, self.damage_states,
                "dmgDistPerAsset")

            for asset_data in assets_data:
                site = asset_data.exposure_data.site
                asset_ref = asset_data.exposure_data.asset_ref

                # lookup the correct <DDNode /> element
                dd_node_el = dd_nodes.get(site.wkt, None)

                # nothing yet related to this site,
                # creating the <DDNode /> element
                if dd_node_el is None:
                    dd_node_el = dd_nodes[site.wkt] = \
                            self._create_dd_node_elem(site)

                # lookup the correct <asset /> element
                asset_node_el = asset_nodes.get(asset_ref, None)

                # nothing yet related to this asset,
                # creating the <asset /> element
                if asset_node_el is None:
                    asset_node_el = asset_nodes[asset_ref] = \
                            _create_asset_elem(dd_node_el, asset_ref)

                _create_damage_elem(asset_node_el, asset_data.dmg_state,
                        asset_data.mean, asset_data.stddev)

            fh.write(etree.tostring(
                self.root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_dd_node_elem(self, site):
        """
        Create the <DDNode /> element related to the given site.
        """

        dd_node_el = etree.SubElement(self.dmg_dist_el, "DDNode")
        site_el = etree.SubElement(dd_node_el, xml.RISK_SITE_TAG)

        point_el = etree.SubElement(site_el, xml.GML_POINT_TAG)
        point_el.set(xml.GML_SRS_ATTR_NAME, xml.GML_SRS_EPSG_4326)

        pos_el = etree.SubElement(point_el, xml.GML_POS_TAG)
        pos_el.text = "%s %s" % (site.x, site.y)

        return dd_node_el


class CollapseMapXMLWriter(object):
    """
    Write the collapse map artifact to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param end_branch_label: logic tree branch which was used for the
        realization associated with this distribution.
    :type end_branch_label: string
    """

    def __init__(self, path, end_branch_label):
        self.path = path
        self.elems_id = 1
        self.end_branch_label = end_branch_label

        # <nrml /> element
        self.root = None

        # <collapseMap /> element
        self.collapse_map_el = None

    def serialize(self, cmap_data):
        """
        Serialize the entire distribution.

        :param cmap_data: the distribution to be written.
        :type cmap_data: list of
            :py:class:`openquake.db.models.CollapseMapData` instances.
            There are no restrictions about the ordering of the elements,
            the component is able to correctly re-order the elements by
            site and asset.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if cmap_data is None or not len(cmap_data):
            raise RuntimeError(
                "empty maps are not supported by the schema.")

        # contains the set of <CMNode /> elements indexed per site
        cm_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.collapse_map_el = self._create_root_elems()

            for cfraction in cmap_data:
                site = cfraction.location

                # lookup the correct <CMNode /> element
                cm_node_el = cm_nodes.get(site.wkt, None)

                # nothing yet related to this site,
                # creating the <CMNode /> element
                if cm_node_el is None:
                    cm_node_el = cm_nodes[site.wkt] = \
                            self._create_cm_node_elem(site)

                _create_cf_elem(cfraction, cm_node_el)

            fh.write(etree.tostring(
                self.root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_cm_node_elem(self, site):
        """
        Create the <CMNode /> element related to the given site.
        """

        cm_node_el = etree.SubElement(self.collapse_map_el, "CMNode")
        cm_node_el.set("%sid" % xml.GML, "n" + str(self.elems_id))
        self.elems_id += 1

        site_el = etree.SubElement(cm_node_el, xml.RISK_SITE_TAG)

        point_el = etree.SubElement(site_el, xml.GML_POINT_TAG)
        point_el.set(xml.GML_SRS_ATTR_NAME, xml.GML_SRS_EPSG_4326)

        pos_el = etree.SubElement(point_el, xml.GML_POS_TAG)
        pos_el.text = "%s %s" % (site.x, site.y)

        return cm_node_el

    def _create_root_elems(self):
        """
        Create the <nrml /> and <collapseMap /> elements.
        """

        root = etree.Element("nrml", nsmap=xml.NSMAP)
        root.set("%sid" % xml.GML, "n" + str(self.elems_id))
        self.elems_id += 1

        cm_el = etree.SubElement(root, "collapseMap")
        cm_el.set("endBranchLabel", str(self.end_branch_label))

        return root, cm_el


def _create_cf_elem(cfraction, cm_node_el):
    """
    Create the <cf /> element related to the given site.
    """

    cf_el = etree.SubElement(cm_node_el, "cf")
    cf_el.set("assetRef", cfraction.asset_ref)

    mean_el = etree.SubElement(cf_el, "mean")
    mean_el.text = str(cfraction.value)

    std_el = etree.SubElement(cf_el, "stdDev")
    std_el.text = str(cfraction.std_dev)


class DmgDistPerTaxonomyXMLWriter(object):
    """
    Write the damage distribution per taxonomy artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param end_branch_label: logic tree branch which was used for the
        realization associated with this distribution.
    :type end_branch_label: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, end_branch_label, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.end_branch_label = end_branch_label

        # <nrml /> element
        self.root = None

        # <dmgDistPerTaxonomy /> element
        self.dmg_dist_el = None

    def serialize(self, taxonomy_data):
        """
        Serialize the entire distribution.

        :param taxonomy_data: the distribution to be written.
        :type taxonomy_data: list of
            :py:class:`openquake.db.models.DmgDistPerTaxonomyData` instances.
            There are no restrictions about the ordering of the elements,
            the component is able to correctly re-order the elements by
            asset taxonomy.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if taxonomy_data is None or not len(taxonomy_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        # contains the set of <DDNode /> elements indexed per taxonomy
        dd_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.dmg_dist_el = _create_root_elems(
                self.end_branch_label, self.damage_states,
                "dmgDistPerTaxonomy")

            for tdata in taxonomy_data:
                # lookup the correct <DDNode /> element
                dd_node_el = dd_nodes.get(tdata.taxonomy, None)

                # nothing yet related to this taxonomy,
                # creating the <DDNode /> element
                if dd_node_el is None:
                    dd_node_el = dd_nodes[tdata.taxonomy] = \
                            self._create_dd_node_elem(tdata.taxonomy)

                _create_damage_elem(dd_node_el, tdata.dmg_state,
                        tdata.mean, tdata.stddev)

            fh.write(etree.tostring(
                    self.root, pretty_print=True, xml_declaration=True,
                    encoding="UTF-8"))

    def _create_dd_node_elem(self, taxonomy):
        """
        Create the <DDNode /> element related to the given taxonomy.
        """

        dd_node_el = etree.SubElement(self.dmg_dist_el, "DDNode")

        # <taxonomy /> node
        taxonomy_el = etree.SubElement(dd_node_el, "taxonomy")
        taxonomy_el.text = taxonomy

        return dd_node_el


class DmgDistTotalXMLWriter(object):
    """
    Write the total damage distribution artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param end_branch_label: logic tree branch which was used for the
        realization associated with this distribution.
    :type end_branch_label: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, end_branch_label, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.end_branch_label = end_branch_label

        # <nrml /> element
        self.root = None

    def serialize(self, total_dist_data):
        """
        Serialize the entire distribution.

        :param total_dist_data: the distribution to be written.
        :type total_dist_data: list of
            :py:class:`openquake.db.models.DmgDistTotalData` instances.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if total_dist_data is None or not len(total_dist_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        with open(self.path, "w") as fh:
            self.root, dmg_dist_el = _create_root_elems(
                self.end_branch_label, self.damage_states,
                "totalDmgDist")

            for tdata in total_dist_data:

                _create_damage_elem(dmg_dist_el, tdata.dmg_state,
                        tdata.mean, tdata.stddev)

            fh.write(etree.tostring(
                    self.root, pretty_print=True, xml_declaration=True,
                    encoding="UTF-8"))


def _create_root_elems(end_branch_label, damage_states, distribution):
    """
    Create the <nrml /> and <dmgDistPer{Taxonomy,Asset} /> elements.
    """

    root = etree.Element("nrml", nsmap=xml.NSMAP)
    root.set("%sid" % xml.GML, "n1")

    dmg_dist_el = etree.SubElement(root, distribution)
    dmg_dist_el.set("endBranchLabel", str(end_branch_label))

    dmg_states = etree.SubElement(dmg_dist_el, "damageStates")
    dmg_states.text = " ".join(damage_states)

    return root, dmg_dist_el


def _create_damage_elem(dd_node, dmg_state, mean, stddev):
    """
    Create the <damage /> element.
    """

    ds_node = etree.SubElement(dd_node, "damage")

    ds_node.set("ds", dmg_state)
    ds_node.set("mean", str(mean))
    ds_node.set("stddev", str(stddev))


def _create_asset_elem(dd_node_el, asset_ref):
    """
    Create the <asset /> element.
    """

    asset_node_el = etree.SubElement(dd_node_el, "asset")
    asset_node_el.set("assetRef", asset_ref)

    return asset_node_el
