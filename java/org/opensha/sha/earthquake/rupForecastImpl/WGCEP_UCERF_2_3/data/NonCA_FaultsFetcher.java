/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_TypeB_EqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.EmpiricalModel;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;

/**
 * It reads the Non-CA faults file to generate a list of non-CA faults.
 *
 * 
 * 
 * @author vipingupta
 *
 */
public class NonCA_FaultsFetcher  implements java.io.Serializable {
	
	
	private ArrayList<FaultRuptureSource> charSources = new ArrayList<FaultRuptureSource>();
	private ArrayList<Frankel02_TypeB_EqkSource> grSources = new ArrayList<Frankel02_TypeB_EqkSource>();
	private ArrayList<FaultRuptureSource> lessThan6_5_Sources = new ArrayList<FaultRuptureSource>();
	private SummedMagFreqDist summedMFD;
	
	

	
	/**
	 * Read files created after reading non-CA faults from NSHMP files
	 * 
	 * @return
	 */
	public ArrayList<ProbEqkSource> getSources(String fileName, double duration, double charMagSigma, 
			double charMagTruncLevel, double rupOffset, EmpiricalModel empiricalModel) {
		
		GaussianMagFreqDist charMFD = null;
		GutenbergRichterMagFreqDist grMFD = null;
		summedMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG);
		charSources = new ArrayList<FaultRuptureSource>();
		grSources = new ArrayList<Frankel02_TypeB_EqkSource>();
		lessThan6_5_Sources = new ArrayList<FaultRuptureSource>();
		
		
		try {
			//FileWriter fw = new FileWriter("NonCA_Sources.txt");
			//fw.write("Total Yearly Rate\tTotal Moment Rate\tSource Name\n");
			ArrayList<String> fileLines = FileUtils.loadJarFile(fileName);
			int numLines = fileLines.size();
			int rakeId, srcTypeId;
			double mag=0, dip, downDipWidth, upperSeisDepth, lowerSeisDepth, latitude, longitude, rake;
			FaultTrace faultTrace;
			String faultName;
			for(int i=0; i<numLines; ) {
				String line = fileLines.get(i++);
				StringTokenizer tokenizer = new StringTokenizer(line);
				srcTypeId = Integer.parseInt(tokenizer.nextToken().trim());
				rakeId = Integer.parseInt(tokenizer.nextToken().trim());
				if(rakeId==1) rake = 0;
				else if(rakeId==2) rake =90;
				else rake = -90;
				int numMags = Integer.parseInt(tokenizer.nextToken().trim());
				if(numMags != 1) throw new RuntimeException("Only one mag supported");
				tokenizer.nextToken();  // we were told this element is useless
				faultName = "";
				while(tokenizer.hasMoreTokens()) faultName+=tokenizer.nextToken()+" ";
				// mag, rate & wt
				line = fileLines.get(i++);
				tokenizer = new StringTokenizer(line);
				if(srcTypeId==1) { // Char case
					mag = Double.parseDouble(tokenizer.nextToken().trim());
					double rate = Double.parseDouble(tokenizer.nextToken().trim());
					double moRate = rate*MomentMagCalc.getMoment(mag);
					double wt = Double.parseDouble(tokenizer.nextToken().trim());
					double wt2 = 1;
					if(mag > 6.5) wt2 = 0.666;
					moRate *= wt*wt2;
					charMFD = new GaussianMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG, 
							mag, charMagSigma, moRate, charMagTruncLevel, 2);
					summedMFD.addIncrementalMagFreqDist(charMFD);
				}
				else if (srcTypeId==2) {
					double aVal=Double.parseDouble(tokenizer.nextToken().trim());
					double bVal=Double.parseDouble(tokenizer.nextToken().trim());
					double magLower=Double.parseDouble(tokenizer.nextToken().trim());
					double magUpper=Double.parseDouble(tokenizer.nextToken().trim());
					double deltaMag=Double.parseDouble(tokenizer.nextToken());
					//System.out.println(faultName+","+magLower+","+magUpper);
					if(magUpper!=magLower) {
						magLower += deltaMag/2.0;
						magUpper -= deltaMag/2.0;
					}
					else {
						magLower=Math.round( (float)((magUpper-UCERF2.MIN_MAG)/deltaMag)) * deltaMag + UCERF2.MIN_MAG;
						magUpper= magLower;
					}
					numMags = Math.round( (float)((magUpper-magLower)/deltaMag + 1.0) );
		            //if(numMags==0) System.out.println(faultName+","+magLower+","+magUpper);
					double moRate = Frankel02_AdjustableEqkRupForecast.getMomentRate(magLower, numMags, deltaMag, aVal, bVal);
					double wt = Double.parseDouble(tokenizer.nextToken().trim());
					double wt2 = 0.334;
					moRate *= wt*wt2;
					grMFD = new GutenbergRichterMagFreqDist(magLower,numMags,deltaMag,moRate,bVal);
					summedMFD.addResampledMagFreqDist(grMFD, true);
				}
				else throw new RuntimeException("Src type not supported");

				// dip, surface width, upper seis depth, surface length
				line = fileLines.get(i++);
				tokenizer = new StringTokenizer(line);
				dip = Double.parseDouble(tokenizer.nextToken().trim());
				downDipWidth = Double.parseDouble(tokenizer.nextToken().trim());
				upperSeisDepth = Double.parseDouble(tokenizer.nextToken().trim());
				lowerSeisDepth = upperSeisDepth + downDipWidth*Math.sin((Math.toRadians(Math.abs(dip))));
				
				//fault trace
				line = fileLines.get(i++);
				int numLocations = Integer.parseInt(line.trim());
				faultTrace = new FaultTrace(faultName);
				for(int locIndex=0; locIndex<numLocations; ++locIndex) {
					line = fileLines.get(i++);
					tokenizer = new StringTokenizer(line);
					latitude = Double.parseDouble(tokenizer.nextToken());
					longitude =Double.parseDouble(tokenizer.nextToken());
					faultTrace.add(new Location(latitude, longitude));
				}
				// surface
				StirlingGriddedSurface surface = new StirlingGriddedSurface(faultTrace, dip, upperSeisDepth,
						lowerSeisDepth, UCERF2.GRID_SPACING);   
				
				// find empirical correction
				double empiricalCorr=1;
				if(empiricalModel!=null) {
					empiricalCorr = empiricalModel.getCorrection(surface);
				}
				
				if(srcTypeId == 1) {
					// reduce rates in MFD
					IncrementalMagFreqDist modMagFreqDist = charMFD.deepClone();
					for(int magIndex=0; magIndex<modMagFreqDist.getNum() && empiricalModel!=null; ++magIndex) {
						modMagFreqDist.set(magIndex, empiricalCorr*modMagFreqDist.getY(magIndex));
					}
					FaultRuptureSource frs = new FaultRuptureSource(modMagFreqDist,surface, rake,duration);
					frs.setName(faultName+" Char");
					if(mag > 6.5) charSources.add(frs);
					else lessThan6_5_Sources.add(frs);
					//fw.write((float)charMFD.getTotalIncrRate()+"\t"+(float)charMFD.getTotalMomentRate()+"\t"+frs.getName()+"\n");
				}
				else {// reduce rates in MFD
					IncrementalMagFreqDist modMagFreqDist = grMFD.deepClone();
					for(int magIndex=0; magIndex<modMagFreqDist.getNum() && empiricalModel!=null; ++magIndex) {
						modMagFreqDist.set(magIndex, empiricalCorr*modMagFreqDist.getY(magIndex));
					}
					Frankel02_TypeB_EqkSource fgrs = new Frankel02_TypeB_EqkSource(modMagFreqDist,surface,
                            rupOffset, rake, duration, faultName+" GR");
					//fw.write((float)grMFD.getTotalIncrRate()+"\t"+(float)grMFD.getTotalMomentRate()+"\t"+fgrs.getName()+"\n");
					grSources.add(fgrs);
				}
			}
			//fw.write("\n\n"+summedMFD.toString());
			//fw.write("\n\n"+summedMFD.getCumRateDist().toString());
			//fw.close();
		}catch (Exception e) {
			e.printStackTrace();
		}
		// combine the sources
		ArrayList<ProbEqkSource> allSources = new ArrayList<ProbEqkSource>();
		allSources.addAll(charSources);
		allSources.addAll(lessThan6_5_Sources);
		allSources.addAll(grSources);
		return allSources;
	}
	
	
	/**
	 * Get Summed MFD for all sources
	 * 
	 * @return
	 */
	public SummedMagFreqDist getSummedMFD()  {
		return this.summedMFD;
	}
	

	
	public static void main(String args[]) {
		NonCA_FaultsFetcher nonCA_FaultsFetcher = new NonCA_FaultsFetcher();
		String fileName = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/NearCA_NSHMP/NonCA_Faults.txt";
		nonCA_FaultsFetcher.getSources(fileName, 1.0, 0.12, 2, 1, null);
	}
}
