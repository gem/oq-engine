package org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthAmericaGridData extends GemFileParser {
	
	private final static boolean D = false;	// for debugging
	
	// directory for grid seismicity files
	private String inDir = "/org/opensha/gem/GEM1/data/nshmp/south_america/grid/";
	
	public NshmpSouthAmericaGridData(double latmin, double latmax, double lonmin, double lonmax){
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing grid file with corresponding weight
		HashMap<String,Double> gridFile = new HashMap<String,Double>();
		
		// shallow active
		gridFile.put(inDir+"SA.grid.0to50km.in",1.0);
		
		// shallow active tierra del fuego
		gridFile.put(inDir+"SA.gridTdF.0to50.in",1.0);
		
		// intraslab earthquakes
		gridFile.put(inDir+"SA.grid.50to100km.in",1.0);
		
		// intraslab earthquakes
		gridFile.put(inDir+"SA.grid.100to150km.in",1.0);
		
		// craton
		gridFile.put(inDir+"SA.gridE.0to50km.in",1.0);
		
		// iterator over files
		Set<String> fileName = gridFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
			NshmpGrid2GemSourceData gm = null;
			if(key.equalsIgnoreCase(inDir+"SA.grid.0to50km.in") || key.equalsIgnoreCase(inDir+"SA.gridTdF.0to50.in")){
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.ACTIVE_SHALLOW,gridFile.get(key),
						latmin, latmax, lonmin, lonmax, true);
			}
			else if(key.equalsIgnoreCase(inDir+"SA.grid.50to100km.in") || key.equalsIgnoreCase(inDir+"SA.grid.100to150km.in")){
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.SUBDUCTION_SLAB,gridFile.get(key),
						latmin, latmax, lonmin, lonmax, true);
			}
			else if(key.equalsIgnoreCase(inDir+"SA.gridE.0to50km.in")){
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.STABLE_SHALLOW,gridFile.get(key),
						latmin, latmax, lonmin, lonmax, true);
			}

			for(int i=0;i<gm.getList().size();i++) srcDataList.add(gm.getList().get(i));
		}
		
	}
	
}
