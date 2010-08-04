/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.calc.IM_EventSet.v03.outputImpl;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;
import java.util.logging.Level;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalc_v3_0_API;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

public class OriginalModWriter extends IM_EventSetOutputWriter {
	public static final String NAME = "OpenSHA Format Writer";
	
	File outputDir;

	public OriginalModWriter(IM_EventSetCalc_v3_0_API calc) {
		super(calc);
	}

	@Override
	public void writeFiles(ArrayList<EqkRupForecastAPI> erfs,
			ArrayList<ScalarIntensityMeasureRelationshipAPI> attenRels, ArrayList<String> imts)
			throws IOException {
		logger.log(Level.INFO, "Writing old format files files");
		outputDir = null;
		boolean multipleERFs = true;
		if (erfs.size() == 1)
			multipleERFs = false;
		for (int erfID=0; erfID<erfs.size(); erfID++) {
			EqkRupForecastAPI erf = erfs.get(erfID);
			if (multipleERFs) {
				outputDir = new File(calc.getOutputDir().getAbsolutePath() + File.separator + "erf" + erfID);
			} else {
				outputDir = calc.getOutputDir();
			}
			logger.log(Level.INFO, "Writing files to: " +  outputDir.getAbsolutePath());
			this.writeOriginalSrcRupMetaFile(erf);
			this.writeOriginalRupDistFile(erf);
			int numIMTs = imts.size();
			for (int i = 0; i < attenRels.size(); ++i) {
				ScalarIntensityMeasureRelationshipAPI attenRel = attenRels.get(i);
				for (int j = 0; j < numIMTs; ++j) {
					this.writeOriginalMeanSigmaFiles(erf, attenRel, imts.get(j));
				}
			}
		}
		logger.log(Level.INFO, "Done writing files.");
	}
	
	/**
	 * This writes the mean and lagarithmic standard deviation values to a file following the
	 * original IM Event Set calculator format, with the only change being the addition of
	 * a column for inter event std dev (at Erdem's request).
	 * 
	 * @param erf
	 * @param attenRel
	 * @throws IOException
	 */
	private void writeOriginalMeanSigmaFiles(EqkRupForecastAPI erf, ScalarIntensityMeasureRelationshipAPI attenRel, String imt) throws IOException {
		setIMTFromString(imt, attenRel);
		logger.log(Level.INFO, "Writing Mean/Sigma file for " + attenRel.getShortName() + ", " + imt);
		ArrayList<ParameterAPI> defaultSiteParams = getDefaultSiteParams(attenRel);

		ArrayList<Site> sites = getInitializedSites(attenRel);
		
		StdDevTypeParam stdDevParam = (StdDevTypeParam)attenRel.getParameter(StdDevTypeParam.NAME);
		boolean hasInterIntra = stdDevParam.isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTER) &&
									stdDevParam.isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTRA);
		
		ParameterAPI<?> im = attenRel.getIntensityMeasure();
		String fname = attenRel.getShortName();
		StringTokenizer imtTok = new StringTokenizer(imt);
		if (imtTok.countTokens() > 1) {
			while (imtTok.hasMoreTokens())
				fname += "_" + imtTok.nextToken();
			fname += ".txt";
		} else {
			fname += "_" + imt + ".txt";
		}
		
		FileWriter fw = new FileWriter(outputDir.getAbsolutePath() + File.separator + fname);

		erf.updateForecast();
		
		int numSources = erf.getNumSources();
		
		for (int sourceID=0; sourceID<numSources; sourceID++) {
			ProbEqkSource source = erf.getSource(sourceID);
			if (!shouldIncludeSource(source))
				continue;
			for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
				ProbEqkRupture rup = source.getRupture(rupID);
				attenRel.setEqkRupture(rup);
				String line = sourceID + " " + rupID;
				for (Site site : sites) {
					attenRel.setSite(site);
					double mean = attenRel.getMean();
					stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
					double total = attenRel.getStdDev();
					double inter = -1;
					if (hasInterIntra) {
						stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_INTER);
						inter = attenRel.getStdDev();
					}
					line += " " + meanSigmaFormat.format(mean) + " " + meanSigmaFormat.format(total)
									+ " " + meanSigmaFormat.format(inter);
				}
				fw.write(line + "\n");
			}
		}
		fw.close();
		logger.log(Level.INFO, "Done writing " + fname);
		// restore the default site params for the atten rel
		setSiteParams(attenRel, defaultSiteParams);
	}
	
	/**
	 * This writes the rupture distance files following the format of the original IM Event Set Calculator.
	 * The file 'rup_dist_info.txt' is equivelant to the old files, and 'rup_dist_jb_info.txt' is similar
	 * but with JB distances (at Erdem's request).
	 * 
	 * @param erf
	 * @throws IOException
	 */
	private void writeOriginalRupDistFile(EqkRupForecastAPI erf) throws IOException {
		logger.log(Level.INFO, "Writing rupture distance files");
		String fname = "rup_dist_info.txt";
		String fname_jb = "rup_dist_jb_info.txt";
		FileWriter fw = new FileWriter(outputDir.getAbsolutePath() + File.separator + fname);
		FileWriter fw_jb = new FileWriter(outputDir.getAbsolutePath() + File.separator + fname_jb);
		
		ArrayList<Site> sites = calc.getSites();
		
		erf.updateForecast();
		
		int numSources = erf.getNumSources();
		
		for (int sourceID=0; sourceID<numSources; sourceID++) {
			ProbEqkSource source = erf.getSource(sourceID);
			if (!shouldIncludeSource(source))
				continue;
			for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
				ProbEqkRupture rup = source.getRupture(rupID);
				String line = sourceID + " " + rupID;
				String lineJB = line;
				for (Site site : sites) {
					PropagationEffect propEffect = new PropagationEffect(site,rup);
					double rupDist = ((Double)propEffect.getParamValue(DistanceRupParameter.NAME)).doubleValue();
					double distJB = ((Double)propEffect.getParamValue(DistanceJBParameter.NAME)).doubleValue();
					line += " " + distFormat.format(rupDist);
					lineJB += " " + distFormat.format(distJB);
				}
				fw.write(line + "\n");
				fw_jb.write(lineJB + "\n");
			}
		}
		fw.close();
		fw_jb.close();
	}
	
	/**
	 * This writes source/rupture metadate to the file 'src_rup_metadata.txt'
	 * 
	 * @param erf
	 * @throws IOException
	 */
	private void writeOriginalSrcRupMetaFile(EqkRupForecastAPI erf) throws IOException {
		logger.log(Level.INFO, "Writing source/rupture metadata file");
		String fname = "src_rup_metadata.txt";
		FileWriter fw = new FileWriter(outputDir.getAbsolutePath() + File.separator + fname);
		
		ArrayList<Site> sites = calc.getSites();
		
		erf.updateForecast();
		
		int numSources = erf.getNumSources();
		
		double duration = ((TimeSpan)erf.getTimeSpan()).getDuration();
		
		for (int sourceID=0; sourceID<numSources; sourceID++) {
			ProbEqkSource source = erf.getSource(sourceID);
			if (!shouldIncludeSource(source))
				continue;
			for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
				ProbEqkRupture rup = source.getRupture(rupID);
				double rate = rup.getMeanAnnualRate(duration);
				fw.write(sourceID + "  " + rupID + " " + (float)rate + "  "
						+ (float)rup.getMag() + "  " + source.getName() + "\n");
			}
		}
		fw.close();
	}
	
	public String getName() {
		return NAME;
	}

}
