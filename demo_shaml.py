# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys

from opengem.parser import shaml
from opengem.output import kml

if __name__ == '__main__':
    name = 'tests/data/NshmpWusFaults.xml'
    if len(sys.argv) > 1:
        name = sys.argv[1]
    s = shaml.ShamlFile(name)
    k = kml.KmlFile('test.kml')
    for cell, value in s:
        k.write(cell, value)
    k.close()
