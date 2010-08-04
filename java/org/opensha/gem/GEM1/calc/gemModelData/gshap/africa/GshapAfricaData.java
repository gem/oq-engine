package org.opensha.gem.GEM1.calc.gemModelData.gshap.africa;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa.GshapAfrica2GemSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa.GshapIberoMagreb2GemSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa.GshapIsrael2GemSourceData;
import org.opensha.gem.GEM1.calc.gemModelParsers.gshap.africa.SsAfrica2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

/**
 * This class builds an array list of GEMAreatSourceData objects 
 * representing the area sources for calculation the seismic hazard in Africa 
 * The input models are:
 * - IberoMagreb
 * - EastMagreb: Libya and Egypt
 * - Western Africa
 * - SubSahara Region - Africa
 *  * @author l.danciu
 */
public class GshapAfricaData extends GemFileParser{

	public GshapAfricaData() throws IOException{

		srcDataList = new ArrayList<GEMSourceData>();

		// IberoMagreb model
		GshapIberoMagreb2GemSourceData model1 = new GshapIberoMagreb2GemSourceData("../../data/gshap/africa/IberoMagreb.dat");
		
		// Israel Model
		GshapIsrael2GemSourceData model2 = new GshapIsrael2GemSourceData("../../data/gshap/africa/Israel.dat");
		
		//EastIberoMagreb 
		GshapAfrica2GemSourceData model3 = new GshapAfrica2GemSourceData("../../data/gshap/africa/EastIberoMagreb.dat");
		
		// Western Africa
		GshapAfrica2GemSourceData model4 = new GshapAfrica2GemSourceData("../../data/gshap/africa/WestAfrica.dat");
		
		// SubSahara Region
		SsAfrica2GemSourceData model5 = new SsAfrica2GemSourceData();

		srcDataList.addAll(model1.getList());
		srcDataList.addAll(model2.getList());
		srcDataList.addAll(model3.getList());
		srcDataList.addAll(model4.getList());
		srcDataList.addAll(model5.getList());
	}
	
	// main method for testing
	public static void main(String[] args) throws IOException{
		
		// read input file and create array list of GEMSourceData
		GshapAfricaData model = new GshapAfricaData();
		
		model.writeAreaKMLfile(new FileWriter("/Users/damianomonelli/Desktop/AfricaAreaSources.kml"));
		
	}

}

