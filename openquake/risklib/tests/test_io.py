import unittest
import tempfile
import shutil
from risklib.io import read_calculator_input, Archive

TEST_INI = '''\
[general]
fragility_file=
exposure_file=
gmf_file=
'''

TEST_FRAGILITY = '''\
continuous	{'IMT': 'PGA', 'imls': None}	['slight', 'moderate', 'extensive', 'complete']
W	[(0.147, 0.414), (0.236, 0.666), (0.416, 1.172), (0.627, 1.77)]	None
A	[(0.122, 0.345), (0.171, 0.483), (0.236, 0.666), (0.383, 1.08)]	None
DS	[(0.081, 0.23), (0.122, 0.345), (0.228, 0.643), (0.326, 0.919)]	None
UFB	[(0.114, 0.322), (0.171, 0.483), (0.326, 0.919), (0.489, 1.379)]	None
RC	[(0.13, 0.368), (0.187, 0.529), (0.334, 0.942), (0.627, 1.77)]	None
'''

TEST_EXPOSURE = '''\
83.313823	29.461172	a1	1.0	W
83.313823	29.236172	a2	1.0	W
83.538823	29.086172	a3	1.0	W
80.688823	28.936172	a4	1.0	W
83.538823	29.011172	a5	1.0	W
81.138823	28.786172	a6	1.0	W
83.988823	28.486172	a7	1.0	W
83.238823	29.386172	a8	1.0	W
83.013823	29.086172	a9	1.0	W
83.313823	28.711172	a10	1.0	W
86.913823	27.736172	a11	1.0	W
83.163823	29.311172	a12	1.0	W
80.613823	28.936172	a13	1.0	W
83.913823	29.011172	a14	1.0	W
82.038823	30.286172	a15	1.0	W
83.388823	29.311172	a16	1.0	W
80.688823	28.861172	a17	1.0	W
83.463823	28.711172	a18	1.0	W
84.138823	28.411172	a19	1.0	W
83.088823	29.161172	a20	1.0	W
84.138823	28.786172	a21	1.0	W
85.113823	28.336172	a22	1.0	W
84.063823	29.011172	a23	1.0	W
83.013823	29.611172	a24	1.0	W
86.838823	27.736172	a25	2.0	W
84.363823	28.786172	a26	2.0	W
84.138823	28.561172	a27	2.0	W
83.163823	29.011172	a28	2.0	W
83.013823	29.236172	a29	2.0	W
82.863823	28.861172	a30	2.0	W
85.038823	28.561172	a31	2.0	W
86.088823	28.036172	a32	2.0	W
83.313823	28.786172	a33	2.0	W
81.888823	28.186172	a34	2.0	W
83.238823	29.311172	a35	2.0	W
84.138823	29.161172	a36	2.0	W
84.213823	28.786172	a37	2.0	W
'''


# 3 sites, 10 realizations each
TEST_GMF = '''\
78.0298926472	25.5045220229	0.000680309484466	0.000711281244213	0.000741986463474	0.000760338585357	0.000942532774277	0.00105704134575	0.00111290390586	0.00135719021051	0.00141060247848	0.00304006405978
78.0298993673	25.5315016711	0.000500184962291	0.000555030095309	0.000831920782746	0.00107838292565	0.00118810710122	0.00138634452968	0.00189281503045	0.00203752528956	0.00211114445991	0.00401726103106
78.029906097	25.5584813193	0.000493201715186	0.000792784635525	0.000921592103304	0.00128163795768	0.00134503886218	0.0015094049347	0.00155088743945	0.00195132567219	0.00250293519835	0.00260471765767
'''


class TestIO(unittest.TestCase):
    def setUp(self):
        # create a temporary directory
        self.path = tempfile.tempdir()
        archive = Archive(self.path)
        with archive.open('job.ini', 'w') as f:
            f.write(TEST_INI)
        with archive.open('fragility.csv', 'w') as f:
            f.write(TEST_FRAGILITY)
        with archive.open('exposure.csv', 'w') as f:
            f.write(TEST_EXPOSURE)
        with archive.open('gmf.csv', 'w') as f:
            f.write(TEST_GMF)

    def test_read_csv_files(self):
        files = read_calculator_input(self.path)
        self.assertEqual(len(files['fragility']) == 3)
        self.assertEqual(len(files['exposure']) == 3)
        self.assertEqual(len(files['gmf']) == 3)

    def tearDown(self):
        # remove the directory
        shutil.rmtree(self.path)
