package org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;

public class NshmpSouthAmericaData extends GemFileParser{
	
	public NshmpSouthAmericaData(double latmin, double latmax, double lonmin, double lonmax) throws IOException{
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		// South America fault model (both shallow active and stable crust sources)
		NshmpSouthAmericaFaultData fault = new NshmpSouthAmericaFaultData(latmin,latmax,lonmin,lonmax);
		
		// South America grid model (both shallow active and stable crust sources plus intraslab sources)
		NshmpSouthAmericaGridData grid = new NshmpSouthAmericaGridData(latmin,latmax,lonmin,lonmax);
		
		// South America subduction model (interface sources)
		NshmpSouthAmericaSubductionData sub = new NshmpSouthAmericaSubductionData(latmin,latmax,lonmin,lonmax);
		
		srcDataList.addAll(fault.getList());
		srcDataList.addAll(grid.getList());
		srcDataList.addAll(sub.getList());
		
	}

}
