# EUR on cole

$ OQ_SAMPLE_SOURCES=.01 oq run EUR.zip -p calculation_mode=preclassical #10585
$ oq run EUR.zip --hc 10585 -c 3000
Reduced the number of point sources from 22_107 -> 21_393
tot_weight=132_713, max_weight=518, num_sources=21_393
Generated at most 266 tiles

# engine-3.20

Has a minor issue with saving the data (slow) so that tasks cannot
be resubmitted fasts enough and the queue of results goes up to
27 GB. There is no memory issue, I am using at most 687M per core.

# no gzip compression
| calc_10586, maxmem=99.9 GB | time_sec | memory_mb | counts      |
|----------------------------+----------+-----------+-------------|
| total classical            | 362_962  | 94.1      | 9_442       |
| get_poes                   | 196_138  | 0.0       | 25_184_121  |
| computing mean_std         | 69_680   | 0.0       | 539_403     |
| composing pnes             | 69_020   | 0.0       | 25_184_121  |
| planar contexts            | 19_294   | 0.0       | 100_168_055 |
| total fast_mean            | 8_816    | 121.4     | 2_996       |
| reading rates              | 8_760    | 121.4     | 2_996       |
| ClassicalCalculator.run    | 3_505    | 13_084    | 1           |
| iter_ruptures              | 3_332    | 0.0       | 3_597_256   |
| storing rates              | 2_470    | 790.3     | 9_442       |

# with gzip compression

There is compression both on the zmq packets and the saved rates.

# master

# engine-3.21
