import textwrap
from openquake.commonlib import sap
from openquake.commonlib.calculators import calculator


def info(name):
    """
    Give information about the given name. For the moment, only the
    names of the available calculators are recognized.
    """
    if name in calculator:
        print textwrap.dedent(calculator[name].__doc__.strip())
    else:
        print "No info for '%s'" % name

parser = sap.Parser(info)
parser.arg('name', 'calculator name', choices=calculator)
