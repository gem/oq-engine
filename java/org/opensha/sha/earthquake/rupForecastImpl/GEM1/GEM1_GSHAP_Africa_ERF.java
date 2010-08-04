package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemModelData.gshap.africa.GshapAfricaData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GEM1_GSHAP_Africa_ERF extends GEM1ERF {
	
	private static final long serialVersionUID = 1L;
	
	public final static String NAME = "GEM1 GSHAP Africa ERF";
	
	public GEM1_GSHAP_Africa_ERF() {
		this(null);
	}
	
	public GEM1_GSHAP_Africa_ERF(CalculationSettings calcSet) {
		try {
			ArrayList<GEMSourceData> list = new GshapAfricaData().getList();
			this.parseSourceListIntoDifferentTypes(list);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
//		for(int i=0; i<gemSourceDataList.size(); i++) System.out.println(i+"\t"+gemSourceDataList.get(i).getName());

		initialize(calcSet);
		
	}

	@Override
	public String getName() {
		return NAME;
	}

}
