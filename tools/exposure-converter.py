#! /usr/bin/env python
"""
This script convert an exposure document from the old 4.0 format to
the new one (which is always nrml 4.0) where each cost type has its
proper <cost> tag
"""

import sys
import os
from lxml import etree
from openquake import nrmllib


def namespace(gml=False):
    if gml:
        return "{%s}" % nrmllib.GML_NAMESPACE
    else:
        return "{%s}" % nrmllib.NAMESPACE


def find(element, tag, gml=False):
    return element.find(".//%s%s" % (namespace(gml), tag))


def text(element, tag, gml=False):
    ret = find(element, tag, gml)
    if ret is not None:
        return ret.text
    else:
        return None


def get(element, attr, gml=False):
    if gml:
        ns = namespace(gml)
    else:
        ns = ""
    return element.get("%s%s" % (ns, attr))


def safe_set(element, attr, value):
    if value is not None:
        element.set(attr, value)


def convert(filename, output_filename):
    exposure = etree.parse(file(filename)).getroot()

    with open(output_filename, "w") as output:
        root = etree.Element("nrml", nsmap={None: nrmllib.NAMESPACE})

        exposure_model = etree.SubElement(root, "exposureModel")
        safe_set(exposure_model, 'id', get(
            find(exposure, "exposureModel"), "id", gml=True))

        safe_set(exposure_model,
                 'category',
                 get(find(exposure, "exposureList"), "assetCategory"))

        safe_set(exposure_model,
                 'taxonomySource',
                 text(exposure, "taxonomySource"))

        description = etree.SubElement(exposure_model, "description")
        description.text = find(exposure, "description", True).text

        conversions = etree.SubElement(exposure_model, "conversions")
        if get(find(exposure, 'exposureList'), "areaUnit"):
            element = etree.SubElement(conversions, "area")
            safe_set(element, 'unit',
                     get(find(exposure, 'exposureList'), "areaUnit"))
            safe_set(
                element, 'type',
                get(find(exposure, 'exposureList'), "areaType"))

        costTypes = {}
        types_el = etree.SubElement(conversions, "costTypes")

        for el, new_el in (("coco", "contents"),
                           ("stco", "structural"),
                           ("nonStco", "non_structural")):
            if get(find(exposure, 'exposureList'), "%sUnit" % el):
                costTypes[el] = etree.SubElement(types_el, "costType")
                costTypes[el].set('name', new_el)
                safe_set(costTypes[el], 'unit',
                         get(find(exposure, 'exposureList'), "%sUnit" % el))
                safe_set(
                    costTypes[el], 'type',
                    get(find(exposure, 'exposureList'), "%sType" % el))

        reco_unit = get(find(exposure, 'exposureList'), "recoUnit")
        reco_type = get(find(exposure, 'exposureList'), "recoType")
        if reco_type is not None:
            costTypes["stco"].set("retrofittedType", reco_type)
            costTypes["stco"].set("retrofittedUnit", reco_unit)

        assets = etree.SubElement(exposure_model, "assets")

        for asset_element in exposure.findall(
                ".//{%s}assetDefinition" % nrmllib.NAMESPACE):
            element = etree.SubElement(assets, "asset")

            safe_set(element, "id", get(asset_element, "id", gml=True))
            safe_set(element, "taxonomy", text(asset_element, "taxonomy"))
            safe_set(element, "area", text(asset_element, "area"))
            safe_set(element, "units", text(asset_element, "number"))

            location = etree.SubElement(element, "location")
            lon, lat = find(asset_element, "pos", True).text.split()
            safe_set(location, "lon", lon)
            safe_set(location, "lat", lat)

            costs = etree.SubElement(element, "costs")
            for el, cost_type in (("coco", "contents"),
                                  ("stco", "structural"),
                                  ("nonStco", "non_structural")):
                if text(asset_element, el) is not None:
                    cost = etree.SubElement(costs, "cost")
                    safe_set(cost, "type", cost_type)
                    safe_set(cost, "value", text(asset_element, el))

                    if cost_type == "structural":
                        safe_set(
                            cost,
                            "retrofitted", text(asset_element, "reco"))
                        safe_set(
                            cost,
                            "deductible", text(asset_element, "deductible"))
                        safe_set(
                            cost,
                            "insuranceLimit", text(asset_element, "limit"))

        output.write(etree.tostring(root,
                                    pretty_print=True,
                                    xml_declaration=True,
                                    encoding="UTF-8"))


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print "Usage: %s <filename to convert> <new filename> <swap>" % (
            sys.argv[0])
        sys.exit(1)

    convert(sys.argv[1], sys.argv[2])
    sys.exit(0)
