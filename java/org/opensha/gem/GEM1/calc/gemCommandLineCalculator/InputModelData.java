package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class InputModelData {

	private ArrayList<GEMSourceData> sourceList;
	
	// border type for area source definition
	private static BorderType borderType = BorderType.GREAT_CIRCLE;
	
	// comment line identifier
	private static String comment = "//";
	
	// for debugging
	private static Boolean D = false;
	
	// contructor
	public InputModelData(String inputModelFile,double mMin,double deltaM) throws IOException{
		
		sourceList = new ArrayList<GEMSourceData>();
		
		// common variables
        // source id
        String sourceID = null;
        // source name
        String sourceName = null;    
        // tectonic region type
        TectonicRegionType trt = null;
        
        // variable for area sources
        // region
        Region reg = null;
        // magnitude frequency distributions for focal mechanims
        MagFreqDistsForFocalMechs magFreqDistForFocalMech = null;
        // rupture top distribution
        ArbitrarilyDiscretizedFunc aveRupTopVsMag = null;
        // average hypocentral depth
        double aveHypoDepth = Double.NaN;
		
        String sRecord = null;
        StringTokenizer st = null;
        
		// open file
		File file = new File(inputModelFile);
        FileInputStream oFIS = new FileInputStream(file.getPath());
        BufferedInputStream oBIS = new BufferedInputStream(oFIS);
        BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));
        
        // start reading the file
        sRecord = oReader.readLine();
        while(sRecord!=null){
        	
        	// skip comments or empty lines
            while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
            	sRecord = oReader.readLine();
            	continue;
            }
            
            // if keyword newsource is found
            if(sRecord.equalsIgnoreCase("newsource")){
            	
            	// read source id
            	sRecord = oReader.readLine();
                while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                	sRecord = oReader.readLine();
                	continue;
                }
                sourceID = sRecord;
                if(D) System.out.println("Source id: "+sourceID);
                
                // read source name
                sRecord = oReader.readLine();
                while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                	sRecord = oReader.readLine();
                	continue;
                }
                sourceName = sRecord;
                if(D) System.out.println("Source name: "+sourceName);
                
                // read tectonic region type
                sRecord = oReader.readLine();
                while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                	sRecord = oReader.readLine();
                	continue;
                }
                trt = TectonicRegionType.getTypeForName(sRecord);
                if(D) System.out.println("Tectonic region type: "+trt.toString());
                
                // continue reading
                sRecord = oReader.readLine();
                while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                	sRecord = oReader.readLine();
                	continue;
                }
                
                // area source definition
                if(sRecord.equalsIgnoreCase("area")){
                	
                	if(D) System.out.println("Source typology: "+sRecord);
                	
                	// read number of vertices in the polygon boundary
                    // read tectonic region type
                	sRecord = oReader.readLine();
                    while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                    	sRecord = oReader.readLine();
                    	continue;
                    }
                    int numVert = Integer.parseInt(sRecord);
                    if(D) System.out.println("Number of polygon vertices: "+numVert);
                    
                	// location list containing border coordinates
                	LocationList areaBorder = new LocationList();
                    
                    // read polygon vertices
                    for(int i=0;i<numVert;i++){
                    	sRecord = oReader.readLine();
                        while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                        	sRecord = oReader.readLine();
                        	continue;
                        }
                        st = new StringTokenizer(sRecord);
                        double lat = Double.parseDouble(st.nextToken());
                        double lon = Double.parseDouble(st.nextToken());
                        areaBorder.add(new Location(lat,lon));
                        if(D) System.out.println("Lat: "+lat+", Lon: "+lon);
                    }
                    
                    // create region
                    reg = new Region(areaBorder, borderType);
                    
                    // read number of mfd-focal mechanisms pairs
                    sRecord = oReader.readLine();
                    while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                    	sRecord = oReader.readLine();
                    	continue;
                    }
                    int numMfdFm = Integer.parseInt(sRecord);
                    
                    
                    // magnitude frequency distribution(s)
                    IncrementalMagFreqDist[] mfd = new IncrementalMagFreqDist[numMfdFm];
                    
                    // focal mechanism(s)
                    FocalMechanism[] fm = new FocalMechanism[numMfdFm];
                    
                    // loop over mfd-fm pairs
                    for(int i=0;i<numMfdFm;i++){
                    	
                    	// read mfd specification
                    	sRecord = oReader.readLine();
                        while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                        	sRecord = oReader.readLine();
                        	continue;
                        }
                        // mfd type
                        st = new StringTokenizer(sRecord);
                        String mfdType = st.nextToken();
                        if(mfdType.equalsIgnoreCase("gr")){
                            double aVal = Double.parseDouble(st.nextToken());
                            double bVal = Double.parseDouble(st.nextToken());
                            double mMax = Double.parseDouble(st.nextToken());
                            if(D) System.out.println("a value: "+aVal+", b value: "+bVal+", maximum magnitude: "+mMax);
                            
                            // round mMin and mMax with respect to delta bin
                            mMin = Math.round(mMin/deltaM)*deltaM;
                            mMax = Math.round(mMax/deltaM)*deltaM;
                            
                            if(mMax<mMin){
                            	System.out.println("Minimum magnitude for source "+sourceName+" is less then mMax");
                            	System.out.println("Check the input file.");
                            	System.out.println("Execution stopped.");
                            	System.exit(0);
                            }
                            
                            if(mMax!=mMin){
                            	// shift to bin center
                            	mMin = mMin+deltaM/2;
                            	mMax = mMax-deltaM/2;
                            }
                            
                            // number of magnitude values in the mfd
                            int numVal = (int)((mMax-mMin)/deltaM + 1);
                            
                            // compute total moment rate above minimum magnitude
                            double totCumRate = Math.pow(10, aVal-bVal*mMin);
                            
                            mfd[i] = new GutenbergRichterMagFreqDist(bVal, totCumRate,
                                    mMin, mMax, numVal);
                            
                            if(D) System.out.println(mfd[i]);
                        }
                        else{
                        	System.out.println("Only GR mfd supported!");
                        	System.out.println("Execution stopped!");
                        	System.exit(0);
                        }
                        
                        // read focal mechanism specification
                        sRecord = oReader.readLine();
                        while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                        	sRecord = oReader.readLine();
                        	continue;
                        }
                        st = new StringTokenizer(sRecord);
                        double strike = Double.parseDouble(st.nextToken());
                        double dip = Double.parseDouble(st.nextToken());
                        double rake = Double.parseDouble(st.nextToken());
                        if(D) System.out.println("strike: "+strike+", dip: "+dip+", rake: "+rake);
                        
                        fm[i] = new FocalMechanism(strike,dip,rake);
                        
                    	
                    } // end loop over mfd-fm
                    
                    // instantiate mfd/fm pairs
                    magFreqDistForFocalMech = new MagFreqDistsForFocalMechs(mfd,fm);
                    
                    // read top of rupture distribution
                    aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
                    sRecord = oReader.readLine();
                    while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                    	sRecord = oReader.readLine();
                    	continue;
                    }
                    // number of values
                    st = new StringTokenizer(sRecord);
                    int numVal = st.countTokens();
                    for(int i=0;i<numVal/2;i++){
                    	double mag = Double.parseDouble(st.nextToken());
                    	double depth = Double.parseDouble(st.nextToken());
                    	aveRupTopVsMag.set(mag, depth);
                    	if(D) System.out.println("Magnitude: "+mag+", depth: "+depth);
                    }
                    
                    // read average hypocentral depth
                    sRecord = oReader.readLine();
                    while(sRecord.contains(comment.subSequence(0, comment.length())) || sRecord.isEmpty()){
                    	sRecord = oReader.readLine();
                    	continue;
                    }
                    aveHypoDepth = Double.parseDouble(sRecord);
                    if(D) System.out.println("Average hypocentral depth: "+aveHypoDepth);
                    
                    // add to source list
                    sourceList.add(new GEMAreaSourceData(sourceID, sourceName, trt, 
                			reg, magFreqDistForFocalMech, aveRupTopVsMag,aveHypoDepth));
                    
                } // end if area
            	
                // continue reading
                sRecord = oReader.readLine();
                
            } // end if new source
            
        } // end if sRecord!=null
		
	}
	
	// for testing
	public static void main(String[] args) throws IOException{
		
		InputModelData data = new InputModelData("/Users/damianomonelli/Documents/workspace/OpenSHA/src/org/opensha/gem/GEM1/data/command_line_input_files/src_model1.dat",5.0,0.1);
		
	}

	public ArrayList<GEMSourceData> getSourceList() {
		return sourceList;
	}
	
}
