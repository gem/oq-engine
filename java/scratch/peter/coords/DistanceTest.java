package scratch.peter.coords;


//import scratch.peter.org.gavaghan.geodesy.Ellipsoid;
//import scratch.peter.org.gavaghan.geodesy.GeodeticCalculator;
//import scratch.peter.org.gavaghan.geodesy.GeodeticCurve;
//import scratch.peter.org.gavaghan.geodesy.GlobalCoordinates;

public class DistanceTest {

	// creating reference points
	public static void main(String[] args) {
		
/*		GeodeticCalculator calc = new GeodeticCalculator();
		GeodeticCurve curve; 
		GlobalCoordinates cStart = new GlobalCoordinates(0,0);
		GlobalCoordinates cEnd = new GlobalCoordinates(0,0);
		Location lStart = new Location();
		Location lEnd = new Location();
		
		
		// from (-90,0) to (90,90)
		double lat = 0;
		double lon = -60;
		cStart.setLatitude(lat);
		cStart.setLongitude(lon);
		lStart.setLatitude(lat);
		lStart.setLongitude(lon);
		lat += 0.01;
		lon += 0.005;
		cEnd.setLatitude(lat);
		cEnd.setLongitude(lon);
		lEnd.setLatitude(lat);
		lEnd.setLongitude(lon);
		
		// faster
		
		for (int i=0; i < 6000; i += 1) {
			curve = calc.calculateGeodeticCurve(Ellipsoid.WGS84, cStart, cEnd);
			double vd = curve.getEllipsoidalDistance() / 1000;

			double surfDist = LocationUtils.surfaceDistance(lStart, lEnd);
			double fastSurfDist = LocationUtils.fastSurfaceDistance(lStart, lEnd);
			double horizDist = LocationUtils.getHorzDistance(lStart, lEnd);
			double approxDist = LocationUtils.getApproxHorzDistance(lStart, lEnd);

			double d1 = surfDist - vd;
			double d2 = fastSurfDist - vd;
			double d3 = horizDist - vd;
			double d4 = approxDist - vd;

			int d2i = (int) Math.round(d2 * 1000);
			int d4i = (int) Math.round(d4 * 1000);

			double p2 = d2/vd * 100;
			double p4 = d4/vd * 100;
			
//			String s = String.format(
//					"lat: %3.1f  lon: %3.1f  vd: %3.4f  d1: %3.4f  " + 
//					"d2: %3.4f  d3: %3.4f  d4: %3.4f",
//					lat, lon, vd, d1, d2, d3, d4);
			
			String s = String.format(
					"lat: %5.1f  lon: %6.1f  vd: %8.3f   " + 
					"fsd: %4dm %5.2f%%   ad: %4dm %5.2f%%",
					lat, lon, vd, d2i, p2, d4i, p4);

			System.out.println(s);
			if (i < 5999) {
				cStart.setLatitude(lat);
				cStart.setLongitude(lon);
				lStart.setLatitude(lat);
				lStart.setLongitude(lon);
				lat += 0.01;
				lon += 0.005;
				cEnd.setLatitude(lat);
				cEnd.setLongitude(lon);
				lEnd.setLatitude(lat);
				lEnd.setLongitude(lon);
			}
		}*/
	}

}
