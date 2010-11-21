# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module plots hazard curves as read from an NRML file.
As plotting engine, matplotlib is used.
The plots are in SVG format.
"""

import matplotlib
import numpy

from matplotlib.font_manager import FontProperties
matplotlib.use('SVG')

from pylab import *

#from osgeo import osr, gdal

from opengem import shapes
from opengem import writer

from opengem.parser import hazard as hazard_parser

IMAGE_FORMAT = "SVG"

#GDAL_PIXEL_DATA_TYPE = gdal.GDT_Float32
#SPATIAL_REFERENCE_SYSTEM = "WGS84"
#TIFF_BAND = 1
#TIFF_LONGITUDE_ROTATION = 0
#TIFF_LATITUDE_ROTATION = 0

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

        for counter, (nrml_point, nrml_attr) in enumerate(
            nrml_element.filter(region_constraint=None)):

            if counter == 0:

                plot(nrml_attr['IMLValues'], nrml_attr['Values'], 
                     color=self.__plotCurve['colors'][0], 
                     linestyle=self.__plotCurve['linestyle'][2], 
                     label=nrml_attr['IDmodel'])

                # set x and y dimension of plot
                ylim( self.__plotAxes['ymin'],  self.__plotAxes['ymax'] )
                xmin, xmax = xlim()
                #xlim(0.0, 3.0)
            
                xlabel(nrml_attr['IMT'], self.__plotLabelsFont)
                ylabel('Probability', self.__plotLabelsFont)
                title("Hazard Curve for %s" % nrml_point)

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
