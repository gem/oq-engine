package scratch.peter.tmp;

import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.FaultTraceUtils;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;

public class TestSubductionFault {

	/**
	 * @param args
	 */
	public static void main(String[] args) {

		double aveSubFaultGridSpacing = 20.0;
		
		// top trace and bottom trace taken from South America subduction fault
		FaultTrace topTrace = new FaultTrace("topTrace");
		topTrace.add(new Location(-3.24840217453,-81.5514490892,10.0));
		topTrace.add(new Location(-3.06000000013,-81.4438422397,10.0));
		topTrace.add(new Location(-2.87027465862,-81.3600000001,10.0));
		topTrace.add(new Location(-2.34000000007,-81.189916992,10.0));
		topTrace.add(new Location(-1.82005371059,-81.0800000001,10.0));
		topTrace.add(new Location(-1.08000000019,-80.9879841615,10.0));
		topTrace.add(new Location(-0.627197265186,-80.9128025054,10.0));
		topTrace.add(new Location(-0.337659911925,-80.8423400875,10.0));
		topTrace.add(new Location(-0.091492309567,-80.7485074611,10.0));
		topTrace.add(new Location(0.116044311577,-80.6360441594,10.0));
		topTrace.add(new Location(0.763280029549,-80.22,10.0));
		topTrace.add(new Location(1.04466674812,-80.08,10.0));
		topTrace.add(new Location(1.56445495567,-79.8644546509,10.0));
		topTrace.add(new Location(1.83901977526,-79.6990194704,10.0));
		topTrace.add(new Location(2.70534118629,-78.9253414916,10.0));
		topTrace.add(new Location(2.83198303187,-78.7719833372,10.0));
		topTrace.add(new Location(3.07327270525,-78.4000000002,10.0));
		topTrace.add(new Location(3.16799560562,-78.2999999996,10.0));
		topTrace.add(new Location(3.28000000042,-78.2170361331,10.0));
		topTrace.add(new Location(3.49673828132,-78.1200000002,10.0));
		topTrace.add(new Location(3.90971740729,-78.0097177127,10.0));
		topTrace.add(new Location(4.29999999968,-77.8809259029,10.0));
		topTrace.add(new Location(4.5400000003,-77.8255297856,10.0));
		topTrace.add(new Location(4.78000000002,-77.7951577759,10.0));
		
		FaultTrace bottomTrace = new FaultTrace("bottomTrace");
		bottomTrace.add(new Location(-2.9475232841,-80.3309622182,50.0));
		bottomTrace.add(new Location(-2.59999999992,-80.2462858583,50.0));
		bottomTrace.add(new Location(-1.96000000036,-80.0265930176,50.0));
		bottomTrace.add(new Location(-0.979999999559,-79.766981354,50.0));
		bottomTrace.add(new Location(0.703570556949,-79.1035705568,50.0));
		bottomTrace.add(new Location(2.04103576693,-78.4210360715,50.0));
		bottomTrace.add(new Location(2.24292602529,-78.2629263303,50.0));
		bottomTrace.add(new Location(2.60242980955,-77.8799999996,50.0));
		bottomTrace.add(new Location(2.8200000002,-77.6901156616,50.0));
		bottomTrace.add(new Location(2.98000000032,-77.5834286495,50.0));
		bottomTrace.add(new Location(3.44527099619,-77.3252713011,50.0));
		bottomTrace.add(new Location(3.87999999972,-77.0479470827,50.0));
		bottomTrace.add(new Location(4.03999999983,-76.9671765134,50.0));
		bottomTrace.add(new Location(4.22000000007,-76.9038186649,50.0));
		bottomTrace.add(new Location(4.66000000016,-76.816644287,50.0));
		
    	// get resampled traces
		// it's an arbitrary chosen number, not derived by the average subfoult grid spacing
		int num = 10;
		FaultTrace resampTopTrace = FaultTraceUtils.resampleTrace(topTrace, num);
		FaultTrace resampBottomTrace = FaultTraceUtils.resampleTrace(bottomTrace, num);


		
		// compute average number of sections along dip
		double aveDist=0;
		for(int ii=0; ii<resampTopTrace.size(); ii++) {
	        Location topLoc = resampTopTrace.get(ii);
			Location botLoc = resampBottomTrace.get(ii);
			aveDist += LocationUtils.linearDistanceFast(topLoc, botLoc);
		}
		aveDist /= resampTopTrace.size();
		int nRows = (int) Math.round(aveDist/aveSubFaultGridSpacing)+1;
		System.out.println("Average width: "+aveDist+", number of sections along dip: "+(nRows-1));
		
		// create the surface object used to define the fault
		ApproxEvenlyGriddedSurface surf = new ApproxEvenlyGriddedSurface(nRows, resampTopTrace.size(), aveSubFaultGridSpacing);
		
		// now set the surface locations
		int indexLoc = 0;
		for(int ii=0; ii<resampTopTrace.size(); ii++) {
			Location topLoc = resampTopTrace.get(ii);
			Location botLoc = resampBottomTrace.get(ii);
			double horzLength = LocationUtils.horzDistance(topLoc, botLoc);
			double vertLength = LocationUtils.vertDistance(topLoc, botLoc);
			double subSecLenHoriz = horzLength/(nRows-1);
			double subSecLenVert = vertLength/(nRows-1);
			LocationVector dir = LocationUtils.vector(topLoc, botLoc);
			System.out.println("Top trace node number: "+(ii+1));
			for(int s=0; s< nRows; s++) {
				double distHoriz = s*subSecLenHoriz;
				double distVert = -s*subSecLenVert;
				dir.setHorzDistance(distHoriz);
				dir.setVertDistance(distVert);
				Location loc = LocationUtils.location(topLoc, dir);
				surf.setLocation(s, ii, loc);
				indexLoc = indexLoc+1;
				System.out.println("Location "+(s+1)+", lat: "+loc.getLatitude()+", lon: "+loc.getLongitude()+", depth: "+loc.getDepth());
			}
		}
		
	}

}
