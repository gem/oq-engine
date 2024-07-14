# EUR on cole

$ OQ_SAMPLE_SOURCES=.01 oq run EUR.zip -p calculation_mode=preclassical #10585
$ oq run EUR.zip --hc 10585 -c 3000
Reduced the number of point sources from 22_107 -> 21_393
tot_weight=132_713, max_weight=518, num_sources=21_393
Generated at most 266 tiles

# engine-3.20

Has a minor issue with saving the data (slow) so that tasks cannot
be resubmitted fasts enough and the queue of results goes up to
27 GB. There is no memory issue, I am using at most 1077M per core.

# no zmq compression
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

| operation-duration | counts | mean    | stddev | min     | max     | slowfac |
|--------------------+--------+---------+--------+---------+---------+---------|
| classical          | 4_050  | 89.6    | 09%    | 0.94719 | 114.4   | 1.27648 |
| fast_mean          | 2_996  | 2.94266 | 27%    | 0.01452 | 5.06240 | 1.72035 |

| task      | sent                                              | received  |
|-----------+---------------------------------------------------+-----------+
| classical | sitecol=65.06 GB cmaker=510.71 MB dstore=660.5 KB | 128.47 GB |
| fast_mean | pgetter=91.86 MB gweights=24.29 MB                | 1.81 GB   |

# with zmq compression the result queue is much smaller and we produce less outputs,
# so it is faster, expecially in "planar contexts" and "storing rates"

| calc_10587, maxmem=94.7 GB | time_sec | memory_mb | counts     |
|----------------------------+----------+-----------+------------|
| total classical            | 354_679  | 99.6      | 4_771      |
| get_poes                   | 192_400  | 0.0       | 24_348_287 |
| computing mean_std         | 68_347   | 0.0       | 521_346    |
| composing pnes             | 67_439   | 0.0       | 24_348_287 |
| planar contexts            | 18_483   | 0.0       | 97_845_201 |
| total fast_mean            | 8_731    | 108.8     | 2_996      |
| reading rates              | 8_675    | 108.8     | 2_996      |
| ClassicalCalculator.run    | 4_112    | 4_127     | 1          |
| iter_ruptures              | 3_100    | 0.0       | 3_489_359  |
| storing rates              | 2_380    | 241.5     | 4_771      |

| operation-duration | counts | mean    | stddev | min     | max     | slowfac |
|--------------------+--------+---------+--------+---------+---------+---------|
| classical          | 4_050  | 87.6    | 11%    | 0.99199 | 129.8   | 1.48183 |
| fast_mean          | 2_996  | 2.91415 | 27%    | 0.01258 | 4.74377 | 1.62784 |

| task      | sent                                              | received |
|-----------+---------------------------------------------------+----------+
| classical | sitecol=26.36 GB cmaker=510.71 MB dstore=660.5 KB | 42.29 GB |
| fast_mean | pgetter=91.85 MB gweights=24.29 MB                | 1.48 GB  |

There is gzip compression on the saved rates.

| /home/michele/oqdata/calc_10587.hdf5 | 44.78 GB  |

# master

There is no compression of the zmq packets and no gzip compression.
Also, source_data is not returned, so it is much faster

$ oq run EUR.zip --hc 10589 -c 3000
# "reading rates" is terribly bad!!
# no gzip compression, save_on_custom_tmp=false
| calc_10590, maxmem=303.5 GB | time_sec | memory_mb | counts     |
|-----------------------------+----------+-----------+------------|
| total classical             | 446_776  | 126.9531  | 3_095      |
| get_poes                    | 196_059  | 0.0       | 71_419_362 |
| computing mean_std          | 157_309  | 0.0       | 2_925_140  |
| composing pnes              | 70_421   | 0.0       | 71_419_362 |
| total fast_mean             | 56_250   | 1_273     | 256        |
| reading rates               | 56_083   | 1_273     | 256        |
| planar contexts             | 14_789   | 0.0       | 74_033_936 |
| ClassicalCalculator.run     | 4_686    | 5_455     | 1          |

| operation-duration | counts | mean     | stddev | min      | max      | slowfac |
|--------------------+--------+----------+--------+----------+----------+---------|
| classical          | 3_095  | 144.3542 | 16%    | 1.1218   | 167.5341 | 1.1606  |
| fast_mean          | 256    | 219.7    | 11%    | 159.5140 | 301.7    | 1.3730  |

| task      | sent                                               | received  |
|-----------+----------------------------------------------------+-----------+
| classical | sitecol=50.01 GB cmaker=382.57 MB dstore=504.75 KB | 128.39 GB |
| fast_mean | pgetter=4.71 MB                                    | 616.49 MB |

| /home/michele/oqdata/calc_10590.hdf5 | 128.79 GB |

The result queue goes up to 25.5G.
I see up top 3.8G per core used.

# engine-3.21

# Is it a good idea to compress the zmq packets?

Yes, because the result queue will be much smaller and your master node
will not run out of memory
Yes, because the packets will be smaller and zmq will be less likely to hang
No, because the decompression on the master node will make everything slower;
for EUR the penalty was significant: from 58m to 1h9m, 17% more.


# Is it a good idea to compress the rates in the datastore?

No, because "reading rates" will be much slower:

| calc_10592, maxmem=308.4 GB | time_sec | memory_mb | counts     |
|-----------------------------+----------+-----------+------------|
| reading rates               | 57_596   | 1_268     | 256        |
| reading rates               | 65_468   | 1_272     | 256        |

The performance penalty will be terrible:
ClassicalCalculator.run 4_784  -> 
