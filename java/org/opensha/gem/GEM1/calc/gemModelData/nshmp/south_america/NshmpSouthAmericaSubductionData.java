package org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpSubduction2GemSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthAmericaSubductionData extends GemFileParser {
	
	private final static boolean D = false;	// for debugging
	
	private String inDir = "/org/opensha/gem/GEM1/data/nshmp/south_america/subduction/";
	
	public NshmpSouthAmericaSubductionData(double latmin, double latmax, double lonmin, double lonmax) throws IOException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing fault file with corresponding weight
		HashMap<String,Double> faultFile = new HashMap<String,Double>();
		
		// Caribbean subduction under North South America
		faultFile.put(inDir+"Caribbean.sub9.in",1.0);
		
		// North of Panama
		faultFile.put(inDir+"pan.sub100n.new.in",0.4845);  // weights taken from combine.sub.allzones.pga
		
		// South of Panama
		faultFile.put(inDir+"pan.sub100s.new.in",0.4845);
		
		// subduction along Pacific
		faultFile.put(inDir+"sub-gr-z1.in",1.0);
		
		faultFile.put(inDir+"sub-gr-z2.in",1.0);
		
		faultFile.put(inDir+"sub-gr-z3.in",1.0);
		
		faultFile.put(inDir+"sub-gr-z4.in",1.0);
		
		faultFile.put(inDir+"sub-gr-z5.in",1.0);
		
		faultFile.put(inDir+"sub-ch9-z4.in",1.0);
		
		faultFile.put(inDir+"sub-ch95-z4.in",1.0);
		
		faultFile.put(inDir+"sub-ch95-z4z5.in",1.0);
		
		faultFile.put(inDir+"sub-ch95-z5.in",1.0);

		faultFile.put(inDir+"sub-char-z2.in",1.0);
		
		faultFile.put(inDir+"sub-char9p0-z1.in",1.0);
		
		faultFile.put(inDir+"sub-char9p0-z3.in",1.0);
		
		// iterator over files
		Set<String> fileName = faultFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+faultFile.get(key));
			NshmpSubduction2GemSourceData fm = null;
			fm = new NshmpSubduction2GemSourceData(key,TectonicRegionType.SUBDUCTION_INTERFACE,faultFile.get(key),
					latmin, latmax, lonmin, lonmax);
			for(int i=0;i<fm.getList().size();i++) srcDataList.add(fm.getList().get(i));
		}
		
	}

}
