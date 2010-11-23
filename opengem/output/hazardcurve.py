# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module plots hazard curves as read from an NRML file.
As plotting engine, matplotlib is used.
The plots are in SVG format.
"""

import geohash
import matplotlib
matplotlib.use('SVG')
import numpy
import pylab

from matplotlib.font_manager import FontProperties

from opengem import shapes
from opengem import writer

from opengem.parser import hazard as hazard_parser

IMAGE_FORMAT = "SVG"
COLOR_CODES = ('k', 'r', 'g', 'b')

class HazardCurvePlotter(object):
    """This class plots hazard curves as read from an NRML file. For
    each Site listed in the NRML file, a separate plot is created. A plot
    can contain multiple hazard curves, one for each logic tree end branch 
    given in the NRML file."""

    def __init__(self, output_base_path, nrml_input_path):

        # remove trailing .svg extension from output file name (if existing)
        self.output_base_path = output_base_path
        if self.output_base_path.endswith(('.svg', '.SVG')):
            self.output_base_path = self.output_base_path[0:-4]

        self.nrml_input_path = nrml_input_path
        self.data = {}
        self.svg_filenames = []

        self._parse_nrml_file()

    def _parse_nrml_file(self):
        """Parse hazard curve data from NRML file into a dictionary."""

        nrml_element = hazard_parser.NrmlFile(self.nrml_input_path)

        # we collect hazard curves for one site into one plot
        # one plot contains hazard curves for several end branches 
        # of the logic tree
        # each end branch can have its own abscissa value set
        for (nrml_point, nrml_attr) in nrml_element.filter(
            region_constraint=None):

            site_hash = nrml_point.hash()
            ebl = nrml_attr['endBranchLabel']

            if site_hash not in self.data:
                self.data[site_hash] = {
                    # capture SVG filename for each site
                    'path': self._generate_filename(site_hash),
                    'endBranches': {}}

            if ebl not in self.data[site_hash]['endBranches']:
                self.data[site_hash]['endBranches'][ebl] = {}

            self.data[site_hash]['endBranches'][ebl] = {
                'IMLValues': nrml_attr['IMLValues'], 
                'Values': nrml_attr['Values'],
                'IMT': nrml_attr['IMT'],
                'Site': nrml_point}

    def plot(self):
        # create a plot for each site
        for site_hash in self.data:
            plot = HazardCurvePlot(self.data[site_hash]['path'])
            plot.write(self.data[site_hash]['endBranches'])
            plot.close()

    def filenames(self):
        for site_hash in self.data:
            yield self.data[site_hash]['path']

    def _generate_filename(self, site_hash):
        site_lat, site_lon = geohash.decode(site_hash)
        return "%s_%7.3f_%6.3f.svg" % (
            self.output_base_path, site_lon, site_lat)


class HazardCurvePlot(writer.FileWriter):
    """Plots hazard curves for one site. On plot can contain several
    hazard curves, one for each end branch of a logic tree."""

    image_format = IMAGE_FORMAT

    _plotFig = {'figsize': (10, 10)}

    _plotCurve = {'markersize': None,
                  'color': 'r',
                  'colors': ('r', 'b'),
                  'linestyle': ('steps', '-', '-'),
                  'linewidth': 1}

    _plotLabels = {'ylabel_size': None,
                   'ylabel_rotation': None}

    _plotLabelsFont = {'fontname': 'serif',       # sans
                       'fontweight': 'normal',    # bold
                       'fontsize':  13}

    _plotAxes = {'ymin': 0.0,
                 'ymax': 1.0,
                 'xmin': 0.0,
                 'xmax': None}

    _plotLegend = {'style'        : 0,
                   'borderpad'    : 1.0,
                   'borderaxespad': 1.0,
                   'markerscale'  : 5.0,
                   'handletextpad': 0.5,
                   'handlelength' : 2.0,
                   'labelspacing' : 0.5}

    _plotLegendFont = {'size'  : 'small',
                       'style' : 'normal',
                       'family': ('serif', 'sans-serif', 'monospace')}

    def __init__(self, path):
        self.color_code_generator = _color_code_generator()
        super(HazardCurvePlot, self).__init__(path)

    def _init_file(self):

        # set figure size
        pylab.rcParams['figure.figsize'] = self._plotFig['figsize']

        # init and clear figure
        pylab.ax = pylab.subplot(111)
        pylab.clf()

    def write(self, data):
        """The method expects a dictionary that holds the end branch
        labels as keys. For each key, the value is a dictionary that holds
        the lists for IMLValues and Values of the hazard curve(s), the IMT
        and the site."""

        for end_branch_label in data:
 
            pylab.plot(data[end_branch_label]['IMLValues'], 
                       data[end_branch_label]['Values'], 
                       color=self.color_code_generator.next(), 
                       linestyle=self._plotCurve['linestyle'][2], 
                       label=end_branch_label)

        # set x and y dimension of plot
        pylab.ylim(self._plotAxes['ymin'], self._plotAxes['ymax'])
        xmin, xmax = pylab.xlim()
    
        pylab.xlabel(data[end_branch_label]['IMT'], self._plotLabelsFont)
        pylab.ylabel('Probability', self._plotLabelsFont)

        pylab.title("Hazard Curves for (%7.3f, %6.3f)" % (
            data[end_branch_label]['Site'].longitude, 
            data[end_branch_label]['Site'].latitude))

        pylab.legend(loc=self._plotLegend['style'],
                     markerscale=self._plotLegend['markerscale'],
                     borderpad=self._plotLegend['borderpad'],
                     borderaxespad=self._plotLegend['borderaxespad'],
                     handletextpad=self._plotLegend['handletextpad'],
                     handlelength=self._plotLegend['handlelength'],
                     labelspacing=self._plotLegend['labelspacing'],
                     prop=FontProperties(
                        size=self._plotLegendFont['size'],
                        style=self._plotLegendFont['style'],
                        family=self._plotLegendFont['family'][1]))

    def close(self):
        """Make sure the file is flushed, and send exit event."""
        pylab.savefig(self.path)
        pylab.close()

        self.finished.send(True)

def _color_code_generator():
    """Generator that walks through a sequence of color codes for matplotlib.
    When reaching the end of the color code list, start at the beginning again."""
    counter = 0
    while(True):
        counter += 1
        color_index = counter % len(COLOR_CODES)
        yield COLOR_CODES[color_index-1]
