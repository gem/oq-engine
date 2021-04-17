import os
import sys
import pathlib
import collections
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import Starmap
from openquake.commonlib.datastore import hdf5new


def count(text):
    c = collections.Counter()
    for word in text.split():
        c += collections.Counter(word)
    return c


def main(dirname):
    dname = pathlib.Path(dirname)
    with hdf5new() as hdf5:  # create a new datastore
        monitor = Monitor('count', hdf5)  # create a new monitor
        iterargs = ((open(dname/fname, encoding='utf-8').read(),)
                    for fname in os.listdir(dname)
                    if fname.endswith('.rst'))  # read the docs
        c = collections.Counter()  # intially empty counter
        for counter in Starmap(count, iterargs, monitor):
            c += counter
        print(c)  # total counts
        print('Performance info stored in', hdf5)


if __name__ == '__main__':
    main(sys.argv[1])  # pass the directory where the .rst files are
