from openquake.commonlib.datastore import view


def rst_table(table):
    """
    Build a .rst table from a list of rows. The first row is assumed to be
    the header. Here is an example:
    
    >>> tbl = [['Name', 'Value'], ['a', 1], ['b', 2]]
    >>> print rst_table(tbl)
    ==== =====
    Name Value
    ==== =====
    a    1    
    b    2    
    ==== =====
    """
    header = tuple(map(str, table[0]))
    col_sizes = map(len, header)
    body = []
    for row in table[1:]:
        row = tuple(map(str, row))
        for (i, col) in enumerate(row):
            col_sizes[i] = max(col_sizes[i], len(col))
        body.append(row)

    sepline = ' '.join(('=' * size for size in col_sizes))
    fmt = ' '.join(('%-{}s'.format(size) for size in col_sizes))
    lines = [sepline, fmt % header, sepline]
    for row in body:
        lines.append(fmt % row)

    lines.append(sepline)
    return '\n'.join(lines)


def classify_gsim_lt(gsim_lt):
    """
    :returns: "trivial", "simple" or "complex"
    """
    trt_gsims = gsim_lt.values.items()
    num_gsims = map(len, gsim_lt.values.itervalues())
    complex_trts = [trt for trt, gsims in trt_gsims if len(gsims) > 1]
    if all(n == 1 for n in num_gsims):  # one gsim per TRT
        return "trivial"
    elif len(complex_trts) == 1:
        return "simple"
    else:
        return "complex"


@view.add('csm_info')
def view_csm_info(token, dstore):
    rlzs_assoc = dstore['rlzs_assoc']
    csm_info = rlzs_assoc.csm_info
    rows = [['source_model', 'num_trts',
             'gsim_logic_tree', 'num_gsims', 'num_realizations']]
    for sm in csm_info.source_models:
        rlzs = rlzs_assoc.rlzs_by_smodel[sm.ordinal]
        num_rlzs = len(rlzs)
        num_branches = [n for n in sm.gsim_lt.get_num_branches().values() if n]
        num_paths = sm.gsim_lt.get_num_paths()
        num_gsims = ','.join(map(str, num_branches))
        tmodels = [tm for tm in sm.trt_models  # effective
                   if tm.trt in sm.gsim_lt.tectonic_region_types]
        row = (sm.name, len(tmodels), classify_gsim_lt(sm.gsim_lt),
               num_gsims, '%d/%d' % (num_rlzs, num_paths))
        rows.append(row)
    return rst_table(rows)
