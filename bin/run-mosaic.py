import os
import sys
import glob


def main(mosaic_root):
    # $ time python bin/run-mosaic.py ~/mosaic | bash
    o = 'OQ_SAMPLE_SITES=.0005'
    p = 'calculation_mode=preclassical,number_of_logic_tree_samples=10,save_disk_space=1'
    e = 'calculation_mode=event_based,number_of_logic_tree_samples=10,save_disk_space=1'
    lf = '%s/x.log' % mosaic_root
    if os.path.exists(lf):
        os.remove(lf)
    for country in os.listdir(mosaic_root):
        if 'AUS' in country or 'CAN' in country:
            continue
        j = ' '.join(glob.glob('%s/%s/in/job*.ini' % (mosaic_root, country)))
        if j:
            print('%s oq engine -r --run %s -p %s -L %s' % (o, j, p, lf))
            print('%s oq engine -r --run %s -p %s -L %s' % (o, j, e, lf))


if __name__ == '__main__':
    main(sys.argv[1])
