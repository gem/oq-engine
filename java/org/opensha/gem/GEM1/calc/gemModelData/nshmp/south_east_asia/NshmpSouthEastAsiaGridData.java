package org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_east_asia;


import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthEastAsiaGridData extends GemFileParser{
	
	private final static boolean D = false;	// for debugging
	
	private static String inDir = "../../data/nshmp/south_east_asia/grid/";

	public NshmpSouthEastAsiaGridData(double latmin, double latmax, double lonmin, double lonmax){
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing grid file with corresponding weight
		HashMap<String,Double> gridFile = new HashMap<String,Double>();
		
//		SEAsiagrid_mt_abc.pga -> SEasia.grid_mt_abc.lowQ.in
//		0.5
		gridFile.put(inDir+"SEasia.grid_mt_abc.lowQ.in",0.5);
		
//		SEAsiagrid_mt_b.pga -> SEasia.grid_mt_b.lowQ.in
//		0.5
		gridFile.put(inDir+"SEasia.grid_mt_b.lowQ.in",0.5);
		
//		SEAsiagrid_mt_c.pga -> SEasia.grid_mt.c.lowQ.in
//		0.5
		gridFile.put(inDir+"SEasia.grid_mt_c.lowQ.in",0.5);
		
//		SEAsiagrid_mt_d.pga -> SEasia.grid_mt.d.lowQ.in
//		1.0
		gridFile.put(inDir+"SEasia.grid_mt_d.lowQ.in",1.0);
		
//		SEasiagrid.lowQ.pga -> SEasia.shallow.lowQ.in
//		1
		gridFile.put(inDir+"SEasia.shallow.lowQ.in",1.0);
		
//		SEAsia.deep200.pga -> SEAsia.deep200.in
//		1
		gridFile.put(inDir+"SEAsia.deep200.in",1.0);
		
//		SEAsia.deep150.pga -> SEAsia.deep150.in
//		1
		gridFile.put(inDir+"SEAsia.deep150.in",1.0);
		
//		SEAsia.deep100.pga -> SEAsia.deep100.in
//		1
		gridFile.put(inDir+"SEAsia.deep100.in",1.0);
		
//		SEAsia.deep50.pga -> SEAsia.deep50.in
//		1
		gridFile.put(inDir+"SEAsia.deep50.in",1.0);
		
//		Stable_Sundagrid.pga -> suma-java.shallow.highQ.in
//		1
		gridFile.put(inDir+"suma-java.shallow.highQ.in",1.0);
		
		// iterator over files
		Set<String> fileName = gridFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
			NshmpGrid2GemSourceData gm = null;
			if(key.equalsIgnoreCase(inDir+"SEAsia.deep100.in") || key.equalsIgnoreCase(inDir+"SEAsia.deep150.in")
					|| key.equalsIgnoreCase(inDir+"SEAsia.deep200.in")
					|| key.equalsIgnoreCase(inDir+"SEAsia.deep50.in")){
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.SUBDUCTION_SLAB,gridFile.get(key),
						latmin, latmax, lonmin, lonmax, false);
			}
			else{
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.ACTIVE_SHALLOW,gridFile.get(key),
						latmin, latmax, lonmin, lonmax, false);
			}

			for(int i=0;i<gm.getList().size();i++) srcDataList.add(gm.getList().get(i));
		
	    }
	}
	
}
