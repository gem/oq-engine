package scratch.kevin.faultParticipationProbs;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.Container2D;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

public class SAF_Test {

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		DeformationModelPrefDataFinal data = new DeformationModelPrefDataFinal();
		int defModel = 82;
		double gridSpacing = 1.0;
		double magThresh = 6.7;
		System.out.println("Creating surfaces");
		ArrayList<StirlingGriddedSurface> surfaces = new ArrayList<StirlingGriddedSurface>();
		for (int faultSectionId : data.getFaultSectionIdsForDeformationModel(defModel)) {
			FaultSectionPrefData fault = data.getFaultSectionPrefData(defModel, faultSectionId);
			SimpleFaultData simpleFaultData = fault.getSimpleFaultData(false);
			StirlingGriddedSurface surface = new StirlingGriddedSurface(simpleFaultData, gridSpacing, gridSpacing);
			surfaces.add(surface);
			surface.setName(fault.getName());
		}
		
		System.out.println("Creating forecast");
		MeanUCERF2 ucerf = new MeanUCERF2();
		ucerf.updateForecast();
		System.out.println("Done");
		
		double maxProb = 0;
		
		for (StirlingGriddedSurface surface : surfaces) {
//			System.out.println("checking fault: " + surface.getName());
			if (!surface.getName().toLowerCase().contains("andreas"))
				continue;
			String safeName = surface.getName();
			safeName = safeName.replaceAll("\\(", "");
			safeName = safeName.replaceAll("\\)", "");
			safeName = safeName.replaceAll(" ", "_");
			File dir = new File("pp_files" + File.separator);
			if (!dir.exists())
				dir.mkdir();
			FileWriter fw = new FileWriter(dir.getAbsolutePath() + File.separator + safeName + ".txt");
			System.out.println("working on fault: " + surface.getName());
			Container2D<Double> participationProbs = new Container2D<Double>(surface.getNumRows(), surface.getNumCols());
			for (int i=0; i<surface.getNumRows(); i++) {
				for (int j=0; j<surface.getNumCols(); j++) {
					participationProbs.set(i, j, new Double(0.0));
				}
			}
			for (int sourceID=0; sourceID<ucerf.getNumSources(); sourceID++) {
				ProbEqkSource source = ucerf.getSource(sourceID);
//				System.out.println("checking on source: " + source.getName());
				if (!source.getName().toLowerCase().contains("andreas"))
					continue;
//				System.out.println("working on source: " + source.getName());
				for (int ruptureID=0; ruptureID<source.getNumRuptures(); ruptureID++) {
					ProbEqkRupture rupture = source.getRupture(ruptureID);
					if (rupture.getMag() < magThresh)
						continue;
					System.out.println("Working on source " + sourceID + " (" + source.getName() + ") rup " + ruptureID);
					EvenlyGriddedSurfaceAPI rupSurface = rupture.getRuptureSurface();
					int closestI = -1;
					int closestJ = -1;
					double closestDist = 0.5;
					Location topLeft = rupSurface.get(0, 0);
					for (int i=0; i<surface.getNumRows(); i++) {
						for (int j=0; j<surface.getNumCols(); j++) {
							Location surfLoc = surface.get(i, j);
							double dist = LocationUtils.linearDistanceFast(topLeft, surfLoc);
							if (dist < closestDist) {
								closestDist = dist;
								closestI = i;
								closestJ = j;
							}
						}
					}
					if (closestI < 0 || closestJ < 0) {
//						System.out.println("no match :-(");
						continue;
					}
					System.out.println("We got a match! i: " + closestI + " j: " + closestJ + " dist: " + closestDist);
					for (int i=0; i<rupSurface.getNumRows(); i++) {
						int fltI = i + closestI;
						if (fltI >= surface.getNumRows())
							continue;
						for (int j=0; j<rupSurface.getNumCols(); j++) {
							int fltJ = j + closestJ;
							if (fltJ >= surface.getNumCols())
								continue;
							double prev = participationProbs.get(fltI, fltJ);
							participationProbs.set(fltI, fltJ, prev + rupture.getProbability());
						}
					}
				}
			}
//			fw.write("* " + surface.getName() + " *" + "\n");
			for (int i=0; i<surface.getNumRows(); i++) {
				for (int j=0; j<surface.getNumCols(); j++) {
					Location loc = surface.get(i, j);
					double val = participationProbs.get(i, j);
					if (val > maxProb)
						maxProb = val;
					fw.write(loc.getLatitude() + "\t" + loc.getLongitude() + "\t" + loc.getDepth() + "\t" + val + "\n");
				}
			}
			fw.close();
		}
		System.out.println("max prob: " + maxProb);
	}

}
