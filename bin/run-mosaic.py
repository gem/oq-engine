import sys
import glob


def main(mosaic_root):
    o = 'OQ_SAMPLE_SITES=.0005'
    p = 'calculation_mode=preclassical,number_of_logic_tree_paths=1'
    e = 'calculation_mode=event_based,number_of_logic_tree_paths=1'
    for name in glob.glob(mosaic_root + '/*/*/job*.ini'):
        if 'AUS' in name or 'CAN' in name:
            continue
        print('%s oq engine -r --run %s -p %s' % (o, name, p))
        print('%s oq engine -r --run %s -p %s' % (o, name, e))


if __name__ == '__main__':
    main(sys.argv[1])
