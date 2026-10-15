# Synthetic compatibility fixtures

These files are software tests. Their shaking values, building inventories
and fragility curves are invented. Coordinates near Tokyo Station and
Shinjuku supply two realistic-looking locations, but no damage prediction
for either locality is implied. `DEMO_WOOD` and `DEMO_RC` are test labels,
not classifications from a Japanese study.

Each shaking CSV has two events at both sites. `exposure.csv` has three
asset groups with counts 10, 20 and 30. Two groups share the first site.
The same probability tables are used on different intensity axes to
exercise native JMA and PGA separately. This is not a JMA-to-PGA relation.

For linear interpolation of these discrete curves and expected damage,
the independently calculated totals are:

| Event | No damage | Slight only | Complete | Total |
| --- | ---: | ---: | ---: | ---: |
| 0 | 43 | 11 | 6 | 60 |
| 1 | 32.5 | 13.5 | 14 | 60 |
| Equal-event mean | 37.75 | 12.25 | 10 | 60 |

Exceedance probability for `slight` includes `complete`. Thus the exclusive
slight probability is `P(slight or worse) - P(complete)`, and the no-damage
probability is `1 - P(slight or worse)`. Fractional counts are expected
numbers, not a claim that part of a particular building is damaged.

The metadata's `synthetic_horizontal` component is a test convention.
Real JMA metadata must describe its own instrumental intensity definition,
rather than inherit this placeholder.
