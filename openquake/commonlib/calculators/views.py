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
    num_gsims = sum(map(len, gsim_lt.values.itervalues()))
    num_trts = len(gsim_lt.values)
    if num_gsims == num_trts:  # one gsim per TRT
        return "trivial"
    elif num_trts == 1:
        return "simple"
    else:
        return "complex"


@view.add('composite_source_model')
def view_composite_source_model(token, dstore):
    csm_info = dstore['rlzs_assoc'].csm_info
    rows = [['source_model', 'num_trts', 'num_samples',
             'gsim_logic_tree', 'num_realizations']]
    for sm in csm_info.source_models:
        row = (sm.name, len(sm.trt_models), sm.samples,
               classify_gsim_lt(sm.gsim_lt),
               sm.gsim_lt.get_num_paths())
        rows.append(row)
    return rst_table(rows)
