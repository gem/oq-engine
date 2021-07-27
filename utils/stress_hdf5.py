import os
import time
import h5py
import numpy


def store(h5, num_gb):
    print(f'Allocating {num_gb} GB in memory')
    data = numpy.random.random((num_gb, 1024*1024*128))
    h5.create_dataset('data', data.shape)
    h5.swmr_mode = True
    t0 = time.time()
    for i in range(num_gb):
        h5['data'][i] = data[i]
        h5.flush()
        print(f'Stored {i+1} GB in {int(time.time()-t0)} seconds')
    speed = int(1024 * num_gb / (time.time() - t0))
    print('speed=%d MB/s' % speed)


if __name__ == '__main__':
    try:
        with h5py.File('tmp.hdf5', 'w', libver='latest') as h5:
            store(h5, 10)
    finally:
        os.remove('tmp.hdf5')
