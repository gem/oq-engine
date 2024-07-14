# EUR on cole

$ OQ_SAMPLE_SOURCES=.01 oq run EUR.zip -p calculation_mode=preclassical #10585
$ oq run EUR.zip --hc 10585 -c 3000
Reduced the number of point sources from 22_107 -> 21_393
tot_weight=132_713, max_weight=518, num_sources=21_393
Generated at most 266 tiles

# engine-3.20

Has a minor issue with saving the data (slow) so that tasks cannot
be resubmitted fasts enough and the queue of results goes up to
8 GB.

There is compression both on the zmq packets and the saved rates.

# master

# engine-3.21
