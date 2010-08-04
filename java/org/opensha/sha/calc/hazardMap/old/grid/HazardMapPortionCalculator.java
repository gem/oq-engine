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

package org.opensha.sha.calc.hazardMap.old.grid;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.rmi.RemoteException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.data.siteData.SiteDataValueListList;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.SiteTranslator;


/**
 * GridHardcodedHazardMapCalculator
 * 
 * Class to calculate a set of hazard curves from a region as part of a grid hazard map
 * computation. All values except for the start and end indices should be hard coded into
 * this class before distributing to compute nodes.
 * @author kevin
 *
 */
public class HazardMapPortionCalculator {

	private boolean xLogFlag = true;
	private DecimalFormat decimalFormat=new DecimalFormat("0.00##");
	private boolean timer = true;
	private boolean lessPrints = false;
	private ArrayList<Long> curveTimes = new ArrayList<Long>();
	private boolean skipPoints = false;
	private int skipFactor = 10;
	
	private SitesInGriddedRegion sites;
	
	private EqkRupForecastAPI erf;
	private ScalarIntensityMeasureRelationshipAPI imr;
	private double maxDistance;
	private String outputDir;
	private ArbitrarilyDiscretizedFunc hazFunction;
	
	private SiteDataValueListList siteDataValues;

	/**
	 * Sets variables for calculation of hazard curves in hazard map
	 * @param sites - sites in gridded region for calculation
	 * @param erf - Earthquake Rupture Forecast (should already be updated) for calculation
	 * @param imr - Attenuation Relationship for calculation
	 * @param imt - Intensity Measure Type
	 * @param maxDistance - maximum source distance for calculation
	 * @param outputDir - directory to store results (or empty string for current working directory)
	 */
	public HazardMapPortionCalculator(SitesInGriddedRegion sites, EqkRupForecastAPI erf,
			ScalarIntensityMeasureRelationshipAPI imr, ArbitrarilyDiscretizedFunc hazFunction,
			SiteDataValueListList siteDataValues, double maxDistance, String outputDir) {
		this.sites = sites;
		
		this.erf = erf;
		this.imr = imr;
		this.maxDistance = maxDistance;
		this.outputDir = outputDir;
		this.hazFunction = hazFunction;
		this.siteDataValues = siteDataValues;
		
		// show timing results if debug mode and timer is selected
		timer = true;
	}
	
	/**
	 * Calculate the curves from the given start index to end index - 1.
	 * 
	 * @param startIndex - index  to start at within sites
	 * @param endIndex - index to end at (the very last one is NOT computed)
	 */
	public void calculateCurves(int startIndex, int endIndex) {
		String overheadStr = "";
		long overhead = 0;
		long start = 0;
		if (timer) {
			start = System.currentTimeMillis();
			System.out.println("Start Time Stamp: " + start);
		}
		int numSites = 0;
		try {
			// add parameters to sites from IMR
			sites.addSiteParams(imr.getSiteParamsIterator());
			//sites.setSiteParamsForRegionFromServlet(true);
			
			System.out.println("Selected ERF: " + erf.getName());
			System.out.println("ERF Params:");
			Iterator erfIt = erf.getAdjustableParamsIterator();
			while (erfIt.hasNext()) {
				ParameterAPI param = (ParameterAPI)erfIt.next();
				System.out.println(param.getName() + ": " + param.getValue());
			}
			try {
				System.out.println("Time Span: " + erf.getTimeSpan().getDuration() + " " + erf.getTimeSpan().getDurationUnits() + " from " + erf.getTimeSpan().getStartTimeYear());
			} catch (RuntimeException e1) {
			}
			System.out.println("Selected IMR: " + imr.getName());
			System.out.println("IMT: " + imr.getIntensityMeasure().getName());

			// create the calculator object used for every curve
			HazardCurveCalculator calc = new HazardCurveCalculator();
			// set maximum source distance
			calc.setMaxSourceDistance(maxDistance);
			
			// total number of sites for the entire map
		    numSites = sites.getRegion().getNodeCount();
		    // number of points on the hazard curve
			int numPoints = hazFunction.getNum();
			
			Site site;
			
			long start_curve = 0;
			if (timer) {
				overhead = System.currentTimeMillis() - start;
				overheadStr = getTime(start);
				System.out.println(overheadStr + " seconds total calculator overhead");
				start_curve = System.currentTimeMillis();
			}
			
			// use the CVM
			SiteTranslator siteTranslator = new SiteTranslator();
			ArrayList<ParameterAPI> defaultSiteParams = null;
			boolean hasSiteData = siteDataValues != null;
			if (hasSiteData) {
				Iterator<ParameterAPI<?>> it = imr.getSiteParamsIterator();
				
				defaultSiteParams = new ArrayList<ParameterAPI>();
				while (it.hasNext()) {
					ParameterAPI param = it.next();
					System.out.println("Loaded default param: " + param.getName() + ", Value: " + param.getValue());
					defaultSiteParams.add((ParameterAPI)param.clone());
				}
			}
			
			System.out.println("Starting Curve Calculations");
			
			// loop through each site in this job's portion of the map
			int j = 0;
			
			for(j = startIndex; j < numSites && j < endIndex; ++j){
				// if we're skipping some of them, then check if this should be skipped
				if (skipPoints && j % skipFactor != 0)
					continue;
				boolean print = true;
				if (lessPrints && j % 100 != 0)
					print = false;
				if (print && timer && j != startIndex) {
					curveTimes.add(System.currentTimeMillis() - start_curve);
					System.out.println("Took " + getTime(start_curve) + " seconds to calculate curve.");
					start_curve = System.currentTimeMillis();
				}
				
				if (print)
					System.out.println("Doing site " + (j - startIndex + 1) + " of " + (endIndex - startIndex) + " (index: " + j + " of " + numSites + " total) ");
				try {
					// get the site at the given index. it should already have all parameters set.
					// it will read the sites along latitude lines, starting with the southernmost
					// latitude in the region, and going west to east along that latitude line.
					site = sites.getSite(j);
					if (hasSiteData) {
						// the index in the cvm files for this site's data
						int cvmIndex = j - startIndex;
						Location loc = site.getLocation();
						if ((cvmIndex) >= siteDataValues.size()) {
							System.err.println("WARNING: CVM index out of bounds! (index: " + j + ")");
							System.err.println("Location: " + loc.getLatitude() + ", " + loc.getLongitude());
						} else {
							ArrayList<SiteDataValue<?>> datas = siteDataValues.getDataList(cvmIndex);
							if (siteDataValues.hasLocations()) {
								Location newLoc = siteDataValues.getDataLocation(cvmIndex);
								if (Math.abs(loc.getLatitude() - newLoc.getLatitude()) >= sites.getRegion().getSpacing()) {
									if (Math.abs(loc.getLongitude() - newLoc.getLongitude()) >= sites.getRegion().getSpacing()) {
										System.err.println("WARNING: CVM data is for the WRONG LOCATION! (index: " + j + ")");
										System.err.println("CVM Location: " + newLoc + " REAL Location: " + loc);
									}
								}
							}
							System.out.println("Site Data Values:");
							for (SiteDataValue<?> val : datas) {
								System.out.println("\t" + val.getDataType() + ": " + val.getValue());
							}
							Iterator<ParameterAPI<?>> it = site.getParametersIterator();
							while (it.hasNext()) {
								ParameterAPI param = it.next();
								
								boolean flag = siteTranslator.setParameterValue(param, datas);
								System.out.println("Setting " + param.getName() + " from site data: " + flag);
								if (!flag) {
									// if we couldn't set the parameter from this set of data, then we need
									// to use the default value
									boolean success = false;
									for (ParameterAPI defaultParam : defaultSiteParams) {
										if (defaultParam.getName().equals(param.getName())) {
											System.out.println("Setting " + param.getName() + " to default: " + defaultParam.getValue());
											param.setValue(defaultParam.getValue());
											success = true;
											break;
										}
									}
									if (!success)
										throw new RuntimeException("Couldn't set param from default vals!");
								}
							}
//							siteTranslator.setAllSiteParams(imr, datas);
						}
					}
//					if (useCVM) {
//						if ((j - startIndex) >= cvmStr.size()) {
//							System.err.println("WARNING: CVM index out of bounds! (index: " + j + ")");
//							System.err.println("Location: " + site.getLocation().getLatitude() + ", " + site.getLocation().getLongitude());
//						} else {
//							String cvm = cvmStr.get(j - startIndex);
//							StringTokenizer tok = new StringTokenizer(cvm);
//							double lat = Double.parseDouble(tok.nextToken());
//							double lon = Double.parseDouble(tok.nextToken());
//							String type = tok.nextToken();
//							double depth;
////							if (basinFromCVM) {
////								String depthStr = tok.nextToken();
////								if (depthStr.contains("NaN")) {
////									depth = Double.NaN;
////								} else
////									depth = Double.parseDouble(depthStr);
////							} else
//								depth = Double.NaN;
//
//							if (Math.abs(lat - site.getLocation().getLatitude()) >= sites.getGridSpacing()) {
//								if (Math.abs(lon - site.getLocation().getLongitude()) >= sites.getGridSpacing()) {
//									System.err.println("WARNING: CVM data is for the WRONG LOCATION! (index: " + j + ")");
//									System.err.println("CVM Location: " + lat + ", " + lon + " REAL Location: " + site.getLocation().getLatitude() + ", " + site.getLocation().getLongitude());
//								}
//							}
//							
//							boolean skipBasin = false;
//							if ((depth + "").contains("NaN"))
//								skipBasin = true;
//							
//							boolean skipType = false;
//							if (type.contains("NA") || type.contains("NaN"))
//								skipType = true;
//
//							Iterator it = site.getParametersIterator();
//							while(it.hasNext()){
//								ParameterAPI tempParam = (ParameterAPI)it.next();
//								
//								boolean flag = false;
//								
//								// this is a basin depth
//								if (tempParam.getName().equals(Field_2000_AttenRel.BASIN_DEPTH_NAME) || tempParam.getName().equals(DepthTo2pt5kmPerSecParam.NAME)) {
//									if (skipBasin) {
////										System.out.println("****SKIPPING A BASIN SET!!!!");
//										flag = false;
//									} else {
//										//Setting the value of each site Parameter from the CVM and translating them into the Attenuation related site
//										flag = siteTranslator.setParameterValue(tempParam,type,depth);
//									}
//								} else { // this is a site type/vs30
//									if (skipType) {
////										System.out.println("****SKIPPING A TYPE SET!!!!");
//										flag = false;
//									} else {
//										//Setting the value of each site Parameter from the CVM and translating them into the Attenuation related site
//										flag = siteTranslator.setParameterValue(tempParam,type,depth);
//									}
//								}
//
//								if (!flag) {
//									for (ParameterAPI param : defaultSiteParams) {
//										if (tempParam.getName().equals(param.getName())) {
//											tempParam.setValue(param.getValue());
//										}
//									}
//								}
//							}
//						}
//					}
				} catch (RegionConstraintException e) {
					System.out.println("No More Sites!");
					break;
				}
				Iterator it = site.getParametersIterator();
				System.out.println("Site Parameters:");
				while (it.hasNext()) {
					ParameterAPI param = (ParameterAPI)it.next();
					System.out.println(param.getName() + ": " + param.getValue());
				}
				
				// get the location from the site for output file naming
				String lat = decimalFormat.format(site.getLocation().getLatitude());
				String lon = decimalFormat.format(site.getLocation().getLongitude());
				String prefix = "";
				String curveDir = "curves/";
				String jobDir = lat + "/";
				prefix += outputDir;
				prefix += curveDir;
				File curveDirFile = new File(prefix);
				if (!curveDirFile.exists()) {
					curveDirFile.mkdir();
				}
				
				prefix += jobDir;
				File dir = new File(prefix);
				if (!dir.exists()) {
					dir.mkdir();
//					chmod(dir.getAbsolutePath());
				}
				String outFileName = prefix + lat + "_" + lon + ".txt";
				
				ArbitrarilyDiscretizedFunc hazFunction = this.hazFunction.deepClone();
				
				// check to see if the file exists...like for a repair run
				File outFileFile = new File(outFileName);
				if (outFileFile.exists()) {
					ArbitrarilyDiscretizedFunc fileFunc = loadCurveFile(outFileName);
					if (fileFunc != null) {
						int numPts = hazFunction.getNum();
						if (fileFunc.getNum() == numPts && fileFunc.getX(0) == hazFunction.getX(0)
								&& fileFunc.getX(numPts -1) == hazFunction.getX(numPts - 1)) {
							// if we're in here then the file loaded fine as a function, has the same number
							// of points, and has the same starting and ending x value...we can skip this site!
							if (print)
								System.out.println("Skipping a Hazard Curve!");
							continue;
						}
					}
				}
				
				// take the log of the hazard function and to send to the calculator
				ArbitrarilyDiscretizedFunc logHazFunction = getLogFunction(hazFunction);

				if (print)
					System.out.println("Calculating Hazard Curve");
				// actually calculate the curve from the log hazard function, site, IMR, and ERF
				calc.getHazardCurve(logHazFunction,site,imr,erf);
				if (print)
					System.out.println("Calculated a curve!");
				
				// convert the hazard function back from log values
				hazFunction = unLogFunction(hazFunction, logHazFunction);
				
				// see if it's empty\
				if (hazFunction.getY(0) == 0 && hazFunction.getY(3) == 0) {
					System.err.println("WARNING: Empty hazard curve!");
					System.err.println("Site index: " + j);
					System.err.println("Site Location: " + site.getLocation().getLatitude() + " " + site.getLocation().getLongitude());
					Iterator it2 = site.getParametersIterator();
					System.err.println("Site Parameters:");
					while (it2.hasNext()) {
						ParameterAPI param = (ParameterAPI)it2.next();
						System.err.println(param.getName() + ": " + param.getValue());
					}
//					System.err.println("SKIPPING!!!");
//					continue;
				}

				// write the result to the file
				if (print)
					System.out.println("Writing Results to File: " + outFileName);
				DiscretizedFunc.writeSimpleFuncFile(hazFunction, outFileName);
//				chmod(outFile.getAbsolutePath());
			}
			if ((lessPrints && j % 100 != 0 || !lessPrints) && timer && j>0) {
				curveTimes.add(System.currentTimeMillis() - start_curve);
				System.out.println("Took " + getTime(start_curve) + " seconds to calculate curve.");
				start_curve = System.currentTimeMillis();
			}

		} catch (ParameterException e) {
			// something bad happened, exit with code 1
			e.printStackTrace();
			System.exit(1);
		} catch (RemoteException e) {
			// something bad happened, exit with code 1
			e.printStackTrace();
			System.exit(1);
		} catch (FileNotFoundException e) {
			// something bad happened, exit with code 1
			e.printStackTrace();
			System.exit(1);
		} catch (IOException e) {
			// something bad happened, exit with code 1
			e.printStackTrace();
			System.exit(1);
		}
		
		if (timer) {
			long total = 0;
			for (Long time:curveTimes)
				total += time;
			double average = (double)total / (double)curveTimes.size();
			System.out.println("Average curve time: " + new DecimalFormat(	"###.##").format(average / 1000d));
			System.out.println("Total overhead: " + overheadStr);
			System.out.println("Total calculation time: " + getTime(start));
			System.out.println();
			
			// calculate an estimate
			int curvesPerJob = 100;
			double estimate = average * (double)numSites + (double)overhead * (numSites / curvesPerJob);
			String estimateHoursStr = new DecimalFormat(	"###.##").format(estimate / 3600000d);
			String estimateSecondsStr = new DecimalFormat(	"###.##").format(estimate / 1000d);
			System.out.println("Estimated Total CPU Time (current region, " + numSites + " sites): " + estimateHoursStr + " hours (" + estimateSecondsStr + " seconds)");
			
			numSites = 180000;
			estimate = average * (double)numSites + (double)overhead * (numSites / curvesPerJob);
			estimateHoursStr = new DecimalFormat(	"###.##").format(estimate / 3600000d);
			estimateSecondsStr = new DecimalFormat(	"###.##").format(estimate / 1000d);
			System.out.println("Estimated Total CPU Time (estimated region, " + numSites + " sites): " + estimateHoursStr + " hours (" + estimateSecondsStr + " seconds)");
		}
		System.out.println("***DONE***");
		System.out.println("End Time Stamp: " + System.currentTimeMillis());
	}
	
	public void chmod(String name) {
		System.out.println("CMODDING: " + name);
		String[] cmd = {"/bin/sh", " /bin/chmod ", " o+rw ", name};
//		try {
//			Runtime.getRuntime().exec(cmd);
//		} catch (IOException e) {
//			e.printStackTrace();
//		}
		try {
			String line;
			Process p = Runtime.getRuntime().exec(cmd);
			p.waitFor();
			System.out.println("MODDED!");
			BufferedReader input =
				new BufferedReader
				(new InputStreamReader(p.getInputStream()));
			while ((line = input.readLine()) != null) {
				System.err.println(line);
			}
			input.close();
		}
		catch (Exception err) {
			err.printStackTrace();
		}

	}

	/**
	 * Calculate and format the time from 'before'
	 * @param before - currentTimeMillis that should be counted from
	 * @return string in seconds of elapsed time
	 */
	public String getTime(long before) {
		double time = ((double)System.currentTimeMillis() - (double)before)/1000d; 
		return new DecimalFormat(	"###.##").format(time);
	}

	/**
	 * Takes the log of the X-values of the given function
	 * @param arb
	 * @return A function with points (Log(x), 1)
	 */
	public static ArbitrarilyDiscretizedFunc getLogFunction(DiscretizedFuncAPI arb) {
		ArbitrarilyDiscretizedFunc new_func = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV or SA
//		if (this.xLogFlag) {
			for (int i = 0; i < arb.getNum(); ++i)
				new_func.set(Math.log(arb.getX(i)), 1);
			return new_func;
//		}
//		else
//			throw new RuntimeException("Unsupported IMT");
	}


	/**
	 *  Un-log the function, keeping the y values from the log function, but matching
	 *  them with the x values of the original (not log) function
	 * @param oldHazFunc - original hazard function
	 * @param logHazFunction - calculated hazard curve with log x values
	 * @return
	 */
	public static ArbitrarilyDiscretizedFunc unLogFunction(
			ArbitrarilyDiscretizedFunc oldHazFunc, ArbitrarilyDiscretizedFunc logHazFunction) {
		int numPoints = oldHazFunc.getNum();
		ArbitrarilyDiscretizedFunc hazFunc = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV or SA
//		if (this.xLogFlag) {
			for (int i = 0; i < numPoints; ++i) {
				hazFunc.set(oldHazFunc.getX(i), logHazFunction.getY(i));
			}
			return hazFunc;
//		}
//		else
//			throw new RuntimeException("Unsupported IMT");
	}
	
	public static ArbitrarilyDiscretizedFunc loadCurveFile(String fileName) {
		try {
			ArbitrarilyDiscretizedFunc func = DiscretizedFunc.loadFuncFromSimpleFile(fileName);
			return func;
		} catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}

	public boolean isTimer() {
		return timer;
	}

	public void setTimer(boolean timer) {
		this.timer = timer;
	}

	public boolean isSkipPoints() {
		return skipPoints;
	}

	public void setSkipPoints(boolean skipPoints) {
		this.skipPoints = skipPoints;
	}

	public int getSkipFactor() {
		return skipFactor;
	}

	public void setSkipFactor(int skipFactor) {
		this.skipFactor = skipFactor;
	}

	public boolean isLessPrints() {
		return lessPrints;
	}

	public void setLessPrints(boolean lessPrints) {
		this.lessPrints = lessPrints;
	}
}
