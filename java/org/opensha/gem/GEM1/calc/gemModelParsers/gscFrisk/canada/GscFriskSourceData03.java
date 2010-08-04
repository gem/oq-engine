package org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.commons.geo.LocationList;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;

import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class GscFriskSourceData03 extends GemFileParser {

	private static boolean INFO = true; 
	private static double MMIN = 5.0;
	private static double MWDT = 0.1;
	private static boolean AREA = true;
	private static boolean FAULT = true;
	
	public GscFriskSourceData03 (BufferedReader file, boolean skipComm) {
		
		ArrayList<GEMSourceData> srclst = new ArrayList<GEMSourceData>();
		EvenlyDiscretizedFunc sumMfd = null;
		Region reg = null;
		FaultTrace trace = null;
		TectonicRegionType tecReg;

		// -----------------------------------------------------------------------------------------
		//                                                                            Reads the file
		GscFriskInputFile gscif = new GscFriskInputFile(file,skipComm);

		// -----------------------------------------------------------------------------------------
		//                                               Get the information contained in the header
		GscFriskInputHeader head = gscif.getHeader();
		
		// Info: number of global alternatives contained in the input file 
		System.out.printf("Number of�global alternatives: %d\n",+head.nGloAlt);
		
		// -----------------------------------------------------------------------------------------
		//                                                            Processing global alternatives
		for (int gaIdx=0; gaIdx<head.nGloAlt; gaIdx++) {
			
			System.out.printf("Global alternative %d of %d\n",gaIdx,head.nGloAlt);
			
			// Get the 'gaIdx' global alternative
			GscFriskInputAlternative ga = gscif.getGlobalAlternatives().get(gaIdx);
			int srcSetIdx = 0;
				
			// -------------------------------------------------------------------------------------
			//                                    Processing the sources into one global alternative
			for (int srcIdx=0; srcIdx<ga.getSourceSet(0).getNumberOfSources(); srcIdx++){
//			for (int srcIdx=0; srcIdx<1; srcIdx++){
				
				// This contains all the information relative to the current source
				GscFriskInputSource src = ga.getSourceSet(srcSetIdx).getSource(srcIdx);

				// Repeat for all the geometries
				for (int geomIdx=0; geomIdx < src.geomNum; geomIdx++) {
	    			System.out.println("---------"+src.name+" source type:"+src.geomTyp[geomIdx]);
					
	    			// -----------------------------------------------------------------------------
					//                                                                  Area sources 
	    			if (src.geomTyp[geomIdx].matches("area")) {
	    				
	    				// This is the source region
	    				reg = new Region(src.coords.get(geomIdx),null);
	    				
		    			// Repeat for all the depths 
						for (int depIdx=0; depIdx < src.geomDepth[geomIdx].length; depIdx++){
		
							// Find the maximum magnitude
							double mmaxlg = -1e10;
							double mminlg = MMIN;
							for (int i=0; i < src.mMax[geomIdx].length; i++) {
								if (mmaxlg < src.mMax[geomIdx][i]) mmaxlg = src.mMax[geomIdx][i];
								System.out.println("Maximum magnitude: "+src.mMax[geomIdx][i]);
							}
							double magDelta = 2.0;
							double mMaxOriginal = mmaxlg;
							mmaxlg = mmaxlg + magDelta;
							int num = (int) Math.round((mmaxlg-mminlg)/MWDT)+1;
							
							// Create the summed EvenlyDiscretizedFunction
							sumMfd = createMfd(ga, src, geomIdx, depIdx, num, magDelta, mminlg);
							
							// Depending on the model, creates the Mfd or converts it from Mlg to Mo
							IncrementalMagFreqDist mfdMo = null; 
							if (skipComm) {
								
								// New mfd for moment magnitude
								num = (int) Math.round((mMaxOriginal-MMIN)/MWDT);
								mfdMo = new IncrementalMagFreqDist(MMIN+MWDT/2,num,MWDT);
								
								// Populating the mfd for moment magnitude
								for (int i=0; i < mfdMo.getNum(); i++){
									double rate = 
										sumMfd.getInterpolatedY(mfdMo.getX(i)-MWDT/2) - 
										sumMfd.getInterpolatedY(mfdMo.getX(i)+MWDT/2);
									mfdMo.set(i,rate);
									if (INFO) {
//										System.out.printf("mlow %6.2f mupp %6.2f rate %6.2e \n",
//												mfdMo.getX(i)-MWDT/2,
//												mfdMo.getX(i)+MWDT/2,
//												rate
//											);
									}
								}
								
							} else {
								
								// Convert from Mlg to Mo
								mfdMo = mfdMlgTomfdMo(sumMfd,mmaxlg, magDelta);
								
							}

							if (mfdMo != null){
							
			    				// Creates the hash map with depths
								ArbitrarilyDiscretizedFunc depTopRup = new ArbitrarilyDiscretizedFunc();
//								if (src.geomDepth[geomIdx][depIdx] < 20.0){
									depTopRup.set(6.0,src.geomDepth[geomIdx][depIdx]);
//								} else {
//									System.out.println("SOURCE: "+String.format("%d",srcIdx)+" "+ 
//											src.geomName[geomIdx]);
//									System.out.println("WARNING: dep to top of rup = "+
//											src.geomDepth[geomIdx][depIdx]);
//									depTopRup.set(6.0,19.99);
//								}
								
								// Creates the final arrays requested to create the MagFreqDistsForFocalMechs
								FocalMechanism[] fmArr = new FocalMechanism[1];
								IncrementalMagFreqDist[] mfArr = new IncrementalMagFreqDist[1];
								mfArr[0] = mfdMo;
								
								fmArr[0] = new FocalMechanism();
								MagFreqDistsForFocalMechs mfdffm = new MagFreqDistsForFocalMechs(mfArr,fmArr);
								
								// ---------------------------------------------------------------------
								//                                 Creating the GEMAreaSourceData object
								tecReg = TectonicRegionType.STABLE_SHALLOW;
								if (skipComm) tecReg = TectonicRegionType.ACTIVE_SHALLOW;
								GEMAreaSourceData srcGem = new GEMAreaSourceData(
										String.format("%d",srcIdx), 
										src.geomName[geomIdx], 
										tecReg, 
										reg, 
										mfdffm, 
										depTopRup,
										src.geomDepth[geomIdx][depIdx]);
								
								if (AREA) srclst.add(srcGem);
								System.out.printf("  Adding source %3d - Tot. rate: %7.4e avg depth: %6.2f \n",
										srclst.size(),mfdffm.getMagFreqDist(0).getTotalIncrRate(),
										srcGem.getAveHypoDepth());
							}
							
						}
		    		// -----------------------------------------------------------------------------
					//                                                                 Fault sources 
	    			} else if (src.geomTyp[geomIdx].matches("fault")){
	    				
	    				trace = new FaultTrace("trace");
	    				trace.addAll(src.coords.get(geomIdx));
	    				trace.reverse();
	    				
		    			// Repeat for all the fault dip values  
						for (int depIdx=0; depIdx < src.geomDip1[geomIdx].length; depIdx++){
		
							// Find the maximum magnitude
							double mmaxlg = -1e10;
							double mminlg = MMIN;
							for (int i=0; i < src.mMax[geomIdx].length; i++){ 
								if (mmaxlg < src.mMax[geomIdx][i]) mmaxlg = src.mMax[geomIdx][i];
								System.out.println("Maximum magnitude: "+src.mMax[geomIdx][i]);
							}
							double mMaxOriginal = mmaxlg;
							double magDelta = 2.0;
							mmaxlg = mmaxlg + magDelta;
							mminlg = mminlg - magDelta;
							int num = (int) Math.round((mmaxlg-mminlg)/MWDT);
							
							// Create the summed Mfd
							sumMfd = createMfd(ga, src, geomIdx, depIdx, num, magDelta, mminlg);
							if (INFO) {
								System.out.println("Created EvenlyDiscretized Function mmin"+
										sumMfd.getMinX()+" mmax"+sumMfd.getMaxX()+" num intervals"+
										sumMfd.getNum());
							}
							
							// Depending on the model, creates the Mfd or converts it from Mlg to Mo
							IncrementalMagFreqDist mfdMo = null; 
							if (skipComm) {
								
								// New mfd for moment magnitude
								num = (int) Math.round((mMaxOriginal-MMIN)/MWDT);
								mfdMo = new IncrementalMagFreqDist(MMIN+MWDT/2,num,MWDT);
								
								// Populating the mfd for moment magnitude
								for (int i=0; i < mfdMo.getNum(); i++){
									double rate = 
										sumMfd.getInterpolatedY(mfdMo.getX(i)-MWDT/2) - 
										sumMfd.getInterpolatedY(mfdMo.getX(i)+MWDT/2);
									mfdMo.set(i,rate);
									if (INFO) {
//										System.out.printf("mlow %6.2f mupp %6.2f rate %6.2e \n",
//												mfdMo.getX(i)-MWDT/2,
//												mfdMo.getX(i)+MWDT/2,
//												rate
//											);
									}
								} 
							} else {
								// Convert from Mlg to Mo
								mfdMo = mfdMlgTomfdMo(sumMfd,mmaxlg, magDelta);
							}
							
//							double topDep = Math.min(19.99,src.geomZ1[geomIdx][depIdx]);
							double topDep = src.geomZ1[geomIdx][depIdx];
							GEMFaultSourceData srcGem = new GEMFaultSourceData(
									String.format("%d",srcIdx), 
									src.geomName[geomIdx], 
									TectonicRegionType.SUBDUCTION_INTERFACE,
									mfdMo, 
									trace, 
									(src.geomDip1[geomIdx][depIdx]+src.geomDip2[geomIdx][depIdx])/2.0, // average dip 
									90.0,// rake
									src.geomZ3[geomIdx][depIdx], // Depth low
									topDep, // Depth upp
									true);
							
							
							if (FAULT) srclst.add(srcGem);
							System.out.println(src.geomZ1[geomIdx][depIdx]+" "+src.geomZ3[geomIdx][depIdx]);
							System.out.println("!!!!!!!!!! Adding source"+src.geomName[geomIdx]);
						}

	    				
	    			} else {
	    			    System.err.println("Source model: unsupported option");
	    			    throw new RuntimeException("");	
	    			}
					
	
				}
			}
			
		}
		
		// Setting tectonic regions
		System.out.println("Setting tectonic region");
		HashMap<String,TectonicRegionType> tecRegMap = new HashMap<String,TectonicRegionType>();
		tecRegMap.put("GEO",  TectonicRegionType.SUBDUCTION_INTERFACE);
		tecRegMap.put("PUG", TectonicRegionType.SUBDUCTION_INTERFACE);
		tecRegMap.put("GSP", TectonicRegionType.SUBDUCTION_INTERFACE);
		tecRegMap.put("QCFH", TectonicRegionType.SUBDUCTION_INTERFACE);
		tecRegMap.put("QCFR", TectonicRegionType.SUBDUCTION_INTERFACE);
		
		int counter = 0;
		int idx = 0;
		for (GEMSourceData srcDat: srclst){
			String[] tmp = srcDat.getName().split("\\s+");
			
			System.out.println(tmp[0].trim());
			if (tecRegMap.containsKey(tmp[0].trim())){
				System.out.printf("Interface....[%d]:%s\n",idx,srcDat.getName());
				srclst.get(idx).setTectReg(TectonicRegionType.SUBDUCTION_INTERFACE);
			} else if (skipComm) {
				System.out.printf("Active sh....[%d]:%s\n",idx,srcDat.getName());
				srclst.get(idx).setTectReg(TectonicRegionType.ACTIVE_SHALLOW);
			}
			
			// Verifying the number of sources contained in the model VS the one wih an assigned 
			// tectonic region 
			if (srcDat instanceof GEMAreaSourceData){
				counter += 1;
			} else if (srcDat instanceof GEMFaultSourceData){
				counter += 1;
			} else if (srcDat instanceof GEMSubductionFaultSourceData){
				counter += 1;
			}
			idx++;
		}
		this.setList(srclst);
		System.out.println("Parsing done");
	}
	
	// Thic converts mlgtomo using the relationship of 
	// 
	private double mlg2mo(double mlg) {
		double mo;
		mo = 2.689 - 0.252*mlg + 0.127*mlg*mlg;
//		mo = 1.12*mlg - 1.00;
		return mo;
	}
	
	/**
	 * 
	 * @param ga
	 * @param src
	 * @param geomIdx
	 * @param depIdx
	 * @param magDelta
	 * @param mminlg
	 */
	private EvenlyDiscretizedFunc createMfd(GscFriskInputAlternative ga, GscFriskInputSource src, int geomIdx, int
			depIdx, int numMfd, double magDelta, double mminlg){
		
		double sumWei = 0.0;
		EvenlyDiscretizedFunc sumMfd = new EvenlyDiscretizedFunc(mminlg,numMfd,MWDT);
		
		// Repeat for all the mmx values 
		for (int mmaxIdx=0; mmaxIdx<src.mMax[geomIdx].length; mmaxIdx++){	
			double tmpMMax = src.mMax[geomIdx][mmaxIdx]+magDelta;
		
			// Repeat for nu-beta couples 
			for (int nubIdx=0; nubIdx<src.beta[geomIdx].length; nubIdx++){
				
				// Compute the weight 
				double weight = 
					ga.getNuBetaWeights()[nubIdx] *
					ga.getMaxMagWeights()[mmaxIdx] *
					ga.getDepthsWeights()[depIdx];
				
				if (tmpMMax > MMIN+MWDT) {
				
					// Parameters of the Gutenberg-Richter distribution
					double betaGR = src.beta[geomIdx][nubIdx];	
					double alphaGR = Math.log(src.nu[geomIdx][nubIdx]);
					
					// Updating the cumulative MFD
					double tmag = mminlg; 
					int idx = 0;
					while (tmag <= tmpMMax && idx < numMfd){
						double tmp = sumMfd.getY(idx)+ Math.exp(alphaGR-betaGR*(tmag))*weight;
						sumMfd.set(idx,tmp);
//						System.out.printf("%5.2f< %5.2f %d %6.2e\n",tmag,tmpMMax,idx,tmp);
						tmag += MWDT;
						idx++;
					}
				
				}
		
				// Taking track of weights
				sumWei += weight;
	
			} 		
		}
		
//		for (int i =0; i < sumMfd.getNum(); i++){
//			System.out.printf("%5.2f %6.2e\n",sumMfd.getX(i),sumMfd.getY(i));
//		}
		
		// 
		return sumMfd;
	}
		
	/**
	 * This method converts an input mfd in terms of Mlg into a mfd in terms of Mo.  
	 * 
	 * @param sumMfd
	 * @param mmaxlg
	 * @param magDelta
	 */
	private IncrementalMagFreqDist mfdMlgTomfdMo(EvenlyDiscretizedFunc sumMfd, 
			double mmaxlg, double magDelta) {
		
		// Fixing minimum an 
		double mminMo = MMIN;
		double mmaxMo = Math.ceil(mlg2mo(mmaxlg-magDelta)/MWDT)*MWDT;
		int numMo = (int) Math.round((mmaxMo-mminMo)/MWDT);
		
		if (INFO) {
			System.out.println("Creating summed Cumulative MFD ==================================");
			System.out.printf( "  Maximum magnitude (orig: %5.2f) %5.2f\n",
				mmaxlg-magDelta,mmaxMo);
		}
		
		if (mmaxMo > MMIN+MWDT){
				
			// New mfd for moment magnitude
			IncrementalMagFreqDist mfdMo = new IncrementalMagFreqDist(mminMo+MWDT/2,
					numMo,MWDT);
			
			// Mfd used for the conversion
			ArbitrarilyDiscretizedFunc mfdMoOriginal = new ArbitrarilyDiscretizedFunc();
			
			// Populating the mfd used for conversion
			for (int i=0; i < sumMfd.getNum(); i++){
				mfdMoOriginal.set(mlg2mo(sumMfd.getX(i)),sumMfd.getY(i));
			}
			
			// Populating the mfd for moment magnitude
			for (int i=0; i < mfdMo.getNum(); i++){
				double rate = mfdMoOriginal.getInterpolatedY(mfdMo.getX(i)-MWDT/2) - 
					mfdMoOriginal.getInterpolatedY(mfdMo.getX(i)+MWDT/2);
				mfdMo.set(i,rate);
				if (INFO) {
//					System.out.printf("mlow %6.2f mupp %6.2f rate %6.2e \n",
//							mfdMo.getX(i)-MWDT/2,
//							mfdMo.getX(i)+MWDT/2,
//							rate
//						);
				}
			}
			
			return mfdMo;
		} else {
			return null;
			
		}

	}
	

}
