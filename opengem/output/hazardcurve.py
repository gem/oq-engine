# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module plots hazard curves as read from an NRML file.
As plotting engine, matplotlib is used.
The plots are in SVG format.
"""

import geohash
import matplotlib
import numpy

from matplotlib.font_manager import FontProperties
matplotlib.use('SVG')

import pylab

from opengem import shapes
from opengem import writer

from opengem.parser import hazard as hazard_parser

IMAGE_FORMAT = "SVG"
COLOR_CODES = ('k', 'r', 'g', 'b')

class HazardCurvePlot(writer.FileWriter):
    """Plots hazard curves as given in an NRML file."""
    
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
                       'family': ('serif', 'sans-serif', 'monospace')
                       }

    def __init__(self, path):

        self.target = None
        self.color_code_generator = _color_code_generator()
        super(HazardCurvePlot, self).__init__(path)
        
    def _init_file(self):

        pylab.rcParams['figure.figsize'] = self._plotFig['figsize']

        # init and clear figure
        pylab.ax = pylab.subplot(111)
        pylab.clf()

    def write(self, hazardcurve_path):
        """The method expects a filename of an NRML file 
        with hazard curve(s)."""

        nrml_element = hazard_parser.NrmlFile(hazardcurve_path)
        data = {}

        # we collect hazard curves for one site into one plot
        # one plot contains hazard curves for several end branches of the logic tree
        # each end branch can have its own abscissa value set
        # for plotting, loop over end branches
        for (nrml_point, nrml_attr) in nrml_element.filter(
            region_constraint=None):

            if nrml_point.hash() not in data:
                data[nrml_point.hash()] = {}
        
            if nrml_attr['endBranchLabel'] not in data[nrml_point.hash()]:
                data[nrml_point.hash()][nrml_attr['endBranchLabel']] = {}

            data[nrml_point.hash()][nrml_attr['endBranchLabel']] = \
                {'IMLValues': nrml_attr['IMLValues'], 
                 'Values': nrml_attr['Values']}

        # FIXME(fab): select one of the sites manually
        selected_site_hash = min(data.keys())

        for end_branch_label in data[selected_site_hash]:
 
            pylab.plot(data[selected_site_hash][end_branch_label]['IMLValues'], 
                data[selected_site_hash][end_branch_label]['Values'], 
                color=self.color_code_generator.next(), 
                linestyle=self._plotCurve['linestyle'][2], 
                label=end_branch_label)

        # set x and y dimension of plot
        pylab.ylim(self._plotAxes['ymin'], self._plotAxes['ymax'])
        xmin, xmax = pylab.xlim()
    
        pylab.xlabel(nrml_attr['IMT'], self._plotLabelsFont)
        pylab.ylabel('Probability', self._plotLabelsFont)

        site_lat, site_lon = geohash.decode(selected_site_hash)
        pylab.title("Hazard Curves for (%7.3f, %6.3f)" % (site_lon, site_lat))

        pylab.legend(loc=self._plotLegend['style'],
                     markerscale=self._plotLegend['markerscale'],
                     borderpad=self._plotLegend['borderpad'],
                     borderaxespad=self._plotLegend['borderaxespad'],
                     handletextpad=self._plotLegend['handletextpad'],
                     handlelength=self._plotLegend['handlelength'],
                     labelspacing=self._plotLegend['labelspacing'],
                     prop=FontProperties(size=self._plotLegendFont['size'],
                                         style=self._plotLegendFont['style'],
                                         family=self._plotLegendFont['family'][1]))

    def close(self):
        """Make sure the file is flushed, and send exit event"""

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
    