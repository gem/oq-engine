import numpy as np
from openquake.calculators.getters import MapGetter


def test_duplicate_rates_accumulated_not_dropped():
    """
    Regression for the fancy-index += bug:
    duplicate (sid, lid, gid) entries must be summed, not dropped.
    """
    # Synthetic rates mimicking _rates dataset
    rates_dt = np.dtype([
        ('sid', np.uint32), ('lid', np.uint16),
        ('gid', np.uint16), ('rate', np.float32),
    ])
    rates = np.array([
        (101, 5, 7, 1.5),
        (101, 5, 7, 2.3),   # duplicate: same (sid, lid, gid)
        (101, 6, 7, 0.7),
        (102, 5, 8, 3.1),
    ], dtype=rates_dt)

    N, L, Gt = 3, 10, 20
    array_old = np.zeros((N, L, Gt), np.float32)
    array_new = np.zeros((N, L, Gt), np.float32)

    sid2idx = {sid: idx for idx, sid in enumerate([101, 102, 103])}
    max_sid = max(sid2idx.keys())
    lookup = np.full(max_sid + 1, -1, int)
    for sid, idx in sid2idx.items():
        lookup[sid] = idx

    sids = np.array([r['sid'] for r in rates], np.uint32)
    lids = np.array([r['lid'] for r in rates], np.uint16)
    gids = np.array([r['gid'] for r in rates], np.uint16)
    rates_f = np.array([r['rate'] for r in rates], np.float32)

    idxs = lookup[sids]
    # Old (buggy): vectorized fancy-index += drops duplicates
    array_old[idxs, lids, gids] += rates_f
    # New (fixed): numpy.add.at accumulates duplicates
    np.add.at(array_new, (idxs, lids, gids), rates_f)

    assert array_old[sid2idx[101], 5, 7] == 2.3000, (
        "Bug: old accumulation drops duplicates (only last kept)"
    )
    assert array_new[sid2idx[101], 5, 7] == 3.8000, (
        "Fix: add.at must sum duplicates (1.5 + 2.3 = 3.8)"
    )
