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

package org.opensha.sha.cybershake.plot;

import java.awt.Color;
import java.awt.HeadlessException;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.rmi.RemoteException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.ListIterator;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.MissingOptionException;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.dom4j.DocumentException;
import org.jfree.chart.ChartUtilities;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.siteData.CachedSiteDataWrapper;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.data.siteData.impl.CVM2BasinDepth;
import org.opensha.commons.data.siteData.impl.CVM4BasinDepth;
import org.opensha.commons.data.siteData.impl.WillsMap2000;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.gui.UserAuthDialog;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeIM;
import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.HazardCurveComputation;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;
import org.opensha.sha.cybershake.db.Runs2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;
import org.opensha.sha.cybershake.gui.CyberShakeDBManagementApp;
import org.opensha.sha.cybershake.gui.util.AttenRelSaver;
import org.opensha.sha.cybershake.gui.util.ERFSaver;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.PlotControllerAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.SiteTranslator;


public class HazardCurvePlotter implements GraphPanelAPI, PlotControllerAPI {
	
	public static final String TYPE_PDF = "pdf";
	public static final String TYPE_PNG = "png";
	public static final String TYPE_JPG = "jpg";
	public static final String TYPE_JPEG = "jpeg";
	public static final String TYPE_TXT = "txt";
	
	public static final String TYPE_DEFAULT = TYPE_PDF;
	
	private double maxSourceDistance = 200;
	
	public static final int PLOT_WIDTH_DEFAULT = 600;
	public static final int PLOT_HEIGHT_DEFAULT = 500;
	
	private int plotWidth = PLOT_WIDTH_DEFAULT;
	private int plotHeight = PLOT_HEIGHT_DEFAULT;
	
	private DBAccess db;
//	private int erfID;
//	private int rupVarScenarioID;
//	private int sgtVarID;
	
	private HazardCurve2DB curve2db;
	
	private GraphPanel gp;
	
	private EqkRupForecast erf = null;
	private ArrayList<AttenuationRelationship> attenRels = new ArrayList<AttenuationRelationship>();
	
	private SiteInfo2DB site2db = null;
	private PeakAmplitudesFromDB amps2db = null;
	private Runs2DB runs2db = null;
	
	CybershakeSite csSite = null;
	
	SiteTranslator siteTranslator = new SiteTranslator();
	
	HazardCurveCalculator calc;
	
//	CybershakeERF selectedERF;
	
	SimpleDateFormat dateFormat = new SimpleDateFormat("MM_dd_yyyy");
	
	private double manualVs30  = -1;
	
	double currentPeriod = -1;
	
	HazardCurvePlotCharacteristics plotChars = HazardCurvePlotCharacteristics.createRobPlotChars();
	
	OrderedSiteDataProviderList dataProviders;
	
	public HazardCurvePlotter(DBAccess db) {
		this.db = db;
		
		init();
	}
	
	private int getRunID(int siteID, int erfID, int rupVarScenarioID, int sgtVarID) {
		ArrayList<Integer> runIDs = runs2db.getRunIDs(siteID, erfID, sgtVarID, rupVarScenarioID, null, null, null, null);
		if (runIDs == null || runIDs.size() == 0)
			return -1;
		int id = -1;
		if (runIDs.size() == 1) {
			id = runIDs.get(0);
		} else {
			// we want to select a runID that has data, if available.
			// we favor the first one with curves, or if that doesn't exist, the first one
			// with amplitudes
			int ampsID = -1;
			for (int runID : runIDs) {
				ArrayList<CybershakeHazardCurveRecord> curves = curve2db.getHazardCurveRecordsForRun(runID);
				if (curves != null && curves.size() > 0) {
					id = runID;
					break;
				} else if (amps2db.hasAmps(runID) && ampsID == -1) {
					ampsID = runID;
				}
			}
			if (id < 0 && ampsID >= 0)
				id = ampsID;
		}
		System.out.println("Detected runID '" + id + "' from " + runIDs.size() + " matches");
		return id;
	}
	
	private void init() {
		gp = new GraphPanel(this);
		
		runs2db = new Runs2DB(db);
		curve2db = new HazardCurve2DB(this.db);
		
		try {
			calc = new HazardCurveCalculator();
			calc.setMaxSourceDistance(maxSourceDistance);
		} catch (RemoteException e) {
			throw new RuntimeException(e);
		}
	}
	
	private OrderedSiteDataProviderList getProviders() {
		if (dataProviders == null) {
			ArrayList<SiteDataAPI<?>> providers = new ArrayList<SiteDataAPI<?>>();
			
			/*		Wills 2006 Map (2000 as backup)	 */
			// try the 2006 map first
			try {
				providers.add(new CachedSiteDataWrapper<Double>(new WillsMap2006()));
			} catch (IOException e) {
				e.printStackTrace();
				providers.add(new CachedSiteDataWrapper<String>(new WillsMap2000()));
			}
			
			/*		CVM4 Depth to 2.5 (CVM2 as backup)	 */
			try {
				providers.add(new CachedSiteDataWrapper<Double>(new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_2_5)));
			} catch (IOException e) {
				e.printStackTrace();
				try {
					providers.add(new CachedSiteDataWrapper<Double>(new CVM2BasinDepth()));
				} catch (IOException e1) {
					e1.printStackTrace();
				}
			}
			
			/*		CVM4 Depth to 1.0					 */
			try {
				providers.add(new CachedSiteDataWrapper<Double>(new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_1_0)));
			} catch (IOException e) {
				e.printStackTrace();
			}
			
			dataProviders = new OrderedSiteDataProviderList(providers);
		}
		return dataProviders;
	}
	
	public static ArrayList<String> commaSplit(String str) {
		str = str.trim();
		ArrayList<String> vals = new ArrayList<String>();
		for (String val : str.split(",")) {
			val = val.trim();
			vals.add(val);
		}
		return vals;
	}
	
	public static ArrayList<Double> commaDoubleSplit(String str) {
		ArrayList<Double> vals = new ArrayList<Double>();
		
		for (String val : commaSplit(str)) {
			vals.add(Double.parseDouble(val));
		}
		
		return vals;
	}
	
	public boolean plotCurvesFromOptions(CommandLine cmd) {
		String siteName = cmd.getOptionValue("site");
		
		SiteInfo2DB site2db = getSite2DB();
		PeakAmplitudesFromDB amps2db = getAmps2DB();
		
		int siteID = site2db.getSiteId(siteName);
		
		int runID;
		if (cmd.hasOption("run-id")) {
			runID = Integer.parseInt(cmd.getOptionValue("run-id"));
			if (runID < 0) {
				System.err.println("Invalid run id '" + runID + "'!");
				return false;
			}
		} else {
			int erfID;
			if (cmd.hasOption("erf-id"))
				erfID = Integer.parseInt(cmd.getOptionValue("erf-id"));
			else
				erfID = -1;
			int rupVarScenarioID;
			if (cmd.hasOption("rv-id"))
				rupVarScenarioID = Integer.parseInt(cmd.getOptionValue("rv-id"));
			else
				rupVarScenarioID = -1;
			int sgtVarID;
			if (cmd.hasOption("sgt-var-id"))
				sgtVarID = Integer.parseInt(cmd.getOptionValue("sgt-var-id"));
			else
				sgtVarID = -1;
			runID = this.getRunID(siteID, erfID, rupVarScenarioID, sgtVarID);
			if (runID < 0) {
				System.err.println("No suitable run ID found! siteID: " + siteID + ", erfID: " + erfID +
						", rupVarScenarioID: " + rupVarScenarioID + ", sgtVarID: " + sgtVarID);
				return false;
			}
		}
		
		CybershakeRun run = runs2db.getRun(runID);
		if (run == null) {
			System.err.println("Invalid run id '" + runID + "'!");
			return false;
		}
		
		System.out.println("Plotting curve(s) for site " + siteName + "=" + siteID + ", RunID=" + runID);
		this.setMaxSourceSiteDistance(siteID);
		
		if (siteID < 0) {
			System.err.println("Site '" + siteName + "' unknown!");
			return false;
		}
		
		if (cmd.hasOption("plot-chars-file")) {
			String pFileName = cmd.getOptionValue("plot-chars-file");
			System.out.println("Reading plot characteristics from " + pFileName);
			try {
				plotChars = HazardCurvePlotCharacteristics.fromXMLMetadata(pFileName);
			} catch (MalformedURLException e) {
				e.printStackTrace();
				System.err.println("WARNING: plot characteristics file not found! Using default...");
			} catch (RuntimeException e) {
				e.printStackTrace();
				System.err.println("WARNING: plot characteristics file parsing error! Using default...");
			} catch (DocumentException e) {
				e.printStackTrace();
				System.err.println("WARNING: plot characteristics file parsing error! Using default...");
			}
		}
		
		String periodStrs = cmd.getOptionValue("period");
		ArrayList<Double> periods = commaDoubleSplit(periodStrs);
		
		System.out.println("Matching periods to IM types...");
		ArrayList<CybershakeIM> ims = amps2db.getIMForPeriods(periods, runID, curve2db);
		
		if (ims == null) {
			System.err.println("No IM's for site=" + siteID + " run=" + runID);
			for (double period : periods) {
				System.err.println("period: " + period);
			}
			return false;
		}
		
		if (cmd.hasOption("ef") && cmd.hasOption("af")) {
			String erfFile = cmd.getOptionValue("ef");
			String attenFiles = cmd.getOptionValue("af");
			
			try {
				erf = ERFSaver.LOAD_ERF_FROM_FILE(erfFile);
				
				for (String attenRelFile : commaSplit(attenFiles)) {
					AttenuationRelationship attenRel = AttenRelSaver.LOAD_ATTEN_REL_FROM_FILE(attenRelFile);
					this.addAttenuationRelationshipComparision(attenRel);
				}
			} catch (DocumentException e) {
				e.printStackTrace();
				System.err.println("WARNING: Unable to parse ERF XML, not plotting comparison curves!");
			} catch (InvocationTargetException e) {
				e.printStackTrace();
				System.err.println("WARNING: Unable to load comparison ERF, not plotting comparison curves!");
			} catch (MalformedURLException e) {
				// TODO Auto-generated catch block
				System.err.println("WARNING: Unable to load comparison ERF, not plotting comparison curves!");
			}
		}
		
		HazardCurveComputation curveCalc = null;
		String user = "";
		String pass = "";
		
		String outDir = "";
		if (cmd.hasOption("o")) {
			outDir = cmd.getOptionValue("o");
			File outDirFile = new File(outDir);
			if (!outDirFile.exists()) {
				boolean success = outDirFile.mkdir();
				if (!success) {
					System.out.println("Directory doesn't exist and couldn't be created: " + outDir);
					return false;
				}
			}
			if (!outDir.endsWith(File.separator))
				outDir += File.separator;
		}
		
		if (cmd.hasOption("vs30")) {
			String vsStr = cmd.getOptionValue("vs30");
			manualVs30 = Double.parseDouble(vsStr);
		}
		
		ArrayList<String> types;
		
		if (cmd.hasOption("t")) {
			String typeStr = cmd.getOptionValue("t");
			
			types = commaSplit(typeStr);
		} else {
			types = new ArrayList<String>();
			types.add(TYPE_PDF);
		}
		
		if (cmd.hasOption("w")) {
			plotWidth = Integer.parseInt(cmd.getOptionValue("w"));
		}
		
		if (cmd.hasOption("h")) {
			plotHeight = Integer.parseInt(cmd.getOptionValue("h"));
		}
		
		int periodNum = 0;
		boolean atLeastOne = false;
		
		boolean calcOnly = cmd.hasOption("calc-only");
		
		if (calcOnly) {
			System.out.println("Calculating/inserting CyberShake curves only, no plotting.");
			atLeastOne = true;
		}
		
		for (CybershakeIM im : ims) {
			if (im == null) {
				System.out.println("IM not found for: site=" + siteName + " period=" + periods.get(periodNum));
				return false;
			}
			periodNum++;
			int curveID = curve2db.getHazardCurveID(runID, im.getID());
			int numPoints = 0;
			if (curveID >= 0)
				numPoints= curve2db.getNumHazardCurvePoints(curveID);
			
			System.out.println("Num points: " + numPoints);
			
			// if no curveID exists, or the curve has 0 points
			if (curveID < 0 || numPoints < 1) {
				if (!cmd.hasOption("n")) {
					if (!cmd.hasOption("f")) {
						// lets ask the user what they want to do
						if (curveID >= 0)
							System.out.println("A record for the selected curve exists in the database, but there " +
									"are no data points: " + curveID + " period=" + im.getVal());
						else
							System.out.println("The selected curve does not exist in the database: " + siteID + " period="
									+ im.getVal() + " run=" + runID);
						boolean skip = false;
						// open up standard input
						BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
						while (true) {
							System.out.print("Would you like to calculate and insert it? (y/n): ");
							try {
								String response = in.readLine();
								response = response.trim().toLowerCase();
								if (response.startsWith("y")) { 
									break;
								} else if (response.startsWith("n")) {
									skip = true;
									break;
								}
							} catch (IOException e) {
								e.printStackTrace();
							}
						}
						if (skip)
							continue;
					}
					int count = amps2db.countAmps(runID, im);
					if (count <= 0) {
						System.err.println("No Peak Amps for: " + siteID + " period="
									+ im.getVal() + " run=" + runID);
						return false;
					}
					System.out.println(count + " amps in DB");
					if (user.equals("") && pass.equals("")) {
						if (cmd.hasOption("pf")) {
							String pf = cmd.getOptionValue("pf");
							try {
								String user_pass[] = CyberShakeDBManagementApp.loadPassFile(pf);
								user = user_pass[0];
								pass = user_pass[1];
							} catch (FileNotFoundException e) {
								e.printStackTrace();
								System.out.println("Password file not found!");
								return false;
							} catch (IOException e) {
								e.printStackTrace();
								System.out.println("Password file not found!");
								return false;
							} catch (Exception e) {
								e.printStackTrace();
								System.out.println("Bad password file!");
								return false;
							}
							if (user.equals("") || pass.equals("")) {
								System.out.println("Bad password file!");
								return false;
							}
						} else {
							try {
								UserAuthDialog auth = new UserAuthDialog(null, true);
								auth.setVisible(true);
								if (auth.isCanceled())
									return false;
								user = auth.getUsername();
								pass = new String(auth.getPassword());
							} catch (HeadlessException e) {
								System.out.println("It looks like you can't display windows, using less secure command line password input.");
								BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
								
								boolean hasUser = false;
								while (true) {
									try {
										if (hasUser)
											System.out.print("Database Password: ");
										else
											System.out.print("Database Username: ");
										String line = in.readLine().trim();
										if (line.length() > 0) {
											if (hasUser) {
												pass = line;
												break;
											} else {
												user = line;
												hasUser = true;
											}
										}
									} catch (IOException e1) {
										e1.printStackTrace();
									}
								}
							}
						}
					}
					
					DBAccess writeDB = null;
					try {
						writeDB = new DBAccess(Cybershake_OpenSHA_DBApplication.HOST_NAME,Cybershake_OpenSHA_DBApplication.DATABASE_NAME, user, pass);
					} catch (IOException e) {
						e.printStackTrace();
						return false;
					}
					
					// calculate the curve
					if (curveCalc == null)
						curveCalc = new HazardCurveComputation(db);
					
					ArbitrarilyDiscretizedFunc func = plotChars.getHazardFunc();
					ArrayList<Double> imVals = new ArrayList<Double>();
					for (int i=0; i<func.getNum(); i++)
						imVals.add(func.getX(i));
					
					DiscretizedFuncAPI curve = curveCalc.computeHazardCurve(imVals, run, im);
					HazardCurve2DB curve2db_write = new HazardCurve2DB(writeDB);
					System.out.println("Inserting curve into database...");
					if (curveID >= 0) {
						curve2db_write.insertHazardCurvePoints(curveID, curve);
					} else {
						curve2db_write.insertHazardCurve(runID, im.getID(), curve);
						curveID = curve2db.getHazardCurveID(runID, im.getID());
					}
				} else {
					System.out.println("Curve not found in DB, and no-add option supplied!");
					return false;
				}
			}
			Date date = curve2db.getDateForCurve(curveID);
			String dateStr = dateFormat.format(date);
			String periodStr = "SA_" + getPeriodStr(im.getVal()) + "sec";
			String outFileName = siteName + "_ERF" + run.getERFID() + "_Run" + runID + "_" + periodStr + "_" + dateStr;
			String outFile = outDir + outFileName;
			if (calcOnly)
				continue;
			boolean textOnly = types.size() == 1 && types.get(0) == TYPE_TXT;
			ArrayList<DiscretizedFuncAPI> curves = this.plotCurve(curveID, run, textOnly);
			if (curves == null) {
				System.err.println("No points could be fetched for curve ID " + curveID + "! Skipping...");
				continue;
			}
			for (String type : types) {
				type = type.toLowerCase();
				
				try {
					if (type.equals(TYPE_PDF)) {
						plotCurvesToPDF(outFile + ".pdf");
						atLeastOne = true;
					} else if (type.equals(TYPE_PNG)) {
						plotCurvesToPNG(outFile + ".png");
						atLeastOne = true;
					} else if (type.equals(TYPE_JPG) || type.equals(TYPE_JPEG)) {
						plotCurvesToJPG(outFile + ".jpg");
						atLeastOne = true;
					} else if (type.equals(TYPE_TXT)) {
						plotCurvesToTXT(outFile + ".txt", curves);
						atLeastOne = true;
					} else
						System.err.println("Unknown plotting type: " + type + "...Skipping!");
				} catch (IOException e) {
					e.printStackTrace();
					return false;
				}
			}
		}
		
		return atLeastOne;
	}
	
	public void setMaxSourceSiteDistance(int siteID) {
		SiteInfo2DB site2db = this.getSite2DB();
		
		this.maxSourceDistance = site2db.getSiteCutoffDistance(siteID);
		System.out.println("Max source distance for site " + siteID + " is " + this.maxSourceDistance);
	}
	
	public void plotCurve(CybershakeRun run, int imTypeID) {
		int curveID = curve2db.getHazardCurveID(run.getRunID(), imTypeID);
		this.plotCurve(curveID, run);
	}
	
	public ArrayList<DiscretizedFuncAPI> plotCurve(int curveID, CybershakeRun run) {
		return plotCurve(curveID, run, false);
	}
	
	ArrayList<String> curveNames = new ArrayList<String>();
	
	public ArrayList<DiscretizedFuncAPI> plotCurve(int curveID, CybershakeRun run, boolean textOnly) {
		curveNames.clear();
		System.out.println("Fetching Curve!");
		DiscretizedFuncAPI curve = curve2db.getHazardCurve(curveID);
		
		if (curve == null)
			return null;
		
		ArrayList<PlotCurveCharacterstics> chars = new ArrayList<PlotCurveCharacterstics>();
		chars.add(new PlotCurveCharacterstics(this.plotChars.getCyberShakeLineType(), this.plotChars.getCyberShakeColor(), 1));
		
		
		CybershakeIM im = curve2db.getIMForCurve(curveID);
		if (im == null) {
			System.err.println("Couldn't get IM for curve!");
			System.exit(1);
		}
		
		System.out.println("Getting Site Info.");
		int siteID = curve2db.getSiteIDFromCurveID(curveID);
		
		SiteInfo2DB site2db = getSite2DB();
		
		csSite = site2db.getSiteFromDB(siteID);
		
		ArrayList<DiscretizedFuncAPI> curves = new ArrayList<DiscretizedFuncAPI>();
		curves.add(curve);
		curveNames.add("CyberShake Hazard Curve. Site: " + csSite.toString());
		
		if (erf != null && attenRels.size() > 0) {
			System.out.println("Plotting comparisons!");
			curveNames.addAll(this.plotComparisions(curves, im, curveID, chars));
		}
		
		curve.setInfo(this.getCyberShakeCurveInfo(csSite, run, im));
		
		String title = HazardCurvePlotCharacteristics.getReplacedTitle(plotChars.getTitle(), csSite);
		
		if (!textOnly) {
			System.out.println("Plotting Curve!");
			
			plotCurvesToGraphPanel(chars, im, curves, title);
		}
		return curves;
	}

	private void plotCurvesToPDF(String outFile) throws IOException {
		System.out.println("Saving PDF to: " + outFile);
		this.gp.saveAsPDF(outFile, plotWidth, plotHeight);
	}
	
	private void plotCurvesToPNG(String outFile) throws IOException {
		System.out.println("Saving PNG to: " + outFile);
		ChartUtilities.saveChartAsPNG(new File(outFile), gp.getCartPanel().getChart(), plotWidth, plotHeight);
	}
	
	private void plotCurvesToJPG(String outFile) throws IOException {
		System.out.println("Saving JPG to: " + outFile);
		ChartUtilities.saveChartAsJPEG(new File(outFile), gp.getCartPanel().getChart(), plotWidth, plotHeight);
	}
	
	private void plotCurvesToTXT(String outFile, ArrayList<DiscretizedFuncAPI> curves) throws IOException {
		System.out.println("Saving TXT to: " + outFile);
		
		boolean useNames = false;
		if (curves.size() == curveNames.size())
			useNames = true;
		
		FileWriter fw = new FileWriter(outFile);
		
		fw.write("# Curves: " + curves.size() + "\n");
		
		for (int i=0; i<curves.size(); i++) {
			DiscretizedFuncAPI curve = curves.get(i);
			
			String header = "# Name: ";
			if (useNames)
				header += curveNames.get(i);
			else
				header += "Curve " + i;
			
			fw.write(header + "\n");
			
			for (int j=0; j<curve.getNum(); j++) {
				fw.write(curve.getX(j) + "\t" + curve.getY(j) + "\n");
			}
		}
		fw.close();
	}

	private void plotCurvesToGraphPanel( ArrayList<PlotCurveCharacterstics> chars, CybershakeIM im,
			ArrayList<DiscretizedFuncAPI> curves, String title) {
		
		String xAxisName = HazardCurvePlotCharacteristics.getReplacedXAxisLabel(plotChars.getXAxisLabel(), im.getVal());
		
		this.currentPeriod = im.getVal();
		
		this.gp.setCurvePlottingCharacterstic(chars);
		
		this.gp.drawGraphPanel(xAxisName, plotChars.getYAxisLabel(), curves, plotChars.isXLog(), plotChars.isYLog(), plotChars.isCustomAxis(), title, this);
		this.gp.setVisible(true);
		
		this.gp.togglePlot(null);
		
		this.gp.validate();
		this.gp.repaint();
	}
	
	public GraphPanel getGraphPanel() {
		return this.gp;
	}
	
	public static String getPeriodStr(double period) {
		int periodInt = (int)(period * 100 + 0.5);
		
		return (periodInt / 100) + "";
	}
	
	private ArrayList<String> plotComparisions(ArrayList<DiscretizedFuncAPI> curves, CybershakeIM im, int curveID, ArrayList<PlotCurveCharacterstics> chars) {
		ArrayList<String> names = new ArrayList<String>();
		System.out.println("Setting ERF Params");
		this.setERFParams();
		
		int i = 0;
		ArrayList<Color> colors = plotChars.getAttenRelColors();
		for (AttenuationRelationship attenRel : attenRels) {
			Color color;
			if (i >= colors.size())
				color = colors.get(colors.size() - 1);
			else
				color = colors.get(i);
			chars.add(new PlotCurveCharacterstics(this.plotChars.getAttenRelLineType(), color, 1));
			
			System.out.println("Setting params for Attenuation Relationship: " + attenRel.getName());
			Site site = this.setAttenRelParams(attenRel, im);
			
			System.out.print("Calculating comparison curve for " + site.getLocation().getLatitude() + "," + site.getLocation().getLongitude() + "...");
			try {
				ArbitrarilyDiscretizedFunc curve = plotChars.getHazardFunc();
				ArbitrarilyDiscretizedFunc logHazFunction = this.getLogFunction(curve);
				calc.getHazardCurve(logHazFunction, site, attenRel, erf);
				curve = this.unLogFunction(curve, logHazFunction);
				curve.setInfo(this.getCurveParametersInfoAsString(attenRel, erf, site));
				System.out.println("done!");
				curves.add(curve);
				names.add(attenRel.getName());
			} catch (RemoteException e) {
				e.printStackTrace();
			}
			i++;
		}
		return names;
	}
	
	public String getCyberShakeCurveInfo(CybershakeSite site, CybershakeRun run, CybershakeIM im) {
		String infoString = "Site: "+ site.getFormattedName() + ";\n";
		if (run != null)
			infoString += run.toString() + ";\n";
		infoString += "SA Period: " + im.getVal() + ";\n";
		
		return infoString;
	}
	
	public String getCurveParametersInfoAsString(AttenuationRelationship imr, EqkRupForecast erf, Site site) {
		return this.getCurveParametersInfoAsHTML(imr, erf, site).replace("<br>", "\n");
	}

	public String getCurveParametersInfoAsHTML(AttenuationRelationship imr, EqkRupForecast erf, Site site) {
		ListIterator<ParameterAPI<?>> imrIt = imr.getOtherParamsIterator();
		String imrMetadata = "IMR = " + imr.getName() + "; ";
		while (imrIt.hasNext()) {
			ParameterAPI tempParam = imrIt.next();
			imrMetadata += tempParam.getName() + " = " + tempParam.getValue();
		}
		String siteMetadata = site.getParameterListMetadataString();
		String imtName = imr.getIntensityMeasure().getName();
		String imtMetadata = "IMT = " + imtName;
		if (imtName.toLowerCase().equals("sa")) {
			imtMetadata += "; ";
			ParameterAPI damp = imr.getParameter(DampingParam.NAME);
			if (damp != null)
				imtMetadata += damp.getName() + " = " + damp.getValue() + "; ";
			ParameterAPI period = imr.getParameter(PeriodParam.NAME);
			imtMetadata += period.getName() + " = " + period.getValue();
		}
//		imr.get
		String erfMetadata = "Eqk Rup Forecast = " + erf.getName();
		erfMetadata += "; " + erf.getAdjustableParameterList().getParameterListMetadataString();
		String timeSpanMetadata = "Duration = " + erf.getTimeSpan().getDuration() + " " + erf.getTimeSpan().getDurationUnits();

		return "<br>"+ "IMR Param List:" +"<br>"+
		"---------------"+"<br>"+
		imrMetadata+"<br><br>"+
		"Site Param List: "+"<br>"+
		"----------------"+"<br>"+
		siteMetadata+"<br><br>"+
		"IMT Param List: "+"<br>"+
		"---------------"+"<br>"+
		imtMetadata+"<br><br>"+
		"Forecast Param List: "+"<br>"+
		"--------------------"+"<br>"+
		erfMetadata+"<br><br>"+
		"TimeSpan Param List: "+"<br>"+
		"--------------------"+"<br>"+
		timeSpanMetadata+"<br><br>"+
		"Max. Source-Site Distance = "+maxSourceDistance;

	}

	private void setERFParams() {
//		this.erf = MeanUCERF2_ToDB.setMeanUCERF_CyberShake_Settings(this.erf);
		this.erf.updateForecast();
	}
	
	private Site setAttenRelParams(AttenuationRelationship attenRel, CybershakeIM im) {
//		// set 1 sided truncation
//		StringParameter truncTypeParam = (StringParameter)attenRel.getParameter(SigmaTruncTypeParam.NAME);
//		truncTypeParam.setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
//		// set truncation at 3 std dev's
//		DoubleParameter truncLevelParam = (DoubleParameter)attenRel.getParameter(SigmaTruncLevelParam.NAME);
//		truncLevelParam.setValue(3.0);
		
		attenRel.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		
		// set IMT
		attenRel.setIntensityMeasure(SA_Param.NAME);
		DoubleDiscreteParameter saPeriodParam = (DoubleDiscreteParameter)attenRel.getParameter(PeriodParam.NAME);
		ArrayList<Double> allowedVals = saPeriodParam.getAllowedDoubles();
		
		double closestPeriod = Double.NaN;
		double minDistance = Double.POSITIVE_INFINITY;
		
		for (double period : allowedVals) {
			double dist = Math.abs(period - im.getVal());
			if (dist < minDistance) {
				minDistance = dist;
				closestPeriod = period;
			}
		}
		saPeriodParam.setValue(closestPeriod);
//		attenRel.setIntensityMeasure(intensityMeasure)
		
		LocationList locList = new LocationList();
		Location loc = new Location(csSite.lat, csSite.lon);
		locList.add(loc);
		
		Site site = new Site(loc);
		
		try{
			OrderedSiteDataProviderList providers = getProviders();
			ArrayList<SiteDataValue<?>> datas = providers.getBestAvailableData(loc);
			
			if (manualVs30 > 0) {
				datas.add(new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30, SiteDataAPI.TYPE_FLAG_INFERRED, manualVs30,
						"Manually Set Vs30 Value"));
			}
			
			Iterator<ParameterAPI<?>> it = attenRel.getSiteParamsIterator(); // get site params for this IMR
			while(it.hasNext()) {
				ParameterAPI tempParam = it.next();
				if(!site.containsParameter(tempParam))
					site.addParameter(tempParam);
				//adding the site Params from the CVM, if site is out the range of CVM then it
				//sets the site with whatever site Parameter Value user has choosen in the application
				boolean flag = siteTranslator.setParameterValue(tempParam, datas);
				if( !flag ) {
					System.err.println("Param " + tempParam.getName() + " not set for site! Not available from web service.");
					if (tempParam.getName().equals(Vs30_Param.NAME)) {
						BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
						System.out.print("Enter Vs30 value (or hit enter for default, " + tempParam.getValue() + "): ");
						String line = in.readLine();
						line = line.trim();
						if (line.length() > 0) {
							try {
								double val = Double.parseDouble(line);
								tempParam.setValue(val);
								System.out.println(tempParam.getName() + " set to: " + tempParam.getValue());
							} catch (Exception e) {
								System.out.println("Using default value: " + tempParam.getValue());
							}
						} else {
							System.out.println("Using default value: " + tempParam.getValue());
						}
						manualVs30 = (Double)tempParam.getValue();
					} else {
						System.out.println("Using default value: " + tempParam.getValue());
					}
				} else {
					System.out.println("Param: "+tempParam.getName() + ", Value: " + tempParam.getValue());
				}
			}
		}catch(Exception e){
			e.printStackTrace();
		}
		return site;
	}
	
	public SiteInfo2DB getSite2DB() {
		if (site2db == null)
			site2db = new SiteInfo2DB(db);
		
		return site2db;
	}
	
	public PeakAmplitudesFromDB getAmps2DB() {
		if (amps2db == null)
			amps2db = new PeakAmplitudesFromDB(db);
		
		return amps2db;
	}
	
	public void addAttenuationRelationshipComparision(AttenuationRelationship attenRel) {
		attenRels.add(attenRel);
	}
	
	public void clearAttenuationRelationshipComparisions() {
		attenRels.clear();
	}
	
	public void setERFComparison(EqkRupForecast erf) {
		this.erf = erf;
	}

	public double getMaxX() {
		if (currentPeriod > 0)
			return plotChars.getXMax(currentPeriod);
		return plotChars.getXMax();
	}

	public double getMaxY() {
		return plotChars.getYMax();
	}

	public double getMinX() {
		return plotChars.getXMin();
	}

	public double getMinY() {
		return plotChars.getYMin();
	}
	
	public int getAxisLabelFontSize() {
		// TODO Auto-generated method stub
		return 12;
	}

	public int getPlotLabelFontSize() {
		// TODO Auto-generated method stub
		return 12;
	}

	public int getTickLabelFontSize() {
		// TODO Auto-generated method stub
		return 10;
	}

	public void setXLog(boolean flag) {
		plotChars.setXLog(flag);
	}

	public void setYLog(boolean flag) {
		plotChars.setYLog(flag);
	}
	
	public void setPlottingCharactersistics(HazardCurvePlotCharacteristics chars) {
		this.plotChars = chars;
	}
	
	boolean xLogFlag = true;
	
	/**
	 * Takes the log of the X-values of the given function
	 * @param arb
	 * @return A function with points (Log(x), 1)
	 */
	private ArbitrarilyDiscretizedFunc getLogFunction(DiscretizedFuncAPI arb) {
		ArbitrarilyDiscretizedFunc new_func = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV or SA
		if (this.xLogFlag) {
			for (int i = 0; i < arb.getNum(); ++i)
				new_func.set(Math.log(arb.getX(i)), 1);
			return new_func;
		}
		else
			throw new RuntimeException("Unsupported IMT");
	}
	
	/**
	 *  Un-log the function, keeping the y values from the log function, but matching
	 *  them with the x values of the original (not log) function
	 * @param oldHazFunc - original hazard function
	 * @param logHazFunction - calculated hazard curve with log x values
	 * @return
	 */
	private ArbitrarilyDiscretizedFunc unLogFunction(
			DiscretizedFuncAPI oldHazFunc, DiscretizedFuncAPI logHazFunction) {
		int numPoints = oldHazFunc.getNum();
		ArbitrarilyDiscretizedFunc hazFunc = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV or SA
		if (this.xLogFlag) {
			for (int i = 0; i < numPoints; ++i) {
				hazFunc.set(oldHazFunc.getX(i), logHazFunction.getY(i));
			}
			return hazFunc;
		}
		else
			throw new RuntimeException("Unsupported IMT");
	}
	
	public static Options createOptions() {
		Options ops = new Options();
		
		// ERF
		Option erf = new Option("e", "erf-id", true, "ERF ID");
		erf.setRequired(false);
		ops.addOption(erf);
		
		Option rv = new Option("r", "rv-id", true, "Rupture Variation ID");
		rv.setRequired(false);
		ops.addOption(rv);
		
		Option sgt = new Option("sgt", "sgt-var-id", true, "STG Variation ID");
		sgt.setRequired(false);
		ops.addOption(sgt);
		
		Option run = new Option("R", "run-id", true, "Run ID");
		run.setRequired(false);
		ops.addOption(run);
		
		Option erfFile = new Option("ef", "erf-file", true, "XML ERF description file for comparison");
		ops.addOption(erfFile);
		
		Option attenRelFiles = new Option("af", "atten-rel-file", true, "XML Attenuation Relationship description file(s) for " + 
				"comparison. Multiple files should be comma separated");
		ops.addOption(attenRelFiles);
		
		Option site = new Option("s", "site", true, "Site short name");
		site.setRequired(true);
		ops.addOption(site);
		
		Option period = new Option("p", "period", true, "Period(s) to calculate. Multiple periods should be comma separated");
		period.setRequired(true);
		ops.addOption(period);
		
		Option pass = new Option("pf", "password-file", true, "Path to a file that contains the username and password for " + 
				"inserting curves into the database. Format should be \"user:pass\"");
		ops.addOption(pass);
		
		Option noAdd = new Option("n", "no-add", false, "Flag to not automatically calculate curves not in the database");
		ops.addOption(noAdd);
		
		Option force = new Option("f", "force-add", false, "Flag to add curves to db without prompt");
		ops.addOption(force);
		
		Option help = new Option("?", "help", false, "Display this message");
		ops.addOption(help);
		
		Option output = new Option("o", "output-dir", true, "Output directory");
		ops.addOption(output);
		
		Option type = new Option("t", "type", true, "Plot save type. Options are png, pdf, jpg, and txt. Multiple types can be " + 
				"comma separated (default is " + TYPE_DEFAULT + ")");
		ops.addOption(type);
		
		Option width = new Option("w", "width", true, "Plot width (default = " + PLOT_WIDTH_DEFAULT + ")");
		ops.addOption(width);
		
		Option height = new Option("h", "height", true, "Plot height (default = " + PLOT_HEIGHT_DEFAULT + ")");
		ops.addOption(height);
		
		Option vs30 = new Option("v", "vs30", true, "Specify default Vs30 for sites with no Vs30 data, or leave blank " + 
				"for default value. Otherwise, you will be prompted to enter vs30 interactively if needed.");
		ops.addOption(vs30);
		
		Option calcOnly = new Option("c", "calc-only", false, "Only calculate and insert the CyberShake curves, don't make " + 
				"plots. If a curve already exists, it will be skipped.");
		ops.addOption(calcOnly);
		
		Option plotChars = new Option("pl", "plot-chars-file", true, "Specify the path to a plot characteristics XML file");
		ops.addOption(plotChars);
		
		return ops;
	}
	
	public static void printHelp(Options options) {
		HelpFormatter formatter = new HelpFormatter();
		formatter.printHelp( "HazardCurvePlotter", options, true );
		System.exit(2);
	}
	
	public static void printUsage(Options options) {
		HelpFormatter formatter = new HelpFormatter();
		PrintWriter pw = new PrintWriter(System.out);
		formatter.printUsage(pw, 80, "HazardCurvePlotter", options);
		pw.flush();
		System.exit(2);
	}

	public static void main(String args[]) throws DocumentException, InvocationTargetException {
		
		try {
			Options options = createOptions();
			
			CommandLineParser parser = new GnuParser();
			
			if (args.length == 0) {
				printUsage(options);
			}
			
			try {
				CommandLine cmd = parser.parse( options, args);
				
				if (cmd.hasOption("help") || cmd.hasOption("?")) {
					printHelp(options);
				}
				
				HazardCurvePlotter plotter = new HazardCurvePlotter(Cybershake_OpenSHA_DBApplication.db);
				
				boolean success = plotter.plotCurvesFromOptions(cmd);
				
				if (!success) {
					System.out.println("FAIL!");
					System.exit(1);
				}
			} catch (MissingOptionException e) {
				// TODO Auto-generated catch block
				Options helpOps = new Options();
				helpOps.addOption(new Option("h", "help", false, "Display this message"));
				try {
					CommandLine cmd = parser.parse( helpOps, args);
					
					if (cmd.hasOption("help")) {
						printHelp(options);
					}
				} catch (ParseException e1) {
					// TODO Auto-generated catch block
//				e1.printStackTrace();
				}
				System.err.println(e.getMessage());
				printUsage(options);
//			e.printStackTrace();
			} catch (ParseException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				printUsage(options);
			}
			
			System.out.println("Done!");
			System.exit(0);
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
	}
}
