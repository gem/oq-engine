# Point-source collapse benchmark

Exploratory benchmark of the point-source collapse option. The filtered
case uses `filter_sourcecodes = pPAM`, `area_source_discretization = 20`,
50 logic-tree samples, and `concurrent_tasks = 4`. The source logic tree was
adjusted in a temporary copy so that `applyToSources` branches for filtered
fault sources were removed. The benchmark uses three-decimal magnitude and
hypocenter grouping; representative strike and rake use rate-weighted
circular means. Higher magnitudes than the cutoff are left unchanged.

`Context rows` is `len(rup/mag)`. `Source CPU` is the sum of
`source_info.calc_time` across tasks; it is not wall-clock time. Curve deltas
are relative changes in mean PGA hazard probabilities at the IMLs shown.

| Collapse through M | Context rows | Reduction | Source CPU (s) | CPU speedup | Curve delta at PGA IMLs 0.01, 0.05, 0.1, 0.2, 0.5, 1.0 (%) |
|---:|---:|---:|---:|---:|---|
| None | 69,153 | — | 7.00 | 1.00x | 0, 0, 0, 0, 0, 0 |
| 5.5 | 50,887 | 26.4% | 6.89 | 1.02x | +0.35, +0.34, +0.34, +0.30, +0.13, 0 |
| 6.5 | 42,691 | 38.3% | 6.80 | 1.03x | +0.34, +0.26, +0.33, +0.73, +2.07, +2.83 |

These results are from a small, one-site model. They show substantial context
reduction but only a modest CPU-time improvement here; larger point-source
calculations are needed to establish end-to-end speedup. The cutoff also
provides a precision/performance tradeoff: 5.5 preserves the upper curve tail
in this case, while 6.5 gives a larger reduction with up to 2.83% change at
the highest tested IML.
