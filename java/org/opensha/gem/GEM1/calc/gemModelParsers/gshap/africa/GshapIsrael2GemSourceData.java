package org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazardLogicTree;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Parser for Iran Model
 * @author l.danciu
 *
 */
public class GshapIsrael2GemSourceData extends GemFileParser {

	// magnitude bin width used to compute the final mfd
	private static double dm = 0.1;

	// MinMag for calculation 
	private static double calcMinMag = 5.0;


	//specifies how lines connecting two points on the earth's surface should be represented
	// used as argument for default method in Region class
	private static BorderType borderType = BorderType.GREAT_CIRCLE;

	// tectonic regions defined in the model

	private TectonicRegionType trt = TectonicRegionType.ACTIVE_SHALLOW;


	// focal mechanism (default values)
	private double strike = 0.0;
	private double dip = 90.0;
	private double rake = 0.0;

	/**
	 * 
	 * @param inputfile: name of the file containing input model
	 * @param trt: tectonic region
	 * @throws FileNotFoundException 
	 */

	//constructor
	public GshapIsrael2GemSourceData(String inputfile) throws FileNotFoundException{

		// ArrayList of GEM area sources
		srcDataList = new ArrayList<GEMSourceData>();

		// arraylist of GEM area sources
	    srcDataList = new ArrayList<GEMSourceData>();
		
	    String myClass = '/'+getClass().getName().replace('.', '/')+".class";
	    URL myClassURL = getClass().getResource(myClass);
	    if ("jar" == myClassURL.getProtocol())
	    {
	    inputfile = inputfile.substring(inputfile.lastIndexOf("./")+1);
	    }
	    BufferedReader oReader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(inputfile)));
	    
        
        String sRecord = null;
        StringTokenizer st = null;
        // start reading
        try {
            
        	int srcIndex = 0;
        	
			double minLat = Double.MAX_VALUE;
			double maxLat = Double.MIN_VALUE;
			double minLon = Double.MAX_VALUE;
			double maxLon = Double.MIN_VALUE;
        	
			// start loop over sources
        	while((sRecord = oReader.readLine())!=null){
        		
        		st = new StringTokenizer(sRecord);
        		
		         // Source name
				String sourceName ="";
				while(st.hasMoreTokens()) sourceName = sourceName+" "+st.nextToken();
				
				//System.out.println(sourceName);
				
				// Read 2nd Line
	        	sRecord = oReader.readLine();
				st = new StringTokenizer(sRecord);

				double  aVal, errAval, bVal, errBval, maxMag;
				double aveHypoDepth = 10;
				double occRate;

				aVal = Double.valueOf(st.nextToken()).doubleValue();
				errAval = Double.valueOf(st.nextToken()).doubleValue();
				bVal = Double.valueOf(st.nextToken()).doubleValue();
				errBval = Double.valueOf(st.nextToken()).doubleValue();
				// Maximum Magnitude
				maxMag = Double.valueOf(st.nextToken()).doubleValue();
				
               // calculation of the occRate considering the calcMinMag
				occRate = Math.pow(10, aVal-bVal*calcMinMag);
				
				//System.out.println(bVal + " " + occRate + " " + aveHypoDepth + " " + maxMag);
				
				// read polygon coordinates
				Region srcRegion = null;
				LocationList srcBoundary = new LocationList();
				while((sRecord = oReader.readLine())!=null && (new StringTokenizer(sRecord).nextToken().equalsIgnoreCase("source"))==false){
				
				    st = new StringTokenizer(sRecord);

				    double lat = Double.valueOf(st.nextToken()).doubleValue();
					double lon  = Double.valueOf(st.nextToken()).doubleValue();
					//System.out.println(lat+" "+lon);
					
					if(lat<minLat) minLat = lat;
					if(lat>maxLat) maxLat = lat;
					if(lon<minLon) minLon = lon;
					if(lon>maxLon) maxLon = lon;
					
					oReader.mark(1000);
					
					//Polygon Boundary
				    srcBoundary.add(new Location(lat, lon));
				}
				oReader.reset();
				
				// create region
				srcRegion = new Region(srcBoundary, borderType);
                // Remove Sources with Mmax<Mmin(5.0) 
				if (maxMag < calcMinMag) continue;

				// Round magnitude interval extremes (with respect to default dm) and move to bin center
				// (if the minimum and maximum magnitudes are different)
				double mmaxR;
				double mminR;
				if(calcMinMag!=maxMag){
					mminR = new BigDecimal(Math.round(calcMinMag/dm)*dm+dm/2).setScale(2, BigDecimal.ROUND_HALF_UP).doubleValue();
					mmaxR = new BigDecimal(Math.round(maxMag/dm)*dm-dm/2).setScale(2, BigDecimal.ROUND_HALF_UP).doubleValue();
					// check if this operation makes mmaxR less than mminR
					if(mmaxR<mminR){
						System.out.println("Maximum magnitude less than minimum magnitude!!! Check for rounding algorithm!");
						System.exit(0);
					}
				}
				else{
					mminR = new BigDecimal(Math.round(calcMinMag/dm)*dm).setScale(2, BigDecimal.ROUND_HALF_UP).doubleValue();	
					mmaxR = new BigDecimal(Math.round(maxMag/dm)*dm).setScale(2, BigDecimal.ROUND_HALF_UP).doubleValue();
				}

				// calculate the number of magnitude values
				int numMag = (int) Math.round((mmaxR-mminR)/dm)+1;
				
				// magnitude frequency distribution					
				GutenbergRichterMagFreqDist mfd = new GutenbergRichterMagFreqDist(mminR,numMag,dm);
				// compute mfd setting the total cumulative rate 
				mfd.setAllButTotMoRate(mminR, mmaxR, occRate, bVal);
				//setAllButTotCumRate(minX, maxX, totMoRate, bValue);
				
				// Definiton of top of rupture depth vs magnitude 
				EvenlyDiscretizedFunc topr = new EvenlyDiscretizedFunc(mminR,mmaxR,numMag);
				for(int im=0;im<numMag;im++) topr.set(im, aveHypoDepth);
				ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc(topr);
					
                // Create a MFD array
                IncrementalMagFreqDist[] mfdArr = new IncrementalMagFreqDist[1];
                mfdArr[0] = mfd;

		        // ArrayList of mfds and focal mechanisms
                FocalMechanism[] focMechArr = new FocalMechanism[1];
                focMechArr[0] = new FocalMechanism(strike,dip,rake);

                // create list of (mag freq dist, focal mechanism)
                // In this case there is only one pair
                MagFreqDistsForFocalMechs mfdffm = new MagFreqDistsForFocalMechs(mfdArr,focMechArr);

                // define tectonic region based on depth
                // actually there are only two values of depth: 12 and 80

                // create GEMAreaSource
    			srcIndex = srcIndex+1;
				GEMAreaSourceData srctmp = new GEMAreaSourceData(Integer.toString(srcIndex), sourceName, trt, srcRegion, mfdffm, aveRupTopVsMag,aveHypoDepth);
				
				//double area_srctmp = srctmp.getArea();
				// Normalized per square km - a-valGR
				//double aValN = aVal-Math.log10(area_srctmp); 
				
				//System.out.println("Area: " + area_srctmp);
				
				srcDataList.add(srctmp);
			
        	} // end loop over sources

} catch (IOException e) {
e.printStackTrace();
}
}
// for testing 
public static void main(String[] args) throws IOException, ClassNotFoundException {

GshapIsrael2GemSourceData isrModel = new GshapIsrael2GemSourceData ("../../data/gshap/africa/israel.zon");

//FileWriter file = new FileWriter("EuropeAreaGMT.dat");
//
//europeModel.writeAreaGMTfile (file);
}
}

