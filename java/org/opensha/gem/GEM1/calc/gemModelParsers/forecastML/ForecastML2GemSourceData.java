package org.opensha.gem.GEM1.calc.gemModelParsers.forecastML;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazardLogicTree;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class ForecastML2GemSourceData extends GemFileParser{
	
	private final static boolean D = false;	// for debugging
	
	// default focal mechanism
	private static double strike = 0.0;
	private static double dip = 90.0;
	private static double rake = 0.0;
	private FocalMechanism fm = new FocalMechanism(strike, dip, rake);
	
	// default tectonic region
	private static TectonicRegionType trt = TectonicRegionType.ACTIVE_SHALLOW;
	
	// default depth
	private static double defaultDepth = 0.0;
	
	// source location and Flinn-Engdhal regions for TripleS model
	private String srcLocFile = "/org/opensha/gem/GEM1/data/global_smooth_seismicity/TripleSGlobalForecastSourceLoc.dat";
	private String srcTectRegFile = "/org/opensha/gem/GEM1/data/global_smooth_seismicity/TripleSGlobalForecastFlinnEndghalReg.dat";
	
	// Flinn-Engdhal regions and tectonic regions
	private String flinnEndghalRegTectReg = "/org/opensha/gem/GEM1/data/flinn_engdhal/flinn-engdhal.dat";
	
	
	public ForecastML2GemSourceData(String inputfile) throws IOException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		String myClass = '/'+getClass().getName().replace('.', '/')+".class";
		URL myClassURL = getClass().getResource(myClass);
		
		// read source locations of tripleS model
        BufferedReader oReader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(srcLocFile)));
        
        String sRecord = null;
        StringTokenizer st = null;
        
        LocationList locList = new LocationList();
		while((sRecord = oReader.readLine())!=null){
			
			st = new StringTokenizer(sRecord);
			
			double lon = Double.valueOf(st.nextToken()).doubleValue();
			double lat = Double.valueOf(st.nextToken()).doubleValue();
			
			locList.add(new Location(lat,lon,0.0));
			
		}
		oReader.close();
		
		// read corresponding Flinn-Engdhal regions
        oReader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(srcTectRegFile)));
        
        ArrayList<String> flinnEngdhalReg = new ArrayList<String>();
		// loop over sources
		while((sRecord = oReader.readLine())!=null){
			
			flinnEngdhalReg.add(sRecord);
			
		}
		oReader.close();
		
		// read tectonic regions associated to Flinn Engdhal regions
        oReader = new BufferedReader(new InputStreamReader(GemComputeHazardLogicTree.class.getResourceAsStream(flinnEndghalRegTectReg)));
        
        HashMap<String,ArrayList<String>> flinnEngdhalTectReg = new HashMap<String,ArrayList<String>>();
		// loop over sources
		while((sRecord = oReader.readLine())!=null){
			
			// region name
			String name = sRecord.toUpperCase();
			
			// tectonic region(s)
			ArrayList<String> tectRegList = new ArrayList<String>();
			sRecord = oReader.readLine();
			while(sRecord.contains("stable continental") ||
					sRecord.contains("ocean or mid-oceanic ridge") ||
					sRecord.contains("subduction zone") ||
					sRecord.contains("active shallow crustal") ||
					sRecord.contains("volcanic") ||
					sRecord.contains("Vrancea-type")){
				tectRegList.add(sRecord);
				sRecord = oReader.readLine();
			}
			
			flinnEngdhalTectReg.put(name, tectRegList);
			
		}
		oReader.close();

		
		try{
            
            int is = 0;
			
		    DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		    DocumentBuilder db = dbf.newDocumentBuilder();
		    Document doc = db.parse(GemComputeHazardLogicTree.class.getResourceAsStream(inputfile));
		    doc.getDocumentElement().normalize();
		    
		    //******* period of the forecast *******//
		    
		    // starting year
		    NodeList forecastStart = doc.getElementsByTagName("forecastStartDate");
		    int startYear = Integer.parseInt(forecastStart.item(0).getFirstChild().getNodeValue().substring(0, 4));
		    if (D) System.out.println("Forecast Start Date: "+startYear);
		    
		    // ending year
		    NodeList forecastEnd = doc.getElementsByTagName("forecastEndDate");
		    int endYear = Integer.parseInt(forecastEnd.item(0).getFirstChild().getNodeValue().substring(0,4));
		    if (D) System.out.println("Forecast End Date: "+endYear);
		    
		    //******** magnitude bin dimension ********//
		    NodeList magBin = doc.getElementsByTagName("defaultMagBinDimension");
		    double delta = Double.parseDouble(magBin.item(0).getFirstChild().getNodeValue());
		    if (D) System.out.println("Default magnitude bin dimension: "+delta);
		    
		    //******** cell dimension *********//
		    NodeList cellDim = doc.getElementsByTagName("defaultCellDimension");
		    double cellDimLat = Double.parseDouble(cellDim.item(0).getAttributes().getNamedItem("latRange").getNodeValue());
		    double cellDimLon = Double.parseDouble(cellDim.item(0).getAttributes().getNamedItem("lonRange").getNodeValue());
		    if (D) System.out.println("Default cell dimension");
		    if (D) System.out.println("Latitude range: "+cellDimLat);
		    if (D) System.out.println("Longitude range: "+cellDimLon);
		    
		    //******* source cells ***********//
		    NodeList cellLst = doc.getElementsByTagName("cell");
		    
		    ArrayList<String> regNotFound = new ArrayList<String>();
		    
		    // loop over cells
		    for (int i = 0; i < cellLst.getLength(); i++) {
		    	
		    	if (D) System.out.println("Cell: "+(i+1)+" of "+cellLst.getLength());
		    
			    Node cell = cellLst.item(i);
			    //******** cell coordinates ***********//
			    // latitude
			    double lat = Double.parseDouble(cell.getAttributes().getNamedItem("lat").getNodeValue());
			    // longitude
			    double lon = Double.parseDouble(cell.getAttributes().getNamedItem("lon").getNodeValue());
			    //System.out.println("Lat: "+lat);
			    //System.out.println("Lon: "+lon);
			    
			    //************ magnitude-frequency distribution ***********//
			    NodeList MFd = cell.getChildNodes();
			    
			    // minimum magnitude
			    double mMin = Double.parseDouble(MFd.item(1).getAttributes().getNamedItem("m").getNodeValue());
			    // maximum magnitude
			    double mMax = Double.parseDouble(MFd.item(MFd.getLength()-2).getAttributes().getNamedItem("m").getNodeValue());
			    // number of values
			    int nVal = (int)(MFd.getLength()-1)/2;
			    
			    // loop over magnitude bins
			    SingleMagFreqDist mfd = new SingleMagFreqDist(mMin,nVal,delta);
			    int ii=0;
			    for(int im=1;im<=MFd.getLength()-2;im = im+2){
			    Node MFd0 = MFd.item(im);
			    // magnitude
			    mfd.set(ii,Double.valueOf(MFd0.getChildNodes().item(0).getNodeValue())/(endYear-startYear));
			    ii = ii+1;
			    }
			    
				// average top of rupture-magnitude distribution
				ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
				for(int iv=0;iv<mfd.getNum();iv++){
					double mag = mfd.getX(iv);
					aveRupTopVsMag.set(mag, defaultDepth);
				}
	
	        	// select only those sources for which rates are different than zero
	        	if(mfd.getY(0)!=0.0){
	        		
				    // define GEMGridSourceData
					// id
					String id = Integer.toString(i);
					
					// name
					String name = "";
					
					// region associated to the source
					Location loc1 = new Location(lat-cellDimLat/2,lon-cellDimLon/2);
					Location loc2 = new Location(lat+cellDimLat/2,lon+cellDimLon/2);
					Region reg = new Region(loc1, loc2);
					
					// mag-freq dist for focal mechanism
					MagFreqDistsForFocalMechs mfdForFocMec = new MagFreqDistsForFocalMechs(mfd, fm);
					
					// find Flinn Engdhal region for current location
				    String regName = flinnEngdhalReg.get(locList.indexOf(new Location(lat,lon,0.0)));

				    // find tectonic regions associated to the Flinn Engdhal region
				    ArrayList<String> tetRegList = null;
				    
				    // default tectonic region type is shallow active
				    TectonicRegionType tectRegType = trt;
		            if((tetRegList = flinnEngdhalTectReg.get(regName))!=null){
		            	// loop over regions and find if it is stable continental
		            	for(int itr=0;itr<tetRegList.size();itr++){
		            		if(tetRegList.get(itr).contains("stable")) 
		            			tectRegType = TectonicRegionType.STABLE_SHALLOW;
	            	    }
		            }
		            else{
		            	System.out.println("Tectonic regions not found for: "+regName);
		            	System.out.println("Execution stopped!");
		            	System.exit(0);
		            }
				    
		            if (D) System.out.println(regName+" "+tectRegType);
				    srcDataList.add(new GEMAreaSourceData(id, name, tectRegType, 
				    		reg, mfdForFocMec, 
				    		aveRupTopVsMag, defaultDepth));

	        	}
		    
		    }


		    
		
		    } catch (Exception e) {
		      e.printStackTrace();
		    }
		
		
	}
	
	public static void main(String[] args) throws IOException{
		
		String inputFile = "../../data/global_smooth_seismicity/zechar.triple_s.global.rate_forecast.xml";
		
		ForecastML2GemSourceData model = new ForecastML2GemSourceData(inputFile);
		
//        try {
//        	String outfile = "/Users/damianomonelli/Desktop/TripleSGlobalForecastSourceLoc.dat";
//        	
//            FileOutputStream oOutFIS = new FileOutputStream(outfile);
//            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
//            BufferedWriter oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));
//            for(int i=0;i<model.getNumSources();i++){
//            	GEMPointSourceData src = (GEMPointSourceData)model.getList().get(i);
//            	oWriter.write(String.format("%+8.3f %+7.3f \n",
//            			src.getHypoMagFreqDistAtLoc().getLocation().getLongitude(),
//            			src.getHypoMagFreqDistAtLoc().getLocation().getLatitude()));
//            }
//            oWriter.close();
//            oOutBIS.close();
//            oOutFIS.close();
//        } catch (Exception ex) {
//            System.err.println("Trouble generating mean hazard map!");
//            ex.printStackTrace();
//            System.exit(-1);
//        }
		
	}
	


}
