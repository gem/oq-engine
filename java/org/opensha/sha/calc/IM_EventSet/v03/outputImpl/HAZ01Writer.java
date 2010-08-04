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
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.logging.Level;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalc_v3_0_API;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class HAZ01Writer extends IM_EventSetOutputWriter {
	
	public static final String NAME = "HAZ01 Format Writer";
	
	public static final String HAZ01A_FILE_NAME = "haz01a.txt";
	public static final String HAZ01B_FILE_NAME = "haz01b.txt";

	public HAZ01Writer(IM_EventSetCalc_v3_0_API calc) {
		super(calc);
	}

	@Override
	public void writeFiles(ArrayList<EqkRupForecastAPI> erfs,
			ArrayList<ScalarIntensityMeasureRelationshipAPI> attenRels, ArrayList<String> imts) throws IOException {
		logger.log(Level.INFO, "Writing HAZ01 files");
		// TODO Auto-generated method stub
		String fileA = this.calc.getOutputDir().getAbsolutePath() + File.separator + HAZ01A_FILE_NAME;
		String fileB = this.calc.getOutputDir().getAbsolutePath() + File.separator + HAZ01B_FILE_NAME;
		logger.log(Level.FINE, "Opening HAZ01A file for writing: " + fileA);
		FileWriter fwA = new FileWriter(fileA);
		logger.log(Level.FINE, "Opening HAZ01B file for writing: " + fileB);
		FileWriter fwB = new FileWriter(fileB);
		
		Date now = new Date();
		SimpleDateFormat formatter = new SimpleDateFormat("EEE, dd-MMM-yyyy HH:mm:ss zzz");
		
		logger.log(Level.FINEST, "Writing headers");
		fwA.write("\"OpenSHA IM Event Set Calculator Output (HAZ01A): " + formatter.format(now) + "\"\n");
		fwB.write("\"OpenSHA IM Event Set Calculator Output (HAZ01B): " + formatter.format(now) + "\"\n");
		fwA.write("ID,ERF,Source,Rupture,GMPE,Site,VS30,Dist,IMT,Median,LSDT,LSDE\n");
		fwB.write("ID,ERF,Source,Rupture,Rate,Mag,SourceName\n");
		
		int lineIDA = 0;
		int lineIDB = 0;
		
		String imtstr = null;
		for (String imt : imts) {
			if (imtstr == null)
				imtstr = "";
			else
				imtstr += ",";
			imtstr += imt;
		}
		String erfstr = null;
		for (EqkRupForecastAPI erf : erfs) {
			if (erfstr == null)
				erfstr = "";
			else
				erfstr += ",";
			erfstr += erf.getName();
		}
		String attenrelstr = null;
		for (ScalarIntensityMeasureRelationshipAPI attenRel : attenRels) {
			if (attenrelstr == null)
				attenrelstr = "";
			else
				attenrelstr += ",";
			attenrelstr += attenRel.getShortName();
		}
		logger.log(Level.FINE, "ERF(S): " + erfstr);
		logger.log(Level.FINE, "IMR(S): " + attenrelstr);
		logger.log(Level.FINE, "IMT(S): " + imts);
		
		for (int erfID=0; erfID<erfs.size(); erfID++) {
//			logger.log(Level.FINEST, "Writing portion for ERF" + (erfID + 1));
			String erfName = "erf" + (erfID + 1);
			EqkRupForecastAPI erf = erfs.get(erfID);
			logger.log(Level.INFO, "Updating forecast for ERF: " + erf.getName());
			erf.updateForecast();
			for (ScalarIntensityMeasureRelationshipAPI attenRel : attenRels) {
//				logger.log(Level.FINEST, "Writing portion for IMR: " + attenRel.getName());
				for (String imt : imts) {
//					logger.log(Level.FINEST, "Writing portion for IMT: " + imt);
					fwA.flush();
					lineIDA = writeHAZ01A_Part(fwA, lineIDA, imt, erfName, erf, attenRel);
				}
			}
			fwB.flush();
			lineIDB = writeHAZ01B_Part(fwB, lineIDB, erfName, erfs.get(erfID));
		}
		fwA.close();
		fwB.close();
		logger.log(Level.INFO, "Done writing HAZ01 files.");
	}
	
	private int writeHAZ01A_Part(FileWriter fw, int lineID, String imt, String erfName,
				EqkRupForecastAPI erf, ScalarIntensityMeasureRelationshipAPI attenRel) throws IOException {
		logger.log(Level.INFO, "Writing HAZ01A portion for ERF: " + erf.getName() + ", IMR: " + attenRel.getShortName()
				+ ", IMT: " + imt);
//		System.out.println("Writing portion of file for erf: " +  erf.getName() +
//				", imr: " + attenRel.getShortName() + ", imt: " + imt);
		setIMTFromString(imt, attenRel);
		ArrayList<ParameterAPI> defaultSiteParams = getDefaultSiteParams(attenRel);
		
		ArrayList<Site> sites = getInitializedSites(attenRel);
		
		StdDevTypeParam stdDevParam = (StdDevTypeParam)attenRel.getParameter(StdDevTypeParam.NAME);
		boolean hasInterIntra = stdDevParam.isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTER) &&
									stdDevParam.isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTRA);
		
		if (!hasInterIntra)
			logger.log(Level.WARNING, "Selected IMR, " + attenRel.getShortName() + ", doesn't allow " +
					"inter event Std Dev...all values will be set to -1");
		
		int numSources = erf.getNumSources();
		
		String gmpe = attenRel.getShortName();
		
		for (int siteID=0; siteID<sites.size(); siteID++) {
			logger.log(Level.FINEST, "Writing portion for site: " + siteID);
			Site site = sites.get(siteID);
			
			HAZ01ASegment haz01a = new HAZ01ASegment(erfName, siteID, gmpe, getHAZ01IMTString(attenRel.getIntensityMeasure()));
			
			float vs30 = -1;
			try {
				vs30 = (float)(double)((Double)attenRel.getParameter(Vs30_Param.NAME).getValue());
			} catch (ParameterException e) {
				logger.log(Level.WARNING, "Selected IMR, " + attenRel.getShortName() + ", " +
						"doesn't have Vs30...all values will be set to -1");
			}
			for (int sourceID=0; sourceID<numSources; sourceID++) {
				logger.log(Level.FINEST, "Writing portion for Source: " + sourceID);
				ProbEqkSource source = erf.getSource(sourceID);
				if (!shouldIncludeSource(source))
					continue;
				for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
					lineID++;
					ProbEqkRupture rup = source.getRupture(rupID);
					attenRel.setEqkRupture(rup);
					
					PropagationEffect propEffect = new PropagationEffect(site,rup);
					double rupDist = ((Double)propEffect.getParamValue(DistanceRupParameter.NAME)).doubleValue();
					
					attenRel.setSite(site);
					double mean = attenRel.getMean();
					stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
					double total = attenRel.getStdDev();
					double inter = -1;
					if (hasInterIntra) {
						stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_INTER);
						inter = attenRel.getStdDev();
					}
					
					String line = haz01a.getLine(lineID, sourceID, rupID, vs30, rupDist, mean, total, inter);
					fw.write(line + "\n");
				}
			}
		}
		logger.log(Level.INFO, "Done with portion");
		// restore the default site params for the atten rel
		setSiteParams(attenRel, defaultSiteParams);
		return lineID;
	}
	
	private int writeHAZ01B_Part(FileWriter fw, int lineID, String erfName,
			EqkRupForecastAPI erf) throws IOException {
		//	System.out.println("Writing portion of file for erf: " +  erf.getName() +
		//			", imr: " + attenRel.getShortName() + ", imt: " + imt);
		
		logger.log(Level.INFO, "Writing HAZ01B for ERF: " + erf.getName());

		ArrayList<Site> sites = calc.getSites();

		erf.updateForecast();

		int numSources = erf.getNumSources();
		
		double duration = ((TimeSpan)erf.getTimeSpan()).getDuration();

		for (int sourceID=0; sourceID<numSources; sourceID++) {
			ProbEqkSource source = erf.getSource(sourceID);
			logger.log(Level.FINEST, "Writing portion for Source: " + sourceID);
			String sourceName = source.getName();
			sourceName = sourceName.replaceAll(",", "");
			if (!shouldIncludeSource(source))
				continue;
			for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
				lineID++;
				ProbEqkRupture rup = source.getRupture(rupID);
				double rate = rup.getMeanAnnualRate(duration);
				String line = lineID + "," + erfName + "," + sourceID + "," + rupID + ","
							+ rateFormat.format(rate) + ","+ (float)rup.getMag() + "," + sourceName;
				fw.write(line + "\n");
			}
		}
		return lineID;
	}
	
	public String getName() {
		return NAME;
	}

}
