# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')

def generate_demofile(name, values):
    path = os.path.join(data_dir, name)
    f = open(path, 'w')
    for i in xrange(150):
        for j in xrange(150):
            value = values[(i + j) % len(values)]
            f.write('%02f %02f %s\n' % (i, j, value))
    f.close()

if __name__ == '__main__':
    #shakemap_values = ['really shaking!', 'shaking a bit', 'not shaking']
    #exposure_values = ['really exposed!', 'exposed a bit', 'not exposed']
    #v11y_values = ['really vulny!', 'vulny a bit', 'not vulny']
    shakemap_values = [0.0, 5.0, 9.0]
    exposure_values = [0.0, 0.2, 1.0]
    v11y_values = [0.0, 0.5, 1.0]

    generate_demofile('shakemap.fake', shakemap_values)
    generate_demofile('exposure.fake', exposure_values)
    generate_demofile('vulnerability.fake', v11y_values)
