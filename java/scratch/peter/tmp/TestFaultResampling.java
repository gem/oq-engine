package scratch.peter.tmp;

import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FaultTraceUtils;
import org.opensha.sha.faultSurface.FaultTrace;

public class TestFaultResampling {

	
	public static void main(String[] args){
		
		// bottom fault trace for panama subduction fault
		// taken from USGS subduction fault model (pa.sub100n.new.in)
		FaultTrace trace = new FaultTrace("Panama");
		
		trace.add(new Location(9.75,-82.91,10));
		trace.add(new Location(9.66,-82.79,10));
		trace.add(new Location(9.33,-82.25,7));
		trace.add(new Location(9.24,-80.05,35));
		trace.add(new Location(9.09,-79.10,48));
		trace.add(new Location(8.00,-77.00,37));
		
    	// get resampled traces
		FaultTrace resampTrace = FaultTraceUtils.resampleTrace(trace, 10);
		
		  // write out each to check
		  System.out.println("RESAMPLED");
		  for(int i=0; i<resampTrace.size(); i++) {
			  Location l = resampTrace.get(i);
			  System.out.println(l.getLatitude()+"\t"+l.getLongitude()+"\t"+l.getDepth());
		  }

		  System.out.println("ORIGINAL");
		  for(int i=0; i<trace.size(); i++) {
			  Location l = trace.get(i);
			  System.out.println(l.getLatitude()+"\t"+l.getLongitude()+"\t"+l.getDepth());
		  }
	
	}
	
}
