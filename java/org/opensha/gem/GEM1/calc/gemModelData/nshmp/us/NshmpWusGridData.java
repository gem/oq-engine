package org.opensha.gem.GEM1.calc.gemModelData.nshmp.us;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpWusGridData  extends GemFileParser{
	
	private final static boolean D = false;	// for debugging
	
	// directory for grid seismicity files
	private String inDir = NshmpUsData.dataDir + "wus/grid/";
	
	public NshmpWusGridData(double latmin, double latmax, double lonmin, double lonmax){
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// hash map containing grid file with corresponding weight
		HashMap<String,Double> gridFile = new HashMap<String,Double>();

		
		// Mendocino South Region model
		gridFile.put(inDir+"Mendomap.in",1.0);
		
		// Mojave Desert model
		gridFile.put(inDir+"mojave.in",1.0);
		
		// San Gorgonio Pass Region model
		gridFile.put(inDir+"sangreg.in",1.0);
		
		// California model
		// GR -> 0.333
		// CHAR -> 0.667
		// Deformation model 2.1 -> 0.5
		// Deformation model 2.4 -> 0.5
		gridFile.put(inDir+"CAmapC_21.in",0.3335);
		gridFile.put(inDir+"CAmapC_24.in",0.3335);
		gridFile.put(inDir+"CAmapG_21.in",0.1665);
		gridFile.put(inDir+"CAmapG_24.in",0.1665);
		
		// Brawley Zone model
		gridFile.put(inDir+"brawmap.in",1.0);
		
		// impext model (I could not find the actual name)
		gridFile.put(inDir+"impextC.in",0.6667);
		gridFile.put(inDir+"impextG.in",0.3333);
		
		// Creeping Section SAF
		gridFile.put(inDir+"creepmap.in",1.0);
		
		// Extensional WUS
		gridFile.put(inDir+"EXTmapC.in",0.6667);
		gridFile.put(inDir+"EXTmapG.in",0.3333);
		
		// Shear Zone California-Nevada border region
		gridFile.put(inDir+"SHEAR1.in",1.0);
		gridFile.put(inDir+"SHEAR2.in",1.0);
		gridFile.put(inDir+"SHEAR3.in",1.0);
		gridFile.put(inDir+"SHEAR4.in",1.0);
		
		// Western United States model
		gridFile.put(inDir+"WUSmapC.in",0.25);
		gridFile.put(inDir+"WUSmapG.in",0.25);
		
		// nopuget model
		gridFile.put(inDir+"nopugetC.in",0.25);
		gridFile.put(inDir+"nopugetG.in",0.25);
		
		// puget model
		gridFile.put(inDir+"pugetmapC.in",0.25);
		gridFile.put(inDir+"pugetmapG.in",0.25);
		
		// pacific north west deep events
		gridFile.put(inDir+"pacnwdeep.in",1.0);
		
		// portdeep model
		gridFile.put(inDir+"portdeep.in",1.0);
		
		// california deep events
		gridFile.put(inDir+"CAdeep.in",1.0);
		
		// iterator over files
		Set<String> fileName = gridFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
			NshmpGrid2GemSourceData gm = null;
			if(key.equalsIgnoreCase(inDir+"pacnwdeep.in") || key.equalsIgnoreCase(inDir+"portdeep.in")
					|| key.equalsIgnoreCase(inDir+"CAdeep.in")){
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.SUBDUCTION_SLAB,gridFile.get(key),
						latmin, latmax, lonmin, lonmax,true);
			}
			else{
				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.ACTIVE_SHALLOW,gridFile.get(key),
						latmin, latmax, lonmin, lonmax,true);
			}

			for(int i=0;i<gm.getList().size();i++) srcDataList.add(gm.getList().get(i));
		}
		
	}

}
