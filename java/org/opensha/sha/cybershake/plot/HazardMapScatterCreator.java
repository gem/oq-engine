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
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.util.XYZClosestPointFinder;
import org.opensha.commons.util.cpt.CPT;
import org.opensha.sha.cybershake.HazardCurveFetcher;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;

public class HazardMapScatterCreator {
	
	public static final Color BLANK_COLOR = Color.WHITE;
	
	ArrayList<CybershakeSite> sites;
	ArrayList<DiscretizedFuncAPI> funcs;
	ArrayList<Double> vals;
	
	ArrayList<CybershakeSite> allSites = null;
	
	ArrayList<XYZClosestPointFinder> comps = new ArrayList<XYZClosestPointFinder>();
	ArrayList<String> compNames = new ArrayList<String>();
	
	CPT cpt;
	
	HazardCurveFetcher fetcher;
	
	public HazardMapScatterCreator(DBAccess db, ArrayList<Integer> erfIDs, int rupVarScenarioID, int sgtVarID, int imTypeID, CPT cpt, boolean isProbAt_IML, double val) {
		this.cpt = cpt;
		
		fetcher = new HazardCurveFetcher(db, erfIDs, rupVarScenarioID, sgtVarID, imTypeID);
		sites = fetcher.getCurveSites();
		funcs = fetcher.getFuncs();
		
		vals = fetcher.getSiteValues(isProbAt_IML, val);
	}
	
	public void addComparison(String name, String fileName) {
		try {
			comps.add(new XYZClosestPointFinder(fileName));
			compNames.add(name);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public void printScatterCommands(String symbol) {
		for (double val : vals) {
			System.out.println("");
		}
	}
	
	private void printVals() {
		ArrayList<CurveSite> curveSites = new ArrayList<CurveSite>();
		for (int i=0; i<vals.size(); i++) {
			double val = vals.get(i);
			CybershakeSite site = sites.get(i);
			curveSites.add(new CurveSite(site, val));
		}
		Collections.sort(curveSites);
		for (CurveSite cs : curveSites) {
			System.out.println(cs.getSite());
			System.out.println("CyberShake: " + cs.getVal());
			for (int i=0; i<comps.size(); i++) {
				XYZClosestPointFinder comp = comps.get(i);
				System.out.println(compNames.get(i) + ": " + comp.getClosestVal(cs.getSite().lat, cs.getSite().lon));
			}
			System.out.println();
		}
	}
	
	private void printCurves() {
		for (int i=0; i<funcs.size(); i++) {
			DiscretizedFuncAPI func = funcs.get(i);
			CybershakeSite site = sites.get(i);
			
			System.out.println("SITE: " + site);
			System.out.println(func);
			System.out.println();
		}
	}
	
	class CurveSite implements Comparable<CurveSite> {
		CybershakeSite site;
		double val;
		
		public CurveSite(CybershakeSite site, double val) {
			this.site = site;
			this.val = val;
		}

		public int compareTo(CurveSite comp) {
			if (comp.getVal() > this.val)
				return 1;
			else if (comp.getVal() < this.val)
				return -1;
			return 0;
		}

		public CybershakeSite getSite() {
			return site;
		}

		public double getVal() {
			return val;
		}
	}
	
	private static ScatterSymbol getSymbol(CybershakeSite site, ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym) {
		if (symbols == null)
			return defaultSym;
		for (ScatterSymbol symbol : symbols) {
			if (symbol.use(site)) {
				return symbol;
			}
		}
		return defaultSym;
	}
	
	private static double scaleSize(double size, ScatterSymbol symbol) {
//		if (symbol.equals("c"))
//			size = 0.75 * size;
//		else if (symbol.equals("d"))
//			size = 0.85 * size;
		return size * symbol.getScaleFactor();
	}
	
	public static String getGMTColorString(Color color) {
		return "-G" + color.getRed() + "/" + color.getGreen() + "/" + color.getBlue();
	}
	
	private static String getGMTSymbolLine(ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym, CybershakeSite site, CPT cpt, double val, double size) {
		
		ScatterSymbol sym = getSymbol(site, symbols, defaultSym);
		if (sym.getSymbol().equals(ScatterSymbol.SYMBOL_INVISIBLE))
			return null;
		double scaledSize = scaleSize(size, sym);
		
		Color color;
		if (val < 0 || cpt == null) {
			color = BLANK_COLOR;
			scaledSize = scaledSize * 0.5;
		} else {
			color = cpt.getColor((float)val);
		}
		
		String colorStr = getGMTColorString(color);
		String outline = "-W" + (float)(size * 0.09) + "i,255/255/255";
//		String outline = "-W2,255/255/255";
		
		String line = "echo " + site.lon + " " + site.lat + " | ";
		// arg 1: plot region
		// arg 2: plot projection
		// arg 3: ps file
		line += "psxy $1 $2 -S" + sym.getSymbol() + scaledSize + "i " + colorStr + " " + outline + " -O -K >> $3";
		
		return line;
	}
	
	public static String getGMTLabelLine(CybershakeSite site, double fontSize) {
		double x = site.lon + (0.025);
		double y = site.lat;
		double angle = 0;
		String fontno = "1";
		String justify = "LM";
		String text = site.short_name;
		
		String colorStr = getGMTColorString(Color.white);
		
		String line = "echo " + x + " " + y + " " + fontSize + " " + angle + " " + fontno + " " + justify + " " + text +  " | ";
		
		// arg 1: plot region
		// arg 2: plot projection
		// arg 3: ps file
		line += "pstext $1 $2 " + colorStr + " -O -K >> $3";
		
		return line;
	}
	
	private ArrayList<CybershakeSite> getAllSites() {
		if (allSites == null) {
			allSites = fetcher.getAllSites();
		}
		return allSites;
	}
	
	private static void writeInitScriptLines(FileWriter write) throws IOException {
		write.write("#!/bin/bash" + "\n");
		write.write("set -o errexit" + "\n");
		write.write("\n");
	}
	
	public void writeScatterColoredScript(ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym, String script, boolean writeEmptySites, boolean labels) throws IOException {
		FileWriter write = new FileWriter(script);
		
		writeInitScriptLines(write);
		
		double size = 0.18;
		double fontSize = 10;
		
		for (CybershakeSite site : this.getAllSites()) {
			double val = -1d;
			for (int i=0; i<vals.size(); i++) {
				CybershakeSite valSite = sites.get(i);
				if (site.id == valSite.id) {
					val = vals.get(i);
					break;
				}
			}
			if (writeEmptySites || val >=0) {
				String line = getGMTSymbolLine(symbols, defaultSym, site, cpt, val, size);
				
				if (line == null)
					continue;
				
				System.out.println(line);
				write.write(line + "\n");
				
				if (labels) {
					line = this.getGMTLabelLine(site, fontSize);
					System.out.println(line);
					write.write(line + "\n");
				}
			}
		}
		
		write.close();
	}
	
	public void writeScatterMarkerScript(ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym, String script, boolean labels) throws IOException {
		writeScatterMarkerScript(symbols, defaultSym, script, labels, false);
	}

	public void writeScatterMarkerScript(ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym, String script,
			boolean labels, boolean curveSitesOnly) throws IOException {
		writeScatterMarkerScript(symbols, defaultSym, script, labels, curveSitesOnly, 10);
	}
	
	public void writeScatterMarkerScript(ArrayList<ScatterSymbol> symbols, ScatterSymbol defaultSym, String script,
			boolean labels, boolean curveSitesOnly, double fontSize) throws IOException {
		FileWriter write = new FileWriter(script);
		
		writeInitScriptLines(write);
		
		double size = 0.18;
//		double fontSize = 10;
		
		ArrayList<CybershakeSite> sites;
		if (curveSitesOnly)
			sites = this.sites;
		else
			sites = this.getAllSites();
		
		for (CybershakeSite site : sites) {
			
			double val = -1d;
			String line = getGMTSymbolLine(symbols, defaultSym, site, cpt, val, size);
			
			if (line == null)
				continue;
			
			System.out.println(line);
			write.write(line + "\n");
			
			if (labels) {
				line = this.getGMTLabelLine(site, fontSize);
				System.out.println(line);
				write.write(line + "\n");
			}
		}
		
		write.close();
	}
	
	public static void writeScatterMarkerScript(ArrayList<CybershakeSite> sites, ArrayList<ScatterSymbol> symbols,
			ScatterSymbol defaultSym, String script, boolean labels, double fontSize) throws IOException {
		FileWriter write = new FileWriter(script);
		
		writeInitScriptLines(write);
		
		double size = 0.18;
//		double fontSize = 10;
		
		for (CybershakeSite site : sites) {
			
			double val = -1d;
			String line = getGMTSymbolLine(symbols, defaultSym, site, null, val, size);
			
			if (line == null)
				continue;
			
			System.out.println(line);
			write.write(line + "\n");
			
			if (labels) {
				line = getGMTLabelLine(site, fontSize);
				System.out.println(line);
				write.write(line + "\n");
			}
		}
		
		write.close();
	}
	
	public static ArrayList<ScatterSymbol> getCyberShakeSymbols(double scaleFactor) {
		ArrayList<ScatterSymbol> symbols = new ArrayList<ScatterSymbol>();
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_SQUARE, CybershakeSite.TYPE_BROADBAND_STATION, scaleFactor));
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_DIAMOND, CybershakeSite.TYPE_PRECARIOUS_ROCK, scaleFactor * 0.85));
		ScatterSymbol circle = new ScatterSymbol(ScatterSymbol.SYMBOL_CIRCLE, CybershakeSite.TYPE_POI, scaleFactor * 0.75);
		symbols.add(circle);
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_INVERTED_TRIANGLE, CybershakeSite.TYPE_GRID_20_KM, scaleFactor * 0.85));
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_INVERTED_TRIANGLE, CybershakeSite.TYPE_GRID_10_KM, scaleFactor * 0.85));
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_INVERTED_TRIANGLE, CybershakeSite.TYPE_GRID_05_KM, scaleFactor * 0.85));
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_DIAMOND, CybershakeSite.TYPE_PRECARIOUS_ROCK, scaleFactor * 0.85));
		symbols.add(new ScatterSymbol(ScatterSymbol.SYMBOL_INVISIBLE, CybershakeSite.TYPE_TEST_SITE));
		return symbols;
	}
	
	public static ArrayList<ScatterSymbol> getCyberShakeCymbols() {
		return getCyberShakeSymbols(1.0);
	}
	
	public static void main(String args[]) {
		try {
			if (args.length == 0) {
				System.err.println("RUNNING FROM DEBUG MODE!!!!");
				args = new String[6];
				
				args[0] = "34,35";
				args[1] = "3";
				args[2] = "5";
				args[3] = "21";
				args[4] = "/home/kevin/CyberShake/scatterMap/cpt.cpt";
				args[5] = "/home/kevin/CyberShake/scatterMap";
			} else if (args.length != 6) {
				System.err.println("USAGE: HazardMapScatterScreator <erfID(s)> <rupVarScenID> <sgtVarID> <imTypeID> <cptFile> <outPutDir>");
				System.exit(1);
			}
			
			String cptFile = args[4];
			System.out.println("CPT File: " + cptFile);
			CPT cpt = null;
			try {
				cpt = CPT.loadFromFile(new File(cptFile));
			} catch (FileNotFoundException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				System.exit(1);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				System.exit(1);
			}
			DBAccess db = Cybershake_OpenSHA_DBApplication.db;
			
			int rupVarScenID = Integer.parseInt(args[1]);
			System.out.println("Rupture Variation Scenario ID: " + rupVarScenID);
			int sgtVarID = Integer.parseInt(args[2]);
			System.out.println("SGT Variation ID: " + sgtVarID);
			int imTypeID = Integer.parseInt(args[3]);
			System.out.println("IM Type ID: " + imTypeID);
			
			boolean isProbAt_IML = false;
			double val = 0.0004;
			
			String erfStr = args[0];
			erfStr = erfStr.trim();
			ArrayList<Integer> erfIDs = new ArrayList<Integer>();
			for (String id : erfStr.split(",")) {
				int idInt = Integer.parseInt(id);
				erfIDs.add(idInt);
				System.out.println("ERF ID: " + idInt);
			}
			
			HazardMapScatterCreator map = new HazardMapScatterCreator(db, erfIDs, rupVarScenID, sgtVarID, imTypeID, cpt, isProbAt_IML, val);
			
//		map.addComparison("CB 2008", "/home/kevin/CyberShake/scatterMap/base_cb.txt");
//		map.addComparison("BA 2008", "/home/kevin/CyberShake/scatterMap/base_ba.txt");
//		map.printCurves();
//		map.printVals();
			
			ArrayList<ScatterSymbol> symbols = getCyberShakeCymbols();
			ScatterSymbol circle = new ScatterSymbol(ScatterSymbol.SYMBOL_CIRCLE, CybershakeSite.TYPE_POI, 0.75);
			
			boolean writeEmptySites = false;
			boolean labels = true;
			
			String outputDir = args[5];
			if (!outputDir.endsWith(File.separator))
				outputDir += File.separator;
			System.out.println("Output Directory: " + outputDir);
			
			try {
				
				map.writeScatterColoredScript(symbols, circle, outputDir + "scatter.sh", writeEmptySites, labels);
				map.writeScatterMarkerScript(symbols, circle, outputDir + "scatter_mark.sh", labels);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				System.exit(1);
			}
			
			db.destroy();
			System.exit(0);
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
	}
}
