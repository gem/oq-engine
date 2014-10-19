from openquake.commonlib import nrml, readinput, sap


def check(fname, pprint):
    """
    Check the validity of NRML files and .ini files.
    Optionally, displays NRML files in indented format.
    """
    if fname.endswith('.xml'):
        node = nrml.read(fname)
        if pprint:
            print node.to_str()
    elif fname.endswith('.ini'):
        oqparam = readinput.getoqparam(fname)
        if pprint:
            print oqparam


parser = sap.Parser(check)
parser.arg('fname', 'file in NRML format or job.ini file')
parser.flg('pprint', 'display in indented format')
