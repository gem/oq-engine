import ConfigParser
import csv
import os
from lxml import etree

from openquake import nrmllib


def _collect_source_model_paths(smlt):
    """
    Given a path to a source model logic tree or a file-like, collect all of
    the soft-linked path names to the source models it contains and return them
    as a uniquified list (no duplicates).
    """
    src_paths = []
    tree = etree.parse(smlt)
    for branch_set in tree.xpath('//nrml:logicTreeBranchSet',
                                 namespaces=nrmllib.PARSE_NS_MAP):

        if branch_set.get('uncertaintyType') == 'sourceModel':
            for branch in branch_set.xpath(
                    './nrml:logicTreeBranch/nrml:uncertaintyModel',
                    namespaces=nrmllib.PARSE_NS_MAP):
                src_paths.append(branch.text)
    return sorted(set(src_paths))


def parse_config(source):
    """Parse a dictionary of parameters from an INI-style config file.

    :param source:
        File-like object containing the config parameters.
    :returns:
        A dictionary containing all of the parameters/values parsed from
        the job.ini file as well as a subdictionary 'inputs' containing
        absolute paths to all of the files referenced in the job.ini, keyed by
        the parameter name.
    """
    cp = ConfigParser.ConfigParser()
    cp.readfp(source)

    base_path = os.path.dirname(
        os.path.join(os.path.abspath('.'), source.name))
    params = dict(base_path=base_path)
    params['inputs'] = dict()

    # Directory containing the config file we're parsing.
    base_path = os.path.dirname(os.path.abspath(source.name))

    for sect in cp.sections():
        for key, value in cp.items(sect):
            if key == 'sites_csv':
                # Parse site coordinates from the csv file,
                # return as a string 'lon1 lat1, lon2 lat2, ... , lonN latN'
                path = value
                if not os.path.isabs(path):
                    # It's a relative path
                    path = os.path.join(base_path, path)
                params['sites'] = _parse_sites_csv(open(path, 'r'))
            elif key.endswith('_file'):
                input_type = key[:-5]
                path = value
                # The `path` may be a path relative to the config file, or it
                # could be an absolute path.
                if not os.path.isabs(path):
                    # It's a relative path.
                    path = os.path.join(base_path, path)

                params['inputs'][input_type] = path
            else:
                params[key] = value

    # convert back to dict as defaultdict is not pickleable
    params['inputs'] = dict(params['inputs'])

    # load source inputs (the paths are the source_model_logic_tree)
    smlt = params['inputs'].get('source_model_logic_tree')
    if smlt:
        params['inputs']['source'] = [
            os.path.join(base_path, src_path)
            for src_path in _collect_source_model_paths(smlt)]

    return params


def _parse_sites_csv(fh):
    """
    Get sites of interest from a csv file. The csv file (``fh``) is expected to
    have 2 columns: lon,lat.

    :param fh:
        File-like containing lon,lat coordinates in csv format.

    :returns:
        lon-lat pairs representing all of the sites in the csv file.
    """
    reader = csv.reader(fh)
    coords = []
    for lon, lat in reader:
        coords.append('%s %s' % (lon, lat))
    return ', '.join(coords)
