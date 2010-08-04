package org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;


import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.gem.GEM1.calc.gemModelParsers.GemFileParser;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class GscFriskSourceData extends GemFileParser {

	private static boolean INFO = false; 
	private static double MMIN = 5.0;
	private static double MWDT = 0.1;
	
	public GscFriskSourceData (BufferedReader file, boolean skipComm) {
		ArrayList<GEMSourceData> srclst = new ArrayList<GEMSourceData>();
		SummedMagFreqDist sumMfd = null;
		Region reg = null;

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
			for (int srcIdx=0; srcIdx<ga.getSourceSet(0).getNumberOfSources(); 
				srcIdx++){
				
				// This contains all the information relative to the current source
				GscFriskInputSource src = ga.getSourceSet(srcSetIdx).getSource(srcIdx);
				
				double sum = 0.0;
//				IncrementalMagFreqDist mfdMean;
				
				for (int geomIdx=0; geomIdx < src.geomNum; geomIdx++){

					// Create the region bordering the source area
					reg = new Region(src.coords.get(geomIdx),null);
					
					for (int depIdx=0; depIdx < src.geomDepth[geomIdx].length; depIdx++){
	
						// Find the maximum magnitude
						double mmax = -1e10;
						for (int i=0; i < src.mMax[geomIdx].length; i++) 
							if (mmax < src.mMax[geomIdx][i]) mmax = src.mMax[geomIdx][i];
						
						int num = (int) Math.round((mmax-MMIN)/MWDT);
						
						// Define the summed mfd
						sumMfd = new SummedMagFreqDist(MMIN+MWDT/2,num,MWDT);
						
						for (int mmaxIdx=0; mmaxIdx<src.mMax[geomIdx].length; mmaxIdx++){
							for (int nubIdx=0; nubIdx<src.beta[geomIdx].length; nubIdx++){
								
				    			System.out.println("---------"+src.name);
								
			    				num = (int) Math.round((src.mMax[geomIdx][mmaxIdx]-MMIN)/MWDT);
								IncrementalMagFreqDist mfd = new IncrementalMagFreqDist(
										MMIN+MWDT/2,src.mMax[geomIdx][mmaxIdx]-MWDT/2, num);
								
								double tmp= src.mMax[geomIdx][mmaxIdx]-MWDT/2;
								
								// Parameters of the Gutenberg-Richter distribution
			    				double betaGR = src.beta[geomIdx][nubIdx];
			    				double alphaGR = Math.log(src.nu[geomIdx][nubIdx] / 
			    					(Math.exp(-betaGR*src.mMin[geomIdx]) - 
			    					 Math.exp(-betaGR*src.mMax[geomIdx][mmaxIdx])) );
			    				
			    				// Filling the mfd distribution - This is the Mlg mfd
			    				double mup = MMIN+ MWDT;
			    				int idx = 0;
				    			while (mup <= src.mMax[geomIdx][mmaxIdx]-MWDT/2) {
			    					double occ = Math.exp(alphaGR-betaGR*(mup-MWDT))-
			    						Math.exp(alphaGR-betaGR*mup);
			    					double lowExt = mup-MWDT/2;
			    					System.out.printf("%7.4e %5.2f:  %5.2f-%5.2f: %7.3f %8.4f\n",
			    							alphaGR,betaGR,mup-MWDT,mup,lowExt,occ);
			    					mup += MWDT;
			    					mfd.add(idx,occ);
			    					idx++;
			    					if (occ < 1e-4) System.exit(0);
			    				}
				    			
				    			// Compute the scaled value of the total moment rate
				    			double moRate = mfd.getTotalMomentRate() *
				    				ga.getNuBetaWeights()[nubIdx] *
				    				ga.getMaxMagWeights()[mmaxIdx] *
				    				ga.getDepthsWeights()[depIdx];
				    			mfd.scaleToTotalMomentRate(moRate);
				    			
				    			sumMfd.addResampledMagFreqDist(mfd,true);

				    			System.out.println("Total Moment Rate: "+sumMfd.getTotalMomentRate());
							}
						} 
						
	    				// Hash map with depths
						ArbitrarilyDiscretizedFunc depTopRup = new ArbitrarilyDiscretizedFunc();
						depTopRup.set(6.0, src.geomDepth[geomIdx][depIdx]);
						
						FocalMechanism[] fmArr = new FocalMechanism[1];
						IncrementalMagFreqDist[] mfArr = new IncrementalMagFreqDist[1];
						mfArr[0] = sumMfd;
						System.out.println("-->"+srcIdx+" "+sumMfd.getTotalIncrRate());
						
						fmArr[0] = new FocalMechanism();
						MagFreqDistsForFocalMechs mfdffm = new MagFreqDistsForFocalMechs(mfArr,fmArr);
						
						GEMAreaSourceData srcGem = new GEMAreaSourceData(
								String.format("%d",srcIdx), 
								src.geomName[geomIdx], 
								TectonicRegionType.STABLE_SHALLOW, 
								reg, 
								mfdffm, 
								depTopRup,src.geomDepth[geomIdx][depIdx]);

						System.out.println("-->"+srcGem.getMagfreqDistFocMech().getMagFreqDist(0).getTotalMomentRate());
						System.out.println("--> Mom rate:"+srcGem.getMagfreqDistFocMech().getMagFreqDist(0).getMomentRate(5));
						srclst.add(srcGem);
					}	
				}
//				System.out.println(" "+sum); // Verifying weights
			}
			
		}
		this.setList(srclst);
	}
	
	private double mlg2mo(double mlg) {
		double mo;
		mo = 2.689 - 0.252*mlg + 0.127*mlg*mlg;
//		mo = 1.12*mlg - 1.00;
		return mo;
	}

}
