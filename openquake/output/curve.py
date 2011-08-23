# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
This module plots curves (hazard/loss/loss ratio) as read from an NRML file.
As plotting engine, matplotlib is used. The plots are in SVG format.
"""

import matplotlib
matplotlib.use('SVG')
import pylab

from matplotlib.font_manager import FontProperties

from openquake import writer
from openquake.parser import hazard as hazard_parser
from openquake.parser import risk as risk_parser

IMAGE_FORMAT = "SVG"
COLOR_CODES = ('k', 'r', 'g', 'b')

CURVE_BRANCH_PLACEHOLDER = 'Curve'


class CurvePlotter(object):
    """Base class for plotting curves from NRML files to SVG.
    For a specific curve plot (hazard/loss/loss ratio),
    a class has to be derived from this one."""

    def __init__(self, output_base_path, nrml_input_path, curve_title=None,
                 render_multi=False):

        # remove trailing .svg extension from output file name (if existing)
        self.output_base_path = output_base_path
        if self.output_base_path.endswith(('.svg', '.SVG')):
            self.output_base_path = self.output_base_path[0:-4]

        self.nrml_input_path = nrml_input_path
        self.curve_title = curve_title
        self.data = {}

        self._parse_nrml_file()
        self.render_multi = render_multi
        if render_multi:
            self.svg_filenames = [self.nrml_input_path.replace('xml', 'svg')]
        else:
            self.svg_filenames = [sd['path'] for sd in self.data.values()]

    def _parse_nrml_file(self):
        """Parse curve data from NRML file into a dictionary, has to
        be implemented by the derived class."""
        pass

    def plot(self, autoscale_y=True):
        """Create a plot for each site in the dataset.
        The argument autoscale_y auto-scales the ordinate axis (default).
        If set to false, the displayed ordinate range is 0...1.
        TODO(fab): let user specify abscissa and ordinate range for plot."""

        if self.render_multi:
            self.__plot_multi(autoscale_y)
        else:
            self.__plot_single(autoscale_y)

    def __plot_single(self, autoscale_y):
        """ Plot only a single curve on the svg """
        for site_data in self.data.values():
            plot = CurvePlot(site_data['path'])
            plot.write(site_data['curves'], autoscale_y)
            plot.close()

    def __plot_multi(self, autoscale_y):
        """ Plot multiple curves on the same svg """
        plot_path = self.svg_filenames[0]
        plot = CurvePlot(plot_path, use_title=True)
        for site_data in self.data.values():
            plot.write(site_data['curves'], autoscale_y)
        plot.close()

    def filenames(self):
        """ Generator yields the path value for each dict in self.data """
        return (path for path in self.svg_filenames)

    def _generate_filename(self, site):
        """ Return a file name string """
        return "%s_%7.3f_%6.3f.svg" % (
            self.output_base_path, site.longitude, site.latitude)


class RiskCurvePlotter(CurvePlotter):
    """This class plots loss/loss ratio curves as read from an NRML file. For
    each Site listed in the NRML file, a separate plot is created. A plot
    contains only one curve, multiple curves per plot are currently not
    supported by the NRML schema.
    TODO(fab): In the future, we may want to plot loss/loss ratio curves
    per asset, multiple assets per site (according to Vitor)."""

    def __init__(self, output_base_path, nrml_input_path, mode='loss',
                 curve_title=None, render_multi=False):
        """mode can be 'loss' or 'loss_ratio', 'loss' is the default."""
        self.mode = mode

        if curve_title is None:
            if self.mode == 'loss_ratio':
                curve_title = 'Loss Ratio Curve'
            else:
                curve_title = 'Loss Curve'

        super(RiskCurvePlotter, self).__init__(output_base_path,
            nrml_input_path, curve_title, render_multi)

    def _parse_nrml_file(self):
        """Parse loss/loss ratio curve data from NRML file into dictionary."""

        if self.mode == 'loss_ratio':
            nrml_element = risk_parser.LossRatioCurveXMLReader(
                self.nrml_input_path)
        else:
            nrml_element = risk_parser.LossCurveXMLReader(self.nrml_input_path)

        # loss/loss ratio curves have a common *ordinate* for all curves
        # in an NRML file
        for (nrml_point, nrml_attr) in nrml_element.filter(
            region_constraint=None):

            site_hash = hash(nrml_point)
            curve_id = nrml_attr['assetID']

            if site_hash not in self.data:
                self.data[site_hash] = {
                    # capture SVG filename for each site
                    'path': self._generate_filename(nrml_point),
                    'curves': {}}

            if curve_id not in self.data[site_hash]['curves']:
                self.data[site_hash]['curves'][curve_id] = {}

            self.data[site_hash]['curves'][curve_id] = {
                'abscissa': nrml_attr[nrml_element.abscissa_output_key],
                'abscissa_property': nrml_element.abscissa_property,
                'ordinate': nrml_attr[nrml_element.ordinate_output_key],
                'ordinate_property': nrml_element.ordinate_property,
                'Site': nrml_point,
                'curve_title': self.curve_title}


class HazardCurvePlotter(CurvePlotter):
    """This class plots hazard curves as read from an NRML file. For
    each Site listed in the NRML file, a separate plot is created. A plot
    can contain multiple hazard curves, one for each logic tree end branch
    given in the NRML file."""

    def __init__(self, output_base_path, nrml_input_path, curve_title=None,
                 render_multi=False):

        if curve_title is None:
            curve_title = 'Hazard Curves'

        super(HazardCurvePlotter, self).__init__(output_base_path,
            nrml_input_path, curve_title, render_multi=False)

    def _parse_nrml_file(self):
        """Parse hazard curve data from NRML file into a dictionary."""

        nrml_element = hazard_parser.NrmlFile(self.nrml_input_path)

        # we collect hazard curves for one site into one plot
        # one plot contains hazard curves for several end branches
        # of the logic tree
        # each end branch can have its own abscissa value set
        for (nrml_point, nrml_attr) in nrml_element.filter(
            region_constraint=None):

            site_hash = hash(nrml_point)
            ebl = nrml_attr['endBranchLabel']

            if site_hash not in self.data:
                self.data[site_hash] = {
                    # capture SVG filename for each site
                    'path': self._generate_filename(nrml_point),
                    'curves': {}}

            if ebl not in self.data[site_hash]['curves']:
                self.data[site_hash]['curves'][ebl] = {}

            self.data[site_hash]['curves'][ebl] = {
                'abscissa': nrml_attr['IMLValues'],
                'abscissa_property': nrml_attr['IMT'],
                'ordinate': nrml_attr['Values'],
                'ordinate_property': 'Probability of Exceedance',
                'Site': nrml_point,
                'curve_title': self.curve_title}


class CurvePlot(writer.FileWriter):
    """Creates an SVG  plot containing curve data for one site.
    At the moment, the class is used for hazard, loss, and loss ratio curves.
    One plot can contain several curves. In the case of hazard curves, this
    would be one curve for each end branch of a logic tree. For loss/loss
    ratio curves, the multiple curve feature is not applicable."""

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

    _plotLegend = {'style': 0,
                   'borderpad': 1.0,
                   'borderaxespad': 1.0,
                   'markerscale': 5.0,
                   'handletextpad': 0.5,
                   'handlelength': 2.0,
                   'labelspacing': 0.5}

    _plotLegendFont = {'size': 'small',
                       'style': 'normal',
                       'family': ('serif', 'sans-serif', 'monospace')}

    def __init__(self, path, use_title=False):
        self.use_title = use_title
        self.color_code_generator = _color_code_generator()
        super(CurvePlot, self).__init__(path)

    def _init_file(self):

        # set figure size
        pylab.rcParams['figure.figsize'] = self._plotFig['figsize']

        # init and clear figure
        pylab.ax = pylab.subplot(111)
        pylab.clf()

    def write(self, data, autoscale_y=True):
        """
        The method expects a dictionary that holds the labels for the separate
        curves to be plotted as keys. For each key, the corresponding value is
        a dictionary that holds lists for abscissa and ordinate values, strings
        for abscissa and ordinate properties, and the title of the plot, and
        the site as shapes.Site object..
        """

        for curve in data:
            pylab.plot(data[curve]['abscissa'],
                       data[curve]['ordinate'],
                       color=self.color_code_generator.next(),
                       linestyle=self._plotCurve['linestyle'][2],
                       label=curve)

        # set x and y dimension of plot
        if autoscale_y is False:
            pylab.ylim(self._plotAxes['ymin'], self._plotAxes['ymax'])

        curve = data.keys()[0]  # We apparently only need to get this once?
        pylab.xlabel(data[curve]['abscissa_property'], self._plotLabelsFont)
        pylab.ylabel(data[curve]['ordinate_property'], self._plotLabelsFont)

        self._set_title(curve, data)

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

    def _set_title(self, curve, data):
        """Set the title of this plot using the given site. Use just
        the title in case there's not site related."""
        try:
            if self.use_title:
                # Multiple curves shouldn't use a site specific long/lat
                raise KeyError

            pylab.title("%s for (%7.3f, %6.3f)" % (
                    data[curve]['curve_title'],
                    data[curve]['Site'].longitude,
                    data[curve]['Site'].latitude))
        except KeyError:
            # no site related to this curve
            pylab.title("%s" % data[curve]['curve_title'])

    def close(self):
        """Make sure the file is flushed, and send exit event."""
        pylab.savefig(self.path)
        pylab.close()


def _color_code_generator():
    """Generator that walks through a sequence of color codes for matplotlib.
    When reaching the end of the color code list, start at the beginning again.
    """
    while(True):
        for code in COLOR_CODES:
            yield code
