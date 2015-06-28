import os
import importlib

from openquake.commonlib import sap, __version__

def oq_lite():
    modnames = ['openquake.commonlib.commands.%s' % mod[:-3]
                for mod in os.listdir(os.path.dirname(__file__))
                if mod.endswith('.py') and not mod.startswith('_')]
    parsers = [importlib.import_module(modname).parser for modname in modnames]
    parser = sap.compose(parsers, version=__version__)
    try:
        parser.callfunc()
    except NotImplementedError as exc:
        print 'Sorry, not implemented yet: %s' % exc
        raise
