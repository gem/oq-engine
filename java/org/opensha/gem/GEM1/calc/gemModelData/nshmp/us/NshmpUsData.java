package org.opensha.gem.GEM1.calc.gemModelData.nshmp.us;

import java.io.FileNotFoundException;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class NshmpUsData  extends GemFileParser{
	
	public static final String dataDir = "/org/opensha/gem/GEM1/data/nshmp/us/";
	
	public NshmpUsData(double latmin, double latmax, double lonmin, double lonmax) throws FileNotFoundException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// Western United States fault model (active shallow tectonics)
		NshmpWusFaultData wusFault =  new NshmpWusFaultData(latmin,latmax,lonmin,lonmax);
		
		// Western United States grid model (active shallow and subduction intraslab)
		NshmpWusGridData wusGrid = new NshmpWusGridData(latmin,latmax,lonmin,lonmax);
		
		// Western United States Cascadia subduction model (subduction interface)
		NshmpCascadiaSubductionData cascadiaSub = new NshmpCascadiaSubductionData(latmin,latmax,lonmin,lonmax);
		
		// Central and Eastern United States fault model (stable shallow tectonics)
		NshmpCeusFaultData ceusFault = new NshmpCeusFaultData(latmin,latmax,lonmin,lonmax);
		
		// Central and Eastern United States grid model (stable shallow tectonics)
		NshmpCeusGridData ceusGrid = new NshmpCeusGridData(latmin,latmax,lonmin,lonmax);
		
		srcDataList.addAll(wusFault.getList());
		srcDataList.addAll(wusGrid.getList());
		srcDataList.addAll(cascadiaSub.getList());
		srcDataList.addAll(ceusFault.getList());
		srcDataList.addAll(ceusGrid.getList());
	}

}
