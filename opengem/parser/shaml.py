# vim: tabstop=4 shiftwidth=4 softtabstop=4

from lxml import etree

from opengem import producer
from opengem import shapes


GML = 'http://www.opengis.net/gml'


class ShamlFile(producer.FileProducer):
    def _parse(self):
        for event, element in etree.iterparse(self.file,
                                              events=('start', 'end')):
            # We currently only care about the tag name, not the namespace
            tag = element.tag.split('}')[-1]

            if event == 'end' and tag == 'BranchLevelList':
                self._build_branching_levels(element)
            elif event == 'start' and tag == 'EndBranchMapping':
                self._set_branch(element.get('label'))
            elif event == 'end' and tag == 'Source':
                yield (self._to_region(element), self._to_source(element))

            # To save space we could clear elements we no longer care about
            # by doing element.clear(), for example on the Source elements

    def _build_branching_levels(self, branching_levels):
        pass

    def _set_branch(self, branch_label):
        self._current_branch = branch_label

    def _to_region(self, element):
        pos_list = element.find('.//{%s}posList' % GML)
        
        # build up the region for this element
        # for now we assume we are getting lat-long, not lat-long-depth.
        parts = pos_list.text.strip().split()
        coords = []
        while parts:
            coords.append((float(parts.pop(0)), float(parts.pop(0))))

        linestring = shapes.LineString(coords)
        return linestring

    def _to_source(self, element):
        # TODO(termie): map the element into a source, using
        #               self._current_branch as context
        return element
