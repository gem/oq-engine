import os
import sys
import glob


def main(mosaic_root):
    # $ time python bin/run-mosaic.py ~/mosaic | bash
    o = 'OQ_SAMPLE_SITES=.0005'
    p = 'calculation_mode=preclassical,number_of_logic_tree_samples=10'
    e = 'calculation_mode=event_based,number_of_logic_tree_samples=10'
    lf = '%s/x.log' % mosaic_root
    if os.path.exists(lf):
        os.remove(lf)
    for name in glob.glob(mosaic_root + '/*/*/job*.ini'):
        if 'AUS' in name or 'CAN' in name:
            continue
        print('%s oq engine -r --run %s -p %s -L %s' % (o, name, p, lf))
        print('%s oq engine -r --run %s -p %s -L %s' % (o, name, e, lf))


if __name__ == '__main__':
    main(sys.argv[1])
