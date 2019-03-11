import os
import sys
import pathlib
import collections
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import Starmap
from openquake.baselib.datastore import hdf5new


def count(text):
    c = collections.Counter()
    for word in text.split():
        c += collections.Counter(word)
    return c


def main(dirname):
    dname = pathlib.Path(dirname)
    with hdf5new() as hdf5:
        iterargs = ((open(dname/fname, encoding='utf-8').read(),)
                    for fname in os.listdir(dname) if fname.endswith('.rst'))
        c = collections.Counter()
        for counter in Starmap(count, iterargs, Monitor('count', hdf5)):
            c += counter
        print(c)
        print('Performance info stored in', hdf5)


if __name__ == '__main__':
    main(sys.argv[1])  # pass the directory where the .rst files are
