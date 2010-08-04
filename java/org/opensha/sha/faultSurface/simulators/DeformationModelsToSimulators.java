package org.opensha.sha.faultSurface.simulators;

import java.util.ArrayList;
import java.util.Collections;

import org.opensha.commons.data.NamedObjectComparator;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.PlaneUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.EvenlyGridCenteredSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

public class DeformationModelsToSimulators {

	protected final static boolean D = false;  // for debugging
	
	private boolean aseisReducesArea;
	private double maxDiscretization;
	private ArrayList<FaultSectionPrefData> allFaultSectionPrefData;
	

	public DeformationModelsToSimulators(int deformationModelID,
			boolean aseisReducesArea,
			double maxDiscretization) {

		/** Set the deformation model
		 * D2.1 = 82
		 * D2.2 = 83
		 * D2.3 = 84
		 * D2.4 = 85
		 * D2.5 = 86
		 * D2.6 = 87
		 */
		
		this.aseisReducesArea = aseisReducesArea;
		this.maxDiscretization = maxDiscretization;

		// fetch the sections
		DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();
		allFaultSectionPrefData = deformationModelPrefDB.getAllFaultSectionPrefData(deformationModelID);

		//Alphabetize:
		Collections.sort(allFaultSectionPrefData, new NamedObjectComparator());

		/*		  
		  // write sections IDs and names
		  for(int i=0; i< this.allFaultSectionPrefData.size();i++)
				System.out.println(allFaultSectionPrefData.get(i).getSectionId()+"\t"+allFaultSectionPrefData.get(i).getName());
		 */

		// remove those with no slip rate
		if (D)System.out.println("Removing the following due to NaN slip rate:");
		for(int i=allFaultSectionPrefData.size()-1; i>=0;i--)
			if(Double.isNaN(allFaultSectionPrefData.get(i).getAveLongTermSlipRate())) {
				if(D) System.out.println("\t"+allFaultSectionPrefData.get(i).getSectionName());
				allFaultSectionPrefData.remove(i);
			}	 

		/*	
		  // find and print max Down-dip width
		  double maxDDW=0;
		  int index=-1;
		  for(int i=0; i<allFaultSectionPrefData.size(); i++) {
			  double ddw = allFaultSectionPrefData.get(i).getDownDipWidth();
			  if(ddw>maxDDW) {
				  maxDDW = ddw;
				  index=i;
			  }
		  }
		  System.out.println("Max Down-Dip Width = "+maxDDW+" for "+allFaultSectionPrefData.get(index).getSectionName());
		 */	
		
		

	}
	
	public ArrayList<SimulatorFaultSurface> getSimulatorSurfaces() {
		ArrayList<SimulatorFaultSurface> surfaces = new ArrayList<SimulatorFaultSurface>();
		
		// Loop over sections and create the simulator elements
		int elementID =0;
		int numberAlongStrike = 0;
		int numberDownDip;
		int faultNumber = -1;
		int sectionNumber =0;
		double elementSlipRate=0;
		double elementStrength = Double.NaN;
		double elementStrike=0, elementDip=0, elementRake=0;
		String sectionName;
		System.out.println("got here");
		for(int i=0;i<allFaultSectionPrefData.size();i++) {
//		for(int i=0;i<2;i++) {
			sectionNumber +=1;
			FaultSectionPrefData faultSectionPrefData = allFaultSectionPrefData.get(i);
			StirlingGriddedSurface surface = new StirlingGriddedSurface(faultSectionPrefData.getSimpleFaultData(aseisReducesArea), maxDiscretization, maxDiscretization);
			EvenlyGridCenteredSurface gridCenteredSurf = new EvenlyGridCenteredSurface(surface);
			double elementLength = gridCenteredSurf.getGridSpacingAlongStrike();
			double elementDDW = gridCenteredSurf.getGridSpacingDownDip(); // down dip width
			elementRake = faultSectionPrefData.getAveRake();
			elementSlipRate = faultSectionPrefData.getAveLongTermSlipRate()/1000;
			sectionName = faultSectionPrefData.getName();
			for(int col=0; col<gridCenteredSurf.getNumCols();col++) {
				numberAlongStrike += 1;
				for(int row=0; row<gridCenteredSurf.getNumRows();row++) {
					elementID +=1;
					numberDownDip = row+1;
					Location centerLoc = gridCenteredSurf.get(row, col);
					Location top1 = surface.get(row, col);
					Location top2 = surface.get(row, col+1);
					Location bot1 = surface.get(row+1, col);
//					Location bot2 = surface.get(row+1, col+1);
					double[] strikeAndDip = PlaneUtils.getStrikeAndDip(top1, top2, bot1);
					elementStrike = strikeAndDip[0];
					elementDip = strikeAndDip[1];	
					
					double hDistAlong = elementLength/2;
					double dipRad = Math.PI*elementDip/180;
					double vDist = (elementDDW/2)*Math.sin(dipRad);
					double hDist = (elementDDW/2)*Math.cos(dipRad);
					
//					System.out.println(elementID+"\telementDDW="+elementDDW+"\telementDip="+elementDip+"\tdipRad="+dipRad+"\tvDist="+vDist+"\thDist="+hDist);
					
					LocationVector vect = new LocationVector(elementStrike+180, hDistAlong, 0);
					Location newMid1 = LocationUtils.location(centerLoc, vect);  // half way down the first edge
					vect.set(elementStrike-90, hDist, -vDist); // up-dip direction
					Location newTop1 = LocationUtils.location(newMid1, vect);
					vect.set(elementStrike+90, hDist, vDist); // down-dip direction
					Location newBot1 = LocationUtils.location(newMid1, vect);
					 
					vect.set(elementStrike, hDistAlong, 0);
					Location newMid2 = LocationUtils.location(centerLoc, vect); // half way down the other edge
					vect.set(elementStrike-90, hDist, -vDist); // up-dip direction
					Location newTop2 = LocationUtils.location(newMid2, vect);
					vect.set(elementStrike+90, hDist, vDist); // down-dip direction
					Location newBot2 = LocationUtils.location(newMid2, vect);
					
					Location[][] pts = new Location[2][2];
					pts[0][0] = newTop1;
					pts[0][1] = newTop2;
					pts[1][0] = newBot1;
					pts[1][1] = newBot2;
/*					
					if(elementID==254) {
						System.out.println(newTop1);
						System.out.println(newTop2);
						System.out.println(newBot1);
						System.out.println(newBot2);
					}
*/					
					FocalMechanism focalMech = new FocalMechanism(elementStrike, elementDip, elementRake);
										
					SimulatorFaultSurface simSurface =
						new SimulatorFaultSurface(elementID, pts, sectionName,
								faultNumber, sectionNumber, numberAlongStrike, numberDownDip,
								elementSlipRate, elementStrength, focalMech);
					
					surfaces.add(simSurface);
					
//					String line = elementID + "\t"+
//						numberAlongStrike + "\t"+
//						numberDownDip + "\t"+
//						faultNumber + "\t"+
//						sectionNumber + "\t"+
//						(float)elementSlipRate + "\t"+
//						(float)elementStrength + "\t"+
//						(float)elementStrike + "\t"+
//						(float)elementDip + "\t"+
//						(float)elementRake + "\t"+
//						(float)newTop1.getLatitude() + "\t"+
//						(float)newTop1.getLongitude() + "\t"+
//						(float)newTop1.getDepth()*-1000 + "\t"+
//						(float)newBot1.getLatitude() + "\t"+
//						(float)newBot1.getLongitude() + "\t"+
//						(float)newBot1.getDepth()*-1000 + "\t"+
//						(float)newBot2.getLatitude() + "\t"+
//						(float)newBot2.getLongitude() + "\t"+
//						(float)newBot2.getDepth()*-1000 + "\t"+
//						(float)newTop2.getLatitude() + "\t"+
//						(float)newTop2.getLongitude() + "\t"+
//						(float)newTop2.getDepth()*-1000 + "\t"+
//						sectionName;
//
//					System.out.println(line);
				}
			}
		}
		
		return surfaces;
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		long startTime=System.currentTimeMillis();
		DeformationModelsToSimulators test = new DeformationModelsToSimulators(82, false, 4.0);
		test.getSimulatorSurfaces();
		int runtime = (int)(System.currentTimeMillis()-startTime)/1000;
		System.out.println("Run took "+runtime+" seconds");
	}



}
