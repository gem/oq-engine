package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NewNshmpWusGridData extends GemFileParser{
	
	// directory for grid seismicity files
	private String inDir = "nshmp/wus_grids/";
	
	public NewNshmpWusGridData(double latmin, double latmax, double lonmin, double lonmax) throws FileNotFoundException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		NshmpGrid2GemSourceData gm = null;
		
		ArrayList<String> inputGridFile = null;
		
		ArrayList<Double> inputGridFileWeight = new ArrayList<Double>();

		
		// Mendocino South Region model
		//gridFile.put(inDir+"Mendomap.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"Mendomap.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// Mojave Desert model
		//gridFile.put(inDir+"mojave.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"mojave.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// San Gorgonio Pass Region model
		//gridFile.put(inDir+"sangreg.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"sangreg.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// California model
		// GR -> 0.333
		// CHAR -> 0.667
		// Deformation model 2.1 -> 0.5
		// Deformation model 2.4 -> 0.5
//		gridFile.put(inDir+"CAmapC_21.in",0.3335);
//		gridFile.put(inDir+"CAmapC_24.in",0.3335);
//		gridFile.put(inDir+"CAmapG_21.in",0.1665);
//		gridFile.put(inDir+"CAmapG_24.in",0.1665);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"CAmapC_21.in");
		inputGridFileWeight.add(0.3335);
		inputGridFile.add(inDir+"CAmapC_24.in");
		inputGridFileWeight.add(0.3335);
		inputGridFile.add(inDir+"CAmapG_21.in");
		inputGridFileWeight.add(0.1665);
		inputGridFile.add(inDir+"CAmapG_24.in");
		inputGridFileWeight.add(0.1665);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		
		
		// Brawley Zone model
		//gridFile.put(inDir+"brawmap.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"brawmap.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// impext model (I could not find the actual name)
//		gridFile.put(inDir+"impextC.in",0.6667);
//		gridFile.put(inDir+"impextG.in",0.3333);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"impextC.in");
		inputGridFileWeight.add(0.6667);
		inputGridFile.add(inDir+"impextG.in");
		inputGridFileWeight.add(0.3333);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// Creeping Section SAF
		//gridFile.put(inDir+"creepmap.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"creepmap.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// Extensional WUS
//		gridFile.put(inDir+"EXTmapC.in",0.6667);
//		gridFile.put(inDir+"EXTmapG.in",0.3333);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"EXTmapC.in");
		inputGridFileWeight.add(0.6667);
		inputGridFile.add(inDir+"EXTmapG.in");
		inputGridFileWeight.add(0.3333);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// Shear Zone California-Nevada border region
		//gridFile.put(inDir+"SHEAR1.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"SHEAR1.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		//gridFile.put(inDir+"SHEAR2.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"SHEAR2.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		//gridFile.put(inDir+"SHEAR3.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"SHEAR3.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		//gridFile.put(inDir+"SHEAR4.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"SHEAR4.in",TectonicRegionType.ACTIVE_SHALLOW,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// Western United States model
//		gridFile.put(inDir+"WUSmapC.in",0.25);
//		gridFile.put(inDir+"WUSmapG.in",0.25);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"WUSmapC.in");
		inputGridFileWeight.add(0.25);
		inputGridFile.add(inDir+"WUSmapG.in");
		inputGridFileWeight.add(0.25);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// nopuget model
//		gridFile.put(inDir+"nopugetC.in",0.25);
//		gridFile.put(inDir+"nopugetG.in",0.25);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"nopugetC.in");
		inputGridFileWeight.add(0.25);
		inputGridFile.add(inDir+"nopugetG.in");
		inputGridFileWeight.add(0.25);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// puget model
//		gridFile.put(inDir+"pugetmapC.in",0.25);
//		gridFile.put(inDir+"pugetmapG.in",0.25);
		inputGridFile = new ArrayList<String>();
		inputGridFileWeight = new ArrayList<Double>();
		inputGridFile.add(inDir+"pugetmapC.in");
		inputGridFileWeight.add(0.25);
		inputGridFile.add(inDir+"pugetmapG.in");
		inputGridFileWeight.add(0.25);
		gm = new NshmpGrid2GemSourceData(inputGridFile,TectonicRegionType.ACTIVE_SHALLOW,inputGridFileWeight,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// pacific north west deep events
		//gridFile.put(inDir+"pacnwdeep.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"pacnwdeep.in",TectonicRegionType.SUBDUCTION_SLAB,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// portdeep model
		//gridFile.put(inDir+"portdeep.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"portdeep.in",TectonicRegionType.SUBDUCTION_SLAB,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
		// california deep events
		//gridFile.put(inDir+"CAdeep.in",1.0);
		gm = new NshmpGrid2GemSourceData(inDir+"CAdeep.in",TectonicRegionType.SUBDUCTION_SLAB,1.0,
				latmin, latmax, lonmin, lonmax,true);
		srcDataList.addAll(gm.getList());
		
//		// iterator over files
//		Set<String> fileName = gridFile.keySet();
//		Iterator<String> iterFileName = fileName.iterator();
//		while(iterFileName.hasNext()){
//			String key = iterFileName.next();
//			System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
//			NshmpGrid2GemSourceData gm = null;
//			if(key.equalsIgnoreCase(inDir+"pacnwdeep.in") || key.equalsIgnoreCase(inDir+"portdeep.in")
//					|| key.equalsIgnoreCase(inDir+"CAdeep.in")){
//				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.SUBDUCTION_SLAB,gridFile.get(key),
//						latmin, latmax, lonmin, lonmax,true);
//			}
//			else{
//				gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.ACTIVE_SHALLOW,gridFile.get(key),
//						latmin, latmax, lonmin, lonmax,true);
//			}
//
//			for(int i=0;i<gm.getList().size();i++) srcDataList.add(gm.getList().get(i));
//		}
		
	}

}
