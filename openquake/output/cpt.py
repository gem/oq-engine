# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
This module contains some utilities for reading cpt colormap files.

For a good source of cpt examples, visit: http://soliton.vm.bytemark.co.uk
"""

import re


class CPTReader(object):
    """This class provides utilities for reading colormap data from cpt files.

    Colormaps have the following properties:

    - z-values: Any sequence of numbers (example: [-2.5, -2.4, ... , 1.4, 1.5])
    - colormap Id (example: seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp)
    - colormap name (example: seminf-haxby)
    - color model (RGB, HSV, or CMYK)
    - RGB, HSV, or CMYK values associated with the ranges defined by the
      z-values
    - Background color
    - Foreground color
    - NaN color
    - colormap type (discrete or continuous; this is determined by the
      arrangement of z- and color values)

    Example RGB colormap:
        {'id': 'seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp',
         'name': 'seminf-haxby',
         'type': 'discrete',
         'model': 'RGB',
         'z_values': [0.00, 1.25, 2.50, ... , 28.75, 30.00],
         'red': [255, 208, 186, ... , 244, 238],
         'green': [255, 216, 197, ... , 116, 79],
         'blue': [255, 251, 247, ... , 74, 77],
         'background': [255, 255, 255],
         'foreground': [238, 79, 77],
         'NaN': [0, 0, 0]}

    See also:
        Library of cpt files:
            http://soliton.vm.bytemark.co.uk
        MAKECPT:
            http://www.soest.hawaii.edu/gmt/gmt/doc/gmt/html/man/makecpt.html

    TODO(LB): Currently, only RGB colormaps are supported. HSV and CMYK
    colormaps are not supported.
    """

    SUPPORTED_COLOR_MODELS = ('RGB',)

    NAME_RE = re.compile(r'^(.+).cpt$')
    ID_RE = re.compile(r'\$Id:\s+(.+)\s+\$')
    COLOR_MODEL_RE = re.compile(r'^COLOR_MODEL\s+=\s+(.+)')

    def __init__(self, path):
        """
        :param path: location of a cpt file, including file name
        :type path: string
        """
        self.path = path
        self.colormap = {
            'id': None,
            'name': None,
            'type': None,
            'model': None,
            'z_values': [],
            'red': [],
            'green': [],
            'blue': [],
            'background': None,
            'foreground': None,
            'NaN': None}

    def get_colormap(self):
        """
        Read the input cpt file and attempt to parse colormap data.

        :returns: dict representation of the colormap
        """
        with open(self.path, 'r') as fh:
            for line in fh:
                # ignore empty lines
                if not line.strip():
                    continue
                elif line[0] == '#':
                    self._parse_comment(line)
                elif line[0] in ['B', 'F', 'N']:
                    self._parse_bfn(line)
                else:
                    self._parse_color_table(line)
        if not self.colormap['model'] in self.SUPPORTED_COLOR_MODELS:
            raise ValueError('Color model type %s is not supported' %
                             self.colormap['model'])
        return self.colormap

    def _parse_comment(self, line):
        """
        Look for name, id, and color model type in a comment line
        (beginning with a '#').

        :param line: a single line read from the cpt file
        """
        text = line.split('#')[1].strip()
        for attr, regex in  (('name', self.NAME_RE),
                             ('id', self.ID_RE),
                             ('model', self.COLOR_MODEL_RE)):
            # if the attr is already defined, skip it
            if self.colormap[attr]:
                continue
            match = regex.match(text)
            if match:
                self.colormap[attr] = match.group(1)

    def _parse_bfn(self, line):
        """
        Parse Background, Foreground, and NaN values from the color table.

        :param line: a single line read from the cpt file
        """
        for token, key in (('B', 'background'),
                           ('F', 'foreground'),
                           ('N', 'NaN')):
            if line[0] == token:
                _bfn, color = line.split(token)
                self.colormap[key] = [int(i) for i in color.split()]
                return

    def _protect_map_type(self, map_type):
        """
        Prevent the parser from changing map types (discrete vs. continuous),
        which could be caused by a malformed cpt file.

        If a map type is defined (not None) and then changed, this will throw
        an :py:exc: `AssertionError`.

        :param map_type: 'discrete' or 'continuous'
        """
        assert (self.colormap['type'] is None
                or self.colormap['type'] == map_type)

    def _parse_color_table(self, line):
        """
        Parse z-values and color values from the color table.

        The map type (discrete or continuous) is also implicity determined from
        these values.

        :param line: a single line read from the cpt file
        """
        drop_tail_extend = lambda lst, ext: lst[:-1] + [x for x in ext]
        strs_to_ints = lambda strs: [int(x) for x in strs]

        values = line.split()
        assert len(values) == 8

        # there are two columns of values (each containing z and color values)
        z_vals = (float(values[0]), float(values[4]))
        self.colormap['z_values'] = drop_tail_extend(self.colormap['z_values'],
                                                     z_vals)

        rgb1 = strs_to_ints(values[1:4])
        rgb2 = strs_to_ints(values[5:8])
        if rgb1 == rgb2:
            map_type = 'discrete'
        else:
            map_type = 'continuous'
        try:
            self._protect_map_type(map_type)
        except AssertionError:
            raise ValueError("Could not determine map type (discrete or"
                             " continuous). The cpt file could be malformed.")
        self.colormap['type'] = map_type

        for i, color in enumerate(('red', 'green', 'blue')):
            if map_type == 'discrete':
                self.colormap[color].append(rgb1[i])
            elif map_type == 'continuous':
                self.colormap[color] = drop_tail_extend(self.colormap[color],
                                                        (rgb1[i], rgb2[i]))
            else:
                raise ValueError("Unknown map type '%s'" % map_type)
