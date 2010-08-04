package org.opensha.gem.GEM1.calc.gemModelData.nshmp.us;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Set;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.gem.GEM1.calc.gemModelParsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpCeusGridData extends GemFileParser implements Serializable {

	private final static boolean D = false;	// for debugging
	
	// directory for grid seismicity files
	private String inDir = NshmpUsData.dataDir + "ceus/grid/";
	
	public NshmpCeusGridData(double latmin, double latmax, double lonmin, double lonmax){
		
		srcDataList = new ArrayList<GEMSourceData>();
		
		ArrayList<String> file = new ArrayList<String>();
		ArrayList<Double> weight = new ArrayList<Double>();
		
		// hash map containing grid file with corresponding weight
		Hashtable<String,Double> gridFile = new Hashtable<String,Double>();

		
//		CEUSABhigh.pga.out
//		0.0333
		gridFile.put(inDir+"CEUS.2007.AB4.in",0.0333);
		
		
		
////		CEUSABstd.pga.out
////		0.08333
		gridFile.put(inDir+"CEUS.2007.AB3.in",0.08333);
		
////		CEUSABmid.pga.out
////		0.0333
		gridFile.put(inDir+"CEUS.2007.AB2.in",0.0333);

//		
////		CEUSABlow.pga.out
////		0.01667
		gridFile.put(inDir+"CEUS.2007.AB1.in",0.01667);

		
//////		CEUSJhigh.pga.out
//////		0.0333
		gridFile.put(inDir+"CEUS.2007.J4.in",0.0333);
		
//////		CEUSJstd.pga.out
//////		0.083333
		gridFile.put(inDir+"CEUS.2007.J3.in",0.083333);
		
//////		CEUSJmid.pga.out
//////		0.0333
		gridFile.put(inDir+"CEUS.2007.J2.in",0.0333);
		
//////		CEUSJlow.pga.out
//////		0.01667
    	gridFile.put(inDir+"CEUS.2007.J1.in",0.01667);
		
//////		CEUSABhigh.pga.nmc
//////		0.0667
		gridFile.put(inDir+"CEUS.2007a.AB4.in",0.0667);
		
//////		CEUSABstd.pga.nmc
//////		0.16666
		gridFile.put(inDir+"CEUS.2007a.AB3.in",0.16666);
		
//////		CEUSABmid.pga.nmc
//////		0.0667
		gridFile.put(inDir+"CEUS.2007a.AB2.in",0.0667);
		
//////		CEUSABlow.pga.nmc
//////		0.0333
		gridFile.put(inDir+"CEUS.2007a.AB1.in",0.0333);
		
//////		CEUSJhigh.pga.nmc
//////		0.06667
		gridFile.put(inDir+"CEUS.2007a.J4.in",0.06667);
		
//////		CEUSJstd.pga.nmc
//////		0.16667
		gridFile.put(inDir+"CEUS.2007a.J3.in",0.16667);
		
//////		CEUSJmid.pga.nmc
//////		0.06667
		gridFile.put(inDir+"CEUS.2007a.J2.in",0.06667);
		
//////		CEUSJlow.pga.nmc
//////		0.0333
		gridFile.put(inDir+"CEUS.2007a.J1.in",0.0333);
		
//////		CEUSchar.broad.pga
//////		0.225		! Broad charleston zone extending further offshore
		gridFile.put(inDir+"CEUSchar.broad.in",0.225);
		
//////		CEUScharA.broad.pga
//////		0.1
		gridFile.put(inDir+"CEUScharA.broad.in",0.1);
		
//////		CEUScharB.broad.pga
//////		0.075
		gridFile.put(inDir+"CEUScharB.broad.in",0.075);
		
//////		CEUScharC.broad.pga
//////		0.1
		gridFile.put(inDir+"CEUScharC.broad.in",0.1);
		
//////		CEUScharna.2007.pga
//////		0.225
		gridFile.put(inDir+"CEUScharn.in",0.225);
		
//////		CEUScharnA.2007.pga
//////		0.1
		gridFile.put(inDir+"CEUScharnA.in",0.1);
		
//////		CEUScharnB.2007.pga
//////		0.075
		gridFile.put(inDir+"CEUScharnB.in",0.075);
		
		
//////		CEUScharnC.2007.pga
//////		0.1
		gridFile.put(inDir+"CEUScharnC.in",0.1);
		
		// iterator over files
		Set<String> fileName = gridFile.keySet();
		Iterator<String> iterFileName = fileName.iterator();
		int indexFile = 1;
		while(iterFileName.hasNext()){
			String key = iterFileName.next();
			if (D) System.out.println("Processing file: "+key+", weight: "+gridFile.get(key));
			NshmpGrid2GemSourceData gm = null;
			gm = new NshmpGrid2GemSourceData(key,TectonicRegionType.STABLE_SHALLOW,gridFile.get(key),
					latmin, latmax, lonmin, lonmax,true);
			for(int i=0;i<gm.getList().size();i++) srcDataList.add(gm.getList().get(i));
//			if(indexFile>1){
//				gridList = trimGridList(gridList);
//			}
//			indexFile = indexFile+1;
			
		}
		
	}
	
	// loop over a list of grid sources and identify the sources with the same data
	// but the mfd and then create only one source with an mfd equal to the sum of the
	// mfds
	private ArrayList<GEMSourceData> trimGridList(ArrayList<GEMSourceData> gridList){
		
		// used to compute the final mfd
		double dm = 0.1;
		
		// new array list of sources
		ArrayList<GEMSourceData> newGridList = new ArrayList<GEMSourceData>();
		
		
		// loop over the sources
		for(int i=0;i<gridList.size();i++){
			
			System.out.println("Source: "+i+" of "+gridList.size());
			
			GEMPointSourceData psi = (GEMPointSourceData) gridList.get(i);
			
			// array list containing indexes of those sources which
			// will be "equal" to psi
			ArrayList<Integer> sameSource = new ArrayList<Integer>();
			
			// loop over remaining sources
			for(int j=i+1;j<gridList.size();j++){
				
				//System.out.println("Comparing source: "+i+" with source: "+j+" of "+gridList.size());
				
				GEMPointSourceData psj = (GEMPointSourceData) gridList.get(j);
				
				// is true only if the two sources have same data but the mfd
				boolean sameSourceData = false;
			    
				// first check if they have the same locations
				Location loci = psi.getHypoMagFreqDistAtLoc().getLocation();
				Location locj = psj.getHypoMagFreqDistAtLoc().getLocation();
				if(locj.getLatitude()==loci.getLatitude() && locj.getLongitude()==loci.getLongitude()){
					
					
					//System.out.println("Yes they have the same location!!");

					// then check if they have the same aveRupTopVsMag
					boolean sameAveRupTopVsMag = false;
					ArbitrarilyDiscretizedFunc rupVsMagi = psi.getAveRupTopVsMag();
					ArbitrarilyDiscretizedFunc rupVsMagj = psj.getAveRupTopVsMag();
					
					// they have the same number of points by definition (in the parser)
					for(int iv=0;iv<rupVsMagi.getNum();iv++){
						if(rupVsMagj.get(iv).getX()!=rupVsMagi.get(iv).getX() || rupVsMagj.get(iv).getY()!=rupVsMagi.get(iv).getY()){
							sameAveRupTopVsMag = false;
							break;
						}
						else{
							sameAveRupTopVsMag = true;
						}
					}
					
					// if they have the same aveRupTopVsMag
					if(sameAveRupTopVsMag){
						
						//System.out.println("Yes they have the same aveRupVsMag!!");
						
						// then check if they have the same number of focal mechanisms
						if(psj.getHypoMagFreqDistAtLoc().getFocalMechanismList().length==psi.getHypoMagFreqDistAtLoc().getFocalMechanismList().length){
							
							//System.out.println("Yes they have the same num of focal mechanism!");
							
							// then loop over focal mechanisms and check if they have the same parameters
							// if one parameter has not the same value in both the two sources break
							for(int ifm=0;ifm<psj.getHypoMagFreqDistAtLoc().getFocalMechanismList().length;ifm++){
								Double strikei = psi.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getStrike();
								Double strikej = psj.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getStrike();
								double dipi = psi.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getDip();
								double dipj = psj.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getDip();
								double rakei = psi.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getRake();
								double rakej = psj.getHypoMagFreqDistAtLoc().getFocalMech(ifm).getRake();
								
								if((strikei.isNaN() && strikej.isNaN()==false)
										|| (strikej.isNaN() && strikei.isNaN()==false)
										|| (strikei.isNaN()==false && strikej.isNaN()==false && strikei!=strikej)
										|| dipj!=dipi || rakej!=rakei){
								   sameSourceData = false;
								   break;
								}
								else{
									sameSourceData = true;
									//System.out.println("Yes they have the same strike, dip and rake!");
								}
							} // end loop over focal mechanism(s)
							
						} // end if focal mechanism(s) List have the same size
						
					}
					
				} // end if loc1==loc2
				
				
				if(sameSourceData){
					
					sameSource.add(j);
				
					IncrementalMagFreqDist[] magDist = new IncrementalMagFreqDist[psi.getHypoMagFreqDistAtLoc().getNumFocalMechs()];
					
					// loop over focal mechanisms
					for(int ifm=0;ifm<psi.getHypoMagFreqDistAtLoc().getNumFocalMechs();ifm++){
						
						ArrayList<IncrementalMagFreqDist> mfds = new ArrayList<IncrementalMagFreqDist>();
						mfds.add(psi.getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));
						mfds.add(psj.getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));
						
						// find lowest and highest mag from mfds
						// find also the lowest dmag
						double lowestMag=Double.MAX_VALUE;
						double highestMag=0;
						double lowestDeltaM = Double.MAX_VALUE;
						for(int imfd=0;imfd<mfds.size();imfd++){
							IncrementalMagFreqDist mfd = mfds.get(imfd);
							if(mfd.getMaxX()>highestMag) highestMag = mfd.getMaxX();
							if(mfd.getMinX()<lowestMag) lowestMag = mfd.getMinX();
							if(mfd.getDelta()<lowestDeltaM) lowestDeltaM = mfd.getDelta();
						}
						// calculate number of magnitude values
						int num = 0;
						if(lowestDeltaM!=0){
							num = (int)Math.round((highestMag-lowestMag)/lowestDeltaM) + 1;
						}
						else{
							lowestDeltaM = dm;
							num = (int)Math.round((highestMag-lowestMag)/lowestDeltaM) + 1;
						}
						SummedMagFreqDist finalMFD = new SummedMagFreqDist(lowestMag,num,lowestDeltaM);
						for(int imfd=0;imfd<mfds.size();imfd++){
							// add mfds conserving total moment rate
							finalMFD.addResampledMagFreqDist(mfds.get(imfd), false);
						}
						
						magDist[ifm] = finalMFD;

					} // end loop over focal mechanisms
					
					HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc = new HypoMagFreqDistAtLoc(magDist, psi.getHypoMagFreqDistAtLoc().getLocation(),psi.getHypoMagFreqDistAtLoc().getFocalMechanismList()); 
					
					psi = new GEMPointSourceData(psi.getID(), psi.getName(), psi.getTectReg(), 
				            hypoMagFreqDistAtLoc, psi.getAveRupTopVsMag(), psi.getAveHypoDepth());
					
					break;
					
				}
				
				

			} // end loop over remaining sources
			
			newGridList.add(psi);

			// remove from gridList all sources the that have matched the previous source
			for(int ir=0;ir<sameSource.size();ir++) gridList.remove(sameSource.get(ir).intValue());
			
		} // end loop over sources
		
		return newGridList;
	}
	
	private ArrayList<GEMSourceData> sumSrc(ArrayList<GEMSourceData> list1, ArrayList<GEMSourceData> list2){
		
		double dm = 0.1;
		
		ArrayList<GEMSourceData> newList = new ArrayList<GEMSourceData>();
		
		for(int i=0;i<list1.size();i++){
			
			System.out.println("Source: "+i+" of "+srcDataList.size());
			
			GEMPointSourceData ps1 = (GEMPointSourceData) list1.get(i);
			GEMPointSourceData ps2 = (GEMPointSourceData) list2.get(i);
			
			IncrementalMagFreqDist[] magDist = new IncrementalMagFreqDist[ps1.getHypoMagFreqDistAtLoc().getNumFocalMechs()];
			
			// loop over focal mechanisms
			for(int ifm=0;ifm<ps1.getHypoMagFreqDistAtLoc().getNumFocalMechs();ifm++){
				
				ArrayList<IncrementalMagFreqDist> mfds = new ArrayList<IncrementalMagFreqDist>();
				mfds.add(ps1.getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));
				mfds.add(ps2.getHypoMagFreqDistAtLoc().getMagFreqDist(ifm));
				
				// find lowest and highest mag from mfds
				// find also the lowest dmag
				double lowestMag=Double.MAX_VALUE;
				double highestMag=0;
				double lowestDeltaM = Double.MAX_VALUE;
				for(int imfd=0;imfd<mfds.size();imfd++){
					IncrementalMagFreqDist mfd = mfds.get(imfd);
					if(mfd.getMaxX()>highestMag) highestMag = mfd.getMaxX();
					if(mfd.getMinX()<lowestMag) lowestMag = mfd.getMinX();
					if(mfd.getDelta()<lowestDeltaM) lowestDeltaM = mfd.getDelta();
				}
				// calculate number of magnitude values
				int num = 0;
				if(lowestDeltaM!=0){
					num = (int)Math.round((highestMag-lowestMag)/lowestDeltaM) + 1;
				}
				else{
					lowestDeltaM = dm;
					num = (int)Math.round((highestMag-lowestMag)/lowestDeltaM) + 1;
				}
				SummedMagFreqDist finalMFD = new SummedMagFreqDist(lowestMag,num,lowestDeltaM);
				for(int imfd=0;imfd<mfds.size();imfd++){
					// add mfds conserving total moment rate
					finalMFD.addResampledMagFreqDist(mfds.get(imfd), false);
				}
				
				magDist[ifm] = finalMFD;

			} // end loop over focal mechanisms
			
			HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc = new HypoMagFreqDistAtLoc(magDist, ps1.getHypoMagFreqDistAtLoc().getLocation(),ps1.getHypoMagFreqDistAtLoc().getFocalMechanismList()); 
			
			GEMPointSourceData newps = new GEMPointSourceData(ps1.getID(), ps1.getName(), ps1.getTectReg(), 
		            hypoMagFreqDistAtLoc, ps1.getAveRupTopVsMag(), ps1.getAveHypoDepth());
			
			newList.add(newps);
			
		}
		
		return newList;
	}
	

}
