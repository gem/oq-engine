import unittest
import geohash

class TestDecode(unittest.TestCase):
	def test_empty(self):
		self.assertEqual(
			geohash.bbox(''),
			{'s':-90.0, 'n':90.0, 'w':-180.0, 'e':180.0})
	
	def test_one(self):
		seq = '0123456789bcdefghjkmnpqrstuvwxyz'
		sws = [
			(-90.0, -180.0),
			(-90.0, -135.0),
			(-45.0, -180.0),
			(-45.0, -135.0),
			(-90.0, -90.0),
			(-90.0, -45.0),
			(-45.0, -90.0),
			(-45.0, -45.0),
			(0.0, -180.0),
			(0.0, -135.0),
			(45.0, -180.0),
			(45.0, -135.0),
			(0.0, -90.0),
			(0.0, -45.0),
			(45.0, -90.0),
			(45.0, -45.0),
			(-90.0, 0.0),
			(-90.0, 45.0),
			(-45.0, 0.0),
			(-45.0, 45.0),
			(-90.0, 90.0),
			(-90.0, 135.0),
			(-45.0, 90.0),
			(-45.0, 135.0),
			(0.0, 0.0),
			(0.0, 45.0),
			(45.0, 0.0),
			(45.0, 45.0),
			(0.0, 90.0),
			(0.0, 135.0),
			(45.0, 90.0),
			(45.0, 135.0)
			]
		for i in zip(seq, sws):
			x = geohash.bbox(i[0])
			self.assertEqual((x['s'], x['w']), i[1])
			self.assertEqual(x['n']-x['s'], 45)
			self.assertEqual(x['e']-x['w'], 45)
	
	def test_ezs42(self):
		x=geohash.bbox('ezs42')
		self.assertEqual(round(x['s'],3), 42.583)
		self.assertEqual(round(x['n'],3), 42.627)

# if __name__=='__main__':
# 	unittest.main()
