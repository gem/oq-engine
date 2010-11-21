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

from pylab import *

from opengem import shapes
from opengem import writer

from opengem.parser import hazard as hazard_parser

IMAGE_FORMAT = "SVG"

class HazardCurvePlot(writer.FileWriter):
    """Plots hazard curves as given in an NRML file."""
    
    image_format = IMAGE_FORMAT
    
    __plotFig    = { 'figsize' : ( 10, 10 ) }

    __plotCurve = { 'markersize' : None,
                    'color': 'r',
                    'colors': ( 'r', 'b' ),
                    'linestyle' : ( 'steps', '-', '-' ),
                    'linewidth' : 1 }
                    
    __plotConfidenceBounds = { 'markersize' : None,
                               'color': 'k',
                               'facecolor' : '0.80',       # 0.90
                               'edgecolor' : '0.80',       # 0.90
                               'alpha': 0.5,
                               'linestyle' : '--',
                               'linewidth' : 1,
                               'shadeLowerLimit': 0.0,     # 0.00
                               'shadeUpperLimit': 1.0 }    # 0.99

    __plotLabels = { 'ylabel_size'     : None,
                     'ylabel_rotation' : None }
                     
    __plotLabelsFont = { 'fontname'   : 'serif',     # sans
                         'fontweight' : 'normal',    # bold
                         'fontsize'   :  13 }
                         
    __plotAxes = { 'ymin' : 0.0,
                   'ymax' : 1.0,
                   'xmin' : 0.0,
                   'xmax' : None }
                   
    __plotLegend = { 'style'         : 0,
                     'borderpad'     : 1.0,
                     'borderaxespad' : 1.0,
                     'markerscale'   : 5.0,
                     'handletextpad' : 0.5,
                     'handlelength'  : 2.0,
                     'labelspacing'  : 0.5 }
                     
    __plotLegendFont = { 'size'   : 'small',
                         'style'  : 'normal',
                         'family' : ( 'serif', 'sans-serif', 'monospace' )       # sans-serif
                       }
                           
    __plotCanvasFill = { 'facecolor' : '0.90' }

    __plotZOrder = { 'modification' :   1,
                     'vertical'     :  20,
                     'grid'         :  25,
                     'rejection'    :  30,
                     'curve'        :  40,
                     'legend'       :  50,
                     'axes'         : 100 }

    def __init__(self, path):

        self.target = None
        super(HazardCurvePlot, self).__init__(path)
        
    def _init_file(self):

        rcParams['figure.figsize'] = self.__plotFig['figsize']

        # clear figure
        ax = subplot(111)
        clf()

    def write(self, hazardcurve_path):
        """The method expects a filename of an NRML file 
        with hazard curve(s)."""

        nrml_element = hazard_parser.NrmlFile(hazardcurve_path)

        data = {}

        # we collect hazard curves for one site into one plot
        # one plot contains hazard curves for several end branches of the logic tree
        # each end branch can have its own abscissae
        # for plotting, loop over end branches
        for counter, (nrml_point, nrml_attr) in enumerate(
            nrml_element.filter(region_constraint=None)):

            if nrml_point.hash() not in data:
                data[nrml_point.hash()] = {}
        
            if nrml_attr['endBranchLabel'] not in data[nrml_point.hash()]:
                data[nrml_point.hash()][nrml_attr['endBranchLabel']] = {}

            data[nrml_point.hash()][nrml_attr['endBranchLabel']] = \
                {'IMLValues': nrml_attr['IMLValues'], 
                 'Values': nrml_attr['Values']}

        # select one of the sites
        selected_site_hash = min(data.keys())
        selected_branch = '1_1'

        plot(data[selected_site_hash][selected_branch]['IMLValues'], 
             data[selected_site_hash][selected_branch]['Values'], 
             color=self.__plotCurve['colors'][0], 
             linestyle=self.__plotCurve['linestyle'][2], 
             label=selected_branch)

        # set x and y dimension of plot
        ylim( self.__plotAxes['ymin'],  self.__plotAxes['ymax'] )
        xmin, xmax = xlim()
    
        xlabel(nrml_attr['IMT'], self.__plotLabelsFont)
        ylabel('Probability', self.__plotLabelsFont)

        site_lat, site_lon = geohash.decode(selected_site_hash)
        title("Hazard Curves for (%7.3f, %6.3f)" % (site_lon, site_lat))

        legend( loc = self.__plotLegend['style'],
                markerscale = self.__plotLegend['markerscale'],
                borderpad = self.__plotLegend['borderpad'],
                borderaxespad = self.__plotLegend['borderaxespad'],
                handletextpad = self.__plotLegend['handletextpad'],
                handlelength = self.__plotLegend['handlelength'],
                labelspacing = self.__plotLegend['labelspacing'],
                prop = FontProperties(size=self.__plotLegendFont['size'],
                                        style=self.__plotLegendFont['style'],
                                        family=self.__plotLegendFont['family'][1]) )

    def close(self):
        """Make sure the file is flushed, and send exit event"""

        savefig(self.path)
        close()

        self.finished.send(True)
    
    def serialize(self, iterable):
        # TODO(JMC): Normalize the values
        #maxval = max(iterable.values())
        #for key, val in iterable.items():
            #self.write((key.column, key.row), val/maxval * 254)
        #self.close()
        pass
