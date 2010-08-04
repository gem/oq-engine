package org.opensha.gem.GEM1.calc.gemModelData.nshmp.us;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpFault2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpCeusFaultData extends GemFileParser {
	
	private final static boolean D = false;	// for debugging
	
	private String inDir = NshmpUsData.dataDir + "ceus/fault/";

	// constructor
	public NshmpCeusFaultData(double latmin, double latmax, double lonmin, double lonmax) throws FileNotFoundException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing fault file with corresponding weight
		HashMap<String,Double> faultFile = new HashMap<String,Double>();
		
		// Cheraw and Meers faults
		faultFile.put(inDir+"CEUScm.in",1.0);

		// New Madrid non-cluster model
		faultFile.put(inDir+"NMSZnocl.500yr.5branch.in",0.45);
		faultFile.put(inDir+"NMSZnocl.1000yr.5branch.in",0.05);
		
		// iterator over files
		Set<String> fileName = faultFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+faultFile.get(key));
			// read NSHMP input file
			NshmpFault2GemSourceData fm = new NshmpFault2GemSourceData(key,TectonicRegionType.STABLE_SHALLOW,faultFile.get(key),
					latmin, latmax, lonmin, lonmax);
			for(int i=0;i<fm.getList().size();i++) srcDataList.add(fm.getList().get(i));
		}
		
		
	}

}
