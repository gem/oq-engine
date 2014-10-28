import textwrap
from openquake.commonlib import sap
from openquake.commonlib.calculators import calculators


def info(name):
    """
    Give information about the given name. For the moment, only the
    names of the available calculators are recognized.
    """
    if name in calculators:
        print textwrap.dedent(calculators[name].__doc__.strip())
    else:
        print "No info for '%s'" % name

parser = sap.Parser(info)
parser.arg('name', 'calculators name', choices=calculators)
