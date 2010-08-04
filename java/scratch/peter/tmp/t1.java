package scratch.peter.tmp;

/**
* Simple implementation of one ERF with one faultfrom the Thailand model
* We use the "Thoen Fault" with data contained in the file thai.new.gr
* 
* Date: 2009-09-13 
*/


import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

//18.26392       99.81272
//18.17707       99.74847
//18.10844       99.69968
//18.04114       99.58109
//18.01505       99.57042
//17.93080       99.45937
//17.78529       99.35471
//17.66522       99.30668
//17.52629       99.20238
//I took from the file 'thai.new.gr' the first fault the list.
//That's the 'Thoen fault'.
//
//I put the geometry (trace) of this fault in the file GEM_fault01.dat.
//
//I hardcoded in the ERF implementation (see the file the other 
//necessary information) some of the remaing information required.
//
//e.g.
//mmax 				= 7.43 
//dip 				= 50.0
//fault width 		= 19.58
//top of fault depth = 0.0

public class t1 extends EqkRupForecast {
		
	// Name of this ERF
	public static String NAME = new String("GEM1 fault 01");
	
	// The ProbEqkSources container 
	private ArrayList<ProbEqkSource> allSources = null;	
	
	// Time duration used to create the TimeSpan object
	private double duration = 50;
	
	// Timespan 
	private TimeSpan timeS = null;
	
	/*
	 * Constructor of the ERF 
	 * Input: 
	 * 	- No arguments
	 */
	public t1() {
		
		int i;
		double gridSpacing = 0.1; // Fault grid spacing 
		double lowerDepth;
		double lat, lon; 
		String[] strarr;
		Matcher matcher;
		
		ArrayList<Double> diparr; // Average fault dip 
		ArrayList<Double> fawarr; // Fault width [km]
		ArrayList<Double> toprarr; // Fault, depth to the top of rupture [km]
		ArrayList<Double> mmaxarr; // Maximum magnitude
		ArrayList<String> flename; // Filename list
		ArrayList<Double> rake; // Fault rake
		
		// 
		diparr 	= new ArrayList<Double>();
		fawarr 	= new ArrayList<Double>(); 
		toprarr = new ArrayList<Double>();
		mmaxarr = new ArrayList<Double>();
		flename = new ArrayList<String>();
		rake 	= new ArrayList<Double>();
		
		// Source 0
		mmaxarr.add(7.43);
		diparr.add(50.0);
		fawarr.add(19.58);
		toprarr.add(0.0);
		rake.add(90.0);
			
		// Input filenames list
		String path = "/Users/marcop/Documents/workspace/GEM1/org/opengem/codes/hazard/opensha/ERFim/Data/";
		flename.add(path + "GEM_fault01.dat");
		
		// Pattern 
		Pattern FLOATNUM = Pattern.compile("\\d+\\.\\d+");

		// Read data and create the ERF 
		try {
			
			// Create a time span object
			timeS = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS); // Start and duration units
			timeS.setDuration(duration);
			
			// Instantiate the list of sources
			allSources = new ArrayList<ProbEqkSource>();
			
			for (i=0; i<diparr.size(); i++) {

				// Create the list of locations 
				FaultTrace locList = new FaultTrace("test");				
			    
				// Reading the files 
			    try {
			    	// Instantiate a BufferedReader
			    	BufferedReader input =  new BufferedReader(new FileReader(flename.get(i)));
			    	try {
			    		// Initialize the line variable
			    		String line = null; 
			    		// Reading file
			    		while ((line = input.readLine()) != null){
			    			line = line.trim();
			    			strarr = line.split("\\s+");
		    				lon = -999;
		    				lat = -999;
		    				matcher = FLOATNUM.matcher(strarr[0]);
		    				if (matcher.find()) lat = Double.valueOf(strarr[0]).doubleValue();
		    				matcher = FLOATNUM.matcher(strarr[1]);
		    				if (matcher.find()) lon = Double.valueOf(strarr[1]).doubleValue();	
		    				locList.add(new Location(lat,lon));
			    		}
			    	}
			    	finally {
			    		input.close();
			    	}
			    }
			    catch (IOException ex){
			    	ex.printStackTrace();
			    }
			    
			    // Compute the lower seismogenic depth
			    lowerDepth = toprarr.get(i) + fawarr.get(i) * Math.sin(diparr.get(i)/180*3.1415);
			    
			    // Compute a gridded fault surface 
			    StirlingGriddedSurface surf = new StirlingGriddedSurface(locList,diparr.get(i),toprarr.get(i),lowerDepth,gridSpacing);

			    // Create a FaultRuptureSource object
				FaultRuptureSource source = new FaultRuptureSource(mmaxarr.get(i), surf, rake.get(i), 1.0);
				
				// Add source to the source list
				allSources.add(source); 
			}
			
		} catch(Exception e) {	
			e.printStackTrace();
		}

	}
	
	/*
	 * Method providing the number of sources contained in the ERF
	 * Input: 
	 * 	- No arguments
	 * Output:
	 *  - (int) number of sources
	 *  
	 * @return sze
	 */
	public int getNumSources() {
   	int sze = allSources.size();
   	return sze;
	}
	
	/*
	 * Method providing one <ProbEqkSource> object contained in the ERF
	 * Input: 
	 * 	- (int) source index
	 * Output:
	 *  - (ProbEqkSource) source
	 *   
	 * @param sourceId
	 * @return prbSrc
	 */
	public ProbEqkSource getSource(int sourceId) {
		ProbEqkSource prbSrc;
		prbSrc = (ProbEqkSource) allSources.get(sourceId);
		return prbSrc;
	}

	/*
	 * Method providing the list of <ProbEqkSource>s contained in the ERF
	 * Input: 
	 * 	- No arguments
	 * Output:
	 *  - List of (ProbEqkSource) 
	 *
	 * @param 
	 * @return allSources
	 */
	public ArrayList getSourceList() {
		return allSources;
	}	
	
	  /*
	   * return the time span object.
	   * In addition to returning the timespan it checks for the type of timeSpan,
	   * which can be time-dependent or time-independent.
	   *
	   * @return : time span object is returned which contains start time and duration
	   */
	  public TimeSpan getTimeSpan() {
	    //return this.timeSpan;
	    return timeS;
	  }	
	
	/*
	 * Method providing the name of the ERF
	 * Input: 
	 * 	- No arguments
	 * Output:
	 *  - List of (ProbEqkSource)  
	 */
	public String getName() {
   	return NAME;
	}

	/*
	 * Method allowing the update of the forecast
	 * Input: 
	 * 	- No arguments
	 * Output:
	 *  - void  
	 */
	public void updateForecast() {
		
		// Return if sources are already defined
		if (allSources != null) { 
			return;
		} 
		
		
	}

}
