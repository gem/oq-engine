package scratch.kevin;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;

import org.opensha.commons.data.NamedObjectComparator;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

public class DefModelPtFileWriter {
	
	public static void main(String args[]) throws IOException {
		int deformationModelID = 82;
		boolean removeNans = false;
		boolean aseisReducesArea = false;
		double maxDiscretization = 3.0;
		
		// fetch the sections
		DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();
		ArrayList<FaultSectionPrefData> allFaultSectionPrefData = deformationModelPrefDB.getAllFaultSectionPrefData(deformationModelID);

		//Alphabetize:
		Collections.sort(allFaultSectionPrefData, new NamedObjectComparator());

		/*		  
		  // write sections IDs and names
		  for(int i=0; i< this.allFaultSectionPrefData.size();i++)
				System.out.println(allFaultSectionPrefData.get(i).getSectionId()+"\t"+allFaultSectionPrefData.get(i).getName());
		 */

		// remove those with no slip rate
		if (removeNans) {
			for(int i=allFaultSectionPrefData.size()-1; i>=0;i--) {
				if(Double.isNaN(allFaultSectionPrefData.get(i).getAveLongTermSlipRate())) {
					allFaultSectionPrefData.remove(i);
				}
			}
		}
		
		FileWriter fw = new FileWriter("/tmp/dm_d.1_pts.txt");
		
		for (FaultSectionPrefData fault : allFaultSectionPrefData) {
			String name = fault.getName();
			double slip = fault.getAveLongTermSlipRate();
			StirlingGriddedSurface surface = new StirlingGriddedSurface(fault.getSimpleFaultData(aseisReducesArea),
					maxDiscretization, maxDiscretization);
			
			fw.write("# name: '" + name + "'\tslip: " + slip + "\n");
			for (Location loc : surface) {
				fw.write(loc.getLatitude() + "\t" + loc.getLongitude() + "\t" + loc.getDepth() + "\n");
			}
		}
		fw.close();
	}

}
