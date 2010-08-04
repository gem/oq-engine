package org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpFault2GemSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthAmericaFaultData extends GemFileParser{
	
	private final static boolean D = false;	// for debugging
	
	private String inDir = "/org/opensha/gem/GEM1/data/nshmp/south_america/fault/";
	
	public NshmpSouthAmericaFaultData(double latmin, double latmax, double lonmin, double lonmax) throws FileNotFoundException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing fault file with corresponding weight
		HashMap<String,Double> faultFile = new HashMap<String,Double>();
		
		// South America active tectonic faults
		// the weights were told to me by Sthepen Harmsen
		faultFile.put(inDir+"sam.fixed.char_modified.txt",0.5);
		faultFile.put(inDir+"sam.fixed.gr_modified.txt",0.5);
		
		// South America craton faults
		faultFile.put(inDir+"sam.craton2.char",0.5);
		faultFile.put(inDir+"sam.craton2.gr",0.5);
		
		// iterator over files
		Set<String> fileName = faultFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+faultFile.get(key));
			NshmpFault2GemSourceData fm = null;
			if(key.equalsIgnoreCase(inDir+"sam.fixed.char_modified.txt") ||  key.equalsIgnoreCase(inDir+"sam.fixed.gr_modified.txt")){
				fm = new NshmpFault2GemSourceData(key,TectonicRegionType.ACTIVE_SHALLOW,faultFile.get(key),
						latmin, latmax, lonmin, lonmax);
			}
			else if(key.equalsIgnoreCase(inDir+"sam.craton2.char") ||  key.equalsIgnoreCase(inDir+"sam.craton2.gr")){
				fm = new NshmpFault2GemSourceData(key,TectonicRegionType.STABLE_SHALLOW,faultFile.get(key),
						latmin, latmax, lonmin, lonmax);
			}
			for(int i=0;i<fm.getList().size();i++) srcDataList.add(fm.getList().get(i));
		}

		
	}
	
}
